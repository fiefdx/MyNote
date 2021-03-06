# -*- coding: utf-8 -*-
'''
Created on 2013-10-27
@summary: login application entrance
@author: YangHaitao

Modified on 2014-05-31
@summary: Add RegisterHandler r_user.user_books
@author: YangHaitao

Modified on 2014-06-04
@summary: Add SettingsHandler
@author: YangHaitao
'''

import json
import logging
import datetime
import dateutil

import tornado.web
from tornado import gen

from config import CONFIG
from base import BaseHandler
from models.item import USER
from utils.user_storage import Storage
from utils import common_utils
from utils.common import Servers

LOG = logging.getLogger(__name__)

COOKIE_TIME = CONFIG["EXPIRES_DAYS"] # day


class LoginHandler(BaseHandler):
    def get(self):
        # self.clear_all_cookies()
        self.render("login/login.html", USER = "")

    def post(self):
        try:
            user = self.get_argument("user", "")
            passwd = self.get_argument("passwd","")
            user_pass = common_utils.sha256sum(passwd)
            user_key = common_utils.md5twice(passwd)
            flag = Servers.DB_SERVER["USER"].get_user_from_db(user)
            if flag != None:
                if flag.user_pass == user_pass:
                    self.set_secure_cookie("user", self.get_argument("user"), expires_days = COOKIE_TIME)
                    self.set_secure_cookie("user_key", user_key, expires_days = COOKIE_TIME)
                    self.set_secure_cookie("user_locale", flag.user_language, expires_days = COOKIE_TIME)
                    LOG.debug("User: %s sign in.", user)
                    self.redirect("/")
                else:
                    self.render("info.html", info_msg = self.locale.translate("Sorry, Invalid User or Invalid Password!"))
            else:
                LOG.debug("User: %s Invalid.", user)
                self.render("info.html", info_msg = self.locale.translate("Sorry, Invalid User!"))
        except Exception, e:
            LOG.exception(e)
            self.render("info.html", info_msg = self.locale.translate("Sorry, Exception Occurs!"))

class RegisterHandler(BaseHandler):
    def get(self):
        self.redirect("/login")

    def post(self):
        try:
            user = self.get_argument("user", "")
            passwd = self.get_argument("passwd", "")
            user_language = self.get_argument("optionsRadios", "en_US")
            user_sha1 = common_utils.sha1sum(user)
            if user != "" and passwd != "":
                r_user = USER()
                r_user.sha1 = user_sha1
                r_user.user_name = user
                r_user.user_pass = common_utils.sha256sum(passwd)
                r_user.note_books = json.dumps([])
                r_user.rich_books = json.dumps([])
                r_user.user_language = user_language
                r_user.register_time = datetime.datetime.now(dateutil.tz.tzlocal())
                storage = Storage(CONFIG["STORAGE_USERS_PATH"], r_user.sha1)
                flag = Servers.DB_SERVER["USER"].get_user_from_db(r_user.user_name)
                if flag is None:
                    flag = storage.init()
                    if flag == True:
                        flag = Servers.DB_SERVER["USER"].save_data_to_db(r_user.to_dict())
                        if flag == True:
                            LOG.debug("register user[%s] success", r_user.user_name)
                            self.render("login/login.html", USER = user)
                        else:
                            LOG.debug("register user[%s] failed: add user error!", r_user.user_name)
                            self.render("info.html", info_msg = self.locale.translate("Sorry, service error[add user error], please retry it!"))
                    else:
                        LOG.debug("register user[%s] failed: init user storage error!", r_user.user_name)
                        self.render("info.html", info_msg = self.locale.translate("Sorry, service error[init user storage error], please retry it!"))
                else:
                    LOG.debug("register user[%s] failed: the user name have been used!", r_user.user_name)
                    self.render("info.html", info_msg = self.locale.translate("Sorry, the user name have been used, please use another one!"))
            else:
                LOG.debug("register user[%s] failed: user name or Password error!", r_user.user_name)
                self.render("info.html", info_msg = self.locale.translate("Sorry, User name or Password error!"))
        except Exception, e:
            LOG.exception(e)
            self.render("error.html", error_msg = self.locale.translate("Sorry, Exception Occurs!"))

class RedirectHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        try:
            user = self.get_current_user_name()
            url = "/home"
            page_name = CONFIG["FUNCTIONS"][0]
            if page_name == "home":
                url = "/home"
            elif page_name == "search":
                url = "/search"
            elif page_name == "note":
                url = "/note"
            elif page_name == "rich":
                url = "/rich"
            else:
                url = "/help"
            self.redirect(url)
        except Exception, e:
            LOG.exception(e)
            self.render("error.html", error_msg = self.locale.translate("Sorry, Exception Occurs!"))

class SettingsHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            old_user_key = self.get_current_user_key()
            user_language = self.get_argument("optionsRadios", "en_US")
            old_passwd = self.get_argument("old_passwd", "")
            new_passwd = self.get_argument("passwd", "")
            passwd_confirm = self.get_argument("passwd_confirm", "")
            http_proxy = self.get_argument("http_proxy", "")
            https_proxy = self.get_argument("https_proxy", "")
            socks_proxy = self.get_argument("socks_proxy", "")
            redirect_to = self.get_argument("redirect_to", "")
            old_user_pass = common_utils.sha256sum(old_passwd)
            user = self.get_current_user_name()
            LOG.debug("user unicode: %s", isinstance(user, unicode))
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            change_passwd_flag = False
            if user_info:
                if user_info.user_pass == old_user_pass and new_passwd == passwd_confirm:
                    user_info.user_pass = common_utils.sha256sum(new_passwd)
                    change_passwd_flag = True
                user_info.user_language = user_language
                user_info.http_proxy = http_proxy
                user_info.https_proxy = https_proxy
                user_info.socks_proxy = socks_proxy
                flag = Servers.DB_SERVER["USER"].save_data_to_db(user_info.to_dict(), mode = "UPDATE")
                if flag:
                    self.set_secure_cookie("user_locale", user_language, COOKIE_TIME)
                    if change_passwd_flag:
                        user_key = common_utils.md5twice(new_passwd)
                        self.set_secure_cookie("user_key", user_key, COOKIE_TIME)
                        if CONFIG["ENCRYPT"]:
                            LOG.info("Update user[%s] all rich notes for update password", user)
                            rich_id_list = []
                            for rich in Servers.DB_SERVER["RICH"].get_rich_from_db_by_user_iter(user):
                                rich_id_list.append(rich.id)
                            for rich_id in rich_id_list:
                                rich = Servers.DB_SERVER["RICH"].get_rich_by_id(rich_id, user)
                                rich.decrypt(old_user_key)
                                rich.encrypt(user_key)
                                flag = Servers.DB_SERVER["RICH"].save_data_to_db(rich.to_dict())
                                if flag:
                                    LOG.info("update user[%s] rich note[%s] success", user, rich.id)
                                else:
                                    LOG.error("update user[%s] rich note[%s] failed", user, rich.id)
                            LOG.info("Update user[%s] all notes for update password", user)
                            note_id_list = []
                            for note in Servers.DB_SERVER["NOTE"].get_note_from_db_by_user_iter(user):
                                note_id_list.append(note.id)
                            for note_id in note_id_list:
                                note = Servers.DB_SERVER["NOTE"].get_note_by_id(note_id, user)
                                note.decrypt(old_user_key)
                                note.encrypt(user_key)
                                flag = Servers.DB_SERVER["NOTE"].save_data_to_db(note.to_dict())
                                if flag:
                                    LOG.info("update user[%s] note[%s] success", user, note.id)
                                else:
                                    LOG.error("update user[%s] note[%s] failed", user, rich.id)
                    LOG.info("Change user[%s] settings success", user)
                else:
                    LOG.error("Change user[%s] settings failed", user)
            self.redirect(redirect_to)
        except Exception, e:
            LOG.exception(e)
            self.redirect("/")

class DeleteUserHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        try:
            user = self.get_current_user_name()
            self.clear_cookie("user")
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            storage = Storage(CONFIG["STORAGE_USERS_PATH"], user_info.sha1)
            flag = Servers.DB_SERVER["USER"].delete_user_from_db(user)
            delete_success = self.locale.translate("Delete the User[") + user + self.locale.translate("] success!") # unicode
            delete_failed = self.locale.translate("Delete the User[") + user + self.locale.translate("] failed!")
            if flag == True:
                flag = storage.rm()
                yield gen.moment
                if flag == True:
                    flag = Servers.DB_SERVER["NOTE"].delete_note_by_user(user)
                    yield gen.moment
                    if flag == True:
                        flag = Servers.DB_SERVER["RICH"].delete_rich_by_user(user)
                        yield gen.moment
                        if flag == True:
                            LOG.debug("Delete the User[%s] success!", user)
                            # do something to reindex
                            self.render("info.html", info_msg = delete_success)
                        else:
                            LOG.debug("Delete the User[%s] success! but, user notes is exists", user)
                            self.render("info.html", info_msg = delete_success)
                    else:
                        LOG.debug("Delete the User[%s] success! but, user notes is exists", user)
                        self.render("info.html", info_msg = delete_success)
                else:
                    LOG.debug("Delete the User[%s] success! but, user storage is exists", user)
                    self.render("info.html", info_msg = delete_success)
            else:
                LOG.debug("Delete the User[%s] failed!", user)
                self.render("info.html", info_msg = delete_failed)
        except Exception, e:
            LOG.exception(e)
            self.render("error.html", error_msg = self.locale.translate("Sorry, Exception Occurs!"))
            
class DeleteCookiesHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.write("Delete all cookies success!")

class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("user_key")
        self.clear_cookie("user_locale")
        self.redirect("/login")

class TestHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.write("Hello, " + name)
