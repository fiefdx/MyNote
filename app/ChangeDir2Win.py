# -*- coding: utf-8 -*-
'''
Created on 2013-11-19 16:25
@summary:  change source dir to dir_win
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

from config import CONFIG

import logger
sys.path.append(CONFIG["APP_PATH"])


PLATFORM = [platform.system(), platform.architecture()[0]]
SYS_ENCODING = sys.stdin.encoding
# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."
LOG = logging.getLogger(__name__)

def change_dir2win(source_dir):
    try:
        file_dir_list = os.listdir(source_dir)
        for i in file_dir_list:
            path = os.path.join(source_dir, i)
            if os.path.isdir(path):
                shutil.move(path, path + "_win")
                LOG.info("Change [%s] to [%s]", path, path + "_win")
    except Exception, e:
        LOG.exception(e)

if __name__ == "__main__":
    logger.config_logging(file_name = "change_dir2win.log", 
                          log_level = CONFIG['LOG_LEVEL'], 
                          dir_name = "logs", 
                          day_rotate = False, 
                          when = "D", 
                          interval = 1, 
                          max_size = 20, 
                          backup_count = 5, 
                          console = True)
    change_dir2win(CONFIG["SOURCE_PATH"])
    LOG.info("Change dirs end.")

