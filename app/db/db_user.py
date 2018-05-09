# -*- coding: utf-8 -*-
'''
Created on 2017-02-09
@summary: Storage: USER.db
@Attention: sqlite in python save and get unicode, not utf-8 !!!
@author: YangHaitao
'''

import time
import logging
import sqlite3

from config import CONFIG
from models.item import USER
from db.sqlite import get_db_path, get_conn_sqlite

LOG = logging.getLogger(__name__)

class DB(object):
    def __init__(self):
        self.name = "USER"
        self.db_path = get_db_path(CONFIG["STORAGE_DB_PATH"], self.name)
        self.conn = get_conn_sqlite(self.db_path)

    def close(self):
        try:
            if self.conn:
                self.conn.close()
            LOG.info("Close user conn success")
        except Exception, e:
            LOG.warning("Close user conn failed")
            LOG.exception(e)

    def save_data_to_db(self, item, mode = "INSERT OR UPDATE", retries = 3):
        result = False
        sql = "INSERT INTO USER VALUES (NULL,?,?,?,?,?,?,?,?,?,?)"
        sql_update = ("UPDATE USER SET "
                      "user_pass = ?, "
                      "note_books = ?, "
                      "rich_books = ?, "
                      "user_language = ?, "
                      "http_proxy = ?, "
                      "https_proxy = ?, "
                      "socks_proxy = ? "
                      "WHERE user_name = ?;")
        sql_param = (item["sha1"],
                     item["user_name"],
                     item["user_pass"],
                     item["note_books"],
                     item["rich_books"],
                     item["user_language"],
                     item["register_time"],
                     item["http_proxy"],
                     item["https_proxy"],
                     item["socks_proxy"])
        sql_update_param = (item["user_pass"],
                            item["note_books"],
                            item["rich_books"],
                            item["user_language"],
                            item["http_proxy"],
                            item["https_proxy"],
                            item["socks_proxy"],
                            item["user_name"])

        for i in xrange(retries):
            try:
                c = self.conn.cursor()
                if mode == "UPDATE":
                    c.execute(sql_update, sql_update_param)
                else:
                    c.execute(sql, sql_param)
                self.conn.commit()
                result = True
                LOG.debug("Save data item[%s] to user success.", item["user_name"])
                break
            except sqlite3.IntegrityError:
                try:
                    if mode == "INSERT OR UPDATE":
                        result = False
                        LOG.info("The item[%s] have been in user service, so ignore the insert action!", item["id"])
                        break
                    else:
                        result = None
                        break
                except sqlite3.IntegrityError:
                    result = None
                    LOG.info("The same item[%s] have been in user service, so ignore the insert & update action!", item["id"])
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

    def get_user_from_db(self, user_name):
        result = False
        try:
            c = self.conn.cursor()
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
                user.socks_proxy = i[10]
                result = user
            LOG.debug("Get user[%s] data from db success", user_name)
        except Exception, e:
            LOG.exception(e)
        return result

    def delete_user_from_db(self, user_name):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM USER WHERE user_name = '%s'" % user_name)
            self.conn.commit()
            result = True
            LOG.debug("Delete user[%s] from db success", user_name)
        except Exception, e:
            if self.conn:
                self.conn.rollback()
            LOG.exception(e)
        return result
