# -*- coding: utf-8 -*-
'''
Created on 2013-11-11
@summary: help handler
@author: YangHaitao
'''

import os.path
import logging
import tornado


from config import CONFIG
from base import BaseHandler

LOG = logging.getLogger(__name__)

class HelpHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user_name()
        user_locale = self.get_user_locale()
        # locale = "zh" if user_locale and user_locale.code == "zh_CN" else "en"
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        self.render("help/help.html", 
                    current_nav = "Help", 
                    user = user,
                    scheme = CONFIG["SERVER_SCHEME"],
                    locale = locale)