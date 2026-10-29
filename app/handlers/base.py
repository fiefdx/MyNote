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

from config import CONFIG

LOG = logging.getLogger(__name__)

COOKIE_TIME = CONFIG["MAX_AGE_DAYS"]

def bytes_2_unicode(string):
    # In Python 3, get_secure_cookie returns bytes; decode to str.
    if isinstance(string, bytes):
        try:
            return string.decode("utf-8")
        except Exception as e:
            LOG.exception(e)
            return string.decode("utf-8", "replace")
    return str(string)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user", max_age_days = COOKIE_TIME)

    def get_current_user_name(self):
        user = self.get_secure_cookie("user", max_age_days = COOKIE_TIME)
        if user:
            return bytes_2_unicode(user)
        return None

    def get_current_user_key(self):
        user_key = self.get_secure_cookie("user_key", max_age_days = COOKIE_TIME)
        if user_key:
            return bytes_2_unicode(user_key)
        return None

    def get_user_locale(self):
        user_locale = self.get_secure_cookie("user_locale", max_age_days = COOKIE_TIME)
        if user_locale:
            # cookie is bytes under Python 3; tornado.locale.get() needs str.
            return tornado.locale.get(bytes_2_unicode(user_locale))
        return None

class BaseSocketHandler(tornado.websocket.WebSocketHandler):
    def get_ping_interval(self):
        """Send a websocket ping every 30s so connections that died during
        machine sleep / network loss are detected and closed (the browser
        then runs its auto-reconnect logic)."""
        return 30

    def get_ping_timeout(self):
        """Close the connection if no pong arrives within 60s."""
        return 60

    def get_current_user(self):
        return self.get_secure_cookie("user", max_age_days = COOKIE_TIME)

    def get_current_user_name(self):
        user = self.get_secure_cookie("user", max_age_days = COOKIE_TIME)
        if user:
            return bytes_2_unicode(user)
        return None

    def get_current_user_key(self):
        user_key = self.get_secure_cookie("user_key", max_age_days = COOKIE_TIME)
        if user_key:
            return bytes_2_unicode(user_key)
        return None

    def get_user_locale(self):
        user_locale = self.get_secure_cookie("user_locale", max_age_days = COOKIE_TIME)
        if user_locale:
            # cookie is bytes under Python 3; tornado.locale.get() needs str.
            return tornado.locale.get(bytes_2_unicode(user_locale))
        return None
