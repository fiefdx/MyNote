# -*- coding: utf-8 -*-
'''
Created on 2013-02-03 20:48
@summary:  html file object
@author: YangHaitao
'''

import os
import sys
import logging

LOG = logging.getLogger(__name__)

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


if __name__ == "__main__":
    html = HTML()
    html.sha1 = "1234"
    print html.sha1
    print 'everything is ok.'