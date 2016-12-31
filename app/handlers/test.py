# -*- coding: utf-8 -*-
'''
Created on 2014-05-28
@summary: test handler
@author: YangHaitao
'''

import os.path
import logging
import tornado


from config import CONFIG
from base import BaseHandler, BaseSocketHandler

LOG = logging.getLogger(__name__)

class TestHandler1(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_name()
        # self.write("This is a Test GET Page!")
        self.render("upload.html")
        # self.render("help/help.html", current_nav = "Help", user = user)

class TestHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user_name()
        LOG.debug("%s", self.request.arguments)
        LOG.debug("%s", self.request.arguments['submit'])
        fname = self.get_argument('file1.name', default = None)
        LOG.debug("file_name: %s", fname)
        fpath = self.get_argument('file1.path', default = None)
        LOG.debug("file_path: %s", fpath)
        test = self.get_argument('test', default = None)
        LOG.debug("test: %s", test)
        # t = self.get_argument('Upload')
        # print t
        self.write("This is a Test POST Page!")

def send_msg(msg, user):
    try:
        if SocketHandler.socket_handlers.has_key(user):
            SocketHandler.socket_handlers[user].write_message(msg)
    except Exception, e:
        LOG.exception(e)
    # for handler in SocketHandler.socket_handlers:
    #     try:
    #         handler.write_message(msg)
    #     except Exception, e:
    #         LOG.exception(e)

class SocketHandler(BaseSocketHandler):
    # socket_handlers = set()
    socket_handlers = {}

    @tornado.web.authenticated
    def open(self):
        user = self.get_current_user_name()
        SocketHandler.socket_handlers[user] = self
        LOG.info("open websocket: %s", user)
        # SocketHandler.socket_handlers.add(self)
        send_msg("Open a websocket", user)
        LOG.info("websocket users: %s", SocketHandler.socket_handlers.keys())

    @tornado.web.authenticated
    def on_close(self):
        user = self.get_current_user_name()
        # SocketHandler.socket_handlers.remove(self)
        SocketHandler.socket_handlers.pop(user)
        LOG.info("close websocket: %s", user)
        LOG.info("websocket users: %s", SocketHandler.socket_handlers.keys())
        # send_msg("Close a websocket", user)

    @tornado.web.authenticated
    def on_message(self, msg):
        user = self.get_current_user_name()
        send_msg(msg, user)
        LOG.info("send msg websocket: %s", user)

