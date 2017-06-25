#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2013-10-27
@summary: main application entrance
@author: YangHaitao
'''

import os
import os.path
import signal
import logging
import platform

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.locale
import tornado.netutil
from tornado.options import define, options

from config import CONFIG
from db.db_html import DB as HTML_DB
from db.db_rich import DB as RICH_DB
from db.db_note import DB as NOTE_DB
from db.db_pic import DB as PIC_DB
from db.db_user import DB as USER_DB
from db.db_flag import DB as FLAG_DB
from ix.ix_html import IX as HTML_IX
from ix.ix_rich import IX as RICH_IX
from ix.ix_note import IX as NOTE_IX
from utils import common
import multiprocessing
from utils.multi_async_tea import MultiProcessNoteTea
from utils.processer import ManagerClient
from app import Application

PLATFORM = [platform.system(), platform.architecture()[0]]

# fork service process without jieba for linux, unix
if PLATFORM[0].lower() != "windows":
    crypt_server = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    common.Servers.CRYPT_SERVER = crypt_server
    processer_server = ManagerClient(CONFIG["PROCESS_NUM"])
    common.Servers.PROCESSER_SERVER = processer_server
else:
    import utils.win_compat

import logger

cwd = CONFIG["APP_PATH"]

define("host", default = CONFIG["SERVER_HOST"], help = "run bind the given host", type = str)
define("port", default = CONFIG["SERVER_PORT"], help = "run on the given port", type = int)
define("log", default = CONFIG["LOG_FILE_NAME"], help = "specify the log file", type = str)

LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    if PLATFORM[0].lower() == "windows":
        multiprocessing.freeze_support()
    PID = str(os.getpid())
    fp = open(os.path.join(CONFIG["PID_PATH"], "application.pid"), "wb")
    fp.write(PID)
    fp.close()
    tornado.options.parse_command_line()
    logger.config_logging(file_name = options.log,
                          log_level = CONFIG['LOG_LEVEL'],
                          dir_name = "logs",
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)

    # init database conns
    common.Servers.DB_SERVER = {"HTML": HTML_DB(),
                                "RICH": RICH_DB(),
                                "NOTE": NOTE_DB(),
                                "PIC": PIC_DB(),
                                "USER": USER_DB(),
                                "FLAG": FLAG_DB()}
    # init index conns
    common.Servers.IX_SERVER = {"HTML": HTML_IX(),
                                "RICH": RICH_IX(),
                                "NOTE": NOTE_IX()}
    # create service process for windows
    if PLATFORM[0].lower() == "windows":
        crypt_server = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
        common.Servers.CRYPT_SERVER = crypt_server
        processer_server = ManagerClient(CONFIG["PROCESS_NUM"])
        common.Servers.PROCESSER_SERVER = processer_server

    tornado.locale.load_translations(os.path.join(cwd, "translations"))
    if CONFIG["SERVER_SCHEME"].lower() == "https":
        http_server = tornado.httpserver.HTTPServer(Application(),
                                                    no_keep_alive = False,
                                                    ssl_options = {
                                                    "certfile": os.path.join(cwd, "keys", "server.crt"),
                                                    "keyfile": os.path.join(cwd, "keys", "server.key")},
                                                    max_buffer_size = CONFIG["MAX_BUFFER_SIZE"])
        LOG.info("Scheme: %s", CONFIG["SERVER_SCHEME"])
    elif CONFIG["SERVER_SCHEME"].lower() == "http":
        http_server = tornado.httpserver.HTTPServer(Application(),
                                                    no_keep_alive = False,
                                                    max_buffer_size = CONFIG["MAX_BUFFER_SIZE"])
        LOG.info("Scheme: %s", CONFIG["SERVER_SCHEME"])
    else:
        http_server = tornado.httpserver.HTTPServer(Application(),
                                                    no_keep_alive = False,
                                                    max_buffer_size = CONFIG["MAX_BUFFER_SIZE"])
        LOG.warning("Scheme: http ignore SERVER_SCHEME")
    LOG.info("MAX_BUFFER_SIZE: %sM", CONFIG["MAX_BUFFER_SIZE"] / 1024 / 1024)
    common.Servers.HTTP_SERVER = http_server
    # http_server.listen(options.port)
    if CONFIG["APP_DEBUG"] == True:
        http_server.listen(options.port)
        LOG.info("Listen: localhost:%s", options.port)
    else:
        if CONFIG["BIND_LOCAL"] == True:
            http_server.bind(options.port, address = "127.0.0.1")
        else:
            http_server.listen(options.port)
            LOG.info("Listen: localhost:%s", options.port)
        http_server.start(num_processes = 1)
    try:
        signal.signal(signal.SIGTERM, common.sig_handler)
        signal.signal(signal.SIGINT, common.sig_handler)
        tornado.ioloop.IOLoop.instance().start()
    except Exception, e:
        LOG.exception(e)
    finally:
        LOG.info("MyNote Exit!")
