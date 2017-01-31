# -*- coding: utf-8 -*-
'''
Modified on 2014-10-29
@summary:  change get_current_user and get_current_user_key to return unicode
@author: YangHaitao
'''

import logging
import os.path

import tornado.web
import tornado.locale
import tornado.websocket

LOG = logging.getLogger(__name__)

def bytes_2_unicode(string):
    string_unicode = string
    try:
        string_unicode = unicode(string)
    except UnicodeDecodeError, e:
        try:
            string_unicode = string.decode("utf-8")
        except Exception, e:
            LOG.exception(e)
    return string_unicode

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user", max_age_days = 1)

    def get_current_user_name(self):
        user = self.get_secure_cookie("user", max_age_days = 1)
        if user:
            return bytes_2_unicode(user)
        return None

    def get_current_user_key(self):
        user_key = self.get_secure_cookie("user_key", max_age_days = 1)
        if user_key:
            return bytes_2_unicode(user_key)
        return None

    def get_user_locale(self):
        user_locale = self.get_secure_cookie("user_locale", max_age_days = 1)
        if user_locale:
            return tornado.locale.get(user_locale)
        return None

class BaseSocketHandler(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user", max_age_days = 1)

    def get_current_user_name(self):
        user = self.get_secure_cookie("user", max_age_days = 1)
        if user:
            return bytes_2_unicode(user)
        return None

    def get_current_user_key(self):
        user_key = self.get_secure_cookie("user_key", max_age_days = 1)
        if user_key:
            return bytes_2_unicode(user_key)
        return None

    def get_user_locale(self):
        user_locale = self.get_secure_cookie("user_locale", max_age_days = 1)
        if user_locale:
            return tornado.locale.get(user_locale)
        return None