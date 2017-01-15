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
from db.sqlite import DB
from utils import common
import multiprocessing
from utils.multi_async_tea import MultiProcessNoteTea
from utils.processer import ManagerClient

PLATFORM = [platform.system(), platform.architecture()[0]]

# fork service process without jieba for linux, unix
if PLATFORM[0].lower() != "windows":
    crypt_server = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    common.Servers.CRYPT_SERVER = crypt_server
    processer_server = ManagerClient(CONFIG["PROCESS_NUM"])
    common.Servers.PROCESSER_SERVER = processer_server
else:
    import utils.win_compat

from utils import index_whoosh
from utils.index_whoosh import IX
import modules.bootstrap as bootstrap
import handlers.search as search
import handlers.view as view
import handlers.login as login
import handlers.static as static
import handlers.note as note
import handlers.rich as rich
import handlers.help as help
import handlers.picture as picture
import handlers.test as test
import logger

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."

define("host", default = CONFIG["SERVER_HOST"], help = "run bind the given host", type = str)
define("port", default = CONFIG["SERVER_PORT"], help = "run on the given port", type = int)
define("log", default = "MyNote.log", help = "specify the log file", type = str)

LOG = logging.getLogger(__name__)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                    (r"/", login.RedirectHandler),
                    (r"/home", search.IndexHandler),
                    (r"/delete", login.DeleteCookiesHandler),
                    (r"/login", login.LoginHandler),
                    (r"/register", login.RegisterHandler),
                    (r"/settings", login.SettingsHandler),
                    (r"/delete_user", login.DeleteUserHandler),
                    (r"/logout", login.LogoutHandler),
                    (r"/search", search.SearchHandler),
                    (r"/view/html/(?P<sha1>[a-fA-F\d]{40})", view.ViewHandler),
                    (r"/getstatic/(?P<sha1>[a-fA-F\d]{40})/(?P<source_path>.*)", static.StaticHandler),
                    (r"/note", note.NoteHandler),
                    (r"/note/", note.NoteHandler),
                    (r"/note/websocket", note.NoteSocketHandler),
                    (r"/note/websocket/", note.NoteSocketHandler),
                    (r"/deletenotes", note.DeleteHandler),
                    (r"/exportnotes", note.ExportHandler),
                    (r"/uploadnotesajax", note.UploadAjaxHandler),
                    (r"/importnotesajax", note.ImportAjaxHandler),
                    (r"/rich", rich.RichHandler),
                    (r"/rich/", rich.RichHandler),
                    (r"/rich/websocket", rich.RichSocketHandler),
                    (r"/rich/websocket/", rich.RichSocketHandler),
                    (r"/exportrichnotes", rich.ExportHandler),
                    (r"/deleterichnotes", rich.DeleteHandler),
                    (r"/uploadrichnotesajax", rich.UploadAjaxHandler),
                    (r"/importrichnotesajax", rich.ImportAjaxHandler),
                    (r"/picture", picture.PictureHandler),
                    (r"/picture/", picture.PictureHandler),
                    (r"/picture/(?P<sha1>[a-fA-F\d]{40})", picture.PictureHandler),
                    (r"/picture/(?P<sha1>[a-fA-F\d]{40})/", picture.PictureHandler),
                    (r"/help", help.HelpHandler),
                    (r"/help/", help.HelpHandler),
                    (r"/upload", test.TestHandler),
                    (r"/upload/", test.TestHandler),
                    (r"/uploadget", test.TestHandler1),
                    (r"/uploadget/", test.TestHandler1),
                    (r"/websocket", test.SocketHandler),
                    (r"/websocket/", test.SocketHandler),
                    ]
        settings = dict(template_path = os.path.join(cwd, "templates"),
                        static_path = os.path.join(cwd, "static"),
                        ui_modules = [bootstrap,],
                        debug = CONFIG["APP_DEBUG"],
                        cookie_secret="yhtx4GsTTzuyOP6ja/HpLGFWOK8hI0dwueN+VwQvxVs=",
                        login_url="/login",
                        xsrf_cookies = True)
        tornado.web.Application.__init__(self, handlers, **settings)


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

    # init database conn
    _ = DB(init_object = False)
    common.Servers.DB_SERVER = DB
    # init index conn
    _ = IX(init_object = False)
    common.Servers.IX_SERVER = IX
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
                                                    "certfile": os.path.join(cwd, "server_test.crt"),
                                                    "keyfile": os.path.join(cwd, "server_test.key")},
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
