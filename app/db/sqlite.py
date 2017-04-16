# -*- coding: utf-8 -*-
'''
Created on 2013-10-26
@summary: Storage: NOTE.db, HTML.db, PIC.db, RICH.db, USER.db
@Attention: sqlite in python save and get unicode, not utf-8 !!!
@author: YangHaitao

Modified on 2014-05-31
@summary: Add note's categories on USER.db, Add connect timeout = 1800 for multiple process
@author: YangHaitao

Modified on 2014-06-09
@summary: Add note's description on NOTE.db and RICH.db, add function get_note_from_db_by_user_iter
@author: YangHaitao

Modified on 2014-10-29
@summary: USER add sha1
@author: YangHaitao

Modified on 2015-03-02
@summary: Change DB class for singleton mode
@author: YangHaitao
'''

import os
import json
import time
import sqlite3
import logging

from models.item import PICTURE as PIC
from models.item import HTML
from models.item import USER
from models.item import NOTE
from models.item import RICH
from config import CONFIG

LOG = logging.getLogger(__name__)

class DB(object):
    html = "HTML"
    pic = "PIC"
    rich = "RICH"
    note = "NOTE"
    user = "USER"
    flag = "FLAG"
    DB_NAMES = ["html", "pic", "rich", "note", "user", "flag"]

    db_html_path = None
    db_pic_path = None
    db_rich_path = None
    db_note_path = None
    db_user_path = None
    db_flag_path = None
    DB_PATHS = ["db_html_path", "db_pic_path", "db_rich_path",
                "db_note_path", "db_user_path", "db_flag_path"]

    conn_html = None
    conn_pic = None
    conn_rich = None
    conn_note = None
    conn_user = None
    conn_flag = None
    DB_CONNS = ["conn_html", "conn_pic", "conn_rich", 
                "conn_note", "conn_user", "conn_flag"]

    def __init__(self, init_object = True):
        for n, db_path_attr in enumerate(DB.DB_PATHS):
            try:
                if hasattr(DB, db_path_attr) and getattr(DB, db_path_attr) == None:
                    setattr(DB, db_path_attr, get_db_path(CONFIG["STORAGE_DB_PATH"], 
                                                          getattr(DB, DB.DB_NAMES[n])))
                    setattr(DB, DB.DB_CONNS[n], get_conn_sqlite(getattr(DB, DB.DB_PATHS[n])))
                    LOG.info("Init %s success", DB.DB_CONNS[n])
                else:
                    LOG.info("Inited %s success", DB.DB_CONNS[n])
            except Exception, e:
                LOG.info("Init %s failed", DB.DB_CONNS[n])
                LOG.exception(e)
        if init_object:
            self.conn_html = get_conn_sqlite(DB.db_html_path)
            self.conn_pic = get_conn_sqlite(DB.db_pic_path)
            self.conn_rich = get_conn_sqlite(DB.db_rich_path)
            self.conn_note = get_conn_sqlite(DB.db_note_path)
            self.conn_user = get_conn_sqlite(DB.db_user_path)
            self.conn_flag = get_conn_sqlite(DB.db_flag_path)
        else:
            self.conn_html = None
            self.conn_pic = None
            self.conn_rich = None
            self.conn_note = None
            self.conn_user = None
            self.conn_flag = None

    @classmethod
    def cls_close(cls):
        for n, db_conn_attr in enumerate(cls.DB_CONNS):
            try:
                if hasattr(cls, db_conn_attr) and getattr(cls, db_conn_attr):
                    getattr(cls, db_conn_attr).close()
                    setattr(cls, cls.DB_PATHS[n], None)
                LOG.info("Close DB %s success", db_conn_attr)
            except Exception, e:
                LOG.info("Close DB %s failed", db_conn_attr)
                LOG.exception(e)

    def close(self):
        for db_conn_attr in DB.DB_CONNS:
            try:
                if hasattr(self, db_conn_attr) and getattr(self, db_conn_attr):
                    getattr(self, db_conn_attr).close()
                LOG.info("Close %s success", db_conn_attr)
            except Exception, e:
                LOG.info("Close %s failed", db_conn_attr)
                LOG.exception(e)

def get_conn_sqlite(db_path):
    conn = False
    try:
        # start_time = time.time()
        conn = sqlite3.connect(db_path, timeout = 1800, check_same_thread = False)
        # end_time = time.time()
        # LOG.info("get conn time: %s", end_time - start_time)
        #  get conn time: 9.70363616943e-05
    except Exception, e:
        LOG.exception(e)
    return conn

def init_sqlite(db_path, db_type):
    result = False
    try:
        conn = get_conn_sqlite(db_path)
        sql = {DB.html: ("CREATE TABLE HTML (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "sha1 text UNIQUE, "
                         "updated_at timestamp, "
                         "file_name text, "
                         "file_content text, "
                         "file_path text)"), 
               DB.rich: ("CREATE TABLE RICH (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "user_name text, "
                         "sha1 text, "
                         "created_at timestamp, "
                         "updated_at timestamp, "
                         "file_title text, "
                         "file_content text, "
                         "rich_content text, "
                         "file_path text, "
                         "description text, "
                         "images text, "
                         "type text)"), 
               DB.note: ("CREATE TABLE NOTE (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "user_name text, "
                         "sha1 text, "
                         "created_at timestamp, "
                         "updated_at timestamp, "
                         "file_title text, "
                         "file_content text, "
                         "file_path text, "
                         "description text, "
                         "type text)"),
               DB.pic: ("CREATE TABLE PIC (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "sha1 text UNIQUE, "
                        "imported_at timestamp, "
                        "file_name text, "
                        "file_path text)"), 
               DB.user: ("CREATE TABLE USER (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "sha1 text UNIQUE, "
                         "user_name text, "
                         "user_pass text, "
                         "note_books text, "
                         "rich_books text, "
                         "user_language text, "
                         "register_time timestamp, "
                         "http_proxy text, "
                         "https_proxy text)"), 
               DB.flag: ("CREATE TABLE FLAG (index_name text PRIMARY KEY, "
                         "old_index_time timestamp, "
                         "new_index_time timestamp)")
               }
        sql_script = {DB.html: "CREATE INDEX sha1_HTML ON HTML (sha1); CREATE INDEX update_at_HTML ON HTML (updated_at); ", 
                      DB.rich: "CREATE INDEX user_name_RICH ON RICH (user_name);" \
                               "CREATE INDEX created_at_RICH ON RICH (created_at);" \
                               "CREATE INDEX updated_at_RICH ON RICH (updated_at);" \
                               "CREATE UNIQUE INDEX user_name_sha1_RICH ON RICH (user_name, sha1);",
                      DB.note: "CREATE INDEX user_name_NOTE ON NOTE (user_name);" \
                               "CREATE INDEX created_at_NOTE ON NOTE (created_at);" \
                               "CREATE INDEX updated_at_NOTE ON NOTE (updated_at);" \
                               "CREATE UNIQUE INDEX user_name_sha1_NOTE ON NOTE (user_name, sha1);",
                      DB.pic: "CREATE INDEX sha1_PIC ON PIC (sha1);", 
                      DB.user: "CREATE INDEX user_name_USER ON USER (user_name);", 
                      DB.flag: "INSERT INTO FLAG VALUES ('HTML',datetime('now', 'localtime'),datetime('now', 'localtime'));" \
                               "INSERT INTO FLAG VALUES ('RICH',datetime('now', 'localtime'),datetime('now', 'localtime'));" \
                               "INSERT INTO FLAG VALUES ('NOTE',datetime('now', 'localtime'),datetime('now', 'localtime'));"
                      }
        if conn != False:
            c = conn.cursor()
            c.execute(sql[db_type])
            if sql_script.has_key(db_type):
                c.executescript(sql_script[db_type])
            conn.commit()
            LOG.debug("init sqlite %s success.", db_type)
            result = True
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

def get_db_path(root_path, db_type):
    """
    """
    result = False
    try:
        db_file_path = os.path.join(root_path, db_type, db_type + ".db")
        db_root_path = os.path.join(root_path, db_type)
        if os.path.exists(db_root_path) and os.path.isdir(db_root_path):
            if os.path.exists(db_file_path) and os.path.isfile(db_file_path):
                result = db_file_path
                LOG.debug("%s.db exists.", db_type)
            else:
                flag = init_sqlite(db_file_path, db_type)
                if flag == True:
                    result = db_file_path
                    LOG.debug("%s.db do not exists and init db success.", db_type)
                else:
                    result = False
                    LOG.debug("%s.db do not exists and init db failed.", db_type)
        else:
            os.makedirs(db_root_path)
            LOG.debug("[%s] do not exists and makedirs success.", db_root_path)
            flag = init_sqlite(db_file_path, db_type)
            if flag == True:
                result = db_file_path
                LOG.debug("%s.db do not exists and init db success.", db_type)
            else:
                result = False
                LOG.debug("%s.db do not exists and init db failed.", db_type)
    except Exception, e:
        LOG.exception(e)
        result = False
    return result

def update_flag(index_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_flag
        sql = {DB.html: "UPDATE FLAG SET new_index_time = (SELECT old_index_time FROM FLAG WHERE index_name = 'HTML') WHERE index_name = 'HTML';",
               DB.rich: "UPDATE FLAG SET new_index_time = (SELECT old_index_time FROM FLAG WHERE index_name = 'RICH') WHERE index_name = 'RICH';",
               DB.note: "UPDATE FLAG SET new_index_time = (SELECT old_index_time FROM FLAG WHERE index_name = 'NOTE') WHERE index_name = 'NOTE';"
               }
        if conn != False:
            c = conn.cursor()
            c.execute(sql[index_name])
            conn.commit()
            result = True
            LOG.debug("Update old_time to new_time to %s success.", index_name)
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

def update_old_flag(index_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_flag
        sql = {DB.html: "UPDATE FLAG SET old_index_time = datetime('now', 'localtime') WHERE index_name = 'HTML';",
               DB.rich: "UPDATE FLAG SET old_index_time = datetime('now', 'localtime') WHERE index_name = 'RICH';",
               DB.note: "UPDATE FLAG SET old_index_time = datetime('now', 'localtime') WHERE index_name = 'NOTE';"
               }
        if conn != False:
            c = conn.cursor()
            c.execute(sql[index_name])
            conn.commit()
            result = True
            LOG.debug("Update old_time to %s success.", index_name, )
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

def get_flag_from_db(index_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_flag
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM FLAG WHERE index_name = '%s'" % index_name)
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the flag in db[%s], so i will return None", index_name)
                result = None
            else:
                result = i[2]
                LOG.debug("Get a flag[%s] from db[%s] success.", result, index_name)
    except Exception, e:
        LOG.exception(e)
    return result

def save_data_to_db(item, db_type, mode = "INSERT OR UPDATE", conn = None, retries = 3):
    result = False
    sql = {DB.html: "INSERT INTO HTML VALUES (NULL,?,?,?,?,?)",
           DB.rich: "INSERT INTO RICH VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)",
           DB.note: "INSERT INTO NOTE VALUES (NULL,?,?,?,?,?,?,?,?,?)",
           DB.pic: "INSERT INTO PIC VALUES (NULL,?,?,?,?)",
           DB.user: "INSERT INTO USER VALUES (NULL,?,?,?,?,?,?,?,?,?)"
           }
    sql_update = {DB.html: ("UPDATE HTML SET "
                            "updated_at = ?, "
                            "file_name = ?, "
                            "file_content = ?, "
                            "file_path = ? "
                            "WHERE sha1 = ?;"),
                  DB.rich: ("UPDATE RICH SET "
                            "updated_at = ?, "
                            "sha1 = ?, "
                            "file_title = ?, "
                            "file_content = ?, "
                            "rich_content = ?, "
                            "file_path = ?, "
                            "description = ?, "
                            "images = ?, "
                            "type = ? "
                            "WHERE id = ?;"),
                  DB.note: ("UPDATE NOTE SET "
                            "updated_at = ?, "
                            "sha1 = ?, "
                            "file_title = ?, "
                            "file_content = ?, "
                            "file_path = ?, "
                            "description = ?, "
                            "type = ? "
                            "WHERE id = ?;"),
                  DB.pic: ("UPDATE PIC SET "
                           "file_name = ?, "
                           "file_path = ? "
                           "WHERE sha1 = ?;"),
                  DB.user: ("UPDATE USER SET "
                            "user_pass = ?, "
                            "note_books = ?, "
                            "rich_books = ?, "
                            "user_language = ?, "
                            "http_proxy = ?, "
                            "https_proxy = ? "
                            "WHERE user_name = ?;")
                  }

    sql_param = ()
    sql_update_param = ()
    if db_type == DB.html:
        if conn == None:
            conn = DB.conn_html
        sql_param = (item["sha1"],
                     item["updated_at"],
                     item["file_name"],
                     item["file_content"],
                     item["file_path"])
        sql_update_param = (item["updated_at"],
                            item["file_name"],
                            item["file_content"],
                            item["file_path"],
                            item["sha1"])
    elif db_type == DB.rich:
        if conn == None:
            conn = DB.conn_rich
        sql_param = (item["user_name"],
                     item["sha1"],
                     item["created_at"],
                     item["updated_at"],
                     item["file_title"],
                     item["file_content"],
                     item["rich_content"],
                     item["file_path"],
                     item["description"],
                     item["images"],
                     item["type"])
        sql_update_param = (item["updated_at"],
                            item["sha1"],
                            item["file_title"],
                            item["file_content"],
                            item["rich_content"],
                            item["file_path"],
                            item["description"],
                            item["images"],
                            item["type"],
                            item["id"])
    elif db_type == DB.note:
        if conn == None:
            conn = DB.conn_note
        sql_param = (item["user_name"],
                     item["sha1"],
                     item["created_at"],
                     item["updated_at"],
                     item["file_title"],
                     item["file_content"],
                     item["file_path"],
                     item["description"],
                     item["type"])
        sql_update_param = (item["updated_at"],
                            item["sha1"],
                            item["file_title"],
                            item["file_content"],
                            item["file_path"],
                            item["description"],
                            item["type"],
                            item["id"])
    elif db_type == DB.pic:
        if conn == None:
            conn = DB.conn_pic
        sql_param = (item["sha1"],
                     item["imported_at"],
                     item["file_name"],
                     item["file_path"])
        sql_update_param = (item["file_name"],
                            item["file_path"],
                            item["sha1"])
    elif db_type == DB.user:
        if conn == None:
            conn = DB.conn_user
        sql_param = (item["sha1"],
                     item["user_name"],
                     item["user_pass"],
                     item["note_books"],
                     item["rich_books"],
                     item["user_language"],
                     item["register_time"],
                     item["http_proxy"],
                     item["https_proxy"])
        sql_update_param = (item["user_pass"],
                            item["note_books"],
                            item["rich_books"],
                            item["user_language"],
                            item["http_proxy"],
                            item["https_proxy"],
                            item["user_name"])

    for i in xrange(retries):
        # if db_type in locks:
        #     locks[db_type].acquire()
        try:
            if conn != False:
                c = conn.cursor()
                if mode == "UPDATE":
                    c.execute(sql_update[db_type], sql_update_param)
                else:
                    c.execute(sql[db_type], sql_param)
                conn.commit()
                result = True
                if db_type == DB.user:
                    LOG.debug("Save data item[%s] to %s success.", item["user_name"], db_type)
                else:
                    LOG.debug("Save data item[%s] to %s success.", item["id"], db_type)
                break
        except sqlite3.IntegrityError:
            try:
                if mode == "INSERT OR UPDATE":
                    if db_type != DB.user:
                        LOG.info("The item[%s] have been in %s service, so update it!", item["id"], db_type)
                        if conn != False:
                            c = conn.cursor()
                            c.execute(sql_update[db_type], sql_update_param)
                            conn.commit()
                            result = True
                            LOG.debug("Update data item[%s] to %s success.", item["id"], db_type)
                            break
                    else:
                        result = False
                        LOG.info("The item[%s] have been in %s service, so ignore the insert action!", item["id"], db_type)
                        break
                else:
                    result = None
                    break
            except sqlite3.IntegrityError:
                result = None
                LOG.info("The same item[%s] have been in %s service, so ignore the insert & update action!", item["id"], db_type)
                break
        except Exception, e:
            if conn:
                conn.rollback()
            if i < retries - 1:
                time.sleep(0.5)
            else:
                LOG.exception(e)
        # if db_type in locks:
        #     locks[db_type].release()
    # finally:
    #     if conn:
    #         conn.close()
    return result

#
# functions for picture
#

def get_data_from_db(conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_pic
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM PIC")
            result = []
            i = c.fetchone()
            while i != None:
                item = PIC()
                item.id = i[0]
                item.sha1 = i[1]
                item.imported_at = i[2]
                item.file_name = i[3]
                item.file_path = i[4]
                result.append(item)
                i = c.fetchone()
            LOG.debug("get all picture from db success.")
    except Exception, e:
        LOG.exception(e)
    return result

def get_data_by_sha1(sha1, conn = None):
    """
    return None when no item.
    """
    result = False
    try:
        if conn == None:
            conn = DB.conn_pic
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM PIC WHERE sha1 = '%s'" % sha1)
            i = c.fetchone()
            if i != None:
                item = PIC()
                item.id = i[0]
                item.sha1 = i[1]
                item.imported_at = i[2]
                item.file_name = i[3]
                item.file_path = i[4]
                result = item
            else:
                result = None
            LOG.debug("get picture from db by sha1[%s] success.", sha1)
    except Exception, e:
        LOG.exception(e)
    return result
#
# functions for note
#
def get_note_by_user_type_created_at(user_name, note_type, order = "DESC", offset = 0, limit = 20, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            if note_type.lower() == "all":
                c.execute("SELECT * FROM NOTE WHERE user_name = '%s' ORDER BY "\
                          "created_at %s LIMIT %s OFFSET %s" % (user_name, order, limit, offset))
            else:
                c.execute("SELECT * FROM NOTE WHERE user_name = '%s' AND type = '%s' ORDER BY "\
                          "created_at %s LIMIT %s OFFSET %s" % (user_name, note_type, order, limit, offset))
            result = []
            i = c.fetchone()
            while i != None:
                item = NOTE()
                item.id = i[0]
                item.user_name = i[1]
                item.sha1 = i[2]
                item.created_at = i[3]
                item.updated_at = i[4]
                item.file_title = i[5]
                item.file_content = i[6]
                item.file_path = i[7]
                item.description = i[8]
                item.type = i[9]
                result.append(item)
                i = c.fetchone()
            LOG.debug("get all note from db success.")
    except Exception, e:
        LOG.exception(e)
    return result

def get_note_by_flag_iter(flag, conn = None):
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM NOTE WHERE updated_at > '%s'" % flag)
            total = 0
            i = c.fetchone()
            while i != None:
                item = NOTE()
                item.id = i[0]
                item.user_name = i[1]
                item.sha1 = i[2]
                item.created_at = i[3]
                item.updated_at = i[4]
                item.file_title = i[5]
                item.file_content = i[6]
                item.file_path = i[7]
                item.description = i[8]
                item.type = i[9]
                LOG.debug("Get note[%s] from db success.", item.file_title)
                total += 1
                yield item
                i = c.fetchone()
            LOG.debug("Get all note[%s] from db success.", total)
    except Exception, e:
        LOG.exception(e)

def get_note_from_db_iter(conn = None, batch = 100):
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            offset = 0
            limit = batch
            finish = False
            total = 0
            while not finish:
                c.execute("SELECT * FROM NOTE LIMIT %s OFFSET %s" % (limit, offset))
                result = c.fetchall()
                for i in result:
                    item = NOTE()
                    item.id = i[0]
                    item.user_name = i[1]
                    item.sha1 = i[2]
                    item.created_at = i[3]
                    item.updated_at = i[4]
                    item.file_title = i[5]
                    item.file_content = i[6]
                    item.file_path = i[7]
                    item.description = i[8]
                    item.type = i[9]
                    LOG.debug("Get note[%s] from db success.", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all note[%s] from db success.", total)
    except Exception, e:
        LOG.exception(e)

def get_note_from_db_by_user_iter(user_name, conn = None, batch = 100):
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            offset = 0
            limit = batch
            finish = False
            total = 0
            while not finish:
                c.execute("SELECT * FROM NOTE WHERE user_name = '%s' LIMIT %s OFFSET %s" % (user_name, limit, offset))
                result = c.fetchall()
                for i in result:
                    item = NOTE()
                    item.id = i[0]
                    item.user_name = i[1]
                    item.sha1 = i[2]
                    item.created_at = i[3]
                    item.updated_at = i[4]
                    item.file_title = i[5]
                    item.file_content = i[6]
                    item.file_path = i[7]
                    item.description = i[8]
                    item.type = i[9]
                    LOG.debug("Get note[%s] from db success.", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all note[%s] by user[%s] from db success.", total, user_name)
    except Exception, e:
        LOG.exception(e)

def get_note_from_db_by_user_type_iter(user_name, note_type, conn = None, batch = 100):
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            offset = 0
            limit = batch
            finish = False
            total = 0
            while not finish:
                if note_type == "All":
                    c.execute("SELECT * FROM NOTE WHERE user_name = '%s' LIMIT %s OFFSET %s" % (user_name, limit, offset))
                else:
                    c.execute("SELECT * FROM NOTE WHERE user_name = '%s' and type = '%s' LIMIT %s OFFSET %s" % (user_name, note_type, limit, offset))
                result = c.fetchall()
                for i in result:
                    item = NOTE()
                    item.id = i[0]
                    item.user_name = i[1]
                    item.sha1 = i[2]
                    item.created_at = i[3]
                    item.updated_at = i[4]
                    item.file_title = i[5]
                    item.file_content = i[6]
                    item.file_path = i[7]
                    item.description = i[8]
                    item.type = i[9]
                    LOG.debug("Get note[%s] from db success.", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all note[%s] by user[%s] type[%s] from db success.", total, user_name, note_type)
    except Exception, e:
        LOG.exception(e)

def get_note_by_id(doc_id, user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM NOTE WHERE id = %s and user_name = '%s'" % (doc_id, user_name))
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the note[%s] by user[%s], so i will return None", doc_id, user_name)
                result = None
            else:
                item = NOTE()
                item.id = i[0]
                item.user_name = i[1]
                item.sha1 = i[2]
                item.created_at = i[3]
                item.updated_at = i[4]
                item.file_title = i[5]
                item.file_content = i[6]
                item.file_path = i[7]
                item.description = i[8]
                item.type = i[9]
                result = item
            LOG.debug("Get a user[%s]'s note[%s] from db success.", user_name, doc_id)
    except Exception, e:
        LOG.exception(e)
    return result

def get_note_by_sha1(sha1, user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM NOTE WHERE sha1 = '%s' and user_name = '%s'" % (sha1, user_name))
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the note[%s] by user[%s], so i will return None", sha1, user_name)
                result = None
            else:
                item = NOTE()
                item.id = i[0]
                item.user_name = i[1]
                item.sha1 = i[2]
                item.created_at = i[3]
                item.updated_at = i[4]
                item.file_title = i[5]
                item.file_content = i[6]
                item.file_path = i[7]
                item.description = i[8]
                item.type = i[9]
                result = item
            LOG.debug("Get a user[%s]'s note[%s] from db success.", user_name, sha1)
    except Exception, e:
        LOG.exception(e)
    return result

def get_note_num_by_type_user(note_type, user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT count(*) FROM NOTE WHERE user_name = '%s' and type = '%s'" % (user_name, note_type))
            i = c.fetchone()
            result = i[0]
            LOG.debug("Get user[%s]'s notebook[%s] num[%s] from db success.", user_name, note_type, i)
    except Exception, e:
        LOG.exception(e)
    return result

def delete_note_by_id(user_name, doc_id, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            c.execute("DELETE FROM NOTE WHERE user_name = '%s' and id = %s" % (user_name, doc_id))
            conn.commit()
            result = True
            LOG.debug("Delete note[%s] by user[%s] from db success.", doc_id, user_name)
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

def delete_note_by_type(user_name, note_type, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            c.execute("DELETE FROM NOTE WHERE user_name = '%s' and type = '%s'" % (user_name, note_type))
            conn.commit()
            result = True
            LOG.debug("Delete notes type[%s] by user[%s] from db success.", note_type, user_name)
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result


def delete_note_by_user(user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_note
        if conn != False:
            c = conn.cursor()
            c.execute("DELETE FROM NOTE WHERE user_name = '%s'" % user_name)
            conn.commit()
            result = True
            LOG.debug("Delete all note by user[%s] from db success.", user_name)
    except Exception, e:
        LOG.debug("Delete all note by user[%s] from db failed.", user_name)
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

#
# functions for rich note
#
def get_rich_by_user_type_created_at(user_name, note_type, order = "DESC", offset = 0, limit = 20, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            if note_type.lower() == "all":
                c.execute("SELECT * FROM RICH WHERE user_name = '%s' ORDER BY "\
                          "created_at %s LIMIT %s OFFSET %s" % (user_name, order, limit, offset))
            else:
                c.execute("SELECT * FROM RICH WHERE user_name = '%s' AND type = '%s' ORDER BY "\
                          "created_at %s LIMIT %s OFFSET %s" % (user_name, note_type, order, limit, offset))
            result = []
            i = c.fetchone()
            while i != None:
                item = RICH()
                item.id = i[0]
                item.user_name = i[1]
                item.sha1 = i[2]
                item.created_at = i[3]
                item.updated_at = i[4]
                item.file_title = i[5]
                item.file_content = i[6]
                item.rich_content = i[7]
                item.file_path = i[8]
                item.description = i[9]
                item.images = json.loads(i[10])
                item.type = i[11]
                result.append(item)
                i = c.fetchone()
            LOG.debug("get all rich from db success.")
    except Exception, e:
        LOG.exception(e)
    return result

def get_rich_by_flag_iter(flag, conn = None):
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM RICH WHERE updated_at > '%s'" % flag)
            total = 0
            i = c.fetchone()
            while i != None:
                item = RICH()
                item.id = i[0]
                item.user_name = i[1]
                item.sha1 = i[2]
                item.created_at = i[3]
                item.updated_at = i[4]
                item.file_title = i[5]
                item.file_content = i[6]
                item.rich_content = i[7]
                item.file_path = i[8]
                item.description = i[9]
                item.images = json.loads(i[10])
                item.type = i[11]
                LOG.debug("Get rich[%s] from db success.", item.file_title)
                total += 1
                yield item
                i = c.fetchone()
            LOG.debug("Get all rich[%s] from db success.", total)
    except Exception, e:
        LOG.exception(e)

def get_rich_from_db_iter(conn = None, batch = 100):
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            offset = 0
            limit = batch
            finish = False
            total = 0
            while not finish:
                c.execute("SELECT * FROM RICH LIMIT %s OFFSET %s" % (limit, offset))
                result = c.fetchall()
                for i in result:
                    item = RICH()
                    item.id = i[0]
                    item.user_name = i[1]
                    item.sha1 = i[2]
                    item.created_at = i[3]
                    item.updated_at = i[4]
                    item.file_title = i[5]
                    item.file_content = i[6]
                    item.rich_content = i[7]
                    item.file_path = i[8]
                    item.description = i[9]
                    item.images = json.loads(i[10])
                    item.type = i[11]
                    LOG.debug("Get rich[%s] from db success.", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all rich[%s] from db success.", total)
    except Exception, e:
        LOG.exception(e)

def get_rich_from_db_by_user_iter(user_name, conn = None, batch = 100):
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            offset = 0
            limit = batch
            finish = False
            total = 0
            while not finish:
                c.execute("SELECT * FROM RICH WHERE user_name = '%s' ORDER BY id LIMIT %s OFFSET %s" % (user_name, limit, offset))
                result = c.fetchall()
                for i in result:
                    item = RICH()
                    item.id = i[0]
                    item.user_name = i[1]
                    item.sha1 = i[2]
                    item.created_at = i[3]
                    item.updated_at = i[4]
                    item.file_title = i[5]
                    item.file_content = i[6]
                    item.rich_content = i[7]
                    item.file_path = i[8]
                    item.description = i[9]
                    item.images = json.loads(i[10])
                    item.type = i[11]
                    LOG.debug("Get rich[%s] from db success.", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all rich[%s] by user[%s] from db success.", total, user_name)
    except Exception, e:
        LOG.exception(e)

def get_rich_from_db_by_user_type_iter(user_name, note_type, conn = None, batch = 100):
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            offset = 0
            limit = batch
            finish = False
            total = 0
            while not finish:
                if note_type == "All":
                    c.execute("SELECT * FROM RICH WHERE user_name = '%s' ORDER BY id LIMIT %s OFFSET %s" % (user_name, limit, offset))
                else:
                    c.execute("SELECT * FROM RICH WHERE user_name = '%s' and type = '%s' ORDER BY id LIMIT %s OFFSET %s" % (user_name, note_type, limit, offset))
                result = c.fetchall()
                for i in result:
                    item = RICH()
                    item.id = i[0]
                    item.user_name = i[1]
                    item.sha1 = i[2]
                    item.created_at = i[3]
                    item.updated_at = i[4]
                    item.file_title = i[5]
                    item.file_content = i[6]
                    item.rich_content = i[7]
                    item.file_path = i[8]
                    item.description = i[9]
                    item.images = json.loads(i[10])
                    item.type = i[11]
                    LOG.debug("Get rich[%s] from db success.", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True

            LOG.debug("Get all rich[%s] by user[%s] type[%s] from db success.", total, user_name, note_type)
    except Exception, e:
        LOG.exception(e)

def get_rich_by_id(doc_id, user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM RICH WHERE id = %s and user_name = '%s'" % (doc_id, user_name))
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the rich[%s] by user[%s], so i will return None", doc_id, user_name)
                result = None
            else:
                item = RICH()
                item.id = i[0]
                item.user_name = i[1]
                item.sha1 = i[2]
                item.created_at = i[3]
                item.updated_at = i[4]
                item.file_title = i[5]
                item.file_content = i[6]
                item.rich_content = i[7]
                item.file_path = i[8]
                item.description = i[9]
                item.images = json.loads(i[10])
                item.type = i[11]
                result = item
            LOG.debug("Get a user[%s]'s rich[%s] from db success.", user_name, doc_id)
    except Exception, e:
        LOG.exception(e)
    return result

def get_rich_by_sha1(sha1, user_name, conn = None, retries = 3):
    result = False
    for i in xrange(retries):
        try:
            if conn == None:
                conn = DB.conn_rich
            if conn != False:
                c = conn.cursor()
                c.execute("SELECT * FROM RICH WHERE sha1 = '%s' and user_name = '%s'" % (sha1, user_name))
                i = c.fetchone()
                if i is None:
                    LOG.warning("Can not find the rich[%s] by user[%s], so i will return None", sha1, user_name)
                    result = None
                else:
                    item = RICH()
                    item.id = i[0]
                    item.user_name = i[1]
                    item.sha1 = i[2]
                    item.created_at = i[3]
                    item.updated_at = i[4]
                    item.file_title = i[5]
                    item.file_content = i[6]
                    item.rich_content = i[7]
                    item.file_path = i[8]
                    item.description = i[9]
                    item.images = json.loads(i[10])
                    item.type = i[11]
                    result = item
                LOG.debug("Get a user[%s]'s rich[%s] from db success.", user_name, sha1)
                break
        except Exception, e:
            if i < retries - 1:
                time.sleep(0.5)
            else:
                LOG.exception(e)
    return result

def get_rich_num_by_type_user(note_type, user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT count(*) FROM RICH WHERE user_name = '%s' and type = '%s'" % (user_name, note_type))
            i = c.fetchone()
            result = i[0]
            # print "Num: %s"%result, type(i)
            LOG.debug("Get user[%s]'s rich notebook[%s] num[%s] from db success.", user_name, note_type, i)
    except Exception, e:
        LOG.exception(e)
    return result

def delete_rich_by_id(user_name, doc_id, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            c.execute("DELETE FROM RICH WHERE user_name = '%s' and id = %s" % (user_name, doc_id))
            conn.commit()
            result = True
            LOG.debug("Delete rich[%s] by user[%s] from db success." % (doc_id, user_name))
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

def delete_rich_by_type(user_name, note_type, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            c.execute("DELETE FROM RICH WHERE user_name = '%s' and type = '%s'" % (user_name, note_type))
            conn.commit()
            result = True
            LOG.debug("Delete rich notes type[%s] by user[%s] from db success.", note_type, user_name)
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

def delete_rich_by_user(user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_rich
        if conn != False:
            c = conn.cursor()
            c.execute("DELETE FROM RICH WHERE user_name = '%s'" % user_name)
            conn.commit()
            result = True
            LOG.debug("Delete all rich by user[%s] from db success.", user_name)
    except Exception, e:
        LOG.debug("Delete all rich by user[%s] from db failed.", user_name)
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result

#
# function for html
#
def get_html_from_db(conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_html
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM HTML")
            result = []
            i = c.fetchone()
            while i != None:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                result.append(html)
                i = c.fetchone()
            LOG.debug("Get all html[%s] from db success.", len(result))
    except Exception, e:
        LOG.exception(e)
    return result

def get_html_from_db_iter(conn = None):
    try:
        if conn == None:
            conn = DB.conn_html
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM HTML WHERE updated_at > '%s'" % flag)
            total = 0
            i = c.fetchone()
            while i != None:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                LOG.debug("Get html[%s] from db success.", html.file_name)
                total += 1
                yield html
                i = c.fetchone()
            LOG.debug("Get all html[%s] from db success.", total)
    except Exception, e:
        LOG.exception(e)

def get_html_by_flag_iter(flag, conn = None):
    try:
        if conn == None:
            conn = DB.conn_html
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM HTML WHERE updated_at > '%s'" % flag)
            total = 0
            i = c.fetchone()
            while i != None:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                LOG.debug("Get html[%s] from db success.", html.file_name)
                total += 1
                yield html
                i = c.fetchone()
            LOG.debug("Get all html[%s] from db success.", total)
    except Exception, e:
        LOG.exception(e)

def get_html_by_id(doc_id, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_html
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM HTML WHERE id = %s" % doc_id)
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the html[%s], so i will return None", doc_id)
                result = None
            else:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                result = html
            LOG.debug("Get a html[%s] from db success.", doc_id)
    except Exception, e:
        LOG.exception(e)
    return result

def get_html_by_sha1(sha1, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_html
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM HTML WHERE sha1 = '%s'" % sha1)
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the html[%s], so i will return None", sha1)
                result = None
            else:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                result = html
            LOG.debug("Get a html[%s] from db success.", sha1)
    except Exception, e:
        LOG.exception(e)
    return result

def get_html_num_from_db(conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_html
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT count(*) FROM HTML")
            i = c.fetchone()
            result = i
            LOG.debug("Get a html num[%s] from db success.", i)
    except Exception, e:
        LOG.exception(e)
    return result

#
# function for user
#
def get_user_from_db(user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_user
        if conn != False:
            c = conn.cursor()
            c.execute("SELECT * FROM USER WHERE user_name = '%s';" % user_name)
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the user[%s], so i will return None", user_name)
                result = None
            else:
                user = USER()
                user.id = i[0]
                user.sha1 = i[1]
                user.user_name = i[2]
                user.user_pass = i[3]
                user.note_books = i[4]
                user.rich_books = i[5]
                user.user_language = i[6]
                user.register_time = i[7]
                user.http_proxy = i[8]
                user.https_proxy = i[9]
                result = user
            LOG.debug("Get user[%s] data from db success.", user_name)
    except Exception, e:
        LOG.exception(e)
    return result

def delete_user_from_db(user_name, conn = None):
    result = False
    try:
        if conn == None:
            conn = DB.conn_user
        if conn != False:
            c = conn.cursor()
            c.execute("DELETE FROM USER WHERE user_name = '%s'" % user_name)
            conn.commit()
            result = True
            LOG.debug("Delete user[%s] from db success.", user_name)
    except Exception, e:
        if conn:
            conn.rollback()
        LOG.exception(e)
    return result
