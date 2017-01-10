# -*- coding: utf-8 -*-
'''
Created on 2013-11-16 17:03
@summary:  some utils
@author: YangHaitao

Modified on 2014-06-09
@summary: add get_description_text common utils for note and rich
@author: YangHaitao
''' 

import os
import re
import logging
import hashlib


# cwd = os.path.split(os.path.realpath(__file__))[0]
cwd = "."
LOG = logging.getLogger(__name__)

def sha1sum(content):
    '''
    param content must be unicode
    result is unicode
    '''
    m = hashlib.sha1(content.encode("utf-8"))
    m.digest()
    result = m.hexdigest().decode("utf-8")
    return result

def sha256sum(content):
    '''
    param content must be unicode
    result is unicode
    '''
    m = hashlib.sha256(content.encode("utf-8"))
    m.digest()
    result = m.hexdigest().decode("utf-8")
    return result

def md5twice(content):
    '''
    param content must be unicode
    result is unicode
    '''
    m = hashlib.md5(content.encode("utf-8")).hexdigest()
    result = hashlib.md5(m).hexdigest().decode("utf-8")
    return result

def get_ftype(fname):
    fname, fext = os.path.spsqlitext(fname)
    result = fext
    LOG.debug("get ext %s."%fext)
    return result

def construct_file_path(file_sha1_name, file_name):
    file_path = ""
    file_ext = os.path.splitext(file_name)[1]
    file_sha1_name = file_sha1_name.strip()
    if len(file_sha1_name) > 4:
        file_path = os.path.join(file_sha1_name[:2], 
                                 file_sha1_name[2:4], 
                                 file_sha1_name + file_ext)
    else:
        file_path = os.path.join(file_sha1_name + file_ext)
    return file_path

def construct_safe_filename(file_name):
    result = False
    illegal_char_list = ["/", "\\", ":", "*", "?", "\"", "\'", "<", ">", "|", "\t"]
    try:
        file_name, ext = os.path.splitext(file_name)
        file_name = file_name.strip()
        ext = ext.strip()
        new_file_name = file_name
        for i in illegal_char_list:
            new_file_name = new_file_name.replace(i, "")
        re_select = '''(?P<multi_space> +)'''
        re_replace = '''_'''
        e_src = re.compile(re_select)
        flag = e_src.findall(new_file_name)
        if flag != []:
            new_file_name = e_src.sub(re_replace, new_file_name)
        result = new_file_name + ext
    except Exception, e:
        LOG.exception(e)
        result = False
    return result

def get_description_text(content, length):
    """
    content: unicode
    """
    re_select = '''(?P<multi_space>  +)'''
    re_replace = ''' '''
    e_src = re.compile(re_select)
    flag = e_src.findall(content)
    if flag != []:
        # LOG.debug("flag: %s"%flag)
        content = e_src.sub(re_replace, content)
    excerpts = u""
    # content = content.replace(' ','')
    len_content = len(content)
    if len_content > length:
        content = content[:length]
    else:
        content = content
    content = content.replace('\r', '')
    content = content.replace('\n', ' ')
    content = content.replace('&','&amp;')
    content = content.replace('<','&lt;')
    content = content.replace('>','&gt;')
    content = content.replace(' ','&nbsp;')
    content = content.replace('\"','&quot;')
    excerpts += content
    # LOG.debug("Get excerpt: %s", excerpts)
    return excerpts

def safe_dir_filename(dir_path):
    change_list = []
    dir_root_path = os.path.split(dir_path)[0]
    try:
        for root, dirs, files in os.walk(dir_path):
            if files != []:
                similar_files = []
                files_str = "\n".join(files)
                files_str_lower = files_str.lower()
                files_lower = files_str_lower.split("\n")
                set_files_lower = set(files_lower)
                for i in set_files_lower:
                    n = files_lower.count(i)
                    if n > 1:
                        similar_files.append(i)
                root_path = root.replace(dir_root_path, "")
                if root_path[0] == os.sep:
                    root_path = root_path[1:]
                result_dict = {"root": root_path, "change_file":[]}
                LOG.debug("similar_files: %s", similar_files)
                for i in similar_files:
                    file_name, file_ext = os.path.splitext(i)
                    e_src_files = '''(?P<file_name>%s)'''%i
                    e_src = re.compile(e_src_files, re.I|re.M)
                    flag = e_src.findall(files_str)
                    if flag != []:
                        LOG.debug("Regulation flag: %s", flag)
                        for j in xrange(len(flag)):
                            new_file_name = file_name + "_%s"%j + file_ext
                            n = j
                            while new_file_name in files:
                                n += 1
                                new_file_name = file_name + "_%s"%n + file_ext
                            files.append(new_file_name)
                            os.rename(os.path.join(root, flag[j]), 
                                      os.path.join(root, new_file_name))
                            LOG.debug("Rename: [%s] to [%s]", 
                                      os.path.join(root, flag[j]), 
                                      os.path.join(root, new_file_name))
                            result_dict["change_file"].append([flag[j], new_file_name])
                    change_list.append(result_dict)
    except Exception, e:
        LOG.exception(e)
        change_list = []
    return change_list