# -*- coding: utf-8 -*-
'''
Created on 2013-10-27
@summary: main application entrance
@author: YangHaitao
'''

import logging

import tornado.web
from tornado import gen

from config import CONFIG
from utils import search_whoosh
from base import BaseHandler
from utils.common import Servers


LOG = logging.getLogger(__name__)

SEARCH_RESULT_THRESHOLD = 1000

class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
        user_locale = self.get_user_locale()
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        self.render("search/index.html",
                    current_nav = "Home",
                    user = user,
                    scheme = CONFIG["SERVER_SCHEME"],
                    functions = CONFIG["FUNCTIONS"],
                    locale = locale,
                    http_proxy = user_info.http_proxy,
                    https_proxy = user_info.https_proxy,
                    socks_proxy = user_info.socks_proxy)

class SearchHandler(BaseHandler):
    @gen.coroutine
    def process_query(self, typed_q, query, user, locale, user_info):
        # get page number
        page_number = self.get_argument("page", "1")
        page_number = int(page_number)
        limits = CONFIG["ITEMS_PER_PAGE"]
        LOG.debug("page_number: %s, limits: %s", page_number, limits)
        result = {}
        if query != "":
            result = yield search_whoosh.search_query_page(Servers.IX_SERVER["HTML"].ix,
                                                           query,
                                                           "HTML",
                                                           page = page_number,
                                                           limits = limits,
                                                           db_html = Servers.DB_SERVER["HTML"])
        else:
            result["totalcount"] = 0
            result["result"] = []
        html_num = Servers.DB_SERVER["HTML"].get_html_num_from_db()
        html_num_string = self.locale.translate("from") + " %s " % html_num + self.locale.translate("documents")
        search_result_prompt = ""
        if result["totalcount"] < SEARCH_RESULT_THRESHOLD:
            search_result_prompt = self.locale.translate("Found") + \
                                   " %(totalcount)s " + \
                                   self.locale.translate("results")
            search_result_prompt = search_result_prompt % (result) + ", " + html_num_string
        else:
            search_result_prompt = self.locale.translate("More than") + \
                                   " %(totalcount)s " + \
                                   self.locale.translate("results") + \
                                   ", " + \
                                   self.locale.translate("please use more specific search terms")
            search_result_prompt = search_result_prompt%(result) + ", " + html_num_string
        self.render("search/result.html", current_nav = "Search",
                                          user = user,
                                          total_count = result["totalcount"],
                                          thumbnails = result["result"],
                                          current_page = page_number,
                                          items_per_page = limits,
                                          typed_search_string = typed_q,
                                          query = query,
                                          search_result_prompt = search_result_prompt,
                                          scheme = CONFIG["SERVER_SCHEME"],
                                          functions = CONFIG["FUNCTIONS"],
                                          locale = locale,
                                          http_proxy = user_info.http_proxy,
                                          https_proxy = user_info.https_proxy,
                                          socks_proxy = user_info.socks_proxy)

    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
        user_locale = self.get_user_locale()
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        q = (self.get_argument("q", "") ).strip()
        typed_q = q

        query = q
        yield self.process_query(typed_q, query, user, locale, user_info)

    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
        user_locale = self.get_user_locale()
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        q = (self.get_argument("q", "")).strip()
        typed_q = q

        query = q
        yield self.process_query(typed_q, query, user, locale, user_info)
