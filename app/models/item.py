# -*- coding: utf-8 -*-
'''
Created on 2013-10-11
@summary: Pictures Storage Item
@author: YangHaitao

Modified on 2014-05-31
@summary: Add USER user_books attribute
@author: YangHaitao

Modified on 2014-06-05
@summary: Add Note/RICH version("0.1") attribute but not in all functions, not effect with sqlite
@author: YangHaitao

Modified on 2014-06-06
@summary: Add Note encrypt decrypt functions
@author: YangHaitao

Modified on 2014-06-09
@summary: Add Note description encrypt and decrypt
@author: YangHaitao

Modified on 2014-06-10
@summary: Add Rich description encrypt and decrypt
@author: YangHaitao

Modified on 2014-10-28
@summary: Add Rich images
@author: YangHaitao

Modified on 2014-10-28
@summary: USER add sha1
@author: YangHaitao
'''

import os
import sys
import logging
import json
import datetime
import time
import dateutil
from dateutil import tz

import tea
from tea import EncryptStr, DecryptStr

LOG = logging.getLogger(__name__)

class USER(object):
    def __init__(self):
        self.clear()

    def __str__(self):
        string_formated = "id: %(id)d\n" \
                          "sha1: %(sha1)s\n" \
                          "user_name: %(user_name)s\n" \
                          "user_pass: %(user_pass)s\n" \
                          "note_books: %(note_books)s\n" \
                          "rich_books: %(rich_books)s\n" \
                          "user_language: %(user_language)s\n" \
                          "register_time: %(register_time)s\n" \
                          %(self.to_dict())
        return string_formated

    def parse_dict(self, source):
        '''
        @summary: parse the given dict to construct this user object
        @param source: dict type input param
        @result: True/False
        '''
        result = False

        self.clear()
        attrs = ["id", "sha1", "user_name", "user_pass", "note_books", 
                 "rich_books", "user_language", "register_time"]
        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to user object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
            result = False
        return result

    def to_dict(self):
        """
        @summary: convert to a dict
        """
        return dict({
                "id" : self.id,
                "sha1" : self.sha1,
                "user_name" : self.user_name,
                "user_pass" : self.user_pass,
                "note_books" : self.note_books,
                "rich_books" : self.rich_books,
                "user_language" : self.user_language,
                "register_time" : self.register_time
                }
            )

    def clear(self):
        """
        @summary: reset property:

        """
        self.id = 0
        self.sha1 = ""
        self.user_name = ""
        self.user_pass = ""
        self.note_books = ""
        self.rich_books = ""
        self.user_language = "" # us_EN or zh_CN
        self.register_time = None

class HTML(object):
    def __init__(self):
        self.clear()

    def __str__(self):
        string_formated = "id: %(id)d\n" \
                          "sha1: %(sha1)s\n" \
                          "updated_at: %(updated_at)s\n" \
                          "file_name: %(file_name)s\n" \
                          "file_content: %(file_content)s\n" \
                          "file_path: %(file_path)s\n" \
                          "excerpts: %(excerpts)s\n" \
                          "description: %(description)s\n" \
                          %(self.to_dict())
        return string_formated

    def parse_dict(self, source):
        '''
        @summary: parse the given dict to construct this html object
        @param source: dict type input param
        @result: True/False
        '''
        result = False

        self.clear()
        attrs = ["id", "sha1", "updated_at", "file_name", "file_content", "file_path"]
        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to html object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
            result = False
        return result

    def to_dict(self):
        """
        @summary: convert to a dict
        """
        return dict({
                "id" : self.id,
                "sha1" : self.sha1,
                "updated_at" : self.updated_at,
                "file_name" : self.file_name,
                "file_content" : self.file_content,
                "file_path" : self.file_path,
                "excerpts" : self.excerpts,
                "description" : self.description
                }
            )
    def clear(self):
        """
        @summary: reset property:

        """
        self.id = 0
        self.sha1 = ""
        self.updated_at = None
        self.file_name = ""
        self.file_content = ""
        self.file_path = ""
        self.excerpts = ""
        self.description ="" 


class NOTE(object):
    VERSION = "0.1"

    def __init__(self):
        self.clear()

    def __str__(self):
        string_formated = "id: %(id)d\n" \
                          "user_name: %(user_name)s\n" \
                          "sha1: %(sha1)s\n" \
                          "oldsha1: %(oldsha1)s\n" \
                          "created_at: %(created_at)s\n" \
                          "updated_at: %(updated_at)s\n" \
                          "file_title: %(file_title)s\n" \
                          "file_content: %(file_content)s\n" \
                          "file_path: %(file_path)s\n" \
                          "type: %(type)s\n" \
                          "excerpts: %(excerpts)s\n" \
                          "description: %(description)s\n" \
                          "version: %(version)s\n" \
                          %(self.to_dict())
        return string_formated

    def parse_dict(self, source):
        '''
        @summary: parse the given dict to construct this note object
        @param source: dict type input param
        @result: True/False
        '''
        result = False

        self.clear()
        attrs = ["id", "user_name", "sha1", "created_at", "updated_at", 
                 "file_title", "file_content", "file_path", "description", "type"]
        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to note object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
            result = False
        return result

    def to_dict(self):
        """
        @summary: convert to a dict
        """
        return dict({
                "id" : self.id,
                "user_name" : self.user_name,
                "sha1" : self.sha1,
                "oldsha1" : self.oldsha1,
                "created_at" : self.created_at,
                "updated_at" : self.updated_at,
                "file_title" : self.file_title,
                "file_content" : self.file_content,
                "file_path" : self.file_path,
                "type" : self.type,
                "excerpts" : self.excerpts,
                "description" : self.description,
                "version" : NOTE.VERSION
                }
            )

    def encrypt(self, key):
        result = False
        try:
            self.description = EncryptStr(self.description, key).decode("utf-8")
            self.file_title = EncryptStr(self.file_title, key).decode("utf-8")
            self.file_content = EncryptStr(self.file_content, key).decode("utf-8")
            result = True
        except Exception, e:
            LOG.exception(e)
        return result

    def decrypt(self, key, decrypt_content = True, decrypt_description = True):
        result = False
        try:
            self.file_title = DecryptStr(self.file_title, key).decode("utf-8")
            if decrypt_description:
                self.description = DecryptStr(self.description, key).decode("utf-8")
            if decrypt_content:
                self.file_content = DecryptStr(self.file_content, key).decode("utf-8")
            result = True
        except Exception, e:
            LOG.exception(e)
        return result

    def clear(self):
        """
        @summary: reset property:

        """
        self.id = 0
        self.user_name = ""
        self.sha1 = ""
        self.oldsha1 = ""
        self.created_at = None
        self.updated_at = None
        self.file_title = ""
        self.file_content = ""
        self.file_path = ""
        self.type = ""
        self.excerpts = ""
        self.description = ""
        self.version = NOTE.VERSION

class RICH(object):
    VERSION = "0.2"

    def __init__(self):
        self.clear()

    def __str__(self):
        string_formated = "id: %(id)d\n" \
                          "user_name: %(user_name)s\n" \
                          "sha1: %(sha1)s\n" \
                          "oldsha1: %(oldsha1)s\n" \
                          "created_at: %(created_at)s\n" \
                          "updated_at: %(updated_at)s\n" \
                          "file_title: %(file_title)s\n" \
                          "file_content: %(file_content)s\n" \
                          "rich_content: %(rich_content)s\n" \
                          "file_path: %(file_path)s\n" \
                          "type: %(type)s\n" \
                          "excerpts: %(excerpts)s\n" \
                          "description: %(description)s\n" \
                          "images: %(images)s\n" \
                          "version: %(version)s\n" \
                          %(self.to_dict())
        return string_formated

    def parse_dict(self, source):
        '''
        @summary: parse the given dict to construct this note object
        @param source: dict type input param
        @result: True/False
        '''
        result = False

        self.clear()
        attrs = ["id", "user_name", "sha1", "created_at", "updated_at", "file_title", 
                 "file_content", "rich_content", "file_path", "description", "type", "images"]
        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to note object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
            result = False
        return result

    def encrypt(self, key):
        result = False
        try:
            self.description = EncryptStr(self.description, key).decode("utf-8")
            self.file_title = EncryptStr(self.file_title, key).decode("utf-8")
            self.file_content = EncryptStr(self.file_content, key).decode("utf-8")
            self.rich_content = EncryptStr(self.rich_content, key).decode("utf-8")
            result = True
        except Exception, e:
            LOG.exception(e)
        return result

    def decrypt(self, key, decrypt_content = True, decrypt_description = True):
        result = False
        try:
            self.file_title = DecryptStr(self.file_title, key).decode("utf-8")
            if decrypt_description:
                self.description = DecryptStr(self.description, key).decode("utf-8")
            if decrypt_content:
                self.file_content = DecryptStr(self.file_content, key).decode("utf-8")
                self.rich_content = DecryptStr(self.rich_content, key).decode("utf-8")
            result = True
        except Exception, e:
            LOG.exception(e)
            # raise e
        return result

    def to_dict(self):
        """
        @summary: convert to a dict
        """
        return dict({
                "id" : self.id,
                "user_name" : self.user_name,
                "sha1" : self.sha1,
                "oldsha1" : self.oldsha1,
                "created_at" : self.created_at,
                "updated_at" : self.updated_at,
                "file_title" : self.file_title,
                "file_content" : self.file_content,
                "rich_content" : self.rich_content,
                "file_path" : self.file_path,
                "type" : self.type,
                "excerpts" : self.excerpts,
                "description" : self.description,
                "images" : json.dumps(self.images),
                "version" : RICH.VERSION
                }
            )

    def to_json(self, attr):
        """
        @summary: convert attr to json string
        """
        return json.dumps(getattr(self, attr) if hasattr(self, attr) else "")

    def from_json(self, attr, value):
        """
        @summary: convert json string to attr
        """
        result = False
        try:
            if hasattr(self, attr):
                setattr(self, attr, json.loads(value))
                result = True
            else:
                result = None
        except Exception, e:
            LOG.exception(e)
        return result

    def clear(self):
        """
        @summary: reset property:

        """
        self.id = 0
        self.user_name = ""
        self.sha1 = ""
        self.oldsha1 = ""
        self.created_at = None
        self.updated_at = None
        self.file_title = ""
        self.file_content = ""
        self.rich_content = ""
        self.file_path = ""
        self.type = ""
        self.excerpts = ""
        self.description = ""
        self.images = []
        self.version = RICH.VERSION

class NoteState(object):
    LOCKED = "locked"
    UNLOCKED = "unlocked"

    def __init__(self):
        self.state = NoteState.UNLOCKED

    def set_lock(self):
        if self.state == NoteState.UNLOCKED:
            self.state = NoteState.LOCKED
        return self.state

    def clear_lock(self):
        if self.state == NoteState.LOCKED:
            self.state = NoteState.UNLOCKED
        return self.state

    def is_locked(self):
        if self.state == NoteState.LOCKED:
            return True
        else:
            return False


class PICTURE(object):
    def __init__(self):
        self.clear()

    def __str__(self):
        string_formated = "id: %(id)s\n" \
                          "sha1: %(sha1)s\n" \
                          "imported_at: %(imported_at)s\n" \
                          "file_name: %(file_name)s\n" \
                          "file_path: %(file_path)s\n" \
                          %(self.to_dict())
        return string_formated

    def parse_dict(self, source):
        '''
        @summary: parse the given dict to construct this note object
        @param source: dict type input param
        @result: True/False
        '''
        result = False

        self.clear()
        attrs = ["id", "sha1", "imported_at", "file_name", "file_path"]
        if hasattr(source, "__getitem__"):
            for attr in attrs:
                try:
                    setattr(self, attr, source[attr])
                except:
                    LOG.debug("some exception occured when extract %s attribute to note object, i will discard it",
                        attr)
                    continue
            result = True
        else:
            LOG.debug("input param source does not have dict-like method, so i will do nothing at all!")
            result = False
        return result

    def to_dict(self):
        """
        @summary: convert to a dict
        """
        return dict({
                "id" : self.id,
                "sha1" : self.sha1,
                "imported_at" : self.imported_at,
                "file_name" : self.file_name,
                "file_path" : self.file_path
                }
            )

    def clear(self):
        """
        @summary: reset property:

        """
        self.id = 0
        self.sha1 = ""
        self.imported_at = None
        self.file_name = ""
        self.file_path = ""

if __name__ == "__main__":
    pass


