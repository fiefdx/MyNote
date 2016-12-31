# -*- coding: utf-8 -*-
'''
Created on 2015-03-04
@summary: multi-process encrypt & decrypt with tea
@author: YangHaitao
'''

import os
import sys
import logging
import time
import signal
import binascii
from time import localtime, strftime
from multiprocessing import Process, Pipe

import tornado
from tornado import gen
from tornado.ioloop import IOLoop
import toro

import tea
from tea import EncryptStr, DecryptStr

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

class NoteTeaProcess(Process):
    def __init__(self, process_id, pipe_client):
        Process.__init__(self)
        self.process_id = process_id
        self.pipe_client = pipe_client

    def run(self):
        date_time = strftime("%Y%m%d_%H%M%S", localtime())
        logger.config_logging(file_name = ("note_tea_%s_" % self.process_id + '.log'), 
                              log_level = CONFIG['LOG_LEVEL'], 
                              dir_name = "logs", 
                              day_rotate = False, 
                              when = "D", 
                              interval = 1, 
                              max_size = 20, 
                              backup_count = 5, 
                              console = True)
        LOG.info("Start NoteTeaProcess(%s)", self.process_id)
        try:
            while True:
                try:
                    # args is (), kwargs is {}, note is RICH or NOTE object
                    command, args, kwargs, note = self.pipe_client.recv()
                    if command == "ENCRYPT":
                        r = note.encrypt(*args, **kwargs)
                        LOG.debug("NoteTeaProcess encrypt %s[%s] to Process(%s)", note.sha1, note.user_name, self.process_id)
                        if r == True:
                            self.pipe_client.send((command, note, True))
                        else:
                            self.pipe_client.send((command, note, False))
                    elif command == "DECRYPT":
                        r = note.decrypt(*args, **kwargs)
                        LOG.debug("NoteTeaProcess decrypt %s[%s] to Process(%s)", note.sha1, note.user_name, self.process_id)
                        if r == True:
                            self.pipe_client.send((command, note, True))
                        else:
                            self.pipe_client.send((command, note, False))
                    elif command == "EXIT":
                        LOG.info("NoteTeaProcess(%s) exit by EXIT command!", self.process_id)
                        return
                except EOFError:
                    LOG.error("EOFError NoteTeaProcess(%s) Write Thread exit!", self.process_id)
                    return
                except Exception, e:
                    LOG.exception(e)
            LOG.info("Leveldb Process(%s) exit!", self.process_id)
        except KeyboardInterrupt:
            LOG.info("KeyboardInterrupt: NoteTeaProcess(%s) exit!", self.process_id)
        except Exception, e:
            LOG.exception(e)

class MultiProcessNoteTea(object):
    PROCESS_LIST = []
    PROCESS_DICT = {}
    WRITE_LOCKS = []
    READ_LOCKS = []
    _instance = None

    def __init__(self, process_num = 1):
        if MultiProcessNoteTea._instance == None:
            self.process_num = process_num
            for i in xrange(process_num):
                pipe_master, pipe_client = Pipe()
                MultiProcessNoteTea.WRITE_LOCKS.append(toro.Lock())
                p = NoteTeaProcess(i, pipe_client)
                p.daemon = True
                MultiProcessNoteTea.PROCESS_LIST.append(p)
                MultiProcessNoteTea.PROCESS_DICT[i] = [p, pipe_master]
                p.start()
            MultiProcessNoteTea._instance = self
        else:
            self.process_num = MultiProcessNoteTea._instance.process_num

    @gen.coroutine
    def encrypt(self, note, *args, **kwargs):
        result = False
        process_id = crc32sum_int(note.sha1) % self.process_num
        # acquire write lock
        LOG.debug("Start encrypt %s to Process(%s)", note.sha1, process_id)
        with (yield MultiProcessNoteTea.WRITE_LOCKS[process_id].acquire()):
            LOG.debug("Get encrypt Lock %s to Process(%s)", note.sha1, process_id)
            MultiProcessNoteTea.PROCESS_DICT[process_id][1].send(("ENCRYPT", args, kwargs, note))
            LOG.debug("Send encrypt %s to Process(%s) end", note.sha1, process_id)
            while not MultiProcessNoteTea.PROCESS_DICT[process_id][1].poll():
                yield gen.moment
            LOG.debug("RECV encrypt %s to Process(%s)", note.sha1, process_id)
            r = MultiProcessNoteTea.PROCESS_DICT[process_id][1].recv()
            LOG.debug("End encrypt %s to Process(%s)", note.sha1, process_id)
        LOG.debug("NoteTeaProcess(%s): %s", process_id, r[2])
        if r[2]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def decrypt(self, note, *args, **kwargs):
        result = False
        process_id = crc32sum_int(note.sha1) % self.process_num
        # acquire write lock
        LOG.debug("Start decrypt %s to Process(%s)", note.sha1, process_id)
        with (yield MultiProcessNoteTea.WRITE_LOCKS[process_id].acquire()):
            LOG.debug("Get decrypt Lock %s to Process(%s)", note.sha1, process_id)
            MultiProcessNoteTea.PROCESS_DICT[process_id][1].send(("DECRYPT", args, kwargs, note))
            LOG.debug("Send decrypt %s to Process(%s) end", note.sha1, process_id)
            while not MultiProcessNoteTea.PROCESS_DICT[process_id][1].poll():
                yield gen.moment
            LOG.debug("RECV decrypt %s to Process(%s)", note.sha1, process_id)
            r = MultiProcessNoteTea.PROCESS_DICT[process_id][1].recv()
            LOG.debug("End decrypt %s to Process(%s)", note.sha1, process_id)
        LOG.debug("NoteTeaProcess(%s): %s", process_id, r[2])
        if r[2]:
            result = r[1]
        raise gen.Return(result)

    def close(self):
        try:
            # for i in MultiProcessNoteTea.PROCESS_DICT.iterkeys():
            #     MultiProcessNoteTea.PROCESS_DICT[i][0].terminate()
            for i in MultiProcessNoteTea.PROCESS_DICT.iterkeys():
                MultiProcessNoteTea.PROCESS_DICT[i][1].send(("EXIT", (), {}, None))
            for i in MultiProcessNoteTea.PROCESS_DICT.iterkeys():
                while MultiProcessNoteTea.PROCESS_DICT[i][0].is_alive():
                    time.sleep(0.5)
            LOG.info("All NoteTea Process Exit!")
        except Exception, e:
            LOG.exception(e)