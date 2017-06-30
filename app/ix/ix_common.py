# -*- coding: utf-8 -*-
'''
Created on 2017-03-04
@summary: whoosh index
@author: YangHaitao
'''

import os
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

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."

LOG = logging.getLogger(__name__)


def get_whoosh_index(index_path, index_name = ""):
    result = None
    try:
        if index_name != "":
            sch = {"HTML": Schema(doc_id = ID(unique = True, stored = True),
                                  file_name = TEXT(analyzer = analyzer),
                                  file_content = TEXT(analyzer = analyzer)),
                   "RICH": Schema(doc_id = ID(unique = True, stored = True),
                                  user_name = ID(stored = True),
                                  file_title = TEXT(analyzer = analyzer),
                                  file_content = TEXT(analyzer = analyzer)),
                   "NOTE": Schema(doc_id = ID(unique = True, stored = True),
                                  user_name = ID(stored = True),
                                  file_title = TEXT(analyzer = analyzer),
                                  file_content = TEXT(analyzer = analyzer))
                   }
            schema = sch[index_name]
            index_path = os.path.join(index_path, index_name)
            LOG.debug("Index path: %s", index_path)
            if not os.path.exists(index_path):
                os.makedirs(index_path)
                ix = index.create_in(index_path, schema = schema, indexname = index_name)
                LOG.debug("Create index[%s, %s]", index_path, index_name)
                result = ix
            else:
                flag = index.exists_in(index_path, indexname = index_name)
                if flag == True:
                    ix = index.open_dir(index_path, indexname = index_name)
                    LOG.debug("Open index[%s, %s]", index_path, index_name)
                    result = ix
                else:
                    ix = index.create_in(index_path, schema = schema, indexname = index_name)
                    LOG.debug("Create index[%s, %s]", index_path, index_name)
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
                if index_name == "HTML":
                    writer.update_document(doc_id = unicode(str(item.id)),
                                           file_name = item.file_name,
                                           file_content = item.file_content)
                elif index_name == "NOTE":
                    writer.update_document(doc_id = unicode(str(item.id)),
                                           user_name = item.user_name,
                                           file_title = item.file_title,
                                           file_content = item.file_content)
                elif index_name == "RICH":
                    writer.update_document(doc_id = unicode(str(item.id)),
                                           user_name = item.user_name,
                                           file_title = item.file_title,
                                           file_content = item.file_content)
                else:
                    LOG.error("index_name error: in the update_whoosh_index_doc!")
                writer.commit(merge = merge)
                LOG.debug("Update index[%s] doc_id[%s]", index_name, item.id)
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
                    if index_name == "HTML":
                        writer.update_document(doc_id = unicode(str(item.id)),
                                               file_name = item.file_name,
                                               file_content = item.file_content)
                    elif index_name == "NOTE":
                        writer.update_document(doc_id = unicode(str(item.id)),
                                               user_name = item.user_name,
                                               file_title = item.file_title,
                                               file_content = item.file_content)
                    elif index_name == "RICH":
                        writer.update_document(doc_id = unicode(str(item.id)),
                                               user_name = item.user_name,
                                               file_title = item.file_title,
                                               file_content = item.file_content)
                    else:
                        LOG.error("index_name error: in the update_whoosh_index_doc_num!")
                    LOG.debug("Update index[%s] doc_id[%s]", index_name, item.id)
                    if n == item_num:
                        writer.commit(merge = merge)
                        LOG.info("Commit index[%s] success", index_name)
                        # writer = index.writer()
                        writer = AsyncWriter(index)
                        n = 0
                if n % item_num != 0:
                    s = time.time()
                    writer.commit(merge = merge)
                    ss = time.time()
                    LOG.debug("Commit use %ss", ss - s)
                    LOG.info("Commit index[%s] success", index_name)
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
                    if index_name == "HTML":
                        writer.delete_by_term("doc_id", unicode(str(item.id)))
                    elif index_name == "NOTE":
                        writer.delete_by_term("doc_id", unicode(str(item.id)))
                    elif index_name == "RICH":
                        writer.delete_by_term("doc_id", unicode(str(item.id)))
                    else:
                        LOG.error("index_name error: in the delete_whoosh_index_doc_num!")
                    LOG.debug("Delete index[%s] doc_id[%s]", index_name, item.id)
                    if n == item_num:
                        writer.commit(merge = merge)
                        LOG.info("Commit index[%s] success", index_name)
                        # writer = index.writer()
                        writer = AsyncWriter(index)
                        n = 0
                if n % item_num != 0:
                    writer.commit(merge = merge)
                    LOG.info("Commit index[%s] success", index_name)
                result = True
            except Exception, e:
                LOG.exception(e)
                writer.cancel()
                result = False
    except Exception, e:
        LOG.exception(e)
    return result

def delete_whoosh_index_doc_num_by_user(index, user_name, index_name, merge = False):
    result = False
    try:
        if index != None and index != False:
            # writer = index.writer()
            writer = AsyncWriter(index)
            try:
                if index_name == "NOTE":
                    writer.delete_by_term("user_name", unicode(str(user_name)))
                elif index_name == "RICH":
                    writer.delete_by_term("user_name", unicode(str(user_name)))
                else:
                    LOG.error("index_name error: in the delete_whoosh_index_doc_num_by_user!")
                LOG.debug("Delete index[%s] user[%s]", index_name, user_name)
                writer.commit(merge = merge)
                LOG.info("Commit index[%s] success", index_name)
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
                LOG.debug("Delete index[%s] doc_id[%s]", index_name, doc_id)
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
