# -*- coding: utf-8 -*-
'''
Created on 2017-02-09
@summary: Storage: NOTE.db
@Attention: sqlite in python save and get unicode, not utf-8 !!!
@author: YangHaitao
'''

import time
import logging
import sqlite3

from config import CONFIG
from models.item import NOTE
from db.sqlite import get_db_path, get_conn_sqlite

LOG = logging.getLogger(__name__)

class DB(object):
    def __init__(self):
        self.name = "NOTE"
        self.db_path = get_db_path(CONFIG["STORAGE_DB_PATH"], self.name)
        self.conn = get_conn_sqlite(self.db_path)

    def close(self):
        try:
            if self.conn:
                self.conn.close()
            LOG.info("Close note conn success")
        except Exception, e:
            LOG.warning("Close note conn failed")
            LOG.exception(e)

    def save_data_to_db(self, item, mode = "INSERT OR UPDATE", retries = 3):
        result = False
        sql = "INSERT INTO NOTE VALUES (NULL,?,?,?,?,?,?,?,?,?)"
        sql_update = ("UPDATE NOTE SET "
                      "updated_at = ?, "
                      "sha1 = ?, "
                      "file_title = ?, "
                      "file_content = ?, "
                      "file_path = ?, "
                      "description = ?, "
                      "type = ? "
                      "WHERE id = ?;")
        sql_update_unique = ("UPDATE NOTE SET "
                             "updated_at = ?, "
                             "sha1 = ?, "
                             "file_title = ?, "
                             "file_content = ?, "
                             "file_path = ?, "
                             "description = ?, "
                             "type = ? "
                             "WHERE user_name = ? AND sha1 = ?;")
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
        sql_update_unique_param = (item["updated_at"],
                                   item["sha1"],
                                   item["file_title"],
                                   item["file_content"],
                                   item["file_path"],
                                   item["description"],
                                   item["type"],
                                   item["user_name"],
                                   item["sha1"])

        for i in xrange(retries):
            try:
                c = self.conn.cursor()
                if mode == "UPDATE":
                    c.execute(sql_update, sql_update_param)
                else:
                    c.execute(sql, sql_param)
                self.conn.commit()
                result = True
                LOG.debug("Save data item[%s] to note success", item["id"])
                break
            except sqlite3.IntegrityError:
                try:
                    if mode == "INSERT OR UPDATE":
                        LOG.info("The item[user_name: %s, sha1: %s] have been in note service, so update it!", item["user_name"], item["sha1"])
                        c = self.conn.cursor()
                        c.execute(sql_update_unique, sql_update_unique_param)
                        self.conn.commit()
                        result = True
                        LOG.debug("Update data item[user_name: %s, sha1: %s] to note success.", item["user_name"], item["sha1"])
                        break
                    else:
                        result = None
                        break
                except sqlite3.IntegrityError:
                    result = None
                    LOG.info("The same item[%s] have been in note service, so ignore the insert & update action!", item["id"])
                    break
            except Exception, e:
                if self.conn:
                    self.conn.rollback()
                if i < retries - 1:
                    time.sleep(0.5)
                else:
                    LOG.exception(e)
        # finally:
        #     if conn:
        #         conn.close()
        return result

    def get_note_by_user_type_created_at(self, user_name, note_type, order = "DESC", offset = 0, limit = 20):
        result = False
        try:
            c = self.conn.cursor()
            if note_type.lower() == "all":
                c.execute("SELECT * FROM NOTE WHERE user_name = '%s' ORDER BY "\
                          "created_at %s LIMIT %s OFFSET %s" % (user_name, order, limit, offset))
            else:
                c.execute("SELECT * FROM NOTE WHERE user_name = '%s' AND type = '%s' ORDER BY "\
                          "created_at %s LIMIT %s OFFSET %s" % (user_name, note_type, order, limit, offset))
            result = []
            i = c.fetchone()
            while i is not None:
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
            LOG.debug("get all note from db success")
        except Exception, e:
            LOG.exception(e)
        return result

    def get_note_by_flag_iter(self, flag):
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM NOTE WHERE updated_at > '%s'" % flag)
            total = 0
            i = c.fetchone()
            while i is not None:
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
                LOG.debug("Get note[%s] from db success", item.file_title)
                total += 1
                yield item
                i = c.fetchone()
            LOG.debug("Get all note[%s] from db success", total)
        except Exception, e:
            LOG.exception(e)

    def get_note_from_db_iter(self, batch = 100):
        try:
            c = self.conn.cursor()
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
                    LOG.debug("Get note[%s] from db success", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all note[%s] from db success", total)
        except Exception, e:
            LOG.exception(e)

    def get_note_from_db_by_user_iter(self, user_name, batch = 100):
        try:
            c = self.conn.cursor()
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
                    LOG.debug("Get note[%s] from db success", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all note[%s] by user[%s] from db success", total, user_name)
        except Exception, e:
            LOG.exception(e)

    def get_note_from_db_by_user_type_iter(self, user_name, note_type, batch = 100):
        try:
            c = self.conn.cursor()
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
                    LOG.debug("Get note[%s] from db success", item.file_title)
                    total += 1
                    yield item
                if len(result) == limit:
                    offset += limit
                else:
                    finish = True
            LOG.debug("Get all note[%s] by user[%s] type[%s] from db success", total, user_name, note_type)
        except Exception, e:
            LOG.exception(e)

    def get_note_by_id(self, doc_id, user_name):
        result = False
        try:
            c = self.conn.cursor()
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
            LOG.debug("Get a user[%s]'s note[%s] from db success", user_name, doc_id)
        except Exception, e:
            LOG.exception(e)
        return result

    def get_note_by_sha1(self, sha1, user_name):
        result = False
        try:
            c = self.conn.cursor()
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
            LOG.debug("Get a user[%s]'s note[%s] from db success", user_name, sha1)
        except Exception, e:
            LOG.exception(e)
        return result

    def get_note_num_by_type_user(self, note_type, user_name):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("SELECT count(*) FROM NOTE WHERE user_name = '%s' and type = '%s'" % (user_name, note_type))
            i = c.fetchone()
            result = i[0]
            LOG.debug("Get user[%s]'s notebook[%s] num[%s] from db success", user_name, note_type, i)
        except Exception, e:
            LOG.exception(e)
        return result

    def get_note_num_by_user(self, user_name):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("SELECT count(*) FROM NOTE WHERE user_name = '%s'" % (user_name, ))
            i = c.fetchone()
            result = i[0]
            LOG.debug("Get user[%s]'s notes num[%s] from db success", user_name, i)
        except Exception, e:
            LOG.exception(e)
        return result

    def delete_note_by_id(self, user_name, doc_id):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM NOTE WHERE user_name = '%s' and id = %s" % (user_name, doc_id))
            self.conn.commit()
            result = True
            LOG.debug("Delete note[%s] by user[%s] from db success", doc_id, user_name)
        except Exception, e:
            if self.conn:
                self.conn.rollback()
            LOG.exception(e)
        return result

    def delete_note_by_type(self, user_name, note_type):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM NOTE WHERE user_name = '%s' and type = '%s'" % (user_name, note_type))
            self.conn.commit()
            result = True
            LOG.debug("Delete notes type[%s] by user[%s] from db success", note_type, user_name)
        except Exception, e:
            if self.conn:
                self.conn.rollback()
            LOG.exception(e)
        return result

    def delete_note_by_user(self, user_name):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM NOTE WHERE user_name = '%s'" % user_name)
            self.conn.commit()
            result = True
            LOG.debug("Delete all note by user[%s] from db success", user_name)
        except Exception, e:
            LOG.debug("Delete all note by user[%s] from db failed", user_name)
            if self.conn:
                self.conn.rollback()
            LOG.exception(e)
        return result
