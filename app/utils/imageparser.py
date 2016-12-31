# -*- coding: utf-8 -*-
'''
Created on 2013-10-17 16:34
@summary: import pictures to datebase
@author: YangHaitao

Modified on 2013-11-10
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
from time import localtime,strftime
from multiprocessing import Process as pProcess
from multiprocessing import Queue
import hashlib

import tornado
from tornado import gen

from config import CONFIG
import utils.note_xml as note_xml
from db import sqlite
from db.sqlite import DB
from models.item import PICTURE as PIC
import utils.common_utils as util
import logger

LOG = logging.getLogger(__name__)

def construct_file_path(file_sha1_name, file_name):
    file_path = ""
    file_ext = os.path.splitext(file_name)[1]
    file_sha1_name = file_sha1_name.strip()
    if len(file_sha1_name) > 4:
        file_path = os.path.join(file_sha1_name[:2], file_sha1_name[2:4], file_sha1_name + file_ext)
    else:
        file_path =os.path.join(file_sha1_name + file_ext)
    return file_path

def process_mission( mission_queue, result_queue, exts = None, storage_path = None, user = ""):
    #init log
    date_time = strftime("%Y%m%d_%H%M%S", localtime())
    logger.config_logging(file_name = ("import_image_pid_" + str( os.getpid() ) + '_' + date_time + '.txt'), 
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
                        fpath = os.path.join( mission_one[0], i )
                        LOG.debug("processing %s", fpath)
                        total_count_file += 1
                        fp = open(fpath, "rb")
                        image = fp.read()
                        fp.close()
                        pic = PIC()
                        m = hashlib.sha1(image)
                        m.digest()
                        pic.sha1 = m.hexdigest()
                        pic.imported_at = datetime.datetime.now(dateutil.tz.tzlocal())
                        pic.file_name = util.construct_safe_filename(i.decode("utf-8"))
                        pic.file_path = construct_file_path(pic.sha1, pic.file_name).decode("utf-8")
                        # db_file_path = sqlite.get_db_path(CONFIG["STORAGE_DB_PATH"], db.pic)
                        storage_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], os.path.split(pic.file_path)[0])
                        storage_file_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path)
                        if (not os.path.exists(storage_path)) or (not os.path.isdir(storage_path)):
                            os.makedirs(storage_path)
                        fp = open(storage_file_path, "wb")
                        fp.write(image)
                        fp.close()
                        flag = sqlite.save_data_to_db(pic.to_dict(), db.pic, conn = db.conn_pic)
                        if flag == True:
                            success_processed_count_file += 1
                            LOG.debug("write image to [%s] success"%storage_file_path)
                        else:
                            LOG.debug("write image to [%s] failed"%storage_file_path)
                else:
                    break
            else:
                time.sleep( 0.01 )
        mission_queue.put('mission complete')
        result_queue.put( [ total_count_file, success_processed_count_file ] )
    except Exception, e:
        LOG.exception(e)
        exc = traceback.format_exc()

def mission_generator(source_dir, process_num, queue_size, exts = None, storage_path = None, user = ""):
    try:
        begin_time = datetime.datetime.now()

        total_count_file = 0

        success_processed_count_file = 0

        # normalize the dir path
        if source_dir is not None:
            source_dir = os.path.normpath(source_dir)

        if not os.path.isdir(source_dir):
            LOG.error("%s is not a dir, please check it!", source_dir)
            return  dict({
                "total_files": 0,
                "processed_files": 0,
                "time_elapsed": 0
                })

        #walk the source dir
        mission_queue = Queue( queue_size )
        result_queue = Queue( process_num )
        process_list = []
        for i in range( process_num ):
            p = pProcess( target = process_mission, args = ( mission_queue, result_queue, exts, storage_path, user ) )
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
        exc = traceback.format_exc()

    # conn_postgres.close()
    end_time = datetime.datetime.now()
    time_elasped = end_time - begin_time
    total_in_microseconds = time_elasped.microseconds + (3600 * 24 * time_elasped.days  + time_elasped.seconds) * (10 ** 6)

    return dict({
        "total_files": total_count_file,
        "processed_files": success_processed_count_file,
        "time_elapsed": total_in_microseconds
        })

def parse_images_and_save_database(user_info, user = "", process_num = 1):
    '''
    @summary: parse avmls and save to database
    @result: None
    '''
    images_dir = ""
    if user == "" or process_num == 0:
        LOG.error("The user is empty, or the process_num = 0, so, exit program!")
        sys.exit()
        
    images_import_dir = CONFIG["STORAGE_PICTURES_PATH"]
    images_dir = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "tmp", "import", "rich_notes", "images")
    
    result = mission_generator(images_dir, process_num, 500, exts = None, storage_path = images_import_dir, user = user)
    msg = "total_files: %(total_files)s\n" \
          "processed_files: %(processed_files)s\n" \
          "time_elapsed: %(time_elapsed)s us" %(result)
    LOG.debug(msg)
    return result

if __name__ == '__main__':
    """
    Usage: python ./image2database_local.py --user=user_name --process_num=2 --index=n --merge_index=n
    """
    logger.config_logging(file_name = "log_image2database.txt", 
                          log_level = CONFIG['LOG_LEVEL'], 
                          dir_name = "logs", 
                          day_rotate = False, 
                          when = "D", 
                          interval = 1, 
                          max_size = 20, 
                          backup_count = 5, 
                          console = True)
    argv_n = len(sys.argv)
    if argv_n < 1:
        LOG.error("Missing parameter! So, exit the program now.")
        sys.exit()

    user = ""
    process_num = 1
    index = True
    merge_index = True

    opts, args = getopt.getopt(sys.argv[1:], None, ["user=", "process_num=", "index=", "merge_index="])
    for o, v in opts:
        if o == "--user":
            user = v
            LOG.debug("Param: user = %s"%user)
        elif o == "--process_num":
            process_num = int(v)
            LOG.debug("Param: process_num = %s"%process_num)
        elif o == '--index':
            if v == 'n':
                index = False
            else:
                index = True
            LOG.debug("Param: index = %s"%index)
        elif o == '--merge_index':
            if v == 'n':
                merge_index = False
            else:
                merge_index = True
            LOG.debug("Param: merge_index = %s"%merge_index)

    parse_images_and_save_database(user, process_num)
    LOG.info("Images: import pictures to database success.")
