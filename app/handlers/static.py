# -*- coding: utf-8 -*-
'''
Created on 2013-10-19
@summary: static for html get
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
from tornado import gen

from config import CONFIG
from base import BaseHandler

LOG = logging.getLogger(__name__)


def construct_file_path(sha1, source_path):
    file_path = ""
    file_ext = os.path.splitext(source_path)[-1]
    sha1 = sha1.strip()
    if len(sha1) > 4:
        file_path = os.path.join(sha1[:2], sha1[2:4], sha1, source_path)
    else:
        file_path = os.path.join(sha1 + file_ext)
    return file_path

class StaticHandler(BaseHandler):
    """
    url: /static/storage/eb/49/eb490c2ac237a15955adc6e12271c7416da5761a/css.css
    """
    @tornado.web.authenticated
    @gen.coroutine
    def get(self, sha1 = "", source_path = ""):
        user = self.get_current_user_name()
        # n = (self.get_argument("namespace", "")).strip()
        # print n
        # self.write(n)
        # self.render("test/editor_2.html", user = user)
        content_type = self.request.headers.get('Accept')
        # LOG.info("headers: %s", self.request.headers)
        # LOG.info("getstatic content_type: %s"%content_type)
        ext = os.path.splitext(source_path)[-1]
        if sha1 != "":
            if ext.lower() == ".css":
                self.set_header('Content-Type', 'text/css; charset=utf-8')
            elif ext.lower() in [".html", ".shtml", ".htm"]:
                self.set_header('Content-Type', 'text/html; charset=utf-8')
            elif ext.lower() in [".js", ".axd"]:
                self.set_header('Content-Type', 'text/javascript; charset=utf-8')
            elif ext.lower() == ".php":
                self.set_header('Content-Type', 'text/php; charset=utf-8')
            elif ext.lower() == ".json":
                self.set_header('Content-Type', 'application/json; charset=utf-8')
            elif ext.lower() == ".swf":
                self.set_header('Content-Type', 'application/x-shockwave-flash; charset=utf-8')
            elif ext.lower() == ".asc":
                self.set_header('Content-Type', 'text/plain; charset=utf-8')
            else:
                self.set_header('Content-Type', 'image/jpeg; charset=utf-8')
            file_path = construct_file_path(sha1, source_path)
            file_path = os.path.join(CONFIG["STORAGE_STATIC_PATH"], file_path)
            if os.path.exists(file_path):
                with open(file_path, "rb") as fp:
                    self.write(fp.read())