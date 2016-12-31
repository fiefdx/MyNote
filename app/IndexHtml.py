# -*- coding: utf-8 -*-
'''
Created on 2013-11-01 22:05
@summary:  index html
@author: YangHaitao
''' 

import sys
import os
import logging
import shutil
import datetime
import time
import dateutil
from dateutil import tz
from time import localtime,strftime
import hashlib
import traceback

from config import CONFIG

import logger
sys.path.append(CONFIG["APP_PATH"])
from utils import index_whoosh
from utils.index_whoosh import IX
import db.sqlite as sqlite
from db.sqlite import DB
import utils.htmlparser as htmlparser
from models.item import HTML


# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."
LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.config_logging(file_name = "html_index.log", 
                          log_level = CONFIG['LOG_LEVEL'], 
                          dir_name = "logs", 
                          day_rotate = False, 
                          when = "D", 
                          interval = 1, 
                          max_size = 20, 
                          backup_count = 5, 
                          console = True)
    db = DB()
    ix = IX()
    index_whoosh.index_all_html_by_num(1000, db = db, ix = ix, merge = True)
    DB.cls_close()
    db.close()
    IX.cls_close()
    ix.close()
    LOG.info("Index htmls end.")