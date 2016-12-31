# -*- coding: utf-8 -*-
'''
Created on 2015-03-06
@summary: multi-process import rich notes
@author: YangHaitao
'''

import os
import sys
import shutil
import logging
import json
import time
import signal
import binascii
import dateutil
import hashlib
import datetime
import time
from time import localtime, strftime
from multiprocessing import Process, Pipe

import tornado
from tornado import gen
from tornado.ioloop import IOLoop
import toro

import tea
from tea import EncryptStr, DecryptStr

from db import sqlite
from db.sqlite import DB
from utils import note_xml
from utils.archive import Archive_Rich_Notes as Archive
from models.item import PICTURE as PIC
from models.item import RICH
from models.item import NOTE
from utils import common_utils
from utils import htmlparser
# from utils import index_whoosh
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


def crc32sum_int(data, crc = None):
    '''
    data is string
    crc is a CRC32 int
    '''
    result = ""
    if crc == None:
        result = binascii.crc32(data)
    else:
        result = binascii.crc32(data, crc)
    return result

def construct_file_path(file_sha1_name, file_name):
    file_path = ""
    file_ext = os.path.splitext(file_name)[1]
    file_sha1_name = file_sha1_name.strip()
    if len(file_sha1_name) > 4:
        file_path = os.path.join(file_sha1_name[:2], file_sha1_name[2:4], file_sha1_name + file_ext)
    else:
        file_path =os.path.join(file_sha1_name + file_ext)
    return file_path

def process_images(source_dir, db = None):
    try:
        total_count_file = 0
        success_processed_count_file = 0
        s_time = time.time()
        for root, dirs, files in os.walk(source_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                LOG.debug("processing %s", fpath)
                total_count_file += 1
                fp = open(fpath, "rb")
                image = fp.read()
                fp.close()
                pic = PIC()
                m = hashlib.sha1(image)
                m.digest()
                pic.sha1 = m.hexdigest()
                pic.imported_at = datetime.datetime.now(dateutil.tz.tzlocal())
                pic.file_name = common_utils.construct_safe_filename(fname.decode("utf-8"))
                pic.file_path = construct_file_path(pic.sha1, pic.file_name).decode("utf-8")
                storage_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], os.path.split(pic.file_path)[0])
                storage_file_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path)
                if (not os.path.exists(storage_path)) or (not os.path.isdir(storage_path)):
                    os.makedirs(storage_path)
                fp = open(storage_file_path, "wb")
                fp.write(image)
                fp.close()
                flag = sqlite.save_data_to_db(pic.to_dict(), db.pic, conn = db.conn_pic)
                if flag == True:
                    success_processed_count_file += 1
                    LOG.debug("write image to [%s] success"%storage_file_path)
                else:
                    LOG.debug("write image to [%s] failed"%storage_file_path)
        e_time = time.time()
        msg = "import images:\n" \
              "total_files: %s\n" \
              "processed_files: %s\n" \
              "time_elapsed: %ss" % (total_count_file, success_processed_count_file, e_time - s_time)
        LOG.info(msg)
    except Exception, e:
        LOG.exception(e)

def process_rich_notes(source_dir, storage_path, key = "", old_key = "", user = "", db = None):
    try:
        total_count_file = 0
        success_processed_count_file = 0
        s_time = time.time()
        for root, dirs, files in os.walk(source_dir):
            for fname in files:
                if ".json" not in fname:
                    fpath = os.path.join(root, fname)
                    LOG.debug("processing [%s]", fpath)
                    total_count_file += 1
                    note = note_xml.get_rich_note_from_xml(xml_path = fpath)
                    if old_key != "":
                        note.decrypt(old_key, decrypt_description = False)
                    note.description = common_utils.get_description_text(note.file_content, CONFIG["NOTE_DESCRIPTION_LENGTH"])
                    note.user_name = user
                    if note.version == "" or note.version == "0.1":
                        note_content = note.rich_content
                        note_content, images = htmlparser.get_rich_content(note_content)
                        note.images = images
                    if key != "":
                        note.encrypt(key)
                    # LOG.debug("Note_dict: %s", note_dict)
                    # note_dict["user_name"] = user
                    # note_dict["id"] = ""
                    note_dict = note.to_dict()
                    if note_dict["version"] == "":
                        # type is unicode
                        note_dict["type"] = common_utils.sha1sum(note_dict["type"])
                    # db = DB()
                    flag = sqlite.save_data_to_db(note_dict, db.rich, mode = "INSERT", conn = db.conn_rich)
                    if flag == True:
                        LOG.debug("write rich note to database success")
                        target = ""
                        note = sqlite.get_rich_by_sha1(note_dict["sha1"], user, conn = db.conn_rich)
                        if storage_path != None:
                            target = os.path.join(storage_path, note_dict["type"], str(note.id))
                            shutil.copyfile(fpath, target)
                            success_processed_count_file += 1
                            LOG.debug("copy rich note[%s] to [%s] success", fpath, target)
                        else:
                            LOG.error("copy rich note[%s] to user[%s] failed", fpath, user)
                    else:
                        LOG.debug("write rich note to database failed")
        e_time = time.time()
        msg = "import rich notes:\n" \
              "total_files: %s\n" \
              "processed_files: %s\n" \
              "time_elapsed: %ss" % (total_count_file, success_processed_count_file, e_time - s_time)
        LOG.info(msg)
    except Exception, e:
        LOG.exception(e)

class NoteImportProcess(Process):
    def __init__(self, process_id, pipe_client):
        Process.__init__(self)
        self.process_id = process_id
        self.pipe_client = pipe_client
        self.db = None
        # self.ix = index_whoosh.IX()

    def run(self):
        date_time = strftime("%Y%m%d_%H%M%S", localtime())
        logger.config_logging(file_name = ("rich_import_%s_" % self.process_id + '.log'), 
                              log_level = CONFIG['LOG_LEVEL'], 
                              dir_name = "logs", 
                              day_rotate = False, 
                              when = "D", 
                              interval = 1, 
                              max_size = 20, 
                              backup_count = 5, 
                              console = True)
        LOG.info("Start NoteImportProcess(%s)", self.process_id)
        if self.db == None:
            self.db = DB()
        try:
            while True:
                try:
                    # args is (), kwargs is {}, note is RICH or NOTE object
                    command, file_name, user, user_key, password = self.pipe_client.recv()
                    if command == "IMPORT":
                        LOG.debug("NoteImportProcess import %s[%s] to Process(%s)", user.sha1, user.user_name, self.process_id)
                        # extract uploaded file
                        arch = Archive(user)
                        archive_name = file_name.split(".")[0]
                        archive_type = os.path.splitext(file_name)[1]
                        if archive_type == ".gz":
                            archive_type = "tar.gz"
                        elif archive_type == ".7z":
                            archive_type = "7z"
                        elif archive_type == ".zip":
                            archive_type = "zip"
                        else:
                            archive_type = "tar"
                        arch.extract(archive_name, archive_type)
                        arch.clear()
                        # update categories
                        categories = []
                        categories_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                       user.sha1, 
                                                       "tmp", 
                                                       "import", 
                                                       "rich_notes", 
                                                       "category.json")
                        if os.path.exists(categories_path) and os.path.isfile(categories_path):
                            fp = open(categories_path, 'rb')
                            categories = json.loads(fp.read())
                            # LOG.info(">>>>>>>>>>>>>>>>>>>>>>>>>>%s", categories)
                            fp.close()
                        else:
                            note_books = ["work", "think", "person", "enjoy", "other"]
                            for n in note_books:
                                categories.append({'name':n, 'sha1':common_utils.sha1sum(n)})
                        note_books = json.loads(user.rich_books)
                        # LOG.info("note_books[%s]: %s", user, note_books)
                        for category in categories:
                            if category not in note_books:
                                note_books.append(category)
                                notes_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                          user.sha1, 
                                                          "rich_notes", 
                                                          "rich_notes", 
                                                          category['sha1'])
                                if not os.path.exists(notes_path):
                                    os.makedirs(notes_path)
                                    LOG.info("create rich notes path[%s] success", notes_path)
                        user.rich_books = json.dumps(note_books)
                        flag = sqlite.save_data_to_db(user.to_dict(), self.db.user, mode = "UPDATE", conn = self.db.conn_user)
                        if flag:
                            LOG.info("import rich notes user[%s] categories success", user.user_name)
                        else:
                            LOG.error("import rich notes user[%s] categories failed", user.user_name)
                        # import images
                        images_dir = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                  user.sha1, 
                                                  "tmp", 
                                                  "import", 
                                                  "rich_notes", 
                                                  "images")
                        process_images(images_dir, db = self.db)
                        # import rich notes
                        import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                   user.sha1, 
                                                   "tmp", 
                                                   "import", 
                                                   "rich_notes", 
                                                   "rich_notes")
                        storage_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                    user.sha1, 
                                                    "rich_notes", 
                                                    "rich_notes")
                        process_rich_notes(import_path, 
                                           storage_path, 
                                           key = user_key if CONFIG["ENCRYPT"] else "", 
                                           old_key = password, 
                                           user = user.user_name,
                                           db = self.db)
                        import_root_path = os.path.split(import_path)[0]
                        if os.path.exists(import_root_path) and os.path.isdir(import_root_path):
                            shutil.rmtree(import_root_path)
                            LOG.info("delete import_path[%s] success.", import_root_path)
                        # index all rich notes
                        # flag = index_whoosh.index_all_rich_by_num_user(1000, 
                        #                                                user.user_name, 
                        #                                                key = user_key if CONFIG["ENCRYPT"] else "",
                        #                                                db = self.db,
                        #                                                ix = self.ix,
                        #                                                merge = True)
                        # if flag:
                        #     LOG.info("Reindex all rich notes user[%s] success", user.user_name)
                        # else:
                        #     LOG.error("Reindex all rich notes user[%s] failed!", user.user_name)
                        # send result
                        if flag == True:
                            self.pipe_client.send((command, True))
                        else:
                            self.pipe_client.send((command, False))
                    elif command == "EXIT":
                        LOG.info("NoteImportProcess(%s) exit by EXIT command!", self.process_id)
                        return
                except EOFError:
                    LOG.error("EOFError NoteImportProcess(%s) Write Thread exit!", self.process_id)
                    return
                except Exception, e:
                    LOG.exception(e)
            LOG.info("Leveldb Process(%s) exit!", self.process_id)
        except KeyboardInterrupt:
            LOG.info("KeyboardInterrupt: NoteImportProcess(%s) exit!", self.process_id)
        except Exception, e:
            LOG.exception(e)
        finally:
            self.db.close()
            LOG.info("NoteImportProcess(%s) close db conn!", self.process_id)
            # self.ix.close()
            # LOG.info("NoteImportProcess(%s) close ix conn!", self.process_id)

class MultiProcessNoteImport(object):
    PROCESS_LIST = []
    PROCESS_DICT = {}
    WRITE_LOCKS = []
    READ_LOCKS = []
    _instance = None

    def __init__(self, process_num = 1):
        if MultiProcessNoteImport._instance == None:
            self.process_num = process_num
            for i in xrange(process_num):
                pipe_master, pipe_client = Pipe()
                MultiProcessNoteImport.WRITE_LOCKS.append(toro.Lock())
                p = NoteImportProcess(i, pipe_client)
                p.daemon = True
                MultiProcessNoteImport.PROCESS_LIST.append(p)
                MultiProcessNoteImport.PROCESS_DICT[i] = [p, pipe_master]
                p.start()
            MultiProcessNoteImport._instance = self
        else:
            self.process_num = MultiProcessNoteImport._instance.process_num

    @gen.coroutine
    def import_notes(self, file_name, user, user_key, password):
        """
        user: is user object from models.item.USER
        file_name: is uploaded file's name
        args: args for encrypt & decrypt
        kwargs: kwargs for encrypt & decrypt 
        """
        result = False
        process_id = crc32sum_int(user.sha1) % self.process_num
        # acquire write lock
        LOG.debug("Start import %s to Process(%s)", user.user_name, process_id)
        with (yield MultiProcessNoteImport.WRITE_LOCKS[process_id].acquire()):
            LOG.debug("Get import Lock %s to Process(%s)", user.user_name, process_id)
            MultiProcessNoteImport.PROCESS_DICT[process_id][1].send(("IMPORT", file_name, user, user_key, password))
            LOG.debug("Send import %s to Process(%s) end", user.user_name, process_id)
            while not MultiProcessNoteImport.PROCESS_DICT[process_id][1].poll():
                yield gen.moment
            LOG.debug("RECV import %s to Process(%s)", user.user_name, process_id)
            r = MultiProcessNoteImport.PROCESS_DICT[process_id][1].recv()
            LOG.debug("End import %s to Process(%s)", user.user_name, process_id)
        LOG.debug("NoteImportProcess(%s): %s", process_id, r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    def close(self):
        try:
            # for i in MultiProcessNoteImport.PROCESS_DICT.iterkeys():
            #     MultiProcessNoteImport.PROCESS_DICT[i][0].terminate()
            for i in MultiProcessNoteImport.PROCESS_DICT.iterkeys():
                MultiProcessNoteImport.PROCESS_DICT[i][1].send(("EXIT", None, None, None, None))
            for i in MultiProcessNoteImport.PROCESS_DICT.iterkeys():
                while MultiProcessNoteImport.PROCESS_DICT[i][0].is_alive():
                    time.sleep(0.5)
            LOG.info("All NoteImport Process Exit!")
        except Exception, e:
            LOG.exception(e)