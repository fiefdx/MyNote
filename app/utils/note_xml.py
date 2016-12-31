# -*- coding: utf-8 -*-
'''
Created on 2013-04-05
@summary: generate note xml file
@author: YangHaitao

Modified on 2013-11-08
@summary: change "notetype" to "type"
@author: YangHaitao

Modified on 2014-06-05
@summary: add version attribute
@author: YangHaitao
''' 

import json
import logging


import lxml
from lxml import etree
from models.item import NOTE, RICH

LOG = logging.getLogger(__name__)

def generate_note_xml(note = None):
    '''
    note's attribute is unicode
    '''
    doc = ""
    try:
        if note!= None:
            root = etree.Element('note')
            doc = etree.ElementTree(root)
            version = etree.SubElement(root, 'version')
            version.text = note.version
            notesha1 = etree.SubElement(root, 'notesha1')
            notesha1.text = note.sha1
            file_title = etree.SubElement(root, 'file_title')
            file_title.text = note.file_title
            created_at = etree.SubElement(root, 'created_at')
            created_at.text = str(note.created_at)[:19]
            updated_at = etree.SubElement(root, 'updated_at')
            updated_at.text = str(note.updated_at)[:19]
            notetype = etree.SubElement(root, 'notetype')
            notetype.text = note.type
            file_path = etree.SubElement(root, 'file_path')
            file_path.text = note.file_path
            file_content = etree.SubElement(root, 'file_content')
            file_content.text = note.file_content
    except Exception , e:
        LOG.exception(e)
        return False
    return doc

def get_note_from_xml(xml_path = ""):
    note = NOTE()
    result = False
    try:
        if xml_path != "":
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
            note.version = version
            note.file_title = file_title
            note.file_content = file_content
            note.created_at = created_at
            note.updated_at = updated_at
            note.type = notetype
            note.sha1 = notesha1
            note.file_path = file_path
            result = note
    except Exception , e:
        LOG.exception(e)
    return result

def generate_rich_note_xml(rich = None):
    doc = ""
    try:
        if rich!= None:
            root = etree.Element('rich')
            doc = etree.ElementTree(root)
            version = etree.SubElement(root, 'version')
            version.text = rich.version
            notesha1 = etree.SubElement(root, 'notesha1')
            notesha1.text = rich.sha1
            file_title = etree.SubElement(root, 'file_title')
            file_title.text = rich.file_title
            created_at = etree.SubElement(root, 'created_at')
            created_at.text = str(rich.created_at)[:19]
            updated_at = etree.SubElement(root, 'updated_at')
            updated_at.text = str(rich.updated_at)[:19]
            notetype = etree.SubElement(root, 'notetype')
            notetype.text = rich.type
            file_path = etree.SubElement(root, 'file_path')
            file_path.text = rich.file_path
            file_content = etree.SubElement(root, 'file_content')
            file_content.text = rich.file_content
            rich_content = etree.SubElement(root, 'rich_content')
            rich_content.text = rich.rich_content
            images = etree.SubElement(root, 'images')
            images.text = rich.to_json("images")
    except Exception , e:
        LOG.exception(e)
        return False
    return doc

def get_rich_note_from_xml(xml_path = ""):
    note = RICH()
    result = False
    try:
        if xml_path != "":
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

            note.version = version
            note.file_title = file_title
            note.file_content = file_content
            note.rich_content = rich_content if rich_content != "" else journal_content
            note.created_at = created_at
            note.updated_at = updated_at
            note.type = notetype if notetype != "" else journaltype
            note.sha1 = notesha1 if notesha1 != "" else journalsha1
            note.file_path = file_path
            note.from_json("images", images)
            result = note
    except Exception , e:
        LOG.exception(e)
    return result

if __name__ == "__main__":
    result = get_note_from_xml(xml_path = "/home/breeze/test")
    print "file_title: ",result['file_title']
    print "file_content: ",result['file_content']
    print "created_at: ",result['created_at']
    print "updated_at: ",result['updated_at']
    print "notetype: ",result['notetype']

