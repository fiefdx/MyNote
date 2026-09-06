# -*- coding: utf-8 -*-
'''
Created on 2013-10-26 21:51
@summary:  parse html
@author: YangHaitao

Modified on 2014-06-11
@summary:  change 
           "for i in page.itertext(" ".join(allow_tags)):"
           to
           "for i in page.itertext(allow_tags):"
@author: YangHaitao

Modified on 2014-10-28
@summary: change html_change_image_src_BS add local_images
@author: YangHaitao
'''
import os
import sys
import re
import logging
import shutil
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import chardet
import urllib.parse
import datetime
import io

import imghdr
import lxml
from lxml import etree
import dateutil
from dateutil import tz
import time
from time import localtime, strftime
import hashlib
import traceback
from bs4 import BeautifulSoup as BS
import requests
import psutil

from config import CONFIG
from models.item import PICTURE as PIC
import utils.common_utils as util

# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."
LOG = logging.getLogger(__name__)

def get_html_charset(file_content):
    encoding = {}
    try:
        content_type = ['utf-8', 'gb2312', 'gbk', 'gb18030', 'big5', 'utf-16']
        page = etree.HTML(file_content)
        meta = page.xpath("/html/head/meta")
        html = page.getroottree()
        LOG.info("HTML encoding: %s", html.docinfo.encoding)
        if html.docinfo.encoding != "" and html.docinfo.encoding != None:
            encoding["encoding"] = html.docinfo.encoding
        if 'encoding' not in encoding:
            encoding = chardet.detect(file_content)
        try:
            page = etree.HTML(file_content.decode(encoding["encoding"]))
        except Exception as e:
            LOG.exception(e)
        meta = page.xpath("/html/head/meta")
        tmp = ''
        charset = ''
        for i in meta:
            tmp += (" ".join(list(i.attrib.values())) + " ")
            if "content" in i.attrib:
                if (encoding["encoding"].upper() in i.attrib["content"]) or (encoding["encoding"].lower() in i.attrib["content"]):
                    i.attrib["content"] = "text/html; charset=UTF-8"
                    LOG.info("Found the content and change it to UTF-8.")
        html = page.getroottree()
        fp = io.StringIO()
        html.write(fp, pretty_print = True, method = "html", encoding = encoding["encoding"])
        fp.seek(0)
        content = fp.read()
        fp.close()
        encoding["content"] = content
    except Exception as e:
        encoding = chardet.detect(file_content)
        LOG.exception(e)
    return encoding

def html_decode_unicode(file_content):
    """
    param: file_content is original html content may be any encoding
    result: unicode
    """
    result = ""
    html_content = ""
    try:
        encoding = get_html_charset(file_content)
        try:
            if "content" in encoding:
                LOG.debug("Use encoding['content']")
                file_content = encoding["content"]
            if 'encoding' in encoding:
                if encoding["encoding"].lower() == "utf-8":
                    html_content = file_content.decode("utf-8")
                else:
                    html_content = file_content.decode(encoding['encoding'])
            elif 'confidence' in encoding and encoding['confidence'] > 0.8:
                html_content = file_content.decode(encoding['encoding'])
            else:
                html_content = file_content.decode('utf-8')
            result = html_content
        except UnicodeDecodeError as e:
            LOG.warning("UnicodeDecodeError!: %s", e)
            return result
    except Exception as e:
        LOG.exception(e)
    return result

def get_html_content_old(file_content):
    result = ""
    try:
        utf8_parser = etree.HTMLParser(encoding="utf-8")
        page = etree.HTML(file_content, parser = utf8_parser)
        iterator = page.getiterator()
        for i in iterator:
            if i.text != None:
                text = i.text.strip() 
                if text !='' and i.tag not in ['script', 'a', 'img', 'style', 'link', ''] and i.tag != lxml.etree.Comment:
                    result += (text + '\n')
        result = result.encode('utf-8')
    except Exception as e:
        LOG.exception(e)
    return result

# Tags whose text is never note content (kept out of file_content / the note
# description / the whoosh index).
NON_CONTENT_TAGS = frozenset(["script", "style", "noscript", "template"])

def _element_text(element):
    """
    Return the text of an element and its descendants, including the tails
    (the text after a child element), skipping non-content subtrees.

    NOTE: this replaces the old `page.itertext(allow_tags)` extraction.
    itertext(tags) is an element *selector*: it only yields .text/.tail of the
    elements that match the list. Text owned by a non-listed element - most
    importantly a bare text node directly inside <body>, which is what the rich
    editor produces for plain typed lines, and <body>/<blockquote> themselves -
    was silently dropped, so file_content (and therefore note.description) came
    out empty for real notes.
    """
    tag = element.tag
    # comments / processing instructions: tag is a callable, not a string
    if not isinstance(tag, str) or tag.lower() in NON_CONTENT_TAGS:
        return ""
    text = element.text or ""
    for child in element:
        text += _element_text(child)
        if child.tail:
            text += child.tail
    return text

def get_html_content(file_content):
    """
    param: file_content is unicode
    result: title and content is unicode
    """
    result = {"title":"", "content":""}
    file_content = file_content.encode("utf-8")
    try:
        utf8_parser = etree.HTMLParser(encoding="utf-8")
        page = etree.HTML(file_content, parser = utf8_parser)
        if page is None:
            return result
        title = page.xpath("//title") # <title></title> title[0].text == None
        title_text = ""
        if title != [] and title[0].text != None and title[0].text.strip() != "":
            title_text = title[0].text.strip()
            LOG.debug("Html Title: %s", title_text)
        text = _element_text(page)
        text = text.replace("\r", "")
        text_list = text.split("\n")
        content = ""
        for i in text_list:
            i = i.strip()
            if i != "":
                content += (i + "\n")
        result["title"] = title_text
        result["content"] = content
    except Exception as e:
        LOG.exception(e)
    return result

def get_html_content_BS(file_content):
    result = ""
    try:
        soup = BS(file_content, "lxml")
        result = soup.get_text().encode("utf-8")
        result_list = result.split("\n")
        result = ""
        for i in result_list:
            if i.strip() != "":
                result += (i.strip() + '\n')
        # LOG.debug("BS: %s"%chardet.detect(result))
    except Exception as e:
        LOG.exception(e)
    return result

def html_change_src(html_content, html_name, external_dirname, new_external_dirname):
    """
    param: html_content is unicode
    param: html_name is unicode
    param: external_dirname is unicode
    param: new_external_dirname is unicode
    """
    # Python 3: operate on str throughout (the regex patterns below are str);
    # encoding to bytes here would break re.sub on a mixed bytes/str case.

    url_external_dirname = urllib.parse.quote(external_dirname)
    url_external_dirname_noplus = urllib.parse.quote(external_dirname, safe="$/,@*+:%&;")
    url_external_dirname_noplus_and = urllib.parse.quote(external_dirname, safe="$/,@*+:%&;").replace("&", "&amp;")
    url_new_external_dirname = urllib.parse.quote(new_external_dirname)
    # re_replace = {'.':'\.', '(':'\(', ')':'\)', '?':'\?', '*':'\*', '+':'\+', '|':'\|', '$':'\$', '^':'\^', '{':'\{', '}':'\}', '[':'\[', ']':'\]'}
    # for i in re_replace:
    #     url_external_dirname = url_external_dirname.replace(i, re_replace[i])
    #     external_dirname = external_dirname.replace(i, re_replace[i])
    # url_external_dirname_un = url_external_dirname
    external_dirname_un = external_dirname
    url_external_dirname = re.escape(url_external_dirname)
    url_external_dirname_noplus = re.escape(url_external_dirname_noplus)
    url_external_dirname_noplus_and = re.escape(url_external_dirname_noplus_and)
    external_dirname = re.escape(external_dirname)
    e_src_old_quote = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + url_external_dirname
    e_src_old_quote_noplus = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + url_external_dirname_noplus
    e_src_old_quote_noplus_and = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + url_external_dirname_noplus_and
    e_src_old_unquote = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + external_dirname
    # print 'e_src_old:',e_src_old
    e_src_new = r'''\g<src_url>''' + url_new_external_dirname
    try:
        content = html_content
        e_src = re.compile(e_src_old_quote)
        flag = e_src.findall(content)
        if flag != []:
            content = e_src.sub(e_src_new, content)
            LOG.info("Change [%s] to [%s]", external_dirname_un, new_external_dirname)
        else:
            e_src = re.compile(e_src_old_quote_noplus)
            flag = e_src.findall(content)
            if flag != []:
                content = e_src.sub(e_src_new, content)
                LOG.info("Change [%s] to [%s], unquote($/,@*+:%%&;)!", external_dirname_un, new_external_dirname)
            else:
                e_src = re.compile(e_src_old_quote_noplus_and)
                flag = e_src.findall(content)
                if flag != []:
                    content = e_src.sub(e_src_new, content)
                    LOG.info("Change [%s] to [%s], unquote($/,@*+:%%&;) and replace '&' to '&amp;'!", external_dirname_un, new_external_dirname)
                else:
                    e_src = re.compile(e_src_old_unquote)
                    flag = e_src.findall(content)
                    if flag != []:
                        content = e_src.sub(e_src_new, content)
                        LOG.info("Change [%s] to [%s], unquote(all)!", external_dirname_un, new_external_dirname)
                    else:
                        LOG.error("Change [%s] to [%s] failed!", external_dirname_un, new_external_dirname)
    except Exception as e:
        LOG.exception(e)
    return content

def html_change_multi_src(html_content, change_list):
    """
    param: html_content is unicode
    """
    # Python 3: keep content as str so it matches the str regex patterns below.
    content = html_content
    try:
        for change_dict in change_list:
            root_path = change_dict["root"]
            for fname in change_dict["change_file"]:
                src_str_old = '/'.join(root_path.split(os.sep)) + '/' + fname[0]
                src_str_old_quote = urllib.parse.quote(src_str_old)
                src_str_old_quote_noplus = urllib.parse.quote(src_str_old, safe="$/,@*+:%&;")
                src_str_old_quote_noplus_and = urllib.parse.quote(src_str_old, safe="$/,@*+:%&;").replace("&", "&amp;")

                src_str_new = '/'.join(root_path.split(os.sep)) + '/' + fname[1]
                src_str_new_quote = urllib.parse.quote(src_str_new)

                e_src_old = re.escape(src_str_old)
                e_src_old_quote = re.escape(src_str_old_quote)
                e_src_old_quote_noplus = re.escape(src_str_old_quote_noplus)
                e_srt_old_quote_noplus_and = re.escape(src_str_old_quote_noplus_and)

                e_src_old = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + e_src_old
                e_src_old_quote = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + e_src_old_quote
                e_src_old_quote_noplus = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + e_src_old_quote_noplus
                e_src_old_quote_noplus_and = '''(?P<src_url>(src|href) *= *["'] *[.]?[/]?)''' + e_src_old_quote_noplus_and
                e_src_new = r'''\g<src_url>''' + src_str_new_quote

                e_src = re.compile(e_src_old_quote)
                flag = e_src.findall(content)
                if flag != []:
                    content = e_src.sub(e_src_new, content)
                    LOG.info("Change [%s] to [%s]", src_str_old, src_str_new)
                else:
                    e_src = re.compile(e_src_old_quote_noplus)
                    flag = e_src.findall(content)
                    if flag != []:
                        content = e_src.sub(e_src_new, content)
                        LOG.info("Change [%s] to [%s], unquote($/,@*+:%%&;)!", src_str_old, src_str_new)
                    else:
                        e_src = re.compile(e_src_old_quote_noplus_and)
                        flag = e_src.findall(content)
                        if flag != []:
                            content = e_src.sub(e_src_new, content)
                            LOG.info("Change [%s] to [%s], unquote($/,@*+:%%&;) and replace '&' to '&amp;'!", src_str_old, src_str_new)
                        else:
                            e_src = re.compile(e_src_old)
                            flag = e_src.findall(content)
                            if flag != []:
                                content = e_src.sub(e_src_new, content)
                                LOG.info("Change [%s] to [%s], unquote(all)!", src_str_old, src_str_new)
                            else:
                                LOG.info("Change [%s] to [%s] failed!", src_str_old, src_str_new)
    except Exception as e:
        LOG.exception(e)
    return content

def construct_file_path(file_sha1_name, file_name):
    file_path = ""
    file_ext = os.path.splitext(file_name)[1]
    file_sha1_name = file_sha1_name.strip()
    if len(file_sha1_name) > 4:
        file_path = os.path.join(file_sha1_name[:2], file_sha1_name[2:4], file_sha1_name + file_ext)
    else:
        file_path =os.path.join(file_sha1_name + file_ext)
    return file_path

def get_web_image_src(file_content):
    """
    param: file_content is unicode
    """
    result = []  # [["old_src", "new_src"], ["old_src", ""], ... ]
    try:
        utf8_parser = etree.HTMLParser(encoding="utf-8")
        page = etree.HTML(file_content.encode("utf-8"), parser = utf8_parser)
        iterator = page.getiterator()
        for i in iterator:
            if i.tag == "img":
                if i.attrib["src"] != "":
                    url = i.attrib["src"]
                    # parse as str (was bytes before, which made urlparse return
                    # bytes parts and `!= ""` always True -> even local
                    # /picture/ images were misclassified as web images).
                    url_parts = urllib.parse.urlparse(url)
                    if url_parts.scheme in ("http", "https") and url_parts.netloc != "":
                        result.append([i.attrib["src"], ""])
                        LOG.debug("img_absolute: %s"%i.attrib["src"])
    except Exception as e:
        LOG.exception(e)
    return result

def is_jpeg_image(file_content):
    result = None
    try:
        if not file_content.startswith(b'\xff\xd8'):
            pass
        else:
            if file_content.endswith(b'\xff\xd9'):
                result = True
            else:
                result = True
    except Exception as e:
        LOG.exception(e)
    return result

def is_svg_image(file_content):
    """
    param: file_content is unicode
    """
    result = False
    try:
        utf8_parser = etree.HTMLParser(encoding="utf-8")
        page = etree.HTML(file_content.encode("utf-8"), parser = utf8_parser)
        body = page.getchildren()[0]
        elements = body.getchildren()
        for element in elements:
            if elements[0].tag.lower() == "svg":
                result = True
                break
    except Exception as e:
        LOG.exception(e)
    return result

def get_web_images(images, db_pic = None, proxy = {}):
    result = []
    image = ""
    try:
        ifaces = psutil.net_if_addrs()
        local_ips = ["localhost", "127.0.0.1", CONFIG["SERVER_HOST"]]
        for _, v in list(ifaces.items()):
            local_ips.append(v[0].address)
        headers = {'User-Agent': 'Mozilla/5.0 (X11;Centos;Linux x86_64;rv:42.0) Gecko/20100101 Firefox/42.0',
                   'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        proxies = {}
        if "socks" in proxy:
            proxies["http"] = "socks5h://" + proxy["socks"]
            proxies["https"] = "socks5h://" + proxy["socks"]
        elif "http" in proxy:
            proxies["http"] = "http://" + proxy["http"]
            if "https" in proxy:
                proxies["https"] = "https://" + proxy["https"]
            else:
                proxies["https"] = "https://" + proxy["http"]
        LOG.debug("use proxy: %s", proxies)
        for i in images:
            try:
                # i[0] is the web src, i[1] is the local src
                url_parts = list(urllib.parse.urlparse(i[0]))
                if url_parts[1].split(":")[0] not in local_ips:
                    # p = opener.open(i[0], timeout = 10)
                    # timeout: this runs synchronously inside the tornado IOLoop;
                    # an unreachable image host would otherwise freeze the whole
                    # server (saving AND searching would hang).
                    p = requests.get(i[0], headers = headers, proxies = proxies, timeout = 15)
                    if p.status_code == 200:
                        image = p.content
                        image_name = os.path.split(list(urllib.parse.urlparse(i[0]))[2])[1]
                        image_name = util.construct_safe_filename(image_name)
                        fp = io.BytesIO(image)  # image is bytes; StringIO(bytes) raises in py3
                        if imghdr.what(fp) != None or is_jpeg_image(image) != None:
                            pic = PIC()
                            m = hashlib.sha1(image)
                            m.digest()
                            pic.sha1 = m.hexdigest()
                            pic.imported_at = datetime.datetime.now(dateutil.tz.tzlocal())
                            pic.file_name = image_name
                            pic.file_path = construct_file_path(pic.sha1, pic.file_name)
                            storage_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], os.path.split(pic.file_path)[0])
                            storage_file_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path)
                            if (not os.path.exists(storage_path)) or (not os.path.isdir(storage_path)):
                                os.makedirs(storage_path)
                            fp = open(storage_file_path, "wb")
                            fp.write(image)
                            fp.close()
                            flag = db_pic.save_data_to_db(pic.to_dict())
                            if flag == True:
                                image_url = "/picture/%s" % pic.sha1
                                result.append([i[0], image_url])
                        elif is_svg_image(image):
                            pic = PIC()
                            m = hashlib.sha1(image)
                            m.digest()
                            pic.sha1 = m.hexdigest()
                            pic.imported_at = datetime.datetime.now(dateutil.tz.tzlocal())
                            pic.file_name = image_name + ".html"
                            pic.file_path = construct_file_path(pic.sha1, pic.file_name)
                            storage_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], os.path.split(pic.file_path)[0])
                            storage_file_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path)
                            if (not os.path.exists(storage_path)) or (not os.path.isdir(storage_path)):
                                os.makedirs(storage_path)
                            fp = open(storage_file_path, "wb")
                            fp.write(image)
                            fp.close()
                            flag = db_pic.save_data_to_db(pic.to_dict())
                            if flag == True:
                                image_url = "/picture/%s" % pic.sha1
                                result.append([i[0], image_url])
                        else:
                            LOG.info("url[%s] is not a picture!", i[0])
                    else:
                        LOG.info("url[%s] get code: %s!", i[0], p.code)
                else:
                    image_url = url_parts[2]
                    result.append([i[0], image_url])
            except Exception as e:
                LOG.exception(e)
    except Exception as e:
        LOG.exception(e)
    return result

def html_change_image_src_BS(html_content, images):
    """
    param: html_content is unicode
    """
    result = ["", []]
    local_images = set()
    try:
        soup = BS(html_content, "lxml")
        # for web images
        if images != []:
            imgs = soup.find_all('img')
            LOG.debug("original html img: %s", imgs)
            for i in imgs:
                for j in images:
                    if i["src"] == j[0]:
                        i["src"] = j[1]
                        if i.has_attr("data-mce-src"):
                            i["data-mce-src"] = j[1]
            for i in imgs:
                if i["src"].startswith("picture/") or i["src"].startswith("/picture/"):
                    local_images.add(os.path.split(i["src"])[-1])
            LOG.debug("final html img: %s", imgs)
        # for local images
        else:
            imgs = soup.find_all('img')
            LOG.debug("original html img: %s", imgs)
            for i in imgs:
                if i["src"].startswith("picture/") or i["src"].startswith("/picture/"):
                    local_images.add(os.path.split(i["src"])[-1])
            LOG.info("web images is empty.")
        result[0] = soup.prettify(encoding = "utf-8", formatter = "html").decode("utf-8")
        result[1] = list(local_images)
        # print "YHT- ", imgs[0]["src"]
    except Exception as e:
        LOG.exception(e)
    return result

def html_head_add_content_type(html_content, content_type = "text/html; charset=utf-8"):
    """
    param: html_content is unicode
    """
    result = html_content
    try:
        soup = BS(html_content, "lxml")
        meta_tag = soup.new_tag("meta", content = content_type)
        meta_tag.attrs["http-equiv"] = "Content-Type"
        head_tag = soup.new_tag("head")
        html_tag = soup.new_tag("html")
        html = soup.find("html")
        if not html:
            html_tag.append(soup)
            soup = html_tag
        head = soup.find("head")
        if not head:
            soup.html.insert(0, head_tag)
        soup.html.head.append(meta_tag)
        result = soup.prettify(encoding = "utf-8", formatter = "html").decode("utf-8")
    except Exception as e:
        LOG.exception(e)
    return result

def get_rich_content(note_content, db_pic = None, proxy = {}):
    local_images = []
    if note_content.strip() != "":
        images = get_web_image_src(note_content)
        LOG.debug("imges: %s", images)
        images = get_web_images(images, db_pic, proxy = proxy)
        LOG.debug("imges_local: %s", images)
        note_content, local_images = html_change_image_src_BS(note_content, images)
        LOG.info("local_images: %s", local_images)
    return (note_content, local_images)

if __name__ == "__main__":
    print("path: ", cwd)
    test_path = "/media/sda8/breeze/MyNoteData/source"
    file_name = "巧用 python 脚本控制你的C程序 - Haippy - 博客园.html"
    file_path = os.path.join(test_path, file_name)
    fp = open(file_path, "rb")
    content = fp.read()
    fp.close()
    time_s = time.time()
    encoding = get_html_charset(content)
    time_m = time.time()
    content = html_decode_unicode(content)
    time_e = time.time()
    content = get_html_content(content)
    time_q = time.time()
    fp = open("./test.txt", "wb")
    fp.write(content)
    fp.close()
    print("encoding: ", encoding)
    # print "content: ", content
    # print "content: ", content
    print("1: ", time_m - time_s)
    print("2: ", time_e - time_m)
    print("3: ", time_q - time_e)
    print("everything is ok")