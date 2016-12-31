# -*- coding: utf-8 -*-
'''
Created on 2013-10-30 21:09
@summary: some utils for html
@author: YangHaitao

Modified on 2013-11-09 22:58
@author: YangHaitao
'''
import urllib
import urlparse

class LinkItem(object):
    """html <a> tag 's python representation"""
    def __init__(self, text = "", url = ""):
        super(LinkItem, self).__init__()
        self.text = text
        self.url = url
        
class ThumbnailItem(object):
    """
        @summary: search result thumbnail representation
    """
    def __init__(self, 
                 title = "", 
                 url = "", 
                 excerpts = "", 
                 description = "", 
                 date_time = "", 
                 add_links = []):
        '''
        @summary: Init method

        @param text: title for the item
        @param url: url attached to this item
        @param excerpts: excerpts for the item
        @param add_links: some additional links,[(text, url), (text, url), ...]

        @result:
        '''
        super(ThumbnailItem, self).__init__()
        self.title = title
        self.url = url
        self.description = description
        self.excerpts = excerpts
        self.add_links = add_links
        self.date_time = date_time

class ThumnailNote(object):
    """
        @summary: search result thumbnail representation
    """
    def __init__(self, 
                 url = "", 
                 noteid = "", 
                 notesha1 = "", 
                 file_title ="", 
                 file_content = "", 
                 created_at = "", 
                 updated_at = "", 
                 excerpts = "", 
                 description = "", 
                 notetype = "", 
                 add_links = []):
        '''
        @summary: Init method

        @param text: title for the item
        @param url: url attached to this item
        @param excerpts: excerpts for the item
        @param add_links: some additional links,[(text, url), (text, url), ...]

        @result:
        '''
        super(ThumnailNote, self).__init__()
        self.noteid = noteid
        self.file_title = file_title
        self.url = url
        self.file_content = file_content
        self.notesha1 = notesha1
        self.created_at = created_at
        self.updated_at = updated_at
        self.add_links = add_links
        self.notetype = notetype
        self.excerpts = excerpts
        self.description = description

class ThumnailRich(object):
    """
        @summary: search result thumbnail representation
    """
    def __init__(self, 
                 url = "", 
                 noteid = "", 
                 notesha1 = "", 
                 file_title ="", 
                 file_content = "", 
                 created_at = "", 
                 updated_at = "", 
                 excerpts = "", 
                 description = "", 
                 notetype = "", 
                 add_links = []):
        '''
        @summary: Init method

        @param text: title for the item
        @param url: url attached to this item
        @param excerpts: excerpts for the item
        @param add_links: some additional links,[(text, url), (text, url), ...]

        @result:
        '''
        super(ThumnailRich, self).__init__()
        self.noteid = noteid
        self.file_title = file_title
        self.url = url
        self.file_content = file_content
        self.notesha1 = notesha1
        self.created_at = created_at
        self.updated_at = updated_at
        self.add_links = add_links
        self.notetype = notetype
        self.excerpts = excerpts
        self.description = description


def add_params_to_url(url, params):
    """
    @summary: add a param to original url
    @param: original url is unicode
    @param params: dict value
    """
    url = url.encode('utf-8')
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)


if __name__ == "__main__":
    print add_params_to_url('/search?q=杨&query=(@(file_name) 杨)|(@(file_content) 杨)&search_project=all_results&search_time=All_Times',dict({'page':10}))
