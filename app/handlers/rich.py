# -*- coding: utf-8 -*-
'''
Created on 2013-11-09
@summary: rich note handler
@author: YangHaitao

Modified on 2014-06-11
@summary: rich note handler with websocket
@author: YangHaitao

Modified on 2014-09-03
@summary: add notes_list when user_key == ""
@author: YangHaitao

Modified on 2014-10-28
@summary: change notes export functions
@author: YangHaitao

Modified on 2014-12-12
@summary: change create_rich_file function for export pictures use sha1 file_name
@author: YangHaitao

Modified on 2015-03-08
@summary: change for coroutine
@author: YangHaitao
'''

import os.path
import json
import time
import logging
import shutil
import datetime
import dateutil

import tornado.web
from tornado import gen
from tornado import ioloop
from whoosh.writing import AsyncWriter

from config import CONFIG
from utils import search_whoosh
from base import BaseHandler, BaseSocketHandler
from utils.archive import Archive_Rich_Notes as Archive
from utils import htmlparser
from models.item import RICH
from utils import common_utils
from utils.multi_async_tea import MultiProcessNoteTea
from utils.processer import ManagerClient
from utils.common import Servers


LOG = logging.getLogger(__name__)

NOTE_NUM_PER_FETCH = CONFIG["NOTE_NUM_PER_FETCH"]


def get_index_key(file_name, user):
    return "index_%s_%s" % (file_name, user.sha1)

@gen.coroutine
def create_rich_file(storage_users_path, user, user_sha1, note, key = "", key1 = ""):
    note_path = os.path.join(storage_users_path, user_sha1, "rich_notes", "rich_notes", note.type)
    note_file_path = os.path.join(storage_users_path, user_sha1, "rich_notes", "rich_notes", note.type, note.sha1)
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

    user_images_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_sha1, "rich_notes", "images")
    for image_sha1 in note.images:
        pic = Servers.DB_SERVER["PIC"].get_data_by_sha1(image_sha1)
        if pic != None and pic != False:
            image_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path)
            file_name = pic.sha1 + os.path.splitext(pic.file_name)[-1]
            target_path = os.path.join(user_images_path, file_name)
            if not os.path.exists(target_path):
                shutil.copyfile(image_path, target_path + '.tmp')
                os.rename(target_path + '.tmp', target_path)
                LOG.info("Copy file[%s] to file[%s]"%(image_path, target_path))
            else:
                LOG.info("Image file[%s] has been existed!"%(target_path,))

def create_category_info(storage_users_path, user_info, category):
    file_path = os.path.join(storage_users_path, user_info.sha1, "rich_notes", "category.json")
    fp = open(file_path, 'wb')
    if category["name"] == "All":
        fp.write(user_info.rich_books)
    else:
        fp.write(json.dumps([category]))
    fp.close()
    LOG.info("create user[%s] category.json[%s]", user_info.user_name, file_path)

def delete_rich_note(storage_users_path, user_sha1, notetype, noteid):
    note_path = os.path.join(storage_users_path, user_sha1, "rich_notes", "rich_notes", notetype, noteid)
    if os.path.exists(note_path) and os.path.isfile(note_path):
        os.remove(note_path)
        LOG.info("Delete rich note[%s] success.", note_path)

def create_rich_note(storage_users_path, user_sha1, rich):
    note_path = os.path.join(storage_users_path, user_sha1, "rich_notes", "rich_notes", rich.type, str(rich.id))
    fp = open(note_path, 'wb')
    doc = rich.to_xml()
    doc.write(fp, xml_declaration=True, encoding='utf-8', pretty_print=True)
    fp.close()
    LOG.info("Create rich note[%s] success.", note_path)

def update_rich_note(storage_users_path, user_sha1, rich):
    note_path = os.path.join(storage_users_path, user_sha1, "rich_notes", "rich_notes", rich.type, str(rich.id))
    if os.path.exists(note_path) and os.path.isfile(note_path):
        os.remove(note_path)
    fp = open(note_path, 'wb')
    doc = rich.to_xml()
    doc.write(fp, xml_declaration=True, encoding='utf-8', pretty_print=True)
    fp.close()
    LOG.info("Update rich note[%s] success.", note_path)

class RichHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
        user_locale = self.get_user_locale()
        locale = "zh_CN" if user_locale and user_locale.code == "zh_CN" else "en_US"
        option = (self.get_argument("option", "")).strip()
        note_id = (self.get_argument("id", "")).strip()
        if option == "rebuild_index":
            flag = Servers.IX_SERVER["RICH"].index_delete_rich_by_user(user)
            if flag:
                LOG.info("Delete all rich notes index user[%s] success", user)
            else:
                LOG.error("Delete all rich notes index user[%s] failed!", user)
            flag = Servers.IX_SERVER["RICH"].index_all_rich_by_num_user(1000,
                                                                        user,
                                                                        key = user_key if CONFIG["ENCRYPT"] else "",
                                                                        db_rich = Servers.DB_SERVER["RICH"],
                                                                        merge = True)
            if flag:
                LOG.info("Reindex all rich notes user[%s] success", user)
            else:
                LOG.error("Reindex all rich notes user[%s] failed!", user)
            self.render("note/rich_tinymce.html",
                        user = user,
                        current_nav = "Rich",
                        scheme = CONFIG["SERVER_SCHEME"],
                        functions = CONFIG["FUNCTIONS"],
                        locale = locale,
                        http_proxy = user_info.http_proxy,
                        https_proxy = user_info.https_proxy)
        else:
            self.render("note/rich_tinymce.html",
                    user = user,
                    current_nav = "Rich",
                    scheme = CONFIG["SERVER_SCHEME"],
                    functions = CONFIG["FUNCTIONS"],
                    locale = locale,
                    http_proxy = user_info.http_proxy,
                    https_proxy = user_info.https_proxy)

@gen.coroutine
def update_categories(user_locale, user):
    user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
    note_books = ['Search', 'All'] + [category['sha1'] for category in json.loads(user_info.rich_books)]
    if user_locale != None:
        trans_books = [user_locale.translate("Search"), user_locale.translate("All")]
        trans_books += [category['name'] for category in json.loads(user_info.rich_books)]
    else:
        trans_books = ['Search', 'All'] + [category['name'] for category in json.loads(user_info.rich_books)]
    note_num_dict = {}
    note_num_dict["All"] = 0
    for i in note_books:
        note_num_dict[i] = Servers.DB_SERVER["RICH"].get_rich_num_by_type_user(i, user)
        note_num_dict["All"] += note_num_dict[i]
    note_num_dict["Search"] = 0
    raise gen.Return({'books':note_books, 'trans':trans_books, 'numbers':note_num_dict})

@gen.coroutine
def update_notes(note_type, user, order = "DESC", user_key = "", offset = 0):
    notes_list = []
    notes = Servers.DB_SERVER["RICH"].get_rich_by_user_type_created_at(user, note_type, order = order, offset = offset, limit = NOTE_NUM_PER_FETCH)
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
    raise gen.Return({"notes":notes, "notes_list":notes_list})

@gen.coroutine
def process_query(query, user, page = 1, user_key = ""):
    result = {}
    LOG.info("process query: %s", query)
    try:
        if query != "":
            result = yield search_whoosh.search_query_page_rich_user(Servers.IX_SERVER["RICH"].ix,
                                                                     query,
                                                                     "RICH",
                                                                     user,
                                                                     page = page,
                                                                     limits = NOTE_NUM_PER_FETCH,
                                                                     key = user_key,
                                                                     db_user = Servers.DB_SERVER["USER"],
                                                                     db_rich = Servers.DB_SERVER["RICH"])
            if not result:
                LOG.error("search_query_no_page_rich_user result False!")
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
        note = Servers.DB_SERVER["RICH"].get_rich_by_id(data['current_note_id'], user)
        if user_key != "":
            # note.decrypt(user_key)
            note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
        note.created_at = str(note.created_at)[:19]
        note.updated_at = str(note.updated_at)[:19]
        data['note'] = note.to_dict()
    else:
        data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
        data['current_note_id'] = None
    data['note_list_action'] = 'init'
    data['current_category'] = 'Search'
    tmp_books = yield update_categories(user_locale, user)
    tmp_books['numbers']['Search'] = result["totalcount"]
    data['books'] = tmp_books
    send_msg(json.dumps(data), user, handler)

@gen.coroutine
def create_category(category_name, user, handler, user_locale, user_key = ""):
    sha1_category_name = common_utils.sha1sum(category_name)
    category = {"name":category_name, "sha1":sha1_category_name}
    LOG.info("create category: %s[%s] for %s", category_name, sha1_category_name, user)
    user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
    if user_info:
        save = "create_category_fail"
        note_books = json.loads(user_info.rich_books)
        if category not in note_books:
            note_books.append(category)
            save = "create_category_ok"
        else:
            save = "create_category_exist"
        user_info.rich_books = json.dumps(note_books)
        flag = Servers.DB_SERVER["USER"].save_data_to_db(user_info.to_dict(), mode = "UPDATE")
        data = {}
        data['note_list_action'] = 'init'
        if flag and save == "create_category_ok":
            data['notes'] = []
            data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
            data['current_note_id'] = None
            tmp_books = yield update_categories(user_locale, user)
            data['books'] = tmp_books
            data['current_category'] = sha1_category_name
            data['save'] = save
            LOG.info("create category[%s] success", category_name)
        else:
            data['notes'] = (yield update_notes('All', user, user_key = user_key, offset = 0))['notes_list']
            if data['notes'] != []:
                data['note'] = data['notes'][0]
                data['current_note_id'] = data['notes'][0]['id']
            else:
                data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
                data['current_note_id'] = None
            data['books'] = yield update_categories(user_locale, user)
            data['current_category'] = 'All'
            data['save'] = save
            LOG.warning("create category[%s] failed: %s", category_name, save)
        send_msg(json.dumps(data), user, handler)

@gen.coroutine
def delete_category(sha1_category_name, user, handler, user_locale, user_key = ""):
    LOG.info("delete sha1_category_name: %s for %s", sha1_category_name, user)
    user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
    category_name = sha1_category_name
    if user_info:
        note_books = json.loads(user_info.rich_books)
        for category in note_books:
            if sha1_category_name == category['sha1']:
                category_name = category['name']
                note_books.remove(category)
        user_info.rich_books = json.dumps(note_books)
        flag = Servers.DB_SERVER["USER"].save_data_to_db(user_info.to_dict(), mode = "UPDATE")
        if flag:
            notes = Servers.DB_SERVER["RICH"].get_rich_from_db_by_user_type_iter(user, sha1_category_name)
            if notes:
                for note in notes:
                    flag = Servers.IX_SERVER["RICH"].index_delete_rich_by_id(str(note.id), user)
                    if flag == True:
                        LOG.info("Delete index rich note[%s] user[%s] category[%s] success.", note.id, user, category_name)
                    else:
                        LOG.info("Delete index rich note[%s] user[%s] category[%s] failed.", note.id, user, category_name)
            yield gen.moment
            flag = Servers.DB_SERVER["RICH"].delete_rich_by_type(user, sha1_category_name)
            if flag:
                data = {}
                data['notes'] = (yield update_notes('All', user, user_key = user_key))['notes_list']
                if data['notes'] != []:
                    data['note'] = data['notes'][0]
                    data['current_note_id'] = data['notes'][0]['id']
                else:
                    data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
                    data['current_note_id'] = None
                data['note_list_action'] = 'init'
                tmp_books = yield update_categories(user_locale, user)
                data['books'] = tmp_books
                send_msg(json.dumps(data), user, handler)
                LOG.info("delete category[%s] success", category_name)
        else:
            LOG.error("delete category[%s] failed", category_name)

@gen.coroutine
def select_category(sha1_category_name, user, handler, user_locale, user_key = ""):
    LOG.info("select category: %s by %s", sha1_category_name, user)
    data = {}
    data['current_category'] = sha1_category_name
    data['notes'] = (yield update_notes(sha1_category_name, user, user_key = user_key))['notes_list']
    if data['notes'] != []:
        data['note'] = data['notes'][0]
        data['current_note_id'] = data['notes'][0]['id']
    else:
        data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
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
def create_note(note_dict, user, handler, user_locale, user_key = "", proxy = {}):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    try:
        note = RICH()
        note.user_name = user
        note.type = note_dict['type'].strip()
        note.file_title = note_dict['note_title']
        note_content = note_dict['note_content']
        note_content, images = htmlparser.get_rich_content(note_content, Servers.DB_SERVER["PIC"], proxy = proxy)
        note.sha1 = common_utils.sha1sum(note.file_title + note_content)
        note.rich_content = note_content
        note.images = images
        note.file_content = htmlparser.get_html_content(note_content)["content"] if note_content.strip() != "" else ""
        data = {}
        if note.type != 'Search' and note.type != 'All':
            LOG.debug("Create Rich Note")
            save = "create_fail"
            note.created_at = datetime.datetime.now(dateutil.tz.tzlocal())
            note.updated_at = note.created_at
            note.description = common_utils.get_description_text(note.file_content, 
                                                                 CONFIG["NOTE_DESCRIPTION_LENGTH"])
            LOG.info("note: %s", note)
            if user_key != "":
                # note.encrypt(user_key)
                note = yield multi_process_note_tea.encrypt(note, *(user_key, ))
            flag = Servers.DB_SERVER["RICH"].save_data_to_db(note.to_dict(), mode = "INSERT")
            if flag == True:
                note = Servers.DB_SERVER["RICH"].get_rich_by_sha1(note.sha1, user)
                flag = Servers.IX_SERVER["RICH"].index_all_rich_by_num_flag(100, key = user_key, db_flag = Servers.DB_SERVER["FLAG"], db_rich = Servers.DB_SERVER["RICH"])
                if flag == True:
                    LOG.info("Index rich note[%s] user[%s] success.", note.file_title, user)
                else:
                    LOG.info("Index rich note[%s] user[%s] failed.", note.file_title, user)
                save = "create_ok"
            elif flag == None:
                save = "create_exist"
                # should index new note here.
            if user_key != "":
                # note.decrypt(user_key)
                note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
            data['notes'] = (yield update_notes(note.type, user, user_key = user_key))['notes_list']
            if save != "create_ok":
                note.parse_dict(data['notes'][0])
            # LOG.info("notes: %s", data['notes'])
            data['current_note_id'] = data['notes'][0]['id']
            data['note_list_action'] = 'init'
            tmp_books = yield update_categories(user_locale, user)
            data['books'] = tmp_books
            note.created_at = str(note.created_at)[:19]
            note.updated_at = str(note.updated_at)[:19]
            data['note'] = note.to_dict()
            data['save'] = save
            send_msg(json.dumps(data), user, handler)
    except Exception, e:
        LOG.exception(e)

@gen.coroutine
def delete_note(note_dict, user, handler, user_locale, page = 1, user_key = ""):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    try:
        note_id = note_dict['note_id']
        LOG.debug("Delete Rich Note")
        data = {}
        flag = Servers.DB_SERVER["RICH"].delete_rich_by_id(user, note_id)
        if flag == True:
            flag = Servers.IX_SERVER["RICH"].index_delete_rich_by_id(str(note_id), user)
            if flag == True:
                LOG.info("Delete index rich note[%s] user[%s] success.", note_id, user)
            else:
                LOG.info("Delete index rich note[%s] user[%s] failed.", note_id, user)
        if note_dict['type'] != 'Search':
            data['notes'] = (yield update_notes(note_dict['type'], user, user_key = user_key))['notes_list']
            if data['notes'] != []:
                data['note'] = data['notes'][0]
                data['current_note_id'] = data['notes'][0]['id']
            else:
                data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
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
                note = Servers.DB_SERVER["RICH"].get_rich_by_id(data['current_note_id'], user)
                if user_key != "":
                    # note.decrypt(user_key)
                    note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                data['note'] = note.to_dict()
            else:
                data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
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
def save_note(note_dict, user, handler, user_locale, page = 1, user_key = "", proxy = {}):
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    try:
        note = RICH()
        note.id = note_dict['note_id']
        note.user_name = user
        note.file_title = note_dict['note_title']
        note_content = note_dict['note_content']
        note_content, images = htmlparser.get_rich_content(note_content, Servers.DB_SERVER["PIC"], proxy = proxy)
        note.sha1 = common_utils.sha1sum(note.file_title + note_content)
        note.rich_content = note_content
        note.images = images
        note.file_content = htmlparser.get_html_content(note_content)["content"] if note_content.strip() != "" else ""
        data = {}
        flag = Servers.DB_SERVER["RICH"].get_rich_by_id(note.id, user)
        note.type = flag.type
        # if note_dict['type'] != 'Search':
        if note.file_title.strip() == "" and note.file_content.strip() == "":
            delete_note(note_dict, user, handler, user_locale, page = 1, user_key = user_key)
        elif flag.sha1 != note.sha1:
            LOG.debug("Update Rich Note")
            save = "save_fail"
            note.created_at = flag.created_at
            note.updated_at = datetime.datetime.now(dateutil.tz.tzlocal())
            note.description = common_utils.get_description_text(note.file_content, CONFIG["NOTE_DESCRIPTION_LENGTH"])
            if user_key != "":
                # note.encrypt(user_key)
                note = yield multi_process_note_tea.encrypt(note, *(user_key, ))
            flag = Servers.DB_SERVER["RICH"].save_data_to_db(note.to_dict(), mode = "UPDATE")
            if flag == True: # save note success
                flag = Servers.IX_SERVER["RICH"].index_all_rich_by_num_flag(100, user_key, Servers.DB_SERVER["FLAG"], Servers.DB_SERVER["RICH"])
                if flag == True:
                    LOG.info("Update index rich note[%s] user[%s] success.", note.file_title, user)
                else:
                    LOG.info("Update index rich note[%s] user[%s] failed.", note.file_title, user)
                save = "save_ok"
            elif flag == None: # have a same content note exist
                save = "save_exist"

            if user_key != "":
                # note.decrypt(user_key)
                note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
            if note_dict["type"] != "Search":
                if save == "save_ok":
                    data['note_list_action'] = 'update'
                else:
                    data['note_list_action'] = 'append'
                data['current_note_id'] = note.id
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                data['note'] = note.to_dict()
            # save note in Search category
            else:
                data['current_note_id'] = note.id
                if save == "save_ok":
                    note = Servers.DB_SERVER["RICH"].get_rich_by_id(data['current_note_id'], user)
                    if user_key != "":
                        # note.decrypt(user_key)
                        note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
                note.created_at = str(note.created_at)[:19]
                note.updated_at = str(note.updated_at)[:19]
                data['note'] = note.to_dict()
                data['note_list_action'] = 'append'
                data['current_category'] = 'Search'
            data['save'] = save
            send_msg(json.dumps(data), user, handler)
        elif flag.sha1 == note.sha1:
            data['save'] = 'save_ok'
            send_msg(json.dumps(data), user, handler)
    except Exception, e:
        LOG.exception(e)

def send_msg(msg, user, handler):
    try:
        handler.write_message(msg)
    except Exception, e:
        LOG.exception(e)

class RichSocketHandler(BaseSocketHandler):
    socket_handlers = {}

    @tornado.web.authenticated
    @gen.coroutine
    def open(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        if user:
            if not CONFIG["ENCRYPT"]:
                user_key = ""
            user_locale = self.get_user_locale()
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            if user_info:
                if RichSocketHandler.socket_handlers.has_key(user):
                    RichSocketHandler.socket_handlers[user].add(self)
                    LOG.info("rich note websocket[%s] len: %s", user, len(RichSocketHandler.socket_handlers[user]))
                else:
                    RichSocketHandler.socket_handlers[user] = set()
                    RichSocketHandler.socket_handlers[user].add(self)
                    LOG.info("rich note websocket[%s] len: %s", user, len(RichSocketHandler.socket_handlers[user]))

                LOG.info("open rich note websocket: %s", user)
                LOG.info("rich note websocket users: %s", RichSocketHandler.socket_handlers.keys())
                data = {}
                data['notes'] = (yield update_notes('All', user, user_key = user_key, offset = 0))['notes_list']
                if data['notes'] != []:
                    data['note'] = data['notes'][0]
                    data['current_note_id'] = data['notes'][0]['id']
                else:
                    data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
                    data['current_note_id'] = None
                data['note_list_action'] = 'init' # init, append
                data['books'] = yield update_categories(user_locale, user)
                send_msg(json.dumps(data), user, self)
            else:
                self.close()
                LOG.info("Server close websocket!")
        else:
            self.close()
            LOG.info("Server close websocket!")

    @tornado.web.authenticated
    @gen.coroutine
    def on_close(self):
        user = self.get_current_user_name()
        if user and RichSocketHandler.socket_handlers.has_key(user):
            RichSocketHandler.socket_handlers[user].remove(self)
            LOG.info("close rich note websocket: %s", user)
            LOG.info("rich note websocket[%s] len: %s", user, len(RichSocketHandler.socket_handlers[user]))
            if len(RichSocketHandler.socket_handlers[user]) == 0:
                RichSocketHandler.socket_handlers.pop(user)
                LOG.info("rich note websocket remove user: %s", user)
        else:
            self.close()
            LOG.info("Server close websocket!")

    @tornado.web.authenticated
    @gen.coroutine
    def on_message(self, msg):
        multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        if user:
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
                    note = Servers.DB_SERVER["RICH"].get_rich_by_id(note_id, user)
                    if user_key != "":
                        start_time = time.time()
                        # note.decrypt(user_key)
                        note = yield multi_process_note_tea.decrypt(note, *(user_key, ))
                        end_time = time.time()
                        LOG.info("Decrypt rich note Time: %s", end_time - start_time)
                    data['note'] = note.to_dict()
                    data['current_note_id'] = note_id
                    send_msg(json.dumps(data), user, self)
                elif cmd == 'save':
                    proxy = {}
                    if msg['note'].has_key('proxy') and msg['note']['proxy']:
                        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
                        if user_info.http_proxy != "":
                            proxy["http"] = user_info.http_proxy
                        if user_info.https_proxy != "":
                            proxy["https"] = user_info.https_proxy
                    note_id = msg['note']['note_id']
                    if note_id == None:
                        yield create_note(msg['note'], user, self, user_locale, user_key = user_key, proxy = proxy)
                    elif note_id != None:
                        yield save_note(msg['note'], user, self, user_locale, page = 1, user_key = user_key, proxy = proxy)
            if msg.has_key('category'):
                cmd = msg['category']['cmd']
                LOG.info("category operation: %s", cmd)
                if cmd == 'create':
                    category_name = msg['category']['category_name'].strip()
                    yield create_category(category_name, user, self, user_locale, user_key = user_key);
                elif cmd == 'delete':
                    category_name = msg['category']['category_name'].strip()
                    yield delete_category(category_name, user, self, user_locale, user_key = user_key);
                elif cmd == 'select':
                    category_name = msg['category']['category_name'].strip()
                    yield select_category(category_name, user, self, user_locale, user_key = user_key);
                elif cmd == 'search':
                    yield search_query(msg['category'], user, self, user_locale, page = 1, user_key = user_key);
                elif cmd =='load':
                    category_name = msg['category']['category_name'].strip()
                    offset = msg['category']['offset']
                    note_id = msg['category']['note_id']
                    q = msg['category']['q']
                    yield load_category(category_name, note_id, user, self, user_locale, user_key, offset, q)
            if msg.has_key('reinit'):
                data = {}
                data['notes'] = (yield update_notes('All', user, user_key = user_key, offset = 0))['notes_list']
                if data['notes'] != []:
                    data['note'] = data['notes'][0]
                    data['current_note_id'] = data['notes'][0]['id']
                else:
                    data['note'] = {'file_title':'', 'file_content':'', 'rich_content':''}
                    data['current_note_id'] = None
                if msg['reinit'].has_key('package_name'):
                    user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
                    arch = Archive(user_info)
                    arch.package_path = os.path.join(arch.export_path, msg['reinit']['package_name'])
                    arch.clear()
                data['note_list_action'] = 'init' # init, append
                data['books'] = yield update_categories(user_locale, user)
                data['current_category'] = 'All'
                data['option'] = msg['reinit']['option'] if msg['reinit'].has_key('option') else ''
                send_msg(json.dumps(data), user, self)
        else:
            self.close()
            LOG.info("Server close websocket!")

class ExportHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
        package_name = self.get_argument("package_name", "")
        LOG.debug("Export rich notes package_name: %s", package_name)
        try:
            arch = Archive(user_info)
            arch.package_path = os.path.join(arch.export_path, package_name)
            LOG.debug("package_path: %s", arch.package_path)
            if os.path.exists(arch.package_path) and os.path.isfile(arch.package_path):
                fp = open(arch.package_path, 'rb')
                self.set_header("Content-Disposition", "attachment; filename=%s" % package_name)
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

class ExportAjaxHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        password = self.get_argument("passwd", "")
        encrypt = self.get_argument("encrypt", "")
        encrypt = True if encrypt == "enable" else False
        export_category = self.get_argument("notes_category", "All")
        LOG.debug("Export rich notes category: %s", export_category)
        if password != "" and encrypt:
            password = common_utils.md5twice(password)
        elif password == "" and encrypt:
            password = user_key
        else:
            password = ""
        LOG.info("export rich notes encrypted: %s", encrypt)
        result = {"flag": False}
        try:
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            manager_client = ManagerClient(CONFIG["PROCESS_NUM"])
            flag = yield manager_client.export_rich_notes(export_category, user_info, user_key, password)
            if flag is not False:
                result["flag"] = True
            else:
                LOG.error("Export rich notes user[%s] failed!", user)
        except Exception, e:
            LOG.exception(e)
        self.write(result)

    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        export_category = self.get_argument("notes_category", "All")
        result = {"flag": False, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0}
        try:
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            manager_client = ManagerClient(CONFIG["PROCESS_NUM"])
            flag = yield manager_client.get_export_rate_of_progress(export_category, user_info)
            LOG.debug("export rich notes %s by user[%s] flag: %s, rate: %s/%s, finish: %s, predict_total: %s", export_category, user, flag["flag"], flag["tasks"], flag["total"], flag["finish"], flag["predict_total"])
            result = flag
        except Exception, e:
            LOG.exception(e)
        self.write(result)

class ArchiveAjaxHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        password = self.get_argument("passwd", "")
        encrypt = self.get_argument("encrypt", "")
        encrypt = True if encrypt == "enable" else False
        export_category = self.get_argument("notes_category", "All")
        LOG.debug("Archive rich notes category: %s", export_category)
        if password != "" and encrypt:
            password = common_utils.md5twice(password)
        elif password == "" and encrypt:
            password = user_key
        else:
            password = ""
        LOG.info("archive rich notes encrypted: %s", encrypt)
        result = {"flag": False}
        try:
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            manager_client = ManagerClient(CONFIG["PROCESS_NUM"])
            flag = yield manager_client.archive_rich_notes(export_category, user_info, user_key, password)
            if flag is not False:
                result["flag"] = True
            else:
                LOG.error("Archive rich notes user[%s] failed!", user)
        except Exception, e:
            LOG.exception(e)
        self.write(result)

    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        export_category = self.get_argument("notes_category", "All")
        result = {"flag": False, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0, "package_name": ""}
        try:
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            manager_client = ManagerClient(CONFIG["PROCESS_NUM"])
            flag = yield manager_client.get_archive_rate_of_progress(export_category, user_info)
            LOG.debug("archive rich notes %s by user[%s] flag: %s, rate: %s/%s, finish: %s, predict_total: %s, package_name: %s", export_category, user, flag["flag"], flag["tasks"], flag["total"], flag["finish"], flag["predict_total"], flag["package_name"])
            result = flag
        except Exception, e:
            LOG.exception(e)
        self.write(result)

class DeleteHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
        try:
            flag = Servers.IX_SERVER["RICH"].index_delete_rich_by_user(user, merge = True)
            yield gen.moment
            if flag:
                LOG.info("Delete user[%s] all rich notes index success", user)
                flag = Servers.DB_SERVER["RICH"].delete_rich_by_user(user)
                import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"],
                                           user_info.sha1,
                                           "tmp",
                                           "import",
                                           "rich_notes")
                user_notes_path = os.path.join(CONFIG["STORAGE_USERS_PATH"],
                                               user_info.sha1,
                                               "rich_notes",
                                               "rich_notes")
                user_images_path = os.path.join(CONFIG["STORAGE_USERS_PATH"],
                                                user_info.sha1,
                                                "rich_notes",
                                                "images")
                # delete user rich notes
                if os.path.exists(user_notes_path) and os.path.isdir(user_notes_path):
                    shutil.rmtree(user_notes_path)
                    os.makedirs(user_notes_path)
                if os.path.exists(user_images_path) and os.path.isdir(user_images_path):
                    shutil.rmtree(user_images_path)
                    os.makedirs(user_images_path)
                yield gen.moment
                if user_info:
                    user_info.rich_books = json.dumps([])
                    flag = Servers.DB_SERVER["USER"].save_data_to_db(user_info.to_dict(), mode = "UPDATE")
                    if flag:
                        LOG.info("delete user[%s] all rich note categories success", user)
                    else:
                        LOG.error("delete user[%s] all rich note categories failed", user)
                if os.path.exists(import_path) and os.path.isdir(import_path):
                    shutil.rmtree(import_path)
                    LOG.debug("delete import_path[%s] success.", import_path)
            else:
                LOG.error("Delete user[%s] all rich notes index failed", user)
            self.redirect("/rich")
        except Exception, e:
            LOG.exception(e)
            self.render("info.html", info_msg = "Delete user[%s]'s rich notes failed." % user)

class UploadAjaxHandler(BaseHandler):
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
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
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
                LOG.error("Upload file failed, You must be sure selected a file!")
                LOG.exception(e)
            if fileinfo is not None:
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
        except Exception, e:
            LOG.exception(e)
        self.write({"result":"ok"})

class ImportAjaxHandler(BaseHandler):
    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        result = {"flag": False}
        try:
            fname = self.get_argument("file_name", "")
            fname = os.path.split(fname.replace("\\", "/"))[-1]
            LOG.debug("ImportAjaxHandler fname: %s", fname)
            password = self.get_argument("passwd", "")
            password = common_utils.md5twice(password) if password != "" else ""
            LOG.info("import notes encrypted: %s", True if password != "" else False)
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            manager_client = ManagerClient(CONFIG["PROCESS_NUM"])
            flag = yield manager_client.import_rich_notes(fname, user_info, user_key, password)
            # index all notes
            if flag is not False:
                result["flag"] = True
            else:
                LOG.error("Import notes user[%s] failed!", user)
        except Exception, e:
            LOG.exception(e)
        self.write(result)

    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        result = {"flag": False, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0}
        try:
            fname = self.get_argument("file_name", "")
            fname = os.path.split(fname.replace("\\", "/"))[-1]
            LOG.debug("ImportRateAjaxHandler fname: %s", fname)
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            manager_client = ManagerClient(CONFIG["PROCESS_NUM"])
            flag = yield manager_client.get_rate_of_progress(fname, user_info)
            LOG.debug("import rich notes %s by user[%s] flag: %s, rate: %s/%s, finish: %s, predict_total: %s", fname, user, flag["flag"], flag["tasks"], flag["total"], flag["finish"], flag["predict_total"])
            result = flag
            if flag is not False and flag["flag"] == True:
                import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"],
                                           user_info.sha1,
                                           "tmp",
                                           "import",
                                           "rich_notes",
                                           "rich_notes")
                import_root_path = os.path.split(import_path)[0]
                if os.path.exists(import_root_path) and os.path.isdir(import_root_path):
                    shutil.rmtree(import_root_path)
                    LOG.info("delete import_path[%s] success.", import_root_path)
        except Exception, e:
            LOG.exception(e)
        self.write(result)

@gen.coroutine
def async_index(fname, user_info, key = "", index_batch_size = 1000, merge = False):
    LOG.debug("async_index start")
    multi_process_note_tea = MultiProcessNoteTea(CONFIG["PROCESS_NUM"])
    flag = Servers.IX_SERVER["RICH"].index_delete_rich_by_user(user_info.user_name)
    if flag:
        LOG.info("Delete all rich notes index user[%s] success", user_info.user_name)
    else:
        LOG.error("Delete all rich notes index user[%s] failed!", user_info.user_name)
    IndexAjaxHandler.tasks[get_index_key(fname, user_info)]["total"] += 1
    IndexAjaxHandler.tasks[get_index_key(fname, user_info)]["tasks"] += 1
    notes_iter = Servers.DB_SERVER["RICH"].get_rich_from_db_by_user_iter(user_info.user_name)
    n = 0
    writer = AsyncWriter(Servers.IX_SERVER["RICH"].ix, writerargs = {"procs": CONFIG["ASYNC_WRITER_PROCESS_NUM"]})
    try:
        for note in notes_iter:
            n += 1
            if key != "":
                note.decrypt(key, decrypt_description = False)
                # note = yield multi_process_note_tea.decrypt(note, *(key, False))
            writer.update_document(doc_id = unicode(str(note.id)), 
                                   user_name = note.user_name, 
                                   file_title = note.file_title, 
                                   file_content = note.file_content)
            IndexAjaxHandler.tasks[get_index_key(fname, user_info)]["total"] += 1
            IndexAjaxHandler.tasks[get_index_key(fname, user_info)]["tasks"] += 1
            LOG.debug("Update index[RICH] doc_id[%s]", note.id)
            if n == index_batch_size:
                writer.commit(merge = merge)
                LOG.info("Commit index[RICH] success.")
                writer = AsyncWriter(Servers.IX_SERVER["RICH"].ix, writerargs = {"procs": CONFIG["ASYNC_WRITER_PROCESS_NUM"]})
                n = 0
                yield gen.moment
            if key != "" and n % 5 == 0:
                yield gen.moment
            elif n % 10 == 0:
                yield gen.moment
        if n % index_batch_size != 0:
            s = time.time()
            writer.commit(merge = merge)
            ss = time.time()
            LOG.debug("Commit use %ss", ss - s)
            LOG.info("Commit index[RICH] success.")
            yield gen.moment
    except Exception, e:
        LOG.exception(e)
        writer.cancel()
    IndexAjaxHandler.tasks[get_index_key(fname, user_info)]["flag"] = True
    LOG.debug("async_index exit")

class IndexAjaxHandler(BaseHandler):
    tasks = {}

    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        result = {"flag": False}
        try:
            fname = self.get_argument("file_name", "")
            fname = os.path.split(fname.replace("\\", "/"))[-1]
            key = user_key if CONFIG["ENCRYPT"] else ""
            LOG.debug("IndexAjaxHandler fname: %s", fname)
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            total_tasks = Servers.DB_SERVER["RICH"].get_rich_num_by_user(user)
            IndexAjaxHandler.tasks[get_index_key(fname, user_info)] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": total_tasks if total_tasks is not False else 0}
            ioloop.IOLoop.current().spawn_callback(async_index, fname, user_info, key, merge = True)
            result["flag"] = True
        except Exception, e:
            LOG.exception(e)
        self.write(result)

    @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user_name()
        user_key = self.get_current_user_key()
        result = {"flag": False, "total": 0, "tasks": 0, "finish": 0, "predict_total": 0}
        try:
            fname = self.get_argument("file_name", "")
            fname = os.path.split(fname.replace("\\", "/"))[-1]
            LOG.debug("IndexRateAjaxHandler fname: %s", fname)
            user_info = Servers.DB_SERVER["USER"].get_user_from_db(user)
            flag = IndexAjaxHandler.tasks[get_index_key(fname, user_info)]
            LOG.debug("index rich notes rate %s by user[%s] flag: %s, rate: %s/%s, finish: %s, predict_total: %s", fname, user, flag["flag"], flag["tasks"], flag["total"], flag["finish"], flag["predict_total"])
            if flag["flag"] is True:
                del IndexAjaxHandler.tasks[get_index_key(fname, user_info)]
            result = flag
        except Exception, e:
            LOG.exception(e)
        self.write(result)
