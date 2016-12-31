# -*- coding: utf-8 -*-
'''
Created on 2013-10-31
@summary: see an avml file
@author: YangHaitao
'''

import os.path
import logging
import tornado.web

from config import CONFIG
from base import BaseHandler
from db import sqlite
from db.sqlite import DB

LOG = logging.getLogger(__name__)

def get_html_path(file_sha1):
    try:
        html = sqlite.get_html_by_sha1(file_sha1, conn = DB.conn_html)
        file_path = ""
        if html != False and html != None:
            file_path = html.file_path
            file_root_path = CONFIG["STORAGE_ROOT_PATH"]
            file_path = os.path.join(file_root_path, file_path)
            return file_path
        else:
            return ""
    except Exception, e:
        LOG.exception(e)
        LOG.debug("there is some except occur, so return ''.")
        return ""

class ViewHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, sha1):
        try:
            q = sha1
            if len(q) == 0:
                self.render("error.html", error_msg = "The q is empty!")
            else:
                file_path = get_html_path(q)
                if file_path != '':
                    fp = open(file_path, 'rb')
                    content = fp.read()
                    fp.close()
                    self.write(content)
                else:
                    self.write("the file_path is ''.")
                # fp = open(file_path, 'rb')
                # buf = fp.read()
                # self.set_header("Content-Type", "text/xml; charset=UTF-8")Connection:keep-alive
                # self.write(buf)
                # self.finish()
        except Exception, e:
            LOG.exception(e)