# -*- coding: utf-8 -*-
'''
Created on 2013-10-27
@summary: whoosh index
@author: YangHaitao

Modified on 2014-06-06
@summary: add decrypt and encrypt for note index
@author: YangHaitao

Modified on 2015-03-03
@summary: add IX class for singleton mode
@author: YangHaitao

Modified on 2017-03-04
@summary: will be deprecated
@author: YangHaitao
'''

import os
import sys
import os.path
import time
import logging
import shutil
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

from db import sqlite
from db.sqlite import DB
from config import CONFIG

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."

LOG = logging.getLogger(__name__)


class IX(object):
    html = "HTML"
    rich = "RICH"
    note = "NOTE"
    IX_NAMES = ["html", "rich", "note"]

    ix_html = None
    ix_rich = None
    ix_note = None
    IX_INDEXS = ["ix_html", "ix_rich", "ix_note"]

    def __init__(self, init_object = True):
        for n, ix_index_attr in enumerate(IX.IX_INDEXS):
            try:
                if hasattr(IX, ix_index_attr) and getattr(IX, ix_index_attr) == None:
                    setattr(IX, 
                            ix_index_attr, 
                            get_whoosh_index(CONFIG["INDEX_ROOT_PATH"], 
                                             getattr(IX, IX.IX_NAMES[n])))
                    LOG.info("Init %s success", IX.IX_INDEXS[n])
                else:
                    LOG.info("Inited %s success", IX.IX_INDEXS[n])
            except Exception, e:
                LOG.info("Init %s failed", IX.IX_INDEXS[n])
                LOG.exception(e)
        if init_object:
            self.ix_html = get_whoosh_index(CONFIG["INDEX_ROOT_PATH"], IX.html)
            self.ix_rich = get_whoosh_index(CONFIG["INDEX_ROOT_PATH"], IX.rich)
            self.ix_note = get_whoosh_index(CONFIG["INDEX_ROOT_PATH"], IX.note)
        else:
            self.ix_html = None
            self.ix_rich = None
            self.ix_note = None

    @classmethod
    def content(cls):
        return "IX: ix_html: %s, ix_rich: %s, ix_note: %s" % (cls.ix_html, 
                                                              cls.ix_rich, 
                                                              cls.ix_note)

    @classmethod
    def cls_close(cls):
        for n, ix_index_attr in enumerate(cls.IX_INDEXS):
            try:
                if hasattr(cls, ix_index_attr) and getattr(cls, ix_index_attr):
                    getattr(cls, ix_index_attr).close()
                    setattr(cls, ix_index_attr, None)
                LOG.info("Close %s success", ix_index_attr)
            except Exception, e:
                LOG.info("Close %s failed", ix_index_attr)
                LOG.exception(e)

    def close(self):
        for ix_index_attr in IX.IX_INDEXS:
            try:
                if hasattr(self, ix_index_attr) and getattr(self, ix_index_attr):
                    getattr(self, ix_index_attr).close()
                LOG.info("Close %s success", ix_index_attr)
            except Exception, e:
                LOG.info("Close %s failed", ix_index_attr)
                LOG.exception(e)

def get_whoosh_index(index_path, index_name = ""):
    result = None
    try:
        if index_name != "":
            sch = {DB.html: Schema(doc_id = ID(unique = True, stored = True), 
                                   file_name = TEXT(analyzer = analyzer), 
                                   file_content = TEXT(analyzer = analyzer)), 
                   DB.rich: Schema(doc_id = ID(unique = True, stored = True), 
                                   user_name = ID(stored = True), 
                                   file_title = TEXT(analyzer = analyzer), 
                                   file_content = TEXT(analyzer = analyzer)), 
                   DB.note: Schema(doc_id = ID(unique = True, stored = True), 
                                   user_name = ID(stored = True), 
                                   file_title = TEXT(analyzer = analyzer), 
                                   file_content = TEXT(analyzer = analyzer))
                   }
            schema = sch[index_name]
            index_path = os.path.join(index_path, index_name)
            LOG.debug("Index path: %s"%index_path)
            if not os.path.exists(index_path):
                os.makedirs(index_path)
                ix = index.create_in(index_path, schema = schema, indexname = index_name)
                LOG.debug("Create index[%s, %s]"%(index_path, index_name))
                result = ix
            else:
                flag = index.exists_in(index_path, indexname = index_name)
                if flag == True:
                    ix = index.open_dir(index_path, indexname = index_name)
                    LOG.debug("Open index[%s, %s]"%(index_path, index_name))
                    result = ix
                else:
                    ix = index.create_in(index_path, schema = schema, indexname = index_name)
                    LOG.debug("Create index[%s, %s]"%(index_path, index_name))
                    result = ix
        else:
            LOG.warning("Lost index name, so return None!")
    except Exception, e:
        LOG.exception(e)
        result = False
    return result

def update_whoosh_index_doc(index, item, index_name, key = "", merge = False):
    result = False
    try:
        if index != None and index != False:
            try:
                if key != "":
                    item.decrypt(key)
                # writer = index.writer()
                writer = AsyncWriter(index)
                if index_name == DB.html:
                    writer.update_document(doc_id = unicode(str(item.id)), 
                                           file_name = item.file_name, 
                                           file_content = item.file_content)
                elif index_name == DB.note:
                    writer.update_document(doc_id = unicode(str(item.id)), 
                                           user_name = item.user_name, 
                                           file_title = item.file_title, 
                                           file_content = item.file_content)
                elif index_name == DB.rich:
                    writer.update_document(doc_id = unicode(str(item.id)), 
                                           user_name = item.user_name, 
                                           file_title = item.file_title, 
                                           file_content = item.file_content)
                else:
                    LOG.error("index_name error: in the update_whoosh_index_doc!")
                writer.commit(merge = merge)
                LOG.debug("Update index[%s] doc_id[%s]"%(index_name, item.id))
                result = True
            except Exception, e:
                LOG.exception(e)
                writer.cancel()
                result = False
    except Exception, e:
        LOG.exception(e)
    return result

def update_whoosh_index_doc_num(index, item_iter, item_num, index_name, key = "", merge = False):
    result = False
    try:
        if index != None and index != False:
            n = 0
            # writer = index.writer()
            writer = AsyncWriter(index)
            try:
                for item in item_iter:
                    n += 1
                    if key != "":
                        item.decrypt(key)
                    if index_name == DB.html:
                        writer.update_document(doc_id = unicode(str(item.id)), 
                                               file_name = item.file_name, 
                                               file_content = item.file_content)
                    elif index_name == DB.note:
                        writer.update_document(doc_id = unicode(str(item.id)), 
                                               user_name = item.user_name, 
                                               file_title = item.file_title, 
                                               file_content = item.file_content)
                    elif index_name == DB.rich:
                        writer.update_document(doc_id = unicode(str(item.id)), 
                                               user_name = item.user_name, 
                                               file_title = item.file_title, 
                                               file_content = item.file_content)
                    else:
                        LOG.error("index_name error: in the update_whoosh_index_doc_num!")
                    LOG.debug("Update index[%s] doc_id[%s]"%(index_name, item.id))
                    if n == item_num:
                        writer.commit(merge = merge)
                        LOG.info("Commit index[%s] success."%index_name)
                        # writer = index.writer()
                        writer = AsyncWriter(index)
                        n = 0
                if n % item_num != 0:
                    s = time.time()
                    writer.commit(merge = merge)
                    ss = time.time()
                    LOG.debug("Commit use %ss", ss - s)
                    LOG.info("Commit index[%s] success."%index_name)
                result = True
            except Exception, e:
                LOG.exception(e)
                writer.cancel()
                result = False
        else:
            LOG.error("index object is False or None!")
    except Exception, e:
        LOG.exception(e)
    return result

def delete_whoosh_index_doc_num(index, item_iter, item_num, index_name, merge = False):
    result = False
    try:
        if index != None and index != False:
            n = 0
            # writer = index.writer()
            writer = AsyncWriter(index)
            try:
                for item in item_iter:
                    n += 1
                    if index_name == DB.html:
                        writer.delete_by_term("doc_id", unicode(str(item.id)))
                    elif index_name == DB.note:
                        writer.delete_by_term("doc_id", unicode(str(item.id)))
                    elif index_name == DB.rich:
                        writer.delete_by_term("doc_id", unicode(str(item.id)))
                    else:
                        LOG.error("index_name error: in the delete_whoosh_index_doc_num!")
                    LOG.debug("Delete index[%s] doc_id[%s]"%(index_name, item.id))
                    if n == item_num:
                        writer.commit(merge = merge)
                        LOG.info("Commit index[%s] success."%index_name)
                        # writer = index.writer()
                        writer = AsyncWriter(index)
                        n = 0
                if n % item_num != 0:
                    writer.commit(merge = merge)
                    LOG.info("Commit index[%s] success."%index_name)
                result = True
            except Exception, e:
                LOG.exception(e)
                writer.cancel()
                result = False
    except Exception, e:
        LOG.exception(e)
    return result

def delete_whoosh_index_doc_num_by_user(index, user_name, item_num, index_name, merge = False):
    result = False
    try:
        if index != None and index != False:
            # writer = index.writer()
            writer = AsyncWriter(index)
            try:
                if index_name == DB.note:
                    writer.delete_by_term("user_name", unicode(str(user_name)))
                elif index_name == DB.rich:
                    writer.delete_by_term("user_name", unicode(str(user_name)))
                else:
                    LOG.error("index_name error: in the delete_whoosh_index_doc_num_by_user!")
                LOG.debug("Delete index[%s] user[%s]"%(index_name, user_name))
                writer.commit(merge = merge)
                LOG.info("Commit index[%s] success."%index_name)
                result = True
            except Exception, e:
                LOG.exception(e)
                writer.cancel()
                result = False
    except Exception, e:
        LOG.exception(e)
    return result

def delete_whoosh_index_doc(index, doc_id, index_name, merge = False):
    result = False
    try:
        if index != None and index != False:
            try:
                # writer = index.writer()
                writer = AsyncWriter(index)
                writer.delete_by_term("doc_id", doc_id)
                writer.commit(merge = merge)
                LOG.debug("Delete index[%s] doc_id[%s]"%(index_name, doc_id))
                result = True
            except Exception, e:
                LOG.exception(e)
                writer.cancel()
                result = False
    except Exception, e:
        LOG.exception(e)
    return result

def delete_whoosh_index(index_path, index_name):
    result = False
    try:
        index_path = os.path.join(index_path, index_name)
        if os.path.exists(index_path) and os.path.isdir(index_path):
            shutil.rmtree(index_path)
            result = True
        else:
            result = True
    except Exception, e:
        LOG.exception(e)
    return result

#
# index for html
#

def index_all_html_by_one(db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        htmls = sqlite.get_html_from_db(conn = db.conn_html)
        if htmls != False:
            for html in htmls:
                flag = update_whoosh_index_doc(ix.ix_html, html, db.html, merge = merge)
                if flag:
                    LOG.debug("Index html[%s] success."%html.file_name)
                else:
                    LOG.debug("Index html[%s] failed."%html.file_name)
            result = True
    except Exception, e:
        LOG.exception(e)
    return result

def index_all_html_by_num(item_num, db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        flag = sqlite.update_old_flag(db.html, conn = db.conn_flag)
        if flag == True:
            flag_time = sqlite.get_flag_from_db(db.html, conn = db.conn_flag)
            if flag_time != False and flag_time != None:
                flag = sqlite.update_flag(db.html, conn = db.conn_flag)
                if flag == True:
                    htmls_iter = sqlite.get_html_by_flag_iter(flag_time, 
                                                              conn = db.conn_html)
                    flag = update_whoosh_index_doc_num(ix.ix_html, 
                                                       htmls_iter, 
                                                       item_num, 
                                                       db.html, 
                                                       merge = merge)
                    result = flag
    except Exception, e:
        LOG.exception(e)
    return result

#
# index for note
#

def index_all_note_by_num_flag(item_num, key = "", db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        flag = sqlite.update_old_flag(db.note, conn = db.conn_flag)
        if flag == True:
            flag_time = sqlite.get_flag_from_db(db.note, conn = db.conn_flag)
            if flag_time != False and flag_time != None:
                flag = sqlite.update_flag(db.note, conn = db.conn_flag)
                if flag == True:
                    notes_iter = sqlite.get_note_by_flag_iter(flag_time, 
                                                              conn = db.conn_note)
                    flag = update_whoosh_index_doc_num(ix.ix_note, 
                                                       notes_iter, 
                                                       item_num, 
                                                       db.note, 
                                                       key = key, 
                                                       merge = merge)
                    result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_all_note_by_num(item_num, key = "", db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        notes_iter = sqlite.get_note_from_db_iter(conn = db.conn_note)
        flag = update_whoosh_index_doc_num(ix.ix_note, 
                                           notes_iter, 
                                           item_num, 
                                           db.note, 
                                           key = key, 
                                           merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_all_note_by_num_user(item_num, user_name, key = "", db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        notes_iter = sqlite.get_note_from_db_by_user_iter(user_name, 
                                                          conn = db.conn_note)
        flag = update_whoosh_index_doc_num(ix.ix_note, 
                                           notes_iter, 
                                           item_num, 
                                           db.note, 
                                           key = key, 
                                           merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_note_by_id(doc_id, user_name, key = "", db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        note = sqlite.get_note_by_id(doc_id, user_name, conn = db.conn_note)
        flag = update_whoosh_index_doc(ix.ix_note, note, db.note, key = key, merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_delete_note_by_id(doc_id, user_name, db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        flag = delete_whoosh_index_doc(ix.ix_note, doc_id, db.note, merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_delete_note_by_user(item_num, user_name, db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        result = delete_whoosh_index_doc_num_by_user(ix.ix_note,
                                                     user_name,
                                                     item_num,
                                                     db.note,
                                                     merge = merge)
    except Exception, e:
        LOG.exception(e)
    return result

#
# index for rich note
#

def index_all_rich_by_num_flag(item_num, key = "", db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        flag = sqlite.update_old_flag(db.rich, conn = db.conn_flag)
        if flag == True:
            flag_time = sqlite.get_flag_from_db(db.rich, conn = db.conn_flag)
            if flag_time != False and flag_time != None:
                flag = sqlite.update_flag(db.rich, conn = db.conn_flag)
                if flag == True:
                    notes_iter = sqlite.get_rich_by_flag_iter(flag_time, 
                                                              conn = db.conn_rich)
                    flag = update_whoosh_index_doc_num(ix.ix_rich, 
                                                       notes_iter, 
                                                       item_num, 
                                                       db.rich, 
                                                       key = key, 
                                                       merge = merge)
                    result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_all_rich_by_num(item_num, key = "", db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        notes_iter = sqlite.get_rich_from_db_iter(conn = db.conn_rich)
        flag = update_whoosh_index_doc_num(ix.ix_rich, 
                                           notes_iter, 
                                           item_num, 
                                           db.rich, 
                                           key = key, 
                                           merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_all_rich_by_num_user(item_num, user_name, key = "", db = None, ix = None, merge = False):
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        notes_iter = sqlite.get_rich_from_db_by_user_iter(user_name, 
                                                          conn = db.conn_rich)
        flag = update_whoosh_index_doc_num(ix.ix_rich, 
                                           notes_iter, 
                                           item_num, 
                                           db.rich, 
                                           key = key, 
                                           merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_rich_by_id(doc_id, user_name, key = "", db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        note = sqlite.get_rich_by_id(doc_id, user_name, conn = db.conn_rich)
        flag = update_whoosh_index_doc(ix.ix_rich, note, db.rich, key = key, merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_delete_rich_by_id(doc_id, user_name, db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        flag = delete_whoosh_index_doc(ix.ix_rich, doc_id, db.rich, merge = merge)
        result = flag
    except Exception, e:
        LOG.exception(e)
    return result

def index_delete_rich_by_user(item_num, user_name, db = None, ix = None, merge = False):
    result = False
    if db == None:
        db = DB
    if ix == None:
        ix = IX
    try:
        result = delete_whoosh_index_doc_num_by_user(ix.ix_rich,
                                                     user_name,
                                                     item_num,
                                                     db.rich,
                                                     merge = merge)
    except Exception, e:
        LOG.exception(e)
    return result
