# -*- coding: utf-8 -*-
'''
Created on 2016-01-09
@summary: task
@author: YangHaitao
'''

import os
import json
import time
import shutil
import logging
import datetime
import hashlib
import dateutil

from db import sqlite
from db.sqlite import DB, NoteLock, ImageLock, RichLock
from utils.archive import Archive
from utils import common_utils
from utils import htmlparser
from models.item import NOTE, RICH, PICTURE
from models.task import TaskProcesser, StopSignal
from config import CONFIG

LOG = logging.getLogger("worker")

def get_key(file_name, user):
    return "%s_%s" % (file_name, user.sha1)

class NoteImportProcesser(TaskProcesser):
    name = "note"

    def __init__(self):
        self.db = DB()
        self.task_key = ""

    def iter(self, file_name, user, user_key, password):
        self.task_key = get_key(file_name, user)
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

        key = user_key if CONFIG["ENCRYPT"] else ""

        try:
            for root, dirs, files in os.walk(import_path):
                for fname in files:
                    if ".json" not in fname:
                        fpath = os.path.join(root, fname)
                        LOG.debug("Processing [%s]", fpath)
                        yield [self.name, self.task_key, fname, fpath, storage_path, user.user_name, key, password]
        except Exception, e:
            LOG.exception(e)
        time.sleep(5)
        yield [self.name, self.task_key, StopSignal, "", "", "", "", ""]

    def map(self, x):
        _, self.task_key, fname, fpath, storage_path, user_name, key, password = x
        result = (self.name, self.task_key, False)
        try:
            if fname != StopSignal:
                note = NOTE()
                note.parse_xml(fpath)
                if password != "":
                    note.decrypt(password, decrypt_description = False)
                note.description = common_utils.get_description_text(note.file_content, CONFIG["NOTE_DESCRIPTION_LENGTH"])
                note.user_name = user_name
                if key != "":
                    note.encrypt(key)
                note_dict = note.to_dict()
                if note_dict["version"] == "":
                    # type is unicode
                    note_dict["type"] = common_utils.sha1sum(note_dict["type"])
                NoteLock.acquire()
                flag = sqlite.save_data_to_db(note_dict, self.db.note, mode = "INSERT", conn = self.db.conn_note)
                NoteLock.release()
                if flag == True:
                    LOG.debug("write note to database success")
                    target = ""
                    if storage_path != None:
                        target = os.path.join(storage_path, note_dict["type"], fname)
                        shutil.copyfile(fpath, target)
                        result = [self.name, self.task_key, True]
                        LOG.debug("copy note[%s] to [%s] success", fpath, target)
                    else:
                        LOG.error("copy note[%s] to user[%s] failed", fpath, user_name)
                else:
                    LOG.error("write note to database failed")
            else:
                result = [self.name, self.task_key, StopSignal]
        except Exception, e:
            LOG.exception(e)
        return result

    def reduce(self, x, y):
        result = (-1, False)
        if isinstance(x, int) and isinstance(y, bool):
            result = (x + 1 if y else x, False)
        elif isinstance(x, bool) and isinstance(y, int):
            result = (y + 1 if x else y, False)
        elif isinstance(x, str) and x == StopSignal:
            result = (y, True)
        elif isinstance(y, str) and y == StopSignal:
            result = (x, True)
        return result

def construct_file_path(file_sha1_name, file_name):
    file_path = ""
    file_ext = os.path.splitext(file_name)[1]
    file_sha1_name = file_sha1_name.strip()
    if len(file_sha1_name) > 4:
        file_path = os.path.join(file_sha1_name[:2], file_sha1_name[2:4], file_sha1_name + file_ext)
    else:
        file_path = os.path.join(file_sha1_name + file_ext)
    return file_path

class RichImportProcesser(TaskProcesser):
    name = "rich"

    def __init__(self):
        self.db = DB()
        self.task_key = ""

    def iter(self, file_name, user, user_key, password):
        self.task_key = get_key(file_name, user)
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
        images_path = os.path.join(CONFIG["STORAGE_USERS_PATH"],
                                   user.sha1,
                                   "tmp",
                                   "import",
                                   "rich_notes",
                                   "images")
        # import notes
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

        key = user_key if CONFIG["ENCRYPT"] else ""

        try:
            for root, dirs, files in os.walk(images_path):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    LOG.debug("processing [%s]", fpath)
                    yield [self.name, self.task_key, fname, fpath, "image", user.user_name, "", ""]
            for root, dirs, files in os.walk(import_path):
                for fname in files:
                    if ".json" not in fname:
                        fpath = os.path.join(root, fname)
                        LOG.debug("Processing [%s]", fpath)
                        yield [self.name, self.task_key, fname, fpath, storage_path, user.user_name, key, password]
        except Exception, e:
            LOG.exception(e)
        time.sleep(10)
        yield [self.name, self.task_key, StopSignal, "", "", "", "", ""]

    def map(self, x):
        _, self.task_key, fname, fpath, storage_path, user_name, key, password = x
        result = (self.name, self.task_key, False)
        try:
            if fname != StopSignal:
                if storage_path == "image":
                    fp = open(fpath, "rb")
                    image = fp.read()
                    fp.close()
                    pic = PICTURE()
                    m = hashlib.sha1(image)
                    m.digest()
                    pic.sha1 = m.hexdigest()
                    pic.imported_at = datetime.datetime.now(dateutil.tz.tzlocal())
                    pic.file_name = common_utils.construct_safe_filename(fname.decode("utf-8"))
                    pic.file_path = construct_file_path(pic.sha1, pic.file_name).decode("utf-8")
                    image_storage_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], os.path.split(pic.file_path)[0])
                    storage_file_path = os.path.join(CONFIG["STORAGE_PICTURES_PATH"], pic.file_path)
                    if (not os.path.exists(image_storage_path)) or (not os.path.isdir(image_storage_path)):
                        os.makedirs(image_storage_path)
                    fp = open(storage_file_path, "wb")
                    fp.write(image)
                    fp.close()
                    ImageLock.acquire()
                    flag = sqlite.save_data_to_db(pic.to_dict(), self.db.pic, conn = self.db.conn_pic)
                    ImageLock.release()
                    if flag == True:
                        result = [self.name, self.task_key, True]
                        LOG.debug("write image to [%s] success", storage_file_path)
                    else:
                        LOG.debug("write image to [%s] failed", storage_file_path)
                else:
                    note = RICH()
                    note.parse_xml(fpath)
                    if password != "":
                        note.decrypt(password, decrypt_description = False)
                    note.description = common_utils.get_description_text(note.file_content, CONFIG["NOTE_DESCRIPTION_LENGTH"])
                    note.user_name = user_name
                    if note.version == "" or note.version == "0.1":
                        note_content = note.rich_content
                        note_content, images = htmlparser.get_rich_content(note_content)
                        note.images = images
                    if key != "":
                        note.encrypt(key)
                    note_dict = note.to_dict()
                    if note_dict["version"] == "":
                        # type is unicode
                        note_dict["type"] = common_utils.sha1sum(note_dict["type"])
                    RichLock.acquire()
                    flag = sqlite.save_data_to_db(note_dict, self.db.rich, mode = "INSERT", conn = self.db.conn_rich)
                    RichLock.release()
                    if flag == True:
                        LOG.debug("write rich note to database success")
                        target = ""
                        RichLock.acquire()
                        note = sqlite.get_rich_by_sha1(note_dict["sha1"], user_name, conn = self.db.conn_rich)
                        RichLock.release()
                        if note:
                            if storage_path != None:
                                target = os.path.join(storage_path, note_dict["type"], str(note.id))
                                shutil.copyfile(fpath, target)
                                result = [self.name, self.task_key, True]
                                LOG.debug("copy rich note[%s] to [%s] success", fpath, target)
                            else:
                                LOG.error("copy rich note[%s] to user[%s] failed", fpath, user_name)
                        elif note == False:
                            LOG.error("get rich note[%s] from db user[%s] failed", fpath, user_name)
                        else:
                            LOG.error("get rich note[%s] from db user[%s] failed, note not exist", fpath, user_name)
                    else:
                        LOG.error("write rich note to database failed")
            else:
                result = [self.name, self.task_key, StopSignal]
        except Exception, e:
            LOG.exception(e)
        return result

    def reduce(self, x, y):
        result = (-1, False)
        if isinstance(x, int) and isinstance(y, bool):
            result = (x + 1 if y else x, False)
        elif isinstance(x, bool) and isinstance(y, int):
            result = (y + 1 if x else y, False)
        elif isinstance(x, str) and x == StopSignal:
            result = (y, True)
        elif isinstance(y, str) and y == StopSignal:
            result = (x, True)
        return result
