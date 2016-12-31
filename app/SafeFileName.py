# -*- coding: utf-8 -*-
'''
Created on 2013-11-15 16:19
@summary:  convert html's filename to safe filename
@author: YangHaitao
''' 

import sys
import os
import re
import platform
import logging
import shutil
import datetime
import time
import dateutil
from dateutil import tz
from time import localtime,strftime
import multiprocessing
from multiprocessing import Process as pProcess
from multiprocessing import Queue
import hashlib
import chardet
import traceback

from config import CONFIG

import logger
sys.path.append(CONFIG["APP_PATH"])
import db.sqlite as sqlite
from db.sqlite import DB
import utils.htmlparser as htmlparser
import utils.common_utils as util
from models.item import HTML

PLATFORM = [platform.system(), platform.architecture()[0]]

if PLATFORM[0].lower() == "windows":
    import utils.win_compat

SYS_ENCODING = sys.stdin.encoding
# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."
LOG = logging.getLogger(__name__)


def process_mission( mission_queue, result_queue, db_file_path, exts = None, storage_path = None, sys_encoding = "utf-8" ):
    #init log, attention no NOSET imported!!!
    date_time = strftime("%Y%m%d_%H%M%S", localtime())
    logger.config_logging(file_name = ("safe_pid_" + str(os.getpid()) + '_' + date_time + '.log'), 
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
                        fpath = os.path.join(mission_one[0], i)
                        fpath = fpath.decode(sys_encoding)
                        LOG.debug("Processing %s", fpath)
                        total_count_file += 1
                        file_dir, ext = os.path.splitext(fpath)
                        file_dir = file_dir + '_files'
                        b_need_process = False

                        if exts is not None and len(exts) > 0:
                            # check ext
                            if ext in exts:
                                b_need_process = True
                            else:
                                LOG.debug("[%s] 's ext [%s] is not allowed to be processed, so i will discard it now.", fpath, ext)
                                b_need_process = False
                        else:
                            b_need_process = True
                        if b_need_process:
                            fp = open(fpath, 'rb')
                            html_content = fp.read()
                            fp.close()
                            m = hashlib.sha1(html_content)
                            m.digest()
                            file_sha1 = m.hexdigest().decode("utf-8") # unicode
                            file_name = os.path.split(fpath)[1] # unicode
                            LOG.debug("Old file name: %s", file_name)
                            new_file_name = file_sha1 + os.path.splitext(file_name)[1] # unicode
                            LOG.debug("New file name: %s", new_file_name)
                            new_file_dir = os.path.splitext(new_file_name)[0] + '_files' # unicode
                            LOG.debug("New file dir: %s", new_file_dir)
                            if file_name != new_file_name:
                                new_content = htmlparser.html_decode_unicode(html_content) # unicode
                                new_content = htmlparser.html_change_src(new_content, file_name, os.path.split(file_dir)[1], new_file_dir) #unicode
                                success_processed_count_file += 1
                                if os.path.exists(file_dir) and os.path.isdir(file_dir):
                                    new_file_dir_path = os.path.join(os.path.split(fpath)[0], new_file_dir)
                                    shutil.move(file_dir, new_file_dir_path)
                                    change_list = util.safe_dir_filename(new_file_dir_path)
                                    new_content = htmlparser.html_change_multi_src(new_content, change_list)
                                fp = open(fpath, 'wb')
                                fp.write(new_content.encode("utf-8"))
                                fp.close()
                                os.rename(fpath, os.path.join(os.path.split(fpath)[0], new_file_name))
                            else:
                                LOG.debug("Old [%s] equal New[%s]", file_name, new_file_name)
                else:
                    break
            else:
                time.sleep(0.01)
        mission_queue.put('mission complete')
        result_queue.put([total_count_file, success_processed_count_file])
    except Exception, e:
        LOG.exception(e)

def mission_generator(source_dir, process_num, queue_size, db_file_path, exts = None, storage_path = None):
    try:
        begin_time = datetime.datetime.now()
        total_count_file = 0
        success_processed_count_file = 0
        # normalize the dir path
        if source_dir is not None:
            source_dir = os.path.normpath(source_dir)

        if not os.path.isdir(source_dir):
            LOG.error("%s is not a dir, please check it!", source_dir.decode(sys.stdin.encoding))
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
            p = pProcess(target = process_mission, args = (mission_queue, result_queue, db_file_path, exts, storage_path, SYS_ENCODING))
            p.start()
            process_list.append(p)
        n = len('_files')
        for root, dirs, files in os.walk(source_dir):
            if files != []:
                if dirs != []:
                    # LOG.debug(dirs)
                    tmp_dirs = []
                    tmp_excess_dirs = []
                    tmp_files = []
                    tmp_excess_files = []
                    # clean dirs
                    for i in dirs:
                        if ((i[:-n] + '.shtml') in files) or \
                           ((i[:-n] + '.html') in files) or \
                           ((i[:-n] + '.htm') in files) or \
                           ((i[:-n] + '.SHTML') in files) or \
                           ((i[:-n] + '.HTML') in files) or \
                           ((i[:-n] + '.HTM') in files):
                            tmp_dirs.append(i)
                            # dirs.remove(i)
                            LOG.debug('tmp_dirs add the dir: %s'%(i.decode(sys.stdin.encoding),))
                        else:
                            tmp_excess_dirs.append(i)
                            LOG.debug('tmp_excess_dirs add the dir: %s'%(i.decode(sys.stdin.encoding),))
                    for i in tmp_dirs:
                        dirs.remove(i)
                        LOG.debug('dirs remove the dir: %s'%(i.decode(sys.stdin.encoding),))
                    for i in tmp_excess_dirs:
                        if '_files' in i:
                            dirs.remove(i)
                            LOG.debug('dirs remove the dir: %s'%(i.decode(sys.stdin.encoding),))
                    # clean files
                    for i in files:
                        if ('.html' in i) or \
                           ('.HTML' in i) or \
                           ('.htm' in i) or \
                           ('.HTM' in i) or \
                           ('.shtml' in i) or \
                           ('.SHTML' in i):
                            tmp_files.append(i)
                            LOG.debug('tmp_files add the file: %s'%(i.decode(sys.stdin.encoding),))
                        else:
                            tmp_excess_files.append(i)
                            LOG.debug('tmp_excess_files add the file: %s'%(i.decode(sys.stdin.encoding),))
                    for i in tmp_excess_files:
                        files.remove(i)
                        LOG.debug('files remove the file: %s'%(i.decode(sys.stdin.encoding),))
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
        mission_queue.put('mission complete')
        for i in process_list:
            i.join()
        for i in range(process_num):
            tmp = result_queue.get()
            total_count_file += tmp[0]
            success_processed_count_file += tmp[1]
    except Exception, e:
        LOG.exception(e)
        # exc = traceback.format_exc()
        # print 'mission_generator :\n',exc

    end_time = datetime.datetime.now()
    time_elasped = end_time - begin_time
    total_in_microseconds = time_elasped.microseconds + (3600 * 24 * time_elasped.days  + time_elasped.seconds) * (10 ** 6)

    return dict({
        "total_files": total_count_file,
        "processed_files": success_processed_count_file,
        "time_elapsed": total_in_microseconds
        })

def rename_htmls(process_num = None):
    '''
    @summary: parse htmls and save to database
    @result: None
    '''
    htmls_dir = CONFIG["SOURCE_PATH"]
    LOG.debug("HTML SOURCE PATH: %s"%htmls_dir.decode(sys.stdin.encoding))
    db = DB()
    db_file_path = sqlite.get_db_path(CONFIG["STORAGE_DB_PATH"], db.html)
    LOG.debug("HTML DB FILE PATH: %s"%db_file_path)
    storage_path = CONFIG['STORAGE_ROOT_PATH']
    LOG.debug("HTML STORAGE ROOT PATH: %s"%storage_path)
    process_num = process_num if process_num != None else CONFIG["PROCESS_NUM"]
    result = mission_generator(htmls_dir, 
                               process_num, 
                               500, 
                               db_file_path, 
                               exts = [".html", ".HTML", ".htm", ".HTM", ".shtml", ".SHTML"], 
                               storage_path = storage_path)
    msg = "total_files: %(total_files)s\n" \
          "processed_files: %(processed_files)s\n" \
          "time_elapsed: %(time_elapsed)s" %(result)
    LOG.debug(msg)

if __name__ == "__main__":
    if PLATFORM[0].lower() == "windows":
        multiprocessing.freeze_support()
    logger.config_logging(file_name = "safe_filename.log", 
                          log_level = CONFIG['LOG_LEVEL'], 
                          dir_name = "logs", 
                          day_rotate = False, 
                          when = "D", 
                          interval = 1, 
                          max_size = 20, 
                          backup_count = 5, 
                          console = True)
    rename_htmls(4)
    # file_name = "30分钟3300%性能提升——python+memcached网页优化小记 | observer专栏杂记_files.html"
    # print construct_safe_filename(file_name)
    LOG.info("Convert htmls end.")

