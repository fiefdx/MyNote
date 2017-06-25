# -*- coding: utf-8 -*-
'''
Created on 2017-02-09
@summary: Storage: PIC.db
@Attention: sqlite in python save and get unicode, not utf-8 !!!
@author: YangHaitao
'''

import time
import logging
import sqlite3

from config import CONFIG
from models.item import PICTURE as PIC
from db.sqlite import get_db_path, get_conn_sqlite

LOG = logging.getLogger(__name__)

class DB(object):
    def __init__(self):
        self.name = "PIC"
        self.db_path = get_db_path(CONFIG["STORAGE_DB_PATH"], self.name)
        self.conn = get_conn_sqlite(self.db_path)

    def close(self):
        try:
            if self.conn:
                self.conn.close()
            LOG.info("Close pic conn success")
        except Exception, e:
            LOG.warning("Close pic conn failed")
            LOG.exception(e)

    def save_data_to_db(self, item, mode = "INSERT OR UPDATE", retries = 3):
        result = False
        sql = "INSERT INTO PIC VALUES (NULL,?,?,?,?)"
        sql_update = ("UPDATE PIC SET "
                      "file_name = ?, "
                      "file_path = ? "
                      "WHERE sha1 = ?;")
        sql_param = (item["sha1"],
                     item["imported_at"],
                     item["file_name"],
                     item["file_path"])
        sql_update_param = (item["file_name"],
                            item["file_path"],
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
                LOG.debug("Save data item[%s] to pic success", item["id"])
                break
            except sqlite3.IntegrityError:
                try:
                    if mode == "INSERT OR UPDATE":
                        LOG.info("The item[sha1: %s] have been in pic, so update it!", item["sha1"])
                        c = self.conn.cursor()
                        c.execute(sql_update, sql_update_param)
                        self.conn.commit()
                        result = True
                        LOG.debug("Update data item[sha1: %s] to pic success.", item["sha1"])
                        break
                    else:
                        result = None
                        break
                except sqlite3.IntegrityError:
                    result = None
                    LOG.info("The same item[%s] have been in pic, so ignore the insert & update action!", item["id"])
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

    def get_data_from_db(self):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM PIC")
            result = []
            i = c.fetchone()
            while i is not None:
                item = PIC()
                item.id = i[0]
                item.sha1 = i[1]
                item.imported_at = i[2]
                item.file_name = i[3]
                item.file_path = i[4]
                result.append(item)
                i = c.fetchone()
            LOG.debug("get all picture from db success")
        except Exception, e:
            LOG.exception(e)
        return result

    def get_data_by_sha1(self, sha1):
        """
        return None when no item.
        """
        result = False
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM PIC WHERE sha1 = '%s'" % sha1)
            i = c.fetchone()
            if i is not None:
                item = PIC()
                item.id = i[0]
                item.sha1 = i[1]
                item.imported_at = i[2]
                item.file_name = i[3]
                item.file_path = i[4]
                result = item
            else:
                result = None
            LOG.debug("get picture from db by sha1[%s] success", sha1)
        except Exception, e:
            LOG.exception(e)
        return result
