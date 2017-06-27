# -*- coding: utf-8 -*-
'''
Created on 2017-06-25
@summary: app
@author: YangHaitao
'''

import os
import logging

import tornado.web

from config import CONFIG
import modules.bootstrap as bootstrap
import handlers.search as search
import handlers.view as view
import handlers.login as login
import handlers.static as static
import handlers.note as note
import handlers.rich as rich
import handlers.help as help
import handlers.picture as picture

LOG = logging.getLogger(__name__)

cwd = CONFIG["APP_PATH"]

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
                    (r"/importratenotesajax", note.ImportRateAjaxHandler),
                    (r"/indexnotesajax", note.IndexAjaxHandler),
                    (r"/indexratenotesajax", note.IndexRateAjaxHandler),
                    (r"/rich", rich.RichHandler),
                    (r"/rich/", rich.RichHandler),
                    (r"/rich/websocket", rich.RichSocketHandler),
                    (r"/rich/websocket/", rich.RichSocketHandler),
                    (r"/exportrichnotes", rich.ExportHandler),
                    (r"/deleterichnotes", rich.DeleteHandler),
                    (r"/uploadrichnotesajax", rich.UploadAjaxHandler),
                    (r"/importrichnotesajax", rich.ImportAjaxHandler),
                    (r"/indexrichnotesajax", rich.IndexAjaxHandler),
                    (r"/picture", picture.PictureHandler),
                    (r"/picture/", picture.PictureHandler),
                    (r"/picture/(?P<sha1>[a-fA-F\d]{40})", picture.PictureHandler),
                    (r"/picture/(?P<sha1>[a-fA-F\d]{40})/", picture.PictureHandler),
                    (r"/help", help.HelpHandler),
                    (r"/help/", help.HelpHandler),
                    ]
        settings = dict(template_path = os.path.join(cwd, "templates"),
                        static_path = os.path.join(cwd, "static"),
                        ui_modules = [bootstrap,],
                        debug = CONFIG["APP_DEBUG"],
                        cookie_secret="yhtx4GsTTzuyOP6ja/HpLGFWOK8hI0dwueN+VwQvxVs=",
                        login_url="/login",
                        xsrf_cookies = True)
        tornado.web.Application.__init__(self, handlers, **settings)
