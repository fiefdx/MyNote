# -*- coding: utf-8 -*-
'''
Created on 2017-02-09
@summary: Storage: HTML.db
@Attention: sqlite in python save and get unicode, not utf-8 !!!
@author: YangHaitao
'''

import time
import logging
import sqlite3

from config import CONFIG
from models.item import HTML
from db.sqlite import get_db_path, get_conn_sqlite

LOG = logging.getLogger(__name__)

class DB(object):
    def __init__(self):
        self.name = "HTML"
        self.db_path = get_db_path(CONFIG["STORAGE_DB_PATH"], self.name)
        self.conn = get_conn_sqlite(self.db_path)

    def close(self):
        try:
            if self.conn:
                self.conn.close()
            LOG.info("Close html conn success")
        except Exception, e:
            LOG.warning("Close html conn failed")
            LOG.exception(e)

    def save_data_to_db(self, item, mode = "INSERT OR UPDATE", retries = 3):
        result = False
        sql = "INSERT INTO HTML VALUES (NULL,?,?,?,?,?)"
        sql_update = ("UPDATE HTML SET "
                      "updated_at = ?, "
                      "file_name = ?, "
                      "file_content = ?, "
                      "file_path = ? "
                      "WHERE sha1 = ?;")
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

        for i in xrange(retries):
            try:
                c = self.conn.cursor()
                if mode == "UPDATE":
                    c.execute(sql_update, sql_update_param)
                else:
                    c.execute(sql, sql_param)
                self.conn.commit()
                result = True
                LOG.debug("Save data item[%s] to html success.", item["id"])
                break
            except sqlite3.IntegrityError:
                try:
                    if mode == "INSERT OR UPDATE":
                        LOG.info("The item[%s] have been in html service, so update it!", item["id"])
                        c = self.conn.cursor()
                        c.execute(sql_update, sql_update_param)
                        self.conn.commit()
                        result = True
                        LOG.debug("Update data item[%s] to html success.", item["id"])
                        break
                    else:
                        result = None
                        break
                except sqlite3.IntegrityError:
                    result = None
                    LOG.info("The same item[%s] have been in html service, so ignore the insert & update action!", item["id"])
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

    def get_html_from_db(self):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM HTML")
            result = []
            i = c.fetchone()
            while i is not None:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                result.append(html)
                i = c.fetchone()
            LOG.debug("Get all html[%s] from db success", len(result))
        except Exception, e:
            LOG.exception(e)
        return result

    def get_html_from_db_iter(self):
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM HTML WHERE updated_at > '%s'" % flag)
            total = 0
            i = c.fetchone()
            while i is not None:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                LOG.debug("Get html[%s] from db success", html.file_name)
                total += 1
                yield html
                i = c.fetchone()
            LOG.debug("Get all html[%s] from db success", total)
        except Exception, e:
            LOG.exception(e)

    def get_html_by_flag_iter(self, flag):
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM HTML WHERE updated_at > '%s'" % flag)
            total = 0
            i = c.fetchone()
            while i is not None:
                html = HTML()
                html.id = i[0]
                html.sha1 = i[1]
                html.updated_at = i[2]
                html.file_name = i[3]
                html.file_content = i[4]
                html.file_path = i[5]
                LOG.debug("Get html[%s] from db success", html.file_name)
                total += 1
                yield html
                i = c.fetchone()
            LOG.debug("Get all html[%s] from db success", total)
        except Exception, e:
            LOG.exception(e)

    def get_html_by_id(self, doc_id):
        result = False
        try:
            c = self.conn.cursor()
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
            LOG.debug("Get a html[%s] from db success", doc_id)
        except Exception, e:
            LOG.exception(e)
        return result

    def get_html_by_sha1(self, sha1):
        result = False
        try:
            c = self.conn.cursor()
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
            LOG.debug("Get a html[%s] from db success", sha1)
        except Exception, e:
            LOG.exception(e)
        return result

    def get_html_num_from_db(self):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("SELECT count(*) FROM HTML")
            i = c.fetchone()
            result = i
            LOG.debug("Get a html num[%s] from db success", i)
        except Exception, e:
            LOG.exception(e)
        return result
