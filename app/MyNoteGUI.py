#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2013-10-27
@summary: main application entrance
@author: YangHaitao
'''

import os
import os.path
import sys
import time
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
import wx

from config import CONFIG, update
from db.sqlite import DB
from utils import common
from threading import Thread
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

TRAY_TOOLTIP = "MyNote"
TRAY_ICON = "./static/favicon.ico"

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

class WebServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.ioloop_instance = None

    def run(self):
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
            http_server = tornado.httpserver.HTTPServer(Application(), no_keep_alive = False)
            LOG.info("Scheme: %s", CONFIG["SERVER_SCHEME"])
        else:
            http_server = tornado.httpserver.HTTPServer(Application(), no_keep_alive = False)
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
            self.ioloop_instance = tornado.ioloop.IOLoop.instance()
            tornado.ioloop.IOLoop.instance().start()
        except Exception, e:
            LOG.exception(e)
        finally:
            LOG.info("IOLoop instance Exit!")

    def close(self):
        deadline = time.time() + common.MAX_WAIT_SECONDS_BEFORE_SHUTDOWN
        LOG.info("Will shutdown in %s seconds ...", common.MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
        def stop_loop():
            now = time.time()
            if now < deadline and (self.ioloop_instance._callbacks or self.ioloop_instance._timeouts):
                self.ioloop_instance.add_timeout(now + 1, stop_loop)
            else:
                self.ioloop_instance.stop()
                LOG.info("MyNote(%s:%s) Shutdown!", CONFIG["SERVER_HOST"], CONFIG["SERVER_PORT"])

        stop_loop()

def restart_program():
    """
    Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function.
    """
    common.sig_thread_handler(signal.SIGINT, None)
    python = sys.executable
    LOG.debug("restart cmd: %s, %s", python, sys.argv)
    fp = open(os.path.join(CONFIG["PID_PATH"], "application.pid"), "wb")
    fp.write("")
    fp.close()
    os.execl(python, python, * sys.argv)

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id = item.GetId())
    menu.AppendItem(item)
    return item


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.preference = None
        # self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Preference', self.on_preference)
        create_menu_item(menu, 'Restart', self.on_restart)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        # print 'Tray icon was left-clicked.'
        pass

    def on_preference(self, event):
        # print 'on Preference'
        w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        if not self.preference:
            self.preference = PreferenceFrame("Preference", (w / 2 - 90, h / 2 - 140), (180, 280))
            self.preference.Show()

    def on_restart(self, event):
        # print 'on Restart'
        restart_program()

    def on_exit(self, event):
        common.sig_thread_handler(signal.SIGINT, None)
        wx.CallAfter(self.Destroy)
        self.frame.Close()

class PreferenceFrame(wx.Frame):
    def __init__(self, title, pos, size):
        wx. Frame.__init__(self, None, -1, title, pos, size, style = wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)
        # self.panel = wx.Panel(self, -1)
        self.ch_bind_local = None
        self.ch_encrypt = None
        self.ch_server_scheme = None
        self.te_server_port = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.set_checkbox()
        self.set_choice()
        self.set_textctrl()
        self.set_button()
        self.SetSizer(self.sizer)
        self.Layout()

    def set_checkbox(self):
        self.ch_bind_local = wx.CheckBox(self, -1, "BIND LOCAL", (35, 40), (145, 20))
        self.ch_bind_local.SetValue(CONFIG["BIND_LOCAL"]) 
        self.ch_encrypt = wx.CheckBox(self, -1, "ENCRYPT", (35, 40), (145, 20))
        self.ch_encrypt.SetValue(CONFIG["ENCRYPT"]) 
        box = self.MakeStaticBoxSizer("Options", [self.ch_bind_local, self.ch_encrypt])
        self.sizer.Add(box, 0, wx.ALL, 10)

    def set_choice(self):
        self.ch_server_scheme = wx.Choice(self, -1, (85, 18), choices = ["https", "http"])
        self.ch_server_scheme.SetStringSelection(CONFIG["SERVER_SCHEME"])
        box = self.MakeStaticBoxSizer("Scheme", [self.ch_server_scheme])
        self.sizer.Add(box, 0, wx.ALL, 10)

    def set_textctrl(self):
        self.te_server_port = wx.TextCtrl(self, -1, str(CONFIG["SERVER_PORT"]))
        sizer = wx.FlexGridSizer(cols = 2, hgap = 6, vgap = 6)
        sizer.AddMany([self.te_server_port])
        box = self.MakeStaticBoxSizer("Server Port", [sizer])
        self.sizer.Add(box, 0, wx.ALL, 10)

    def set_button(self):
        self.save_button = wx.Button(self, -1, label = "Save")
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.save_button)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.save_button, 0, wx.RIGHT | wx.BOTTOM)
        self.sizer.Add(sizer, 0, wx.ALIGN_CENTER)

    def MakeStaticBoxSizer(self, boxlabel, items):
        box = wx.StaticBox(self, -1, boxlabel)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        for item in items:
            sizer.Add(item, 0, wx.ALL, 2)
        return sizer

    def OnSave(self, event):
        values = {}
        if self.ch_bind_local:
            values["BIND_LOCAL"] = self.ch_bind_local.GetValue()
        if self.ch_encrypt:
            values["ENCRYPT"] = self.ch_encrypt.GetValue()
        if self.ch_server_scheme:
            values["SERVER_SCHEME"] = ["https", "http"][self.ch_server_scheme.GetCurrentSelection()]
        if self.te_server_port:
            try:
                v = int(self.te_server_port.GetValue())
                values["SERVER_PORT"] = v
            except Exception, e:
                LOG.exception(e)
        update(**values)
        self.Destroy()

    def OnQuit(self, event):
        self.Close()

class App(wx.App):
    def OnInit(self):
        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


if __name__ == "__main__":
    if PLATFORM[0].lower() == "windows":
        multiprocessing.freeze_support()
    should_start_new = True
    PID = ""
    pid_file_path = os.path.join(CONFIG["PID_PATH"], "application.pid")
    if os.path.exists(pid_file_path) and os.path.isfile(pid_file_path):
        fp = open(pid_file_path, "rb")
        PID = fp.read()
        fp.close()
    try:
        if PID != "":
            os.kill(int(PID), 0)
            should_start_new = False
    except Exception, e:
        LOG.exception(e)
        LOG.info("PID: %s do not exists")
    if should_start_new:
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
        webserver = WebServer()
        common.Servers.WEB_SERVER = webserver
        signal.signal(signal.SIGTERM, common.sig_thread_handler)
        signal.signal(signal.SIGINT, common.sig_thread_handler)
        webserver.daemon = True
        webserver.start()
        try:
            # app = wx.PySimpleApp()
            # app = wx.App()
            app = App(False)
            # print help(app.MainLoop)
            # TaskBarIcon()
            app.MainLoop()
            # print "test"
        except Exception, e:
            LOG.exception(e)
        LOG.info("MyNote Exit!")
    else:
        LOG.info("MyNote Process exists!")
