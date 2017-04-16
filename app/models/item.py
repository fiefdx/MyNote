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

Modified on 2017-01-10
@summary: Reconstruct note
@author: YangHaitao
'''

import logging
import json

from lxml import etree

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
                          "http_proxy: %(http_proxy)s\n" \
                          "https_proxy: %(https_proxy)s\n" \
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
                 "rich_books", "user_language", "register_time", "http_proxy", "https_proxy"]
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
                "http_proxy" : self.http_proxy,
                "https_proxy" : self.https_proxy,
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
        self.http_proxy = ""
        self.https_proxy = ""
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

    def parse_xml(self, xml_path):
        result = False
        try:
            fp = open(xml_path, "rb")
            doc = etree.parse(fp)
            tmp = doc.xpath('//version/text()')
            version = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//notesha1/text()')
            notesha1 = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//file_title/text()')
            file_title = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//file_path/text()')
            file_path = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//file_content/text()')
            file_content = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//created_at/text()')
            created_at = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//updated_at/text()')
            updated_at = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//notetype/text()')
            notetype = tmp[0] if tmp != [] else ""

            self.version = version
            self.file_title = file_title
            self.file_content = file_content
            self.created_at = created_at
            self.updated_at = updated_at
            self.type = notetype
            self.sha1 = notesha1
            self.file_path = file_path
            result = True
            fp.close()
        except Exception , e:
            LOG.exception(e)
        return result

    def to_xml(self):
        '''
        note's attribute is unicode
        '''
        result = ""
        try:
            root = etree.Element('note')
            result = etree.ElementTree(root)
            version = etree.SubElement(root, 'version')
            version.text = self.version
            notesha1 = etree.SubElement(root, 'notesha1')
            notesha1.text = self.sha1
            file_title = etree.SubElement(root, 'file_title')
            file_title.text = self.file_title
            created_at = etree.SubElement(root, 'created_at')
            created_at.text = str(self.created_at)[:19]
            updated_at = etree.SubElement(root, 'updated_at')
            updated_at.text = str(self.updated_at)[:19]
            notetype = etree.SubElement(root, 'notetype')
            notetype.text = self.type
            file_path = etree.SubElement(root, 'file_path')
            file_path.text = self.file_path
            file_content = etree.SubElement(root, 'file_content')
            file_content.text = self.file_content
        except Exception , e:
            LOG.exception(e)
            result = False
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

    def parse_xml(self, xml_path):
        result = False
        try:
            fp = open(xml_path, "rb")
            doc = etree.parse(fp)
            tmp = doc.xpath('//version/text()')
            version = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//notesha1/text()')
            notesha1 = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//journalsha1/text()')
            journalsha1 = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//file_title/text()')
            file_title = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//file_path/text()')
            file_path = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//file_content/text()')
            file_content = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//rich_content/text()')
            rich_content = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//journal_content/text()')
            journal_content = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//created_at/text()')
            created_at = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//updated_at/text()')
            updated_at = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//notetype/text()')
            notetype = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//journaltype/text()')
            journaltype = tmp[0] if tmp != [] else ""
            tmp = doc.xpath('//images/text()')
            images = tmp[0] if tmp != [] else '[]'

            self.version = version
            self.file_title = file_title
            self.file_content = file_content
            self.rich_content = rich_content if rich_content != "" else journal_content
            self.created_at = created_at
            self.updated_at = updated_at
            self.type = notetype if notetype != "" else journaltype
            self.sha1 = notesha1 if notesha1 != "" else journalsha1
            self.file_path = file_path
            self.from_json("images", images)
            result = True
            fp.close()
        except Exception , e:
            LOG.exception(e)
        return result

    def to_xml(self):
        result = ""
        try:
            root = etree.Element('rich')
            result = etree.ElementTree(root)
            version = etree.SubElement(root, 'version')
            version.text = self.version
            notesha1 = etree.SubElement(root, 'notesha1')
            notesha1.text = self.sha1
            file_title = etree.SubElement(root, 'file_title')
            file_title.text = self.file_title
            created_at = etree.SubElement(root, 'created_at')
            created_at.text = str(self.created_at)[:19]
            updated_at = etree.SubElement(root, 'updated_at')
            updated_at.text = str(self.updated_at)[:19]
            notetype = etree.SubElement(root, 'notetype')
            notetype.text = self.type
            file_path = etree.SubElement(root, 'file_path')
            file_path.text = self.file_path
            file_content = etree.SubElement(root, 'file_content')
            file_content.text = self.file_content
            rich_content = etree.SubElement(root, 'rich_content')
            rich_content.text = self.rich_content
            images = etree.SubElement(root, 'images')
            images.text = self.to_json("images")
        except Exception , e:
            LOG.exception(e)
            result = False
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
