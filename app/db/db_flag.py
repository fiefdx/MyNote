# -*- coding: utf-8 -*-
'''
Created on 2017-02-09
@summary: Storage: FLAG.db
@Attention: sqlite in python save and get unicode, not utf-8 !!!
@author: YangHaitao
'''

import logging

from config import CONFIG
from db.sqlite import get_db_path, get_conn_sqlite

LOG = logging.getLogger(__name__)

class DB(object):
    def __init__(self):
        self.name = "FLAG"
        self.db_path = get_db_path(CONFIG["STORAGE_DB_PATH"], self.name)
        self.conn = get_conn_sqlite(self.db_path)

    def close(self):
        try:
            if self.conn:
                self.conn.close()
            LOG.info("Close flag conn success")
        except Exception, e:
            LOG.warning("Close flag conn failed")
            LOG.exception(e)

    def update_flag(self, index_name):
        result = False
        try:
            sql = {"HTML": "UPDATE FLAG SET new_index_time = (SELECT old_index_time FROM FLAG WHERE index_name = 'HTML') WHERE index_name = 'HTML';",
                   "RICH": "UPDATE FLAG SET new_index_time = (SELECT old_index_time FROM FLAG WHERE index_name = 'RICH') WHERE index_name = 'RICH';",
                   "NOTE": "UPDATE FLAG SET new_index_time = (SELECT old_index_time FROM FLAG WHERE index_name = 'NOTE') WHERE index_name = 'NOTE';"
                   }
            c = self.conn.cursor()
            c.execute(sql[index_name])
            self.conn.commit()
            result = True
            LOG.debug("Update old_time to new_time to %s success", index_name)
        except Exception, e:
            if self.conn:
                self.conn.rollback()
            LOG.exception(e)
        return result

    def update_old_flag(self, index_name):
        result = False
        try:
            sql = {"HTML": "UPDATE FLAG SET old_index_time = datetime('now', 'localtime') WHERE index_name = 'HTML';",
                   "RICH": "UPDATE FLAG SET old_index_time = datetime('now', 'localtime') WHERE index_name = 'RICH';",
                   "NOTE": "UPDATE FLAG SET old_index_time = datetime('now', 'localtime') WHERE index_name = 'NOTE';"
                   }
            c = self.conn.cursor()
            c.execute(sql[index_name])
            self.conn.commit()
            result = True
            LOG.debug("Update old_time to %s success", index_name)
        except Exception, e:
            if self.conn:
                self.conn.rollback()
            LOG.exception(e)
        return result

    def get_flag_from_db(self, index_name):
        result = False
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM FLAG WHERE index_name = '%s'" % index_name)
            i = c.fetchone()
            if i is None:
                LOG.warning("Can not find the flag in db[%s], so i will return None", index_name)
                result = None
            else:
                result = i[2]
                LOG.debug("Get a flag[%s] from db[%s] success", result, index_name)
        except Exception, e:
            LOG.exception(e)
        return result
