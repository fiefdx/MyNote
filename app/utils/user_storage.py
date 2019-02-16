# -*- coding: utf-8 -*-
'''
Created on 2013-09-01 12:42
@summary:  multi-user storage
@author: YangHaitao

Modified on 2014-05-31
@summary: change note_type_list = []
@author: YangHaitao
'''

import os
import logging
import shutil


LOG = logging.getLogger(__name__)

class Storage(object):
    def __init__(self, root, user_sha1):
        try:
            self.root = root
            self.user = user_sha1
            self.user_path = os.path.join(root, user_sha1)
            self.user_path_dirs = ["notes", "share", "tmp", "rich_notes", "rich_note"]
            self.rich_note_path_list = ["rich_notes", "images"]
            self.note_type_list = []
        except Exception, e:
            LOG.exception(e)

    def init(self):
        result = False
        try:
            if os.path.exists(self.user_path) and os.path.isdir(self.user_path):
                shutil.rmtree(self.user_path)
                LOG.debug("init user_path[%s] exists, so rm it."%self.user_path)
            else:
                LOG.debug("init user_path[%s] do not exists"%self.user_path)
            os.makedirs(self.user_path)
            for i in self.user_path_dirs:
                tmp_path = os.path.join(self.user_path, i)
                os.makedirs(tmp_path)
            for i in self.note_type_list:
                tmp_path = os.path.join(self.user_path, "notes", i)
                os.makedirs(tmp_path)
            for i in self.rich_note_path_list:
                tmp_path = os.path.join(self.user_path, "rich_notes", i)
                os.makedirs(tmp_path)
            for i in self.note_type_list:
                tmp_path = os.path.join(self.user_path, "rich_notes", "rich_notes", i)
                os.makedirs(tmp_path)
            for i in ["import", "export"]:
                tmp_path = os.path.join(self.user_path, "tmp", i)
                os.makedirs(tmp_path)
            tmp_path = os.path.join(self.user_path, "rich_note", "picture")
            os.makedirs(tmp_path)
            LOG.debug("init user_path[%s] success"%self.user_path)
            result = True
        except Exception, e:
            LOG.exception(e)
            result = False
        return result

    def rm(self):
        result = False
        try:
            if os.path.exists(self.user_path) and os.path.isdir(self.user_path):
                shutil.rmtree(self.user_path)
                LOG.debug("rm user_path[%s] success"%self.user_path)
                result = True
            else:
                LOG.debug("rm user_path[%s] do not exists"%self.user_path)
                result = True
        except Exception, e:
            LOG.exception(e)
            result = False
        return result
