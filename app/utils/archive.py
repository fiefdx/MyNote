# -*- coding: utf-8 -*-
'''
Created on 2013-07-29 14:44
@summary:  archive files
@author: YangHaitao

Modified on 2013-09-01 17:46
@author: YangHaitao

Modified on 2013-11-14 22:50
@author: YangHaitao
'''

import sys
import os
import platform
import logging
import shutil
import zipfile
import tarfile
from time import localtime,strftime
from subprocess import PIPE
from subprocess import Popen

from config import CONFIG

LOG = logging.getLogger(__name__)

PLATFORM = [platform.system(), platform.architecture()[0]]

def archive_py_zip( file_list, zip_path, archive_name ):
    '''
    @summary:
        Compressed files with zip.
    @param:
        file_list:["D:\\dir\\filename",] or ["/home/user/dir/filename"]
    @result:
        True os False.
    '''
    zip_path = os.path.join( zip_path, ( archive_name + '.zip' ) )
    try:
        z = zipfile.ZipFile( zip_path, "w" )
        for f in file_list :
            z.write( f, os.path.split( f )[-1] )
            # LOG.info( 'Add the file :%s into zipfile : %s.'%( f, zip_path ) )
        z.close()
        return zip_path
    except Exception , ex:
        LOG.exception(ex)
        return False

def archive_py_tar(file_path, archive_path, archive_name, archive_type):
    '''
    @summary:
        Compressed files with tar.gz use tarfile
    @param:
    @result:
    '''
    result = False
    archive_t = {
                'tar' : '.tar',
                'tar.gz' : '.tar.gz'
                }
    archive_c = {
                'tar' : 'w',
                'tar.gz' : 'w:gz'
                }
    archive_name = archive_name + archive_t[archive_type]
    targz_path = os.path.join(archive_path, archive_name)
    try:
        t = tarfile.open(targz_path, archive_c[archive_type])
        if os.path.exists(file_path):
            t.add(file_path, os.path.split(file_path)[1])
            t.close()
            result = archive_name
        else:
            LOG.warning("The file_path do not exists!")
    except Exception , ex:
        LOG.exception(ex)
        result = False
    return result

def extract_py_tar(extract_path, archive_path, archive_name, archive_type):
    '''
    @summary:
        extract files with tarfile
    @param:
        pack_format: 'tar','tar.gz'
        archive_name: only name like 'test'
    @result:
    '''
    result = False
    archive_t = {
                'tar' : '.tar',
                'tar.gz' : '.tar.gz'
                }
    archive_c = {
                'tar' : 'r',
                'tar.gz' : 'r:gz'
                }
    archive_name = archive_name + archive_t[archive_type]
    targz_path = os.path.join(archive_path, archive_name)
    try:
        t = tarfile.open(targz_path, archive_c[archive_type])
        if os.path.exists(extract_path):
            t.extractall(path = extract_path)
            t.close()
            result = archive_name
        else:
            LOG.warning("The extract_path do not exists!")
    except Exception , ex:
        LOG.exception(ex)
        result = False
    return result

def archive_7z(file_path, archive_path, archive_name, archive_type):
    '''
    @summary:
        Compressed files with 7z
    @param:
        pack_format: 'tar','tar.gz','zip','7z'
        archive_name: only name like 'test'
    @result:
    '''
    result = False
    archive_t = {
                'tar' : '.tar',
                'zip' : '.zip',
                'tar.gz' : '.tar.gz',
                '7z' : '.7z'
                }
    archive_name = archive_name + archive_t[archive_type]
    archive_path = os.path.join(archive_path, archive_name)
    try:
        cmd = '7z a %s %s'%(archive_path, file_path)
        # Popen(cmd, shell = True)
        pipe = Popen(cmd, shell = True, stdout = PIPE).stdout
        msg = pipe.read()
        LOG.debug("7z msg: %s"%msg)
        result = archive_name
    except Exception, e:
        LOG.exception(e)
        result = False
    return result

def extract_7z(extract_path, archive_path, archive_name, archive_type):
    '''
    @summary:
        extract files with tar
    @param:
        pack_format: 'tar','zip','7z'
        archive_name: only name like 'test'
    @result:
    '''
    result = False
    archive_t = {
                'tar' : '.tar',
                'zip' : '.zip',
                '7z' : '.7z'
                }
    archive_name = archive_name + archive_t[archive_type]
    archive_path = os.path.join(archive_path, archive_name)
    cmd = ""
    try:
        if archive_type == "tar.gz":
            LOG.debug("there is a tar.gz package! do not use 7z now.")
            return result
        cmd = '7z x %s -o%s'%(archive_path, extract_path)
        # Popen(cmd, shell = True)
        pipe = Popen(cmd, shell = True, stdout = PIPE).stdout
        msg = pipe.read()
        LOG.debug("7z extract msg: %s"%msg)
        result = archive_name
    except Exception, e:
        LOG.exception(e)
        result = False
    return result

def archive_tar(file_path, archive_path, archive_name, archive_type):
    '''
    @summary:
        Compressed files with tar
    @param:
        pack_format: 'tar','tar.gz'
        archive_name: only name like 'test'
    @result:
    '''
    result = False
    archive_t = {
                'tar' : '.tar',
                'tar.gz' : '.tar.gz'
                }
    archive_name = archive_name + archive_t[archive_type]
    archive_path = os.path.join(archive_path, archive_name)
    try:
        cmd = 'tar cvzf %s -C %s %s'%(archive_path, os.path.split(file_path)[0], os.path.split(file_path)[1])
        # Popen(cmd, shell = True)
        pipe = Popen(cmd, shell = True, stdout = PIPE).stdout
        msg = pipe.read()
        LOG.debug("tar msg: %s"%msg)
        result = archive_name
    except Exception, e:
        LOG.exception(e)
        result = False
    return result

def extract_tar(extract_path, archive_path, archive_name, archive_type):
    '''
    @summary:
        extract files with tar
    @param:
        pack_format: 'tar','tar.gz'
        archive_name: only name like 'test'
    @result:
    '''
    result = False
    archive_t = {
                'tar' : '.tar',
                'tar.gz' : '.tar.gz'
                }
    archive_name = archive_name + archive_t[archive_type]
    archive_path = os.path.join(archive_path, archive_name)
    cmd = ""
    try:
        if archive_type == "tar":
            cmd = 'tar xvf %s -C %s'%(archive_path, extract_path)
        else:
            cmd = 'tar xvzf %s -C %s'%(archive_path, extract_path)
        # Popen(cmd, shell = True)
        pipe = Popen(cmd, shell = True, stdout = PIPE).stdout
        msg = pipe.read()
        LOG.debug("tar extract msg: %s"%msg)
        result = archive_name
    except Exception, e:
        LOG.exception(e)
        result = False
    return result

class Archive(object):
    def __init__(self, user_info):
        self.export_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "tmp", "export")
        self.import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "tmp", "import")
        self.user = user_info.user_name
        self.package = ""
        self.package_path = ""
        self.file_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "notes")

    def archive(self, archive_type, category = "", encrypt = False):
        date_time = strftime("%Y%m%d_%H%M", localtime())
        archive_name = "%s_notes_%s"%(self.user, date_time) if category == "" else "%s_notes_%s_%s"%(self.user, category, date_time)
        if encrypt:
            archive_name += "_encrypted"
        package_name = ""
        try:
            if archive_type == "tar.gz":
                if PLATFORM[0].lower() == "windows":
                    package_name = archive_py_tar(self.file_path, self.export_path, archive_name, "tar.gz")
                    LOG.info("Use python tarfile to archive.")
                else:
                    package_name = archive_tar(self.file_path, self.export_path, archive_name, "tar.gz")
                    LOG.info("Use tar to archive.")
            else:
                package_name = archive_7z(self.file_path, self.export_path, archive_name, archive_type)
            self.package = package_name
            self.package_path = os.path.join(self.export_path, self.package)
            LOG.debug("Created package[%s] success"%self.package)
        except Exception, e:
            LOG.exception(e)

    def extract(self, archive_name, archive_type):
        """
        archive_name: full file name "filename.tar.gz"
        """
        package_name = ""
        archive_t = {
                'tar' : '.tar',
                'tar.gz' : '.tar.gz'
                }
        # archive_path = os.path.join(self.import_path, archive_name + archive_t[archive_type])
        # LOG.debug("archive_path: [%s]"%archive_path)
        try:
            if archive_type == "tar.gz" or archive_type == "tar":
                if PLATFORM[0].lower() == "windows":
                    package_name = extract_py_tar(self.import_path, self.import_path, archive_name, archive_type)
                    LOG.info("Use python tarfile to extract.")
                else:
                    package_name = extract_tar(self.import_path, self.import_path, archive_name, archive_type)
                    LOG.info("Use tar to extract.")
            else:
                package_name = extract_7z(self.import_path, self.import_path, archive_name, archive_type)
            self.package = package_name
            self.package_path = os.path.join(self.import_path, self.package)
            LOG.debug("Extract package[%s] success"%self.package)
        except Exception, e:
            LOG.exception(e)

    def clear(self):
        try:
            # file_path = os.path.join(self.export_path, self.package)
            file_path = self.package_path
            if os.path.isfile(file_path) and os.path.exists(file_path):
                os.remove(file_path)
                LOG.debug("Clear [%s]"%file_path)
        except Exception, e:
            LOG.exception(e)

class Archive_Rich_Notes(object):
    def __init__(self, user_info):
        self.export_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "tmp", "export")
        self.import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "tmp", "import")
        self.user = user_info.user_name
        self.package = ""
        self.package_path = ""
        self.file_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "rich_notes")

    def archive(self, archive_type, category = "", encrypt = False):
        date_time = strftime("%Y%m%d_%H%M", localtime())
        archive_name = "%s_rich_notes_%s"%(self.user, date_time) if category == "" else "%s_rich_notes_%s_%s"%(self.user, category, date_time)
        if encrypt:
            archive_name += "_encrypted"
        package_name = ""
        try:
            if archive_type == "tar.gz":
                if PLATFORM[0].lower() == "windows":
                    package_name = archive_py_tar(self.file_path, self.export_path, archive_name, "tar.gz")
                    LOG.info("Use python tarfile to archive.")
                else:
                    package_name = archive_tar(self.file_path, self.export_path, archive_name, "tar.gz")
                    LOG.info("Use tar to archive.")
            else:
                package_name = archive_7z(self.file_path, self.export_path, archive_name, archive_type)
            self.package = package_name
            self.package_path = os.path.join(self.export_path, self.package)
            LOG.debug("Created package[%s] success"%self.package)
        except Exception, e:
            LOG.exception(e)

    def extract(self, archive_name, archive_type):
        """
        archive_name: full file name "filename.tar.gz"
        """
        package_name = ""
        archive_t = {
                'tar' : '.tar',
                'tar.gz' : '.tar.gz'
                }
        # archive_path = os.path.join(self.import_path, archive_name + archive_t[archive_type])
        # LOG.debug("archive_path: [%s]"%archive_path)
        try:
            if archive_type == "tar.gz" or archive_type == "tar":
                if PLATFORM[0].lower() == "windows":
                    package_name = extract_py_tar(self.import_path, self.import_path, archive_name, archive_type)
                    LOG.info("Use python tarfile to extract.")
                else:
                    package_name = extract_tar(self.import_path, self.import_path, archive_name, archive_type)
                    LOG.info("Use tar to extract.")
            else:
                package_name = extract_7z(self.import_path, self.import_path, archive_name, archive_type)
            self.package = package_name
            self.package_path = os.path.join(self.import_path, self.package)
            LOG.debug("Extract package[%s] success"%self.package)
        except Exception, e:
            LOG.exception(e)

    def clear(self):
        try:
            # file_path = os.path.join(self.export_path, self.package)
            file_path = self.package_path
            if os.path.isfile(file_path) and os.path.exists(file_path):
                os.remove(file_path)
                LOG.debug("Clear [%s]"%file_path)
        except Exception, e:
            LOG.exception(e)

class Archive_Rich_Note(object):
    def __init__(self, user_info):
        self.export_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "tmp", "export")
        self.import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "tmp", "import")
        self.user = user_info.user_name
        self.package = ""
        self.package_path = ""
        self.file_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], user_info.sha1, "rich_note")

    def archive(self, archive_type, note_name):
        date_time = strftime("%Y%m%d_%H%M", localtime())
        archive_name = "%s_%s" % (note_name, date_time)
        package_name = ""
        try:
            if archive_type == "tar.gz":
                if PLATFORM[0].lower() == "windows":
                    package_name = archive_py_tar(self.file_path, self.export_path, archive_name, "tar.gz")
                    LOG.info("Use python tarfile to archive.")
                else:
                    package_name = archive_tar(self.file_path, self.export_path, archive_name, "tar.gz")
                    LOG.info("Use tar to archive.")
            else:
                package_name = archive_7z(self.file_path, self.export_path, archive_name, archive_type)
            self.package = package_name
            self.package_path = os.path.join(self.export_path, self.package)
            LOG.debug("Created package[%s] success"%self.package)
        except Exception, e:
            LOG.exception(e)

    def clear(self):
        try:
            # file_path = os.path.join(self.export_path, self.package)
            file_path = self.package_path
            if os.path.isfile(file_path) and os.path.exists(file_path):
                os.remove(file_path)
                LOG.debug("Clear [%s]"%file_path)
        except Exception, e:
            LOG.exception(e)
