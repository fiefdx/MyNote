# -*- coding: utf-8 -*-
'''
Created on 2017-03-04
@summary: whoosh index for html
@author: YangHaitao
'''

import logging

import whoosh
from whoosh import index
from whoosh.filedb.filestore import FileStorage
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh.analysis import CharsetFilter, StemmingAnalyzer
from whoosh.support.charset import accent_map
from whoosh.writing import AsyncWriter
import jieba
# jieba.initialize()
from jieba.analyse import ChineseAnalyzer
analyzer = ChineseAnalyzer()

from config import CONFIG
from ix.ix_common import get_whoosh_index, update_whoosh_index_doc, update_whoosh_index_doc_num

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."

LOG = logging.getLogger(__name__)


class IX(object):
    def __init__(self):
        self.name = "HTML"
        self.ix = None
        try:
            self.ix = get_whoosh_index(CONFIG["INDEX_ROOT_PATH"], self.name)
        except Exception, e:
            LOG.info("Init index(%s) failed", self.name)
            LOG.exception(e)

    def close(self):
        try:
            if self.ix:
                self.ix.close()
            LOG.info("Close index(%s) success", self.name)
        except Exception, e:
            LOG.info("Close index(%s) failed", self.name)
            LOG.exception(e)

    def index_all_html_by_one(self, db_html = None, merge = False):
        result = False
        try:
            htmls = db_html.get_html_from_db()
            if htmls != False:
                for html in htmls:
                    flag = update_whoosh_index_doc(self.ix, html, self.name, merge = merge)
                    if flag:
                        LOG.debug("Index html[%s] success", html.file_name)
                    else:
                        LOG.debug("Index html[%s] failed", html.file_name)
                result = True
        except Exception, e:
            LOG.exception(e)
        return result

    def index_all_html_by_num(self, item_num, db_flag = None, db_html = None, merge = False):
        result = False
        try:
            flag = db_flag.update_old_flag(self.name)
            if flag == True:
                flag_time = db_flag.get_flag_from_db(self.name)
                if flag_time != False and flag_time != None:
                    flag = db_flag.update_flag(self.name)
                    if flag == True:
                        htmls_iter = db_html.get_html_by_flag_iter(flag_time)
                        flag = update_whoosh_index_doc_num(self.ix,
                                                           htmls_iter,
                                                           item_num,
                                                           self.name,
                                                           merge = merge)
                        result = flag
        except Exception, e:
            LOG.exception(e)
        return result
