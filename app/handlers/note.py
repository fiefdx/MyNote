# -*- coding: utf-8 -*-
'''
Created on 2013-11-04
@summary: note handler
@author: YangHaitao

Modified on 2014-05-30
@summary: add websocket handler
@author: YangHaitao

Modified on 2014-06-05
@summary: change post/get method to websocket method and add category operation
@author: YangHaitao

Modified on 2014-06-09
@summary: change import and export functions
@author: YangHaitao

Modified on 2014-09-02
@summary: add notes_list when user_key == ""
@author: YangHaitao

Modified on 2014-09-03
@summary: add clear user_notes_path code
@author: YangHaitao
'''

import os.path
import logging
import shutil
import time
import datetime
import dateutil
import StringIO
import json

import tornado.web
from tornado import gen

from db import sqlite
from db.sqlite import DB
from config import CONFIG
from utils import index_whoosh
from utils.index_whoosh import IX
from utils import search_whoosh
from base import BaseHandler, BaseSocketHandler
from utils.archive import Archive
from models.item import NOTE
from utils import common_utils
from utils.multi_async_tea import MultiProcessNoteTea
from utils.multi_async_note_import import MultiProcessNoteImport


LOG = logging.getLogger(__name__)

NOTE_NUM_PER_FETCH = 20


@gen.coroutine
def create_note_file(storage_users_path, user, user_sha1, note, key = "", key1 = ""):
    note_path = os.path.join(storage_users_path, user_sha1, "notes", note.type)
    note_file_path = os.path.join(storage_users_path, user_sha1, "notes", note.type, note.sha1)
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    if not os.path.exists(note_path):
        os.makedirs(note_path)
        LOG.info("create user[%s] path[%s]", user, note_path)
    if key != "":
        # note.decrypt(key)
        note = yield multi_process_note_tea.decrypt(note, *(key, ))
    if key1 != "":
        # note.encrypt(key1)
        note = yield multi_process_note_tea.encrypt(note, *(key1, ))
    fp = open(note_file_path, 'wb')
    doc = note.to_xml()
    doc.write(fp, xml_declaration=True, encoding='utf-8', pretty_print=True)
    fp.close()

def create_category_info(storage_users_path, user_info, category):
    file_path = os.path.join(storage_users_path, user_info.sha1, "notes", "category.json")
    fp = open(file_path, 'wb')
    if category["name"] == "All":
        fp.write(user_info.note_books)
    else:
        fp.write(json.dumps([category]))
    fp.close()
    LOG.info("create user[%s] category.json[%s]", user_info.user_name, file_path)

class NoteHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        user_locale = self.get_user_locale()
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        option = (self.get_argument("option", "")).strip()
        note_id = (self.get_argument("id", "")).strip()
        if option == "rebuild_index":
            flag = index_whoosh.index_delete_note_by_user(1000, user)
            if flag:
                LOG.info("Delete all notes index user[%s] success", user)
            else:
                LOG.error("Delete all notes index user[%s] failed!", user)
            flag = index_whoosh.index_all_note_by_num_user(1000, user, key = user_key if CONFIG["ENCRYPT"] else "", merge = True)
            if flag:
                LOG.info("Reindex all notes user[%s] success", user)
            else:
                LOG.error("Reindex all notes user[%s] failed!", user)
            self.render("note/note.html", 
                        user = user, 
                        current_nav = "Note",
                        scheme = CONFIG["SERVER_SCHEME"],
                        functions = CONFIG["FUNCTIONS"],
                        locale = locale)
        elif option == "download" and note_id != "":
            note = sqlite.get_note_by_id(note_id, user, conn = DB.conn_note)
            # note's file_content and file_title are unicode
            if CONFIG["ENCRYPT"]:
                # note.decrypt(user_key)
                note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
            fp = StringIO.StringIO(note.file_content.encode("utf-8"))
            self.set_header("Content-Disposition", 
                            "attachment; filename=%s.txt"%note.file_title.encode("utf-8").replace(" ", "_"))
            while True:
                buf = fp.read(1024 * 4)
                if not buf:
                    fp.close()
                    break
                self.write(buf)
            self.finish()
        else:
            self.render("note/note.html", 
                    user = user, 
                    current_nav = "Note",
                    scheme = CONFIG["SERVER_SCHEME"],
                    functions = CONFIG["FUNCTIONS"],
                    locale = locale)

@gen.coroutine
def update_categories(user_locale, user):
    user_info = sqlite.get_user_from_db(user, conn = DB.conn_user)
    note_books = ['Search', 'All'] + [category['sha1'] for category in json.loads(user_info.note_books)]
    if user_locale != None:
        trans_books = [user_locale.translate("Search"), user_locale.translate("All")]
        trans_books += [category['name'] for category in json.loads(user_info.note_books)]
    else:
        trans_books = ['Search', 'All'] + [category['name'] for category in json.loads(user_info.note_books)]
    note_num_dict = {}
    note_num_dict["All"] = 0
    for i in note_books:
        note_num_dict[i] = sqlite.get_note_num_by_type_user(i, user, conn = DB.conn_note)
        note_num_dict["All"] += note_num_dict[i]
    note_num_dict["Search"] = 0
    raise gen.Return({'books':note_books, 'trans':trans_books, 'numbers':note_num_dict})

@gen.coroutine
def update_notes(note_type, user, order = "DESC", user_key = "", offset = 0):
    notes_list = []
    notes = sqlite.get_note_by_user_type_created_at(user, note_type, order = order, offset = offset, limit = NOTE_NUM_PER_FETCH, conn = DB.conn_note)
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    if len(notes) > 0:
        note = notes[0]
        if user_key != "":
            note = yield multi_process_note_tea.decrypt(note, *(user_key, ), **{"decrypt_content": True})
            # note.decrypt(user_key, decrypt_content = True)
            note.created_at = str(note.created_at)[:19]
            note.updated_at = str(note.updated_at)[:19]
            notes_list.append(note.to_dict())
            # notes[0] = note
        else:
            note.created_at = str(note.created_at)[:19]
            note.updated_at = str(note.updated_at)[:19]
            notes_list.append(note.to_dict())
        for note in notes[1:]:
            if user_key != "":
                note = yield multi_process_note_tea.decrypt(note, *(user_key, ), **{"decrypt_content": False})
                # note.decrypt(user_key, decrypt_content = False)
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                notes_list.append(note.to_dict())
            else:
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                notes_list.append(note.to_dict())
    # return {"notes":notes, "notes_list":notes_list}
    raise gen.Return({"notes":notes, "notes_list":notes_list})

@gen.coroutine
def process_query(query, user, page = 1, user_key = ""):
    result = {}
    LOG.info("process query: %s", query)
    try:
        if query != "":
            result = yield search_whoosh.search_query_page_note_user(IX.ix_note, 
                                                                     query, 
                                                                     DB.note, 
                                                                     user, 
                                                                     page = page, 
                                                                     limits = NOTE_NUM_PER_FETCH, 
                                                                     key = user_key)
            if not result:
                LOG.error("search_query_no_page_note_user result False!")
                result = {}
                result["totalcount"] = 0
                result["result"] = []   
        else:
            result["totalcount"] = 0
            result["result"] = []
    except Exception, e:
        LOG.exception(e)
        result["totalcount"] = 0
        result["result"] = []
    raise gen.Return(result)

@gen.coroutine
def search_query(msg_category, user, handler, user_locale, page = 1, user_key = ""):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    typed_q = msg_category['q'].strip()
    query = msg_category['q'].strip()
    LOG.info("Search query: %s", query)
    result = yield process_query(query, user, page = page, user_key = user_key)
    data = {}
    data['notes'] = result['result']
    if data["notes"] != []:
        data['current_note_id'] = data['notes'][0]['id']
        note = sqlite.get_note_by_id(data['current_note_id'], user, conn = DB.conn_note)
        if user_key != "":
            # note.decrypt(user_key)
            note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
        note.created_at = str(note.created_at)[:19]
        note.updated_at = str(note.updated_at)[:19]
        data['note'] = note.to_dict()
    else:
        data['note'] = {'file_title':'', 'file_content':''}
        data['current_note_id'] = None
    data['note_list_action'] = 'init'
    data['current_category'] = 'Search'
    tmp_books = yield update_categories(user_locale, user)
    tmp_books['numbers']['Search'] = result["totalcount"]
    data['books'] = tmp_books
    send_msg(json.dumps(data), user, handler)

@gen.coroutine
def create_category(category_name, user, handler, user_locale):
    sha1_category_name = common_utils.sha1sum(category_name)
    category = {"name":category_name, "sha1":sha1_category_name}
    LOG.info("create category: %s[%s] for %s", category_name, sha1_category_name, user)
    user_info = sqlite.get_user_from_db(user, conn = DB.conn_user)
    if user_info:
        note_books = json.loads(user_info.note_books)
        if category not in note_books:
            note_books.append(category)
        user_info.note_books = json.dumps(note_books)
        flag = sqlite.save_data_to_db(user_info.to_dict(), DB.user, mode = "UPDATE", conn = DB.conn_user)
        if flag:
            data = {}
            data['note_list_action'] = 'init'
            data['notes'] = []
            data['note'] = {'file_title':'', 'file_content':''}
            data['current_note_id'] = None
            tmp_books = yield update_categories(user_locale, user)
            data['books'] = tmp_books
            data['current_category'] = sha1_category_name
            send_msg(json.dumps(data), user, handler)
            LOG.info("create category[%s] success", category_name)
        else:
            LOG.error("create category[%s] failed", category_name)

@gen.coroutine
def delete_category(sha1_category_name, user, handler, user_locale, user_key = ""):
    LOG.info("delete sha1_category_name: %s for %s", sha1_category_name, user)
    user_info = sqlite.get_user_from_db(user, conn = DB.conn_user)
    category_name = sha1_category_name
    if user_info:
        note_books = json.loads(user_info.note_books)
        for category in note_books:
            if sha1_category_name == category['sha1']:
                category_name = category['name']
                note_books.remove(category)
        user_info.note_books = json.dumps(note_books)
        flag = sqlite.save_data_to_db(user_info.to_dict(), DB.user, mode = "UPDATE", conn = DB.conn_user)
        if flag:
            notes = sqlite.get_note_from_db_by_user_type_iter(user, sha1_category_name, conn = DB.conn_note)
            if notes:
                for note in notes:
                    flag = index_whoosh.index_delete_note_by_id(str(note.id), user)
                    if flag == True:
                        LOG.info("Delete index note[%s] user[%s] category[%s] success.", note.id, user, category_name)
                    else:
                        LOG.info("Delete index note[%s] user[%s] category[%s] failed.", note.id, user, category_name)
            yield gen.moment
            flag = sqlite.delete_note_by_type(user, sha1_category_name, conn = DB.conn_note)
            if flag:
                data = {}
                data['notes'] = (yield update_notes('All', user, user_key = user_key))['notes_list']
                if data['notes'] != []:
                    data['note'] = data['notes'][0]
                    data['current_note_id'] = data['notes'][0]['id']
                else:
                    data['note'] = {'file_title':'', 'file_content':''}
                    data['current_note_id'] = None
                data['note_list_action'] = 'init'
                tmp_books = yield update_categories(user_locale, user)
                data['books'] = tmp_books
                send_msg(json.dumps(data), user, handler)
                LOG.info("delete category[%s] success", category_name)
        else:
            LOG.error("delete category[%s] failed", category_name)

@gen.coroutine
def select_catedory(sha1_category_name, user, handler, user_locale, user_key = ""):
    LOG.info("select category: %s by %s", sha1_category_name, user)
    data = {}
    data['current_category'] = sha1_category_name
    data['notes'] = (yield update_notes(sha1_category_name, user, user_key = user_key))['notes_list']
    if data['notes'] != []:
        data['note'] = data['notes'][0]
        data['current_note_id'] = data['notes'][0]['id']
    else:
        data['note'] = {'file_title':'', 'file_content':''}
        data['current_note_id'] = None
    data['note_list_action'] = 'init'
    tmp_books = yield update_categories(user_locale, user)
    data['books'] = tmp_books
    send_msg(json.dumps(data), user, handler)

@gen.coroutine
def load_category(sha1_category_name, note_id, user, handler, user_locale, user_key = "", offset = 0, q = ""):
    LOG.info("load category: %s by %s", sha1_category_name, user)
    data = {}
    if sha1_category_name != "Search":
        data['current_category'] = sha1_category_name
        data['notes'] = (yield update_notes(sha1_category_name, user, user_key = user_key, offset = offset))['notes_list']
        data['note_id'] = note_id
        data['note_list_action'] = 'append'
        tmp_books = yield update_categories(user_locale, user)
        data['books'] = tmp_books
    else:
        query = q.strip()
        page = int(offset / NOTE_NUM_PER_FETCH) + 1
        result = yield process_query(query, user, page = page, user_key = user_key)
        data['notes'] = result['result']
        data['current_category'] = 'Search'
        data['note_id'] = note_id
        data['note_list_action'] = 'append'
        tmp_books = yield update_categories(user_locale, user)
        tmp_books['numbers']['Search'] = result["totalcount"]
        data['books'] = tmp_books
    send_msg(json.dumps(data), user, handler)

@gen.coroutine
def create_note(note_dict, user, handler, user_locale, user_key = ""):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    try:
        note = NOTE()
        note.user_name = user
        note.type = note_dict['type'].strip()
        note.file_title = note_dict['note_title']
        note.file_content = note_dict['note_content']
        note.sha1 = common_utils.sha1sum(note.file_title + note.file_content)
        data = {}
        if note.type != 'Search' and note.type != 'All':
            LOG.debug("Create Note")
            note.created_at = datetime.datetime.now(dateutil.tz.tzlocal())
            note.updated_at = note.created_at
            note.description = common_utils.get_description_text(note.file_content, 
                                                                 CONFIG["NOTE_DESCRIPTION_LENGTH"])
            if user_key != "":
                # note.encrypt(user_key)
                note = yield multi_process_note_tea.encrypt(note, *(user_key, ))
            flag = sqlite.save_data_to_db(note.to_dict(), DB.note, conn = DB.conn_note)
            if flag == True:
                flag = index_whoosh.index_all_note_by_num_flag(100, key = user_key)
                if flag == True:
                    LOG.info("Index note[%s] user[%s] success.", note.file_title, user)
                else:
                    LOG.info("Index note[%s] user[%s] failed.", note.file_title, user)
                # should index new note here.
            if user_key != "":
                # note.decrypt(user_key)
                note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
            data['notes'] = (yield update_notes(note.type, user, user_key = user_key))['notes_list']
            data['current_note_id'] = data['notes'][0]['id']
            data['note_list_action'] = 'init'
            tmp_books = yield update_categories(user_locale, user)
            data['books'] = tmp_books
            note.created_at = str(note.created_at)[:19]
            note.updated_at = str(note.updated_at)[:19]
            data['note'] = note.to_dict()
            send_msg(json.dumps(data), user, handler)
    except Exception, e:
        LOG.exception(e)

@gen.coroutine
def delete_note(note_dict, user, handler, user_locale, page = 1, user_key = ""):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    try:
        note_id = note_dict['note_id']
        LOG.debug("Delete Note")
        data = {}
        flag = sqlite.delete_note_by_id(user, note_id, conn = DB.conn_note)
        if flag == True:
            flag = index_whoosh.index_delete_note_by_id(str(note_id), user)
            if flag == True:
                LOG.info("Delete index note[%s] user[%s] success.", note_id, user)
            else:
                LOG.info("Delete index note[%s] user[%s] failed.", note_id, user)
        if note_dict['type'] != 'Search':
            data['notes'] = (yield update_notes(note_dict['type'], user, user_key = user_key))['notes_list']
            if data['notes'] != []:
                data['note'] = data['notes'][0]
                data['current_note_id'] = data['notes'][0]['id']
            else:
                data['note'] = {'file_title':'', 'file_content':''}
                data['current_note_id'] = None
            data['note_list_action'] = 'init'
            tmp_books = yield update_categories(user_locale, user)
            data['books'] = tmp_books
        else:
            query = note_dict['q'].strip()
            result = yield process_query(query, user, page = page, user_key = user_key)
            data['notes'] = result['result']
            if data["notes"] != []:
                data['current_note_id'] = data['notes'][0]['id']
                note = sqlite.get_note_by_id(data['current_note_id'], user, conn = DB.conn_note)
                if user_key != "":
                    # note.decrypt(user_key)
                    note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                data['note'] = note.to_dict()
            else:
                data['note'] = {'file_title':'', 'file_content':''}
                data['current_note_id'] = None
            data['note_list_action'] = 'init'
            data['current_category'] = 'Search'
            tmp_books = yield update_categories(user_locale, user)
            tmp_books['numbers']['Search'] = result["totalcount"]
            data['books'] = tmp_books
        send_msg(json.dumps(data), user, handler)
    except Exception, e:
        LOG.exception(e)

@gen.coroutine
def save_note(note_dict, user, handler, user_locale, page = 1, user_key = ""):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    try:
        note = NOTE()
        note.id = note_dict['note_id']
        note.user_name = user
        note.file_title = note_dict['note_title']
        note.file_content = note_dict['note_content']
        note.sha1 = common_utils.sha1sum(note.file_title + note.file_content)
        data = {}
        flag = sqlite.get_note_by_id(note.id, user, conn = DB.conn_note)
        note.type = flag.type
        if note.file_title.strip() == "" and note.file_content.strip() == "":
            delete_note(note_dict, user, handler, user_locale, page = 1, user_key = user_key)
        elif flag.sha1 != note.sha1:
            LOG.debug("Update Note")
            note.created_at = flag.created_at
            note.updated_at = datetime.datetime.now(dateutil.tz.tzlocal())
            note.description = common_utils.get_description_text(note.file_content, 
                                                                 CONFIG["NOTE_DESCRIPTION_LENGTH"])
            if user_key != "":
                # note.encrypt(user_key)
                note = yield multi_process_note_tea.encrypt(note, *(user_key, ))
            flag = sqlite.save_data_to_db(note.to_dict(), DB.note, mode = "UPDATE", conn = DB.conn_note)
            if flag == True:
                flag = index_whoosh.index_all_note_by_num_flag(100, user_key)
                if flag == True:
                    LOG.info("Update index note[%s] user[%s] success.", note.file_title, user)
                else:
                    LOG.info("Update index note[%s] user[%s] failed.", note.file_title, user)
                # should index updated note here.
            if user_key != "":
                # note.decrypt(user_key)
                note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
            if note_dict["type"] != "Search":
                data['note_list_action'] = 'update'
                data['current_note_id'] = note.id
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                data['note'] = note.to_dict()
            # save note in Search category
            else:
                data['current_note_id'] = note.id
                note = sqlite.get_note_by_id(data['current_note_id'], user, conn = DB.conn_note)
                if user_key != "":
                    # note.decrypt(user_key)
                    note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                data['note'] = note.to_dict()
                data['note_list_action'] = 'append'
                data['current_category'] = 'Search'
            data['save'] = 'ok'
            send_msg(json.dumps(data), user, handler)
        elif flag.sha1 == note.sha1:
            data['save'] = 'ok'
            send_msg(json.dumps(data), user, handler)
    except Exception, e:
        LOG.exception(e)

def send_msg(msg, user, handler):
    try:
        handler.write_message(msg)
    except Exception, e:
        LOG.exception(e)

class NoteSocketHandler(BaseSocketHandler):
    socket_handlers = {}

    @tornado.web.authenticated
    @gen.coroutine
    def open(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        if not CONFIG["ENCRYPT"]:
            user_key = ""
        user_locale = self.get_user_locale()
        user_info = sqlite.get_user_from_db(user, conn = DB.conn_user)
        if user_info:
            if NoteSocketHandler.socket_handlers.has_key(user):
                NoteSocketHandler.socket_handlers[user].add(self)
                LOG.info("note websocket[%s] len: %s", user, len(NoteSocketHandler.socket_handlers[user]))
            else:
                NoteSocketHandler.socket_handlers[user] = set()
                NoteSocketHandler.socket_handlers[user].add(self)
                LOG.info("note websocket[%s] len: %s", user, len(NoteSocketHandler.socket_handlers[user]))
        else:
            self.redirect("/login")
        LOG.info("open note websocket: %s", user)
        LOG.info("note websocket users: %s", NoteSocketHandler.socket_handlers.keys())
        data = {}
        data['notes'] = (yield update_notes('All', user, user_key = user_key, offset = 0))['notes_list']
        if data['notes'] != []:
            data['note'] = data['notes'][0]
            data['current_note_id'] = data['notes'][0]['id']
        else:
            data['note'] = {'file_title':'', 'file_content':''}
            data['current_note_id'] = None
        data['note_list_action'] = 'init'
        data['books'] = yield update_categories(user_locale, user)
        send_msg(json.dumps(data), user, self)

    @tornado.web.authenticated
    @gen.coroutine
    def on_close(self):
        user = self.get_current_user_name()
        NoteSocketHandler.socket_handlers[user].remove(self)
        LOG.info("close note websocket: %s", user)
        LOG.info("note websocket[%s] len: %s", user, len(NoteSocketHandler.socket_handlers[user]))
        if len(NoteSocketHandler.socket_handlers[user]) == 0:
            NoteSocketHandler.socket_handlers.pop(user)
            LOG.info("note websocket remove user: %s", user)

    @tornado.web.authenticated
    @gen.coroutine
    def on_message(self, msg):
        multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        if not CONFIG["ENCRYPT"]:
            user_key = ""
        user_locale = self.get_user_locale()
        msg = json.loads(msg)
        data = {}
        note_list = []
        if msg.has_key('note'):
            cmd = msg['note']['cmd']
            if cmd == 'select':
                note_id = msg['note']['note_id']
                note = sqlite.get_note_by_id(note_id, user, conn = DB.conn_note)
                if user_key != "":
                    start_time = time.time()
                    # note.decrypt(user_key)
                    note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
                    end_time = time.time()
                    LOG.info("Decrypt note Time: %s", end_time - start_time)
                data['note'] = note.to_dict()
                data['current_note_id'] = note_id
                send_msg(json.dumps(data), user, self)
            elif cmd == 'save':
                note_id = msg['note']['note_id']
                if note_id == None:
                    yield create_note(msg['note'], user, self, user_locale, user_key = user_key)
                elif note_id != None:
                    yield save_note(msg['note'], user, self, user_locale, page = 1, user_key = user_key)
        if msg.has_key('category'):
            cmd = msg['category']['cmd']
            LOG.info("category operation: %s", cmd)
            if cmd == 'create':
                category_name = msg['category']['category_name'].strip()
                yield create_category(category_name, user, self, user_locale);
            elif cmd == 'delete':
                category_name = msg['category']['category_name'].strip()
                yield delete_category(category_name, user, self, user_locale, user_key = user_key);
            elif cmd == 'select':
                category_name = msg['category']['category_name'].strip()
                yield select_catedory(category_name, user, self, user_locale, user_key = user_key);
            elif cmd == 'search':
                yield search_query(msg['category'], user, self, user_locale, page = 1, user_key = user_key);
            elif cmd =='load':
                category_name = msg['category']['category_name'].strip()
                offset = msg['category']['offset']
                note_id = msg['category']['note_id']
                q = msg['category']['q']
                yield load_category(category_name, note_id, user, self, user_locale, user_key, offset, q)
        if msg.has_key('notes'):
            cmd = msg['notes']['cmd']
            if cmd == 'delete':
                pass


class ImportHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        try:
            fname = ""
            fbody = ""
            fileinfo = None
            up_file_path = None
            password = self.get_argument("passwd","")
            password = common_utils.md5twice(password) if password != "" else ""
            LOG.info("import notes encrypted: %s", True if password != "" else False)
            user_info = sqlite.get_user_from_db(user, conn = DB.conn_user)
            multi_process_note_import = MultiProcessNoteImport(CONFIG["PROCESS_NUM"])
            try:
                if not CONFIG["WITH_NGINX"]:
                    fileinfo = self.request.files["up_file"][0]
                    fname = fileinfo["filename"]
                    fbody = fileinfo["body"]
                else:
                    fileinfo = True
                    fname = self.get_argument("up_file.name", "")
                    up_file_path = self.get_argument("up_file.path", "")
            except Exception, e:
                fileinfo = None
                LOG.debug("Upload file failed, You must be sure selected a file!")
                LOG.exception(e)
            if fileinfo != None:
                fpath = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                     user_info.sha1, 
                                     "tmp", 
                                     "import", 
                                     fname)
                if not CONFIG["WITH_NGINX"]:
                    fp = open(fpath, 'wb')
                    fp.write(fbody)
                    fp.close()
                else:
                    shutil.move(up_file_path, fpath)
                flag = yield multi_process_note_import.import_notes(fname, user_info, user_key, password)
                # index all notes
                if flag:
                    flag = index_whoosh.index_all_note_by_num_user(1000, 
                                                                   user, 
                                                                   key = user_key if CONFIG["ENCRYPT"] else "",
                                                                   db = DB,
                                                                   ix = IX,
                                                                   merge = True)
                    if flag:
                        LOG.info("Reindex all notes user[%s] success", user)
                    else:
                        LOG.error("Reindex all notes user[%s] failed!", user)
            self.redirect("/note")
        except Exception, e:
            LOG.exception(e)

class ExportHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        password = self.get_argument("passwd", "")
        user_info = sqlite.get_user_from_db(user, conn = DB.conn_user)
        encrypt = self.get_argument("encrypt","")
        encrypt = True if encrypt == "enable" else False
        export_category = self.get_argument("notes_category", "All")
        LOG.debug("Export notes category: %s", export_category)
        if password != "" and encrypt:
            password = common_utils.md5twice(password)
        elif password == "" and encrypt:
            password = user_key
        else:
            password = ""
        LOG.info("export notes encrypted: %s", encrypt)
        try:
            notes_iter = sqlite.get_note_from_db_by_user_type_iter(user, export_category, conn = DB.conn_note)
            user_notes_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "notes")
            shutil.rmtree(user_notes_path)
            LOG.info("remove user[%s] path[%s]", user, user_notes_path)
            os.makedirs(user_notes_path)
            LOG.info("create user[%s] path[%s]", user, user_notes_path)
            for note in notes_iter:
                yield create_note_file(CONFIG["STORAGE_USERS_PATH"], 
                                       user, 
                                       user_info.sha1,
                                       note, 
                                       key = user_key if CONFIG["ENCRYPT"] else "", 
                                       key1 = password)
            category = ""
            if export_category == "All":
                category = {"sha1": "", "name": "All"}
            else:
                for c in json.loads(user_info.note_books):
                    if c["sha1"] == export_category:
                        category = c
            create_category_info(CONFIG["STORAGE_USERS_PATH"], user_info, category)
            arch = Archive(user_info)
            arch.archive("tar.gz", category["name"])
            LOG.debug("arch.package_path: %s"%arch.package_path)
            if os.path.exists(arch.package_path) and os.path.isfile(arch.package_path):
                fp = open(arch.package_path, 'rb')
                self.set_header("Content-Disposition", "attachment; filename=%s"%arch.package)
                while True:
                    buf = fp.read(1024 * 4)
                    if not buf:
                        fp.close()
                        arch.clear()
                        break
                    self.write(buf)
                self.finish()
            else:
                self.write("Download Archive Error!")
        except Exception, e:
            LOG.exception(e)

class DeleteHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        user_info = sqlite.get_user_from_db(user, conn = DB.conn_user)
        try:
            flag = index_whoosh.index_delete_note_by_user(1000, user, merge = True)
            yield gen.moment
            if flag:
                LOG.info("Delete user[%s] all notes index success", user)
                if user_info:
                    user_info.note_books = json.dumps([])
                    flag = sqlite.save_data_to_db(user_info.to_dict(), DB.user, mode = "UPDATE", conn = DB.conn_user)
                    if flag:
                        LOG.info("Delete user[%s] all notes categories success", user)
                    else:
                        LOG.error("Delete user[%s] all notes categories failed", user)
                flag = sqlite.delete_note_by_user(user, conn = DB.conn_note)
                yield gen.moment
                import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                           user_info.sha1, 
                                           "tmp", 
                                           "import", 
                                           "notes")
                user_notes_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                               user_info.sha1, 
                                               "notes")
                if os.path.exists(user_notes_path) and os.path.isdir(user_notes_path):
                    shutil.rmtree(user_notes_path)
                    os.makedirs(user_notes_path)
                if os.path.exists(import_path) and os.path.isdir(import_path):
                    shutil.rmtree(import_path)
                    LOG.debug("delete import_path[%s] success."%import_path)
            else:
                LOG.info("Delete user[%s] all notes index failed", user)
            self.redirect("/note")
        except Exception, e:
            LOG.exception(e)
            self.render("info.html", info_msg = "Delete user[%s]'s notes failed."%user)

class AjaxNoteHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, note_id = ""):
        user = self.get_current_user_name()

    @tornado.web.authenticated
    def post(self, note_id = ""):
        user = self.get_current_user_name()
