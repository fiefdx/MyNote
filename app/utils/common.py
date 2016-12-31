# -*- coding: utf-8 -*-
'''
Created on 2015-03-07
@summary: common utilities
@author: YangHaitao
'''
import os
import time
import json
import logging

import tornado.ioloop

from config import CONFIG

LOG = logging.getLogger(__name__)
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3

class Servers(object):
    HTTP_SERVER = None
    DB_SERVER = None
    IX_SERVER = None
    RICH_SERVER = None
    NOTE_SERVER = None
    CRYPT_SERVER = None
    TORNADO_INSTANCE = None
    WEB_SERVER = None

def shutdown():
    LOG.info("Stopping MyNote(%s:%s)", CONFIG["SERVER_HOST"], CONFIG["SERVER_PORT"])
    if Servers.HTTP_SERVER:
        Servers.HTTP_SERVER.stop()
        LOG.info("Stop http server!")
    if Servers.RICH_SERVER:
        Servers.RICH_SERVER.close()
        LOG.info("Stop rich server!")
    if Servers.NOTE_SERVER:
        Servers.NOTE_SERVER.close()
        LOG.info("Stop note server!")
    if Servers.DB_SERVER:
        Servers.DB_SERVER.cls_close()
        LOG.info("Stop db server!")
    if Servers.IX_SERVER:
        Servers.IX_SERVER.cls_close()
        LOG.info("Stop ix server!")
    if Servers.CRYPT_SERVER:
        Servers.CRYPT_SERVER.close()
        LOG.info("Stop encrypt & decrypt server!")
    if Servers.WEB_SERVER:
        Servers.WEB_SERVER.close()
        LOG.info("Stop web server!")
    LOG.info("Will shutdown in %s seconds ...", MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()
    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN
 
    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            LOG.info("MyNote(%s:%s) Shutdown!", CONFIG["SERVER_HOST"], CONFIG["SERVER_PORT"])

    stop_loop()

def shutdown_thread():
    LOG.info("Stopping MyNote(%s:%s)", CONFIG["SERVER_HOST"], CONFIG["SERVER_PORT"])
    if Servers.HTTP_SERVER:
        Servers.HTTP_SERVER.stop()
        LOG.info("Stop http server!")
    if Servers.RICH_SERVER:
        Servers.RICH_SERVER.close()
        LOG.info("Stop rich server!")
    if Servers.NOTE_SERVER:
        Servers.NOTE_SERVER.close()
        LOG.info("Stop note server!")
    if Servers.DB_SERVER:
        Servers.DB_SERVER.cls_close()
        LOG.info("Stop db server!")
    if Servers.IX_SERVER:
        Servers.IX_SERVER.cls_close()
        LOG.info("Stop ix server!")
    if Servers.CRYPT_SERVER:
        Servers.CRYPT_SERVER.close()
        LOG.info("Stop encrypt & decrypt server!")
    if Servers.WEB_SERVER:
        Servers.WEB_SERVER.close()
        LOG.info("Stop web server!")

def sig_handler(sig, frame):
    LOG.warning("Caught signal: %s", sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)

def sig_thread_handler(sig, frame):
    LOG.warning("Caught signal: %s", sig)
    shutdown_thread()