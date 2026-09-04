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
    PROCESSER_SERVER = None

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
        for n in Servers.DB_SERVER:
            Servers.DB_SERVER[n].close()
            LOG.info("Stop db[%s] server!", Servers.DB_SERVER[n].name)
    if Servers.IX_SERVER:
        for n in Servers.IX_SERVER:
            Servers.IX_SERVER[n].close()
            LOG.info("Stop ix[%s] server!", Servers.IX_SERVER[n].name)
    if Servers.CRYPT_SERVER:
        Servers.CRYPT_SERVER.close()
        LOG.info("Stop encrypt & decrypt server!")
    if Servers.PROCESSER_SERVER:
        Servers.PROCESSER_SERVER.close()
        LOG.info("Stop processer server!")
    if Servers.WEB_SERVER:
        Servers.WEB_SERVER.close()
        LOG.info("Stop web server!")
    LOG.info("Will shutdown in %s seconds ...", MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.current()
    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

    def stop_loop():
        # Tornado 6 / asyncio IOLoop has no _callbacks/_timeouts attributes, so
        # just give in-flight requests MAX_WAIT_SECONDS and then stop the loop.
        io_loop.stop()
        LOG.info("MyNote(%s:%s) Shutdown!", CONFIG["SERVER_HOST"], CONFIG["SERVER_PORT"])

    io_loop.add_timeout(deadline, stop_loop)

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
        for n in Servers.DB_SERVER:
            Servers.DB_SERVER[n].close()
            LOG.info("Stop db[%s] server!", Servers.DB_SERVER[n].name)
    if Servers.IX_SERVER:
        for n in Servers.IX_SERVER:
            Servers.IX_SERVER[n].close()
            LOG.info("Stop ix[%s] server!", Servers.IX_SERVER[n].name)
    if Servers.CRYPT_SERVER:
        Servers.CRYPT_SERVER.close()
        LOG.info("Stop encrypt & decrypt server!")
    if Servers.PROCESSER_SERVER:
        Servers.PROCESSER_SERVER.close()
        LOG.info("Stop processer server!")
    if Servers.WEB_SERVER:
        Servers.WEB_SERVER.close()
        LOG.info("Stop web server!")

def sig_handler(sig, frame):
    LOG.warning("Caught signal: %s", sig)
    # Under Python 3 / Tornado 6 (asyncio), add_callback() from a signal handler
    # does NOT reliably wake the event loop; add_callback_from_signal() is the
    # documented way to schedule a callback from within a signal handler.
    tornado.ioloop.IOLoop.current().add_callback_from_signal(shutdown)

def sig_thread_handler(sig, frame):
    LOG.warning("Caught signal: %s", sig)
    shutdown_thread()
