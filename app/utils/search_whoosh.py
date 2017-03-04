# -*- coding: utf-8 -*-
'''
Created on 2013-10-27
@summary: whoosh search
@author: YangHaitao

Modified on 2015-03-08
@summary: for tornado coroutine
@author: YangHaitao
'''

import os
import sys
import json
import os.path
import logging

from tornado import gen

import whoosh
from whoosh import index
from whoosh.filedb.filestore import FileStorage
from whoosh.fields import Schema, ID, TEXT, STORED

from whoosh.qparser import QueryParser 
from whoosh.qparser import MultifieldParser
from whoosh import query
from whoosh.highlight import HtmlFormatter
from whoosh.analysis import CharsetFilter, StemmingAnalyzer
from whoosh.support.charset import accent_map

from config import CONFIG
from utils.html import ThumbnailItem, ThumnailNote, add_params_to_url
from utils.multi_async_tea import MultiProcessNoteTea 
from models.item import NOTE, RICH

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."

LOG = logging.getLogger(__name__)

@gen.coroutine
def search_index_page(index, query, index_name, page, limits, filter = None):
    result = []
    try:
        search_field = {"HTML": ["file_name", "file_content"],
                        "NOTE": ["file_title", "file_content"],
                        "RICH": ["file_title", "file_content"]}
        searcher = index.searcher()
        mparser = MultifieldParser(search_field[index_name], schema = index.schema)
        q = mparser.parse(query)
        result = searcher.search_page(q, page, filter = filter, pagelen = limits)
    except Exception, e:
        LOG.exception(e)
        result = False
    raise gen.Return(result)

@gen.coroutine
def search_index_no_page(index, query, index_name, limits = None, filter = None):
    result = []
    try:
        search_field = {"HTML": ["file_name", "file_content"],
                        "NOTE": ["file_title", "file_content"],
                        "RICH": ["file_title", "file_content"]}
        searcher = index.searcher()
        mparser = MultifieldParser(search_field[index_name], schema = index.schema)
        q = mparser.parse(query)
        result = searcher.search(q, filter = filter, limit = limits)
    except Exception, e:
        LOG.exception(e)
        result = False
    raise gen.Return(result)

@gen.coroutine
def search_query_page(ix, query_string, index_name, page = 0, limits = None, db_html = None):
    result = {"result":[], "totalcount": 0}
    try:
        query_string = query_string
        LOG.debug("Query_string: %s"%query_string)
        hf = HtmlFormatter(tagname="em", classname="match", termclass="term")
        results = yield search_index_page(ix, query_string, index_name, page, limits)
        results.results.formatter = hf
        results.results.fragmenter.charlimit = 100*1024
        results.results.fragmenter.maxchars = 20
        # results.results.fragmenter.surround = 5
        results_len = 0
        if results.results.has_exact_length():
            results_len = len(results)
        LOG.debug("Have %s results:"%results_len)
        results_len = len(results)
        result["totalcount"] = results_len
        LOG.debug("Have %s results:"%results_len)
        results_num = 0
        for hit in results:
            item = ThumbnailItem()
            results_num += 1
            LOG.debug("Result: %s", results_num)
            fields = hit.fields()
            LOG.debug("Doc_id: %s", fields["doc_id"])
            html = db_html.get_html_by_id(fields["doc_id"])
            title = hit.highlights("file_name", text = html.file_name[0:-5])
            item.title = title if title.strip() != "" else html.file_name[0:-5]
            item.title = html.file_name
            item.excerpts = hit.highlights("file_content", top = 5, text = html.file_content)
            item.url = "/view/html/%s"%html.sha1
            item.date_time = html.updated_at
            item.description = html.updated_at[0:19]
            result["result"].append(item)
            yield gen.moment
    except Exception, e:
        LOG.exception(e)
        result = False
    # return result
    raise gen.Return(result)

@gen.coroutine
def search_query_page_note_user(ix, query_string, index_name, user_name, page = 0, limits = None, key = "", db_user = None, db_note = None):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    result = {"result":[], "totalcount": 0}
    try:
        note_books = {}
        user_info = db_user.get_user_from_db(user_name)
        if user_info:
            note_books_tmp = json.loads(user_info.note_books)
            for category in note_books_tmp:
                note_books[category['sha1']] = category['name']
        query_string = query_string
        LOG.debug("Query_string: %s"%query_string)
        hf = HtmlFormatter(tagname="em", classname="match", termclass="term")
        allow_q = query.Term("user_name", user_name)
        # results = search_index(ix, query_string, filter = allow_q)
        # results = yield search_index_no_page(ix, query_string, index_name, limits, filter = allow_q)
        results = yield search_index_page(ix, query_string, index_name, page, limits, filter = allow_q)
        results.results.formatter = hf
        results.results.fragmenter.charlimit = 100*1024
        results.results.fragmenter.maxchars = 30
        # results.results.fragmenter.surround = 5
        results_len = 0
        if results.results.has_exact_length():
            results_len = len(results)
        LOG.debug("Have %s results:"%results_len)
        results_len = len(results)
        result["totalcount"] = results_len
        LOG.debug("Have %s results:"%results_len)
        results_num = 0
        for hit in results:
            results_num += 1
            LOG.debug("Result: %s", results_num)

            fields = hit.fields()
            LOG.debug("Doc_id: %s", fields["doc_id"])
            note = db_note.get_note_by_id(fields["doc_id"], user_name)
            if key != "":
                # note.decrypt(key)
                note = yield multi_process_note_tea.decrypt(note, *(key, ))
            LOG.info("file_title unicode: %s", isinstance(note.file_title, unicode))
            file_title = hit.highlights("file_title", text = note.file_title)
            note_tmp = NOTE()
            note_tmp.id = note.id
            note_tmp.sha1 = note.sha1
            note_tmp.type = note.type
            note_tmp.file_title = file_title if file_title.strip() != "" else note.file_title
            note_tmp.description = hit.highlights("file_title", text = note.file_title) + \
                                   " " + \
                                   hit.highlights("file_content", top = 20, text = note.file_content)
            note_tmp.file_content = note.file_content
            note_tmp.created_at = str(note.created_at)[:19]
            note_tmp.updated_at = str(note.updated_at)[:19]
            note_tmp.type = note_books[note.type]
            result["result"].append(note_tmp.to_dict())
            if results_num == 1:
                result["note"] = note
            yield gen.moment
    except Exception, e:
        LOG.exception(e)
        result = False
    # return result
    raise gen.Return(result)

@gen.coroutine
def search_query_no_page_note_user(ix, query_string, index_name, user_name, limits = None, key = "", db_user = None, db_note = None):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    result = {"result":[], "totalcount": 0}
    try:
        note_books = {}
        user_info = db_user.get_user_from_db(user_name)
        if user_info:
            note_books_tmp = json.loads(user_info.note_books)
            for category in note_books_tmp:
                note_books[category['sha1']] = category['name']
        query_string = query_string
        LOG.debug("Query_string: %s"%query_string)
        hf = HtmlFormatter(tagname="em", classname="match", termclass="term")
        allow_q = query.Term("user_name", user_name)
        # results = search_index(ix, query_string, filter = allow_q)
        results = yield search_index_no_page(ix, query_string, index_name, limits, filter = allow_q)
        results.formatter = hf
        results.fragmenter.charlimit = 100*1024
        results.fragmenter.maxchars = 20
        # results.results.fragmenter.surround = 5
        results_len = 0
        if results.has_exact_length():
            results_len = len(results)
        LOG.debug("Have %s results:"%results_len)
        results_len = len(results)
        result["totalcount"] = results_len
        LOG.debug("Have %s results:"%results_len)
        results_num = 0
        for hit in results:
            results_num += 1
            LOG.debug("Result: %s", results_num)

            fields = hit.fields()
            LOG.debug("Doc_id: %s", fields["doc_id"])
            note = db_note.get_note_by_id(fields["doc_id"], user_name)
            if key != "":
                # note.decrypt(key)
                note = yield multi_process_note_tea.decrypt(note, *(key, ))
            LOG.info("file_title unicode: %s", isinstance(note.file_title, unicode))
            file_title = hit.highlights("file_title", text = note.file_title)
            note_tmp = NOTE()
            note_tmp.id = note.id
            note_tmp.sha1 = note.sha1
            note_tmp.type = note.type
            note_tmp.file_title = file_title if file_title.strip() != "" else note.file_title
            note_tmp.description = hit.highlights("file_title", text = note.file_title) + \
                                   " " + \
                                   hit.highlights("file_content", top = 20, text = note.file_content)
            note_tmp.file_content = note.file_content
            note_tmp.created_at = str(note.created_at)[:19]
            note_tmp.updated_at = str(note.updated_at)[:19]
            note_tmp.type = note_books[note.type]
            result["result"].append(note_tmp.to_dict())
            if results_num == 1:
                result["note"] = note
            yield gen.moment
    except Exception, e:
        LOG.exception(e)
        result = False
    # return result
    raise gen.Return(result)

@gen.coroutine
def search_query_page_rich_user(ix, query_string, index_name, user_name, page = 0, limits = None, key = "", db_user = None, db_rich = None):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    result = {"result":[], "totalcount": 0}
    try:
        note_books = {}
        user_info = db_user.get_user_from_db(user_name)
        if user_info:
            note_books_tmp = json.loads(user_info.rich_books)
            for category in note_books_tmp:
                note_books[category['sha1']] = category['name']
        query_string = query_string
        LOG.debug("Query_string: %s"%query_string)
        hf = HtmlFormatter(tagname="em", classname="match", termclass="term")
        allow_q = query.Term("user_name", user_name)
        LOG.debug("search filter by user_name: %s", user_name)
        # results = search_index(ix, query_string, filter = allow_q)
        # results = yield search_index_no_page(ix, query_string, index_name, limits, filter = allow_q)
        results = yield search_index_page(ix, query_string, index_name, page, limits, filter = allow_q)
        results.results.formatter = hf
        results.results.fragmenter.charlimit = 100*1024
        results.results.fragmenter.maxchars = 30
        results.results.fragmenter.surround = 5
        results_len = 0
        if results.results.has_exact_length():
            results_len = len(results)
        LOG.debug("Have %s rich results:"%results_len)
        results_len = len(results)
        result["totalcount"] = results_len
        LOG.debug("Have %s rich results:"%results_len)
        results_num = 0
        for hit in results:
            results_num += 1
            LOG.debug("Result: %s", results_num)

            fields = hit.fields()
            LOG.debug("Doc_id: %s", fields["doc_id"])
            note = db_rich.get_rich_by_id(fields["doc_id"], user_name)
            if key != "":
                # note.decrypt(key)
                note = yield multi_process_note_tea.decrypt(note, *(key, ))
            file_title = hit.highlights("file_title", text = note.file_title)
            note_tmp = RICH()
            note_tmp.id = note.id
            note_tmp.sha1 = note.sha1
            note_tmp.type = note.type
            note_tmp.file_title = file_title if file_title.strip() != "" else note.file_title
            note_tmp.description = hit.highlights("file_title", text = note.file_title) + \
                                   " " + \
                                   hit.highlights("file_content", text = note.file_content)
            note_tmp.rich_content = note.rich_content
            note_tmp.created_at = str(note.created_at)[:19]
            note_tmp.updated_at = str(note.updated_at)[:19]
            note_tmp.type = note_books[note.type]
            result["result"].append(note_tmp.to_dict())
            if results_num == 1:
                result["note"] = note
            yield gen.moment
    except Exception, e:
        LOG.exception(e)
        result = False
    # return result
    raise gen.Return(result)

@gen.coroutine
def search_query_no_page_rich_user(ix, query_string, index_name, user_name, limits = None, key = "", db_user = None, db_rich = None):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    result = {"result":[], "totalcount": 0}
    try:
        note_books = {}
        user_info = db_user.get_user_from_db(user_name)
        if user_info:
            note_books_tmp = json.loads(user_info.rich_books)
            for category in note_books_tmp:
                note_books[category['sha1']] = category['name']
        query_string = query_string
        LOG.debug("Query_string: %s"%query_string)
        hf = HtmlFormatter(tagname="em", classname="match", termclass="term")
        allow_q = query.Term("user_name", user_name)
        # results = search_index(ix, query_string, filter = allow_q)
        results = yield search_index_no_page(ix, query_string, index_name, limits, filter = allow_q)
        results.formatter = hf
        results.fragmenter.charlimit = 100*1024
        results.fragmenter.maxchars = 30
        results.fragmenter.surround = 5
        results_len = 0
        if results.has_exact_length():
            results_len = len(results)
        LOG.debug("Have %s rich results:"%results_len)
        results_len = len(results)
        result["totalcount"] = results_len
        LOG.debug("Have %s rich results:"%results_len)
        results_num = 0
        for hit in results:
            results_num += 1
            LOG.debug("Result: %s", results_num)

            fields = hit.fields()
            LOG.debug("Doc_id: %s", fields["doc_id"])
            note = db_rich.get_rich_by_id(fields["doc_id"], user_name)
            if key != "":
                # note.decrypt(key)
                note = yield multi_process_note_tea.decrypt(note, *(key, ))
            file_title = hit.highlights("file_title", text = note.file_title)
            note_tmp = RICH()
            note_tmp.id = note.id
            note_tmp.sha1 = note.sha1
            note_tmp.type = note.type
            note_tmp.file_title = file_title if file_title.strip() != "" else note.file_title
            note_tmp.description = hit.highlights("file_title", text = note.file_title) + \
                                   " " + \
                                   hit.highlights("file_content", text = note.file_content)
            note_tmp.rich_content = note.rich_content
            note_tmp.created_at = str(note.created_at)[:19]
            note_tmp.updated_at = str(note.updated_at)[:19]
            note_tmp.type = note_books[note.type]
            result["result"].append(note_tmp.to_dict())
            if results_num == 1:
                result["note"] = note
            yield gen.moment
    except Exception, e:
        LOG.exception(e)
        result = False
    # return result
    raise gen.Return(result)

if __name__ == "__main__":
    import logger
    logger.config_logging(file_name = "whoosh_index.log", 
                          log_level = CONFIG['LOG_LEVEL'], 
                          dir_name = "logs", 
                          day_rotate = False, 
                          when = "D", 
                          interval = 1, 
                          max_size = 20, 
                          backup_count = 5, 
                          console = True)
    LOG.debug("App start")
    LOG.debug("CWD: %s"%cwd)
    LOG.debug("SOURCE: %s"%source_path)
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage: %s QUERY" % sys.argv[0]
        sys.exit(1)
    doc_num = 0
    query_string = str.join(' ', sys.argv[1:])
    query_string = query_string.decode("utf-8")
    LOG.debug("Query_string: %s"%query_string)
    try:
        hf = HtmlFormatter(tagname="em", classname="match", termclass="term")
        ix = get_whoosh_index(index_path, "test")
        allow_q = query.Term("doc_id", "1")
        # results = search_index(ix, query_string, filter = allow_q)
        results = search_index(ix, query_string)
        results.formatter = hf
        results.fragmenter.charlimit = 32*1024
        results.fragmenter.maxchars = 20
        results.fragmenter.surround = 5
        results_len = 0
        if results.has_exact_length():
            results_len = len(results)
        print "Have %s results:"%results_len
        results_num = 0
        for hit in results:
            # print dir(hit)
            results_num += 1
            print ">"*30, " %s "%results_num, "<"*30
            # print hit.matched_terms()
            # print "Doc Num: ", hit.docnum
            # print dir(hit.highlights)
            fields = hit.fields()
            print "Doc_id: ", fields["doc_id"]
            # print "Title: ", fields["title"]
            # print "Content: ", fields["content"]
            print "Highlights Title: ", hit.highlights("title", top = 2)
            print "Highlights Content: ", hit.highlights("content", top = 2)
        print "="*65
        # ix.close()
    except Exception, e:
        LOG.exception(e)
    LOG.debug("Index all file OK!")
