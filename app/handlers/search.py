# -*- coding: utf-8 -*-
'''
Created on 2013-10-27
@summary: main application entrance
@author: YangHaitao
'''

import logging
import os.path
import urllib
import chardet

import tornado.web
from tornado import gen

from db import sqlite
from db.sqlite import DB
from config import CONFIG
from utils.html import ThumbnailItem, add_params_to_url
from utils import index_whoosh
from utils.index_whoosh import IX
from utils import search_whoosh
from base import BaseHandler


LOG = logging.getLogger(__name__)

SEARCH_RESULT_THRESHOLD = 1000

class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_locale = self.get_user_locale()
        # locale = "zh" if user_locale and user_locale.code == "zh_CN" else "en"
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        self.render("search/index.html", 
                    current_nav = "Home", 
                    user = user,
                    scheme = CONFIG["SERVER_SCHEME"],
                    locale = locale)

class SearchHandler(BaseHandler):
    @gen.coroutine
    def process_query(self, typed_q, query, user, locale):
        # get page number
        page_number = self.get_argument("page", "1")
        page_number = int(page_number)
        limits = CONFIG["ITEMS_PER_PAGE"]
        LOG.debug("page_number: %s, limits: %s", page_number, limits)
        result = {}
        if query != "":
            result = yield search_whoosh.search_query_page(IX.ix_html, 
                                                           query, 
                                                           DB.html, 
                                                           page = page_number, 
                                                           limits = limits)
        else:
            result["totalcount"] = 0
            result["result"] = []
        html_num = sqlite.get_html_num_from_db(conn = DB.conn_html)
        html_num_string = self.locale.translate("from") + " %s "%html_num + self.locale.translate("documents")
        search_result_prompt = ""
        if result["totalcount"] < SEARCH_RESULT_THRESHOLD:
            search_result_prompt = self.locale.translate("Found") + \
                                   " %(totalcount)s " + \
                                   self.locale.translate("results")
            search_result_prompt = search_result_prompt%(result) + ", " + html_num_string
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
                                          locale = locale)

    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_locale = self.get_user_locale()
        # locale = "zh" if user_locale and user_locale.code == "zh_CN" else "en"
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        q = (self.get_argument("q", "") ).strip()
        typed_q = q

        query = q
        yield self.process_query(typed_q, query, user, locale)

    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_locale = self.get_user_locale()
        # locale = "zh" if user_locale and user_locale.code == "zh_CN" else "en"
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        q = (self.get_argument("q", "")).strip()
        typed_q = q

        query = q
        yield self.process_query(typed_q, query, user, locale)
