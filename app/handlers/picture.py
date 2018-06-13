# -*- coding: utf-8 -*-
'''
Created on 2013-11-09
@summary: picture get or post
@author: YangHaitao
'''

import os
import sys
import logging
import hashlib
import urllib
import chardet
import shutil
import datetime
import time
import dateutil
from dateutil import tz

import tornado.web

from config import CONFIG
from base import BaseHandler
from models.item import PICTURE as PIC
from utils import common_utils
from utils.common import Servers

LOG = logging.getLogger(__name__)


class PictureHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, sha1 = ""):
        user = self.get_current_user_name()
        if sha1 != "":
            pic = Servers.DB_SERVER["PIC"].get_data_by_sha1(sha1)
            LOG.debug("pic: %s"%pic)
            if pic != False and pic != None:
                fp = open(os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path), "rb")
                ext = os.path.splitext(pic.file_path)[-1]
                if ext.lower() == ".html":
                    self.set_header('Content-Type', 'image/svg+xml; charset=utf-8')
                else:
                    self.set_header('Content-Type', 'image/jpeg; charset=utf-8')
                self.write(fp.read())
        else:
            self.write("error: image sha1 is empty!")

    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_name()
        q = (self.get_argument("up_file", "")).strip()
        LOG.debug("up_file: %s, %s"%(q,type(q)))
        filename = self.request.files['up_file'][0]["filename"]
        filebody = self.request.files['up_file'][0]["body"]
        myfile = { 'name': filename, 'body' : filebody }
        pic = PIC()
        m = hashlib.sha1(myfile['body'])
        m.digest()
        pic.sha1 = m.hexdigest()
        pic.imported_at = datetime.datetime.now(dateutil.tz.tzlocal())
        pic.file_name = myfile['name']
        pic.file_path = common_utils.construct_file_path(pic.sha1, pic.file_name)
        storage_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], os.path.split(pic.file_path)[0])
        storage_file_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path)
        if (not os.path.exists(storage_path)) or (not os.path.isdir(storage_path)):
            os.makedirs(storage_path)
        fp = open(storage_file_path, "wb")
        fp.write(myfile["body"])
        fp.close()
        flag = Servers.DB_SERVER["PIC"].save_data_to_db(pic.to_dict())
        result = "<p id='name'>%s</p><p id='url'>picture/%s</p>"%(pic.file_name, pic.sha1)
        LOG.debug("Post_return: %s"%result)
        self.write(result)