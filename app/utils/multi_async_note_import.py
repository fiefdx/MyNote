# -*- coding: utf-8 -*-
'''
Created on 2015-03-06
@summary: multi-process import text notes
@author: YangHaitao
'''

import os
import shutil
import logging
import json
import time
import binascii
from time import localtime, strftime
from multiprocessing import Process, Pipe

from tornado import gen
import toro

from db import sqlite
from db.sqlite import DB
from utils.archive import Archive
from models.item import NOTE
from utils import common_utils
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

def process_notes(source_dir, storage_path, key = "", old_key = "", user = "", db = None):
    try:
        total_count_file = 0
        success_processed_count_file = 0
        s_time = time.time()
        for root, dirs, files in os.walk(source_dir):
            for fname in files:
                if ".json" not in fname:
                    fpath = os.path.join(root, fname)
                    LOG.debug("Processing [%s]", fpath)
                    total_count_file += 1
                    note = NOTE()
                    note.parse_xml(fpath)
                    if old_key != "":
                        note.decrypt(old_key, decrypt_description = False)
                    note.description = common_utils.get_description_text(note.file_content, CONFIG["NOTE_DESCRIPTION_LENGTH"])
                    note.user_name = user
                    if key != "":
                        note.encrypt(key)
                    note_dict = note.to_dict()
                    if note_dict["version"] == "":
                        # type is unicode
                        note_dict["type"] = common_utils.sha1sum(note_dict["type"])
                    flag = sqlite.save_data_to_db(note_dict, db.note, mode = "INSERT", conn = db.conn_note)
                    if flag == True:
                        LOG.debug("write note to database success")
                        target = ""
                        if storage_path != None:
                            target = os.path.join(storage_path, note_dict["type"], fname)
                            shutil.copyfile(fpath, target)
                            success_processed_count_file += 1
                            LOG.debug("copy note[%s] to [%s] success", fpath, target)
                        else:
                            LOG.error("copy note[%s] to user[%s] failed", fpath, user)
                    else:
                        LOG.debug("write note to database failed")
        e_time = time.time()
        msg = "import notes:\n" \
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
        logger.config_logging(file_name = ("note_import_%s_" % self.process_id + '.log'), 
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
                                                       "notes", 
                                                       "category.json")
                        if os.path.exists(categories_path) and os.path.isfile(categories_path):
                            fp = open(categories_path, 'rb')
                            categories = json.loads(fp.read())
                            fp.close()
                        else:
                            note_books = ["work", "think", "person", "enjoy", "other"]
                            for n in note_books:
                                categories.append({'name':n, 'sha1':common_utils.sha1sum(n)})
                        note_books = json.loads(user.note_books)
                        # LOG.info("note_books[%s]: %s", user, note_books)
                        for category in categories:
                            if category not in note_books:
                                note_books.append(category)
                                notes_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                          user.sha1, 
                                                          "notes", 
                                                          category['sha1'])
                                if not os.path.exists(notes_path):
                                    os.makedirs(notes_path)
                                    LOG.info("create notes path[%s] success", notes_path)
                        user.note_books = json.dumps(note_books)
                        flag = sqlite.save_data_to_db(user.to_dict(), self.db.user, mode = "UPDATE", conn = self.db.conn_user)
                        if flag:
                            LOG.info("import notes user[%s] categories success", user.user_name)
                        else:
                            LOG.error("import notes user[%s] categories failed", user.user_name)
                        # import notes
                        import_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                   user.sha1, 
                                                   "tmp", 
                                                   "import",  
                                                   "notes")
                        storage_path = os.path.join(CONFIG["STORAGE_USERS_PATH"], 
                                                    user.sha1, 
                                                    "notes")
                        process_notes(import_path, 
                                      storage_path, 
                                      key = user_key if CONFIG["ENCRYPT"] else "", 
                                      old_key = password, 
                                      user = user.user_name,
                                      db = self.db)
                        if os.path.exists(import_path) and os.path.isdir(import_path):
                            shutil.rmtree(import_path)
                            LOG.info("delete import_path[%s] success.", import_path)
                        # index all notes
                        # flag = index_whoosh.index_all_note_by_num_user(1000, 
                        #                                                user.user_name, 
                        #                                                key = user_key if CONFIG["ENCRYPT"] else "",
                        #                                                db = self.db,
                        #                                                ix = self.ix,
                        #                                                merge = True)
                        # if flag:
                        #     LOG.info("Reindex all notes user[%s] success", user.user_name)
                        # else:
                        #     LOG.error("Reindex all notes user[%s] failed!", user.user_name)
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