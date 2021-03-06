# -*- coding: utf-8 -*-
'''
Created on 2017-03-04
@summary: whoosh index for notes
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
from ix.ix_common import delete_whoosh_index_doc_num_by_user, delete_whoosh_index_doc

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."

LOG = logging.getLogger(__name__)


class IX(object):
    def __init__(self):
        self.name = "NOTE"
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

    def index_all_note_by_num_flag(self, item_num, key = "", db_flag = None, db_note = None, merge = False):
        result = False
        try:
            flag = db_flag.update_old_flag(self.name)
            if flag == True:
                flag_time = db_flag.get_flag_from_db(self.name)
                if flag_time != False and flag_time != None:
                    flag = db_flag.update_flag(self.name)
                    if flag == True:
                        notes_iter = db_note.get_note_by_flag_iter(flag_time)
                        flag = update_whoosh_index_doc_num(self.ix,
                                                           notes_iter,
                                                           item_num,
                                                           self.name,
                                                           key = key,
                                                           merge = merge)
                        result = flag
        except Exception, e:
            LOG.exception(e)
        return result

    def index_all_note_by_num(self, item_num, key = "", db_note = None, merge = False):
        result = False
        try:
            notes_iter = db_note.get_note_from_db_iter()
            flag = update_whoosh_index_doc_num(self.ix,
                                               notes_iter,
                                               item_num,
                                               self.name,
                                               key = key,
                                               merge = merge)
            result = flag
        except Exception, e:
            LOG.exception(e)
        return result

    def index_all_note_by_num_user(self, item_num, user_name, key = "", db_note = None, merge = False):
        result = False
        try:
            notes_iter = db_note.get_note_from_db_by_user_iter(user_name)
            flag = update_whoosh_index_doc_num(self.ix,
                                               notes_iter,
                                               item_num,
                                               self.name,
                                               key = key,
                                               merge = merge)
            result = flag
        except Exception, e:
            LOG.exception(e)
        return result

    def index_note_by_id(self, doc_id, user_name, key = "", db_note = None, merge = False):
        result = False
        try:
            note = db_note.get_note_by_id(doc_id, user_name)
            flag = update_whoosh_index_doc(self.ix, note, self.name, key = key, merge = merge)
            result = flag
        except Exception, e:
            LOG.exception(e)
        return result

    def index_delete_note_by_id(self, doc_id, user_name, merge = False):
        result = False
        try:
            flag = delete_whoosh_index_doc(self.ix, doc_id, self.name, merge = merge)
            result = flag
        except Exception, e:
            LOG.exception(e)
        return result

    def index_delete_note_by_user(self, user_name, merge = False):
        result = False
        try:
            result = delete_whoosh_index_doc_num_by_user(self.ix,
                                                         user_name,
                                                         self.name,
                                                         merge = merge)
        except Exception, e:
            LOG.exception(e)
        return result
