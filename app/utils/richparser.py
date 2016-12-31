# -*- coding: utf-8 -*-
'''
Created on 2013-11-08 20:06
@summary:  parse note and import datebase
@author: YangHaitao

Modified on 2014-06-11
@summary:  change for add note description and encrypt and decrypt
@author: YangHaitao
''' 

import sys
import os
import getopt
import logging
import shutil
import datetime
import time
import multiprocessing
import dateutil
from dateutil import tz
from time import localtime,strftime
from multiprocessing import Process as pProcess
from multiprocessing import Queue
import hashlib
import chardet

from config import CONFIG
from db import sqlite
from db.sqlite import DB
from utils import note_xml
from models.item import RICH
from utils import common_utils
from utils import htmlparser
import logger

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."
LOG = logging.getLogger(__name__)


def process_mission( mission_queue, result_queue, db_file_path, exts = None, storage_path = None, key = "", old_key = "", user = ""):
    #init log
    date_time = strftime("%Y%m%d_%H%M%S", localtime())
    logger.config_logging(file_name = ("import_rich_pid_" + str( os.getpid() ) + '_' + date_time + '.log'), 
                          log_level = CONFIG['LOG_LEVEL'], 
                          dir_name = "logs", 
                          day_rotate = False, 
                          when = "D", 
                          interval = 1, 
                          max_size = 20, 
                          backup_count = 5, 
                          console = True)
    LOG = logging.getLogger(__name__)
    db = DB()
    try:
        total_count_file = 0
        success_processed_count_file = 0
        while True:
            if mission_queue.empty() == False:
                mission_one = mission_queue.get()
                if mission_one != 'mission complete':
                    # [1] is files [0] is root
                    for i in mission_one[1]:
                        if ".json" not in i:
                            fpath = os.path.join( mission_one[0], i )
                            LOG.debug("Processing [%s]", fpath)
                            total_count_file += 1
                            note = note_xml.get_rich_note_from_xml(xml_path = fpath)
                            if old_key != "":
                                note.decrypt(old_key, decrypt_description = False)
                            note.description = common_utils.get_description_text(note.file_content, CONFIG["NOTE_DESCRIPTION_LENGTH"])
                            note.user_name = user
                            if note.version == "" or note.version == "0.1":
                                note_content = note.rich_content
                                note_content, images = htmlparser.get_rich_content(note_content)
                                note.images = images
                            if key != "":
                                note.encrypt(key)
                            # LOG.debug("Note_dict: %s", note_dict)
                            # note_dict["user_name"] = user
                            # note_dict["id"] = ""
                            note_dict = note.to_dict()
                            if note_dict["version"] == "":
                                # type is unicode
                                note_dict["type"] = common_utils.sha1sum(note_dict["type"])
                            flag = sqlite.save_data_to_db(note_dict, db.rich, mode = "INSERT", conn = db.conn_rich)
                            if flag == True:
                                LOG.debug("write rich note to database success")
                                target = ""
                                note = sqlite.get_rich_by_sha1(note_dict["sha1"], user, conn = db.conn_rich)
                                if storage_path != None:
                                    target = os.path.join(storage_path, note_dict["type"], str(note.id))
                                    shutil.copyfile(fpath, target)
                                    success_processed_count_file += 1
                                    LOG.debug("copy rich note[%s] to [%s] success", fpath, target)
                                else:
                                    LOG.error("copy rich note[%s] to user[%s] failed", fpath, user)
                            else:
                                LOG.debug("write rich note to database failed")
                else:
                    break
            else:
                time.sleep( 0.01 )
        mission_queue.put('mission complete')
        result_queue.put( [ total_count_file, success_processed_count_file ] )
    except Exception, e:
        LOG.exception(e)

def mission_generator(source_dir, process_num, queue_size, db_file_path, exts = None, storage_path = None, key = "", old_key = "", user = ""):
    try:
        begin_time = datetime.datetime.now()
        total_count_file = 0
        success_processed_count_file = 0

        # normalize the dir path
        if source_dir is not None:
            source_dir = os.path.normpath(source_dir)

        if not os.path.isdir(source_dir):
            LOG.error("[%s] is not a dir, please check it!", source_dir)
            return  dict({
                "total_files": 0,
                "processed_files": 0,
                "time_elapsed": 0
                })

        #walk the source dir
        mission_queue = Queue(queue_size)
        result_queue = Queue(process_num)
        process_list = []
        for i in range(process_num):
            p = pProcess(target = process_mission, args = (mission_queue, result_queue, db_file_path, exts, storage_path, key, old_key, user))
            p.start()
            process_list.append( p )
        for root, dirs, files in os.walk(source_dir):
            if files != []:
                files_len = len(files)
                if files_len >= process_num:
                    mission_len = int(files_len/process_num)
                    for i in xrange(process_num):
                        while mission_queue.full() == True:
                            time.sleep( 0.01 )
                        if i != (process_num - 1):
                            mission_queue.put([root, files[i*mission_len:(i+1)*mission_len]])
                        else:
                            mission_queue.put([root, files[i*mission_len:]])
                else:
                    while mission_queue.full() == True:
                        time.sleep( 0.01 )
                    mission_queue.put([root, files])
                LOG.debug(root)
                # while mission_queue.full() == True:
                #     time.sleep( 0.01 )
                # mission_queue.put( [ root, files ] )
                # LOG.debug(root)
        mission_queue.put( 'mission complete' )
        for i in process_list:
            i.join()
        for i in range( process_num ):
            tmp = result_queue.get()
            total_count_file += tmp[0]
            success_processed_count_file += tmp[1]
    except Exception, e:
        LOG.exception(e)

    end_time = datetime.datetime.now()
    time_elasped = end_time - begin_time
    total_in_microseconds = time_elasped.microseconds + (3600 * 24 * time_elasped.days  + time_elasped.seconds) * (10 ** 6)

    return dict({
        "total_files": total_count_file,
        "processed_files": success_processed_count_file,
        "time_elapsed": total_in_microseconds
        })