# -*- coding: utf-8 -*-
'''
Created on 2013-11-11
@summary: help handler
@author: YangHaitao
'''

import logging
import tornado

from config import CONFIG
from base import BaseHandler

LOG = logging.getLogger(__name__)

class HelpHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_name()
        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
        user_locale = self.get_user_locale()
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        self.render("help/help.html",
                    current_nav = "Help",
                    user = user,
                    scheme = CONFIG["SERVER_SCHEME"],
                    functions = CONFIG["FUNCTIONS"],
                    locale = locale,
                    http_proxy = user_info.http_proxy,
                    https_proxy = user_info.https_proxy,
                    socks_proxy = user_info.socks_proxy)
