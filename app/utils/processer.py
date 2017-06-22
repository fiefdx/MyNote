# -*- coding: utf-8 -*-
'''
Created on 2016-01-09
@summary: processer
@author: YangHaitao
'''

import time
import logging
import threading
from threading import Thread
from multiprocessing import Process, Queue, Pipe

import toro
from tornado import gen

from utils.tasks import get_key, NoteImportProcesser, RichImportProcesser
from models.mapping import Mapping
from models.task import StopSignal
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)

TaskQueue = Queue(CONFIG["PROCESS_NUM"] * CONFIG["THREAD_NUM"] * 2)
ResultQueue = Queue(CONFIG["PROCESS_NUM"] * CONFIG["THREAD_NUM"] * 2)
ImportRich = "IMPORT_RICH"
ImportNote = "IMPORT_NOTE"
Exit = "EXIT"
GetRate = "GET_RATE"

class StoppableThread(Thread):
    """
    Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition.
    """

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class Processer(StoppableThread):
    def __init__(self, pid, task_queue, result_queue, mapping):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.mapping = mapping
        for _, processer in self.mapping.iter():
            processer.init()

    def run(self):
        LOG = logging.getLogger("worker")
        LOG.info("Processer(%03d) start", self.pid)
        try:
            while True:
                if not self.stopped():
                    try:
                        task = self.task_queue.get()
                        if task != StopSignal:
                            job = task
                            LOG.debug("processing task: %s", task)
                            processer = self.mapping.get(job[0])
                            if processer:
                                r = processer.map(job)
                                self.result_queue.put(r)
                            else:
                                LOG.warning("processer not found for task: %s", job)
                            LOG.debug("processed task: %s", job[0])
                        else:
                            break
                    except Exception, e:
                        LOG.exception(e)
                else:
                    LOG.info("Processer(%03d) exit by signal!", self.pid)
                    break
            self.task_queue.put(StopSignal)
        except Exception, e:
            LOG.exception(e)
        LOG.info("Processer(%03d) exit", self.pid)

class Worker(Process):
    def __init__(self, wid, task_queue, result_queue, mapping):
        Process.__init__(self)
        self.wid = wid
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.mapping = mapping
        for _, processer in self.mapping.iter():
            processer.init()

    def sig_handler(self, sig, frame):
        LOG.warning("Worker(%03d) Caught signal: %s", self.wid, sig)

    def run(self):
        logger.config_logging(file_name = CONFIG["LOG_FILE_NAME"],
                              log_level = CONFIG['LOG_LEVEL'],
                              dir_name = "logs",
                              day_rotate = False,
                              when = "D",
                              interval = 1,
                              max_size = 20,
                              backup_count = 5,
                              console = True)
        logger.config_logging(logger_name = "worker",
                              file_name = ("worker_%s" % self.wid + ".log"),
                              log_level = CONFIG["LOG_LEVEL"],
                              dir_name = "logs",
                              day_rotate = False,
                              when = "D",
                              interval = 1,
                              max_size = 20,
                              backup_count = 5,
                              console = True)
        LOG = logging.getLogger("worker")
        LOG.propagate = False
        LOG.info("Worker(%03d) start", self.wid)
        try:
            threads = []
            for i in xrange(CONFIG["THREAD_NUM"]):
                t = Processer(i, self.task_queue, self.result_queue, self.mapping)
                threads.append(t)

            for t in threads:
                t.start()

            for t in threads:
                t.join()
        except Exception, e:
            LOG.exception(e)
        LOG.info("Worker(%03d) exit", self.wid)

class Dispatcher(StoppableThread):
    def __init__(self, pid, tasks, queue, task_queue, mapping):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid
        self.tasks = tasks
        self.queue = queue
        self.task_queue = task_queue
        self.mapping = mapping
        for _, processer in self.mapping.iter():
            processer.init()

    def run(self):
        LOG = logging.getLogger("manager")
        LOG.propagate = False
        LOG.info("Dispatcher start")
        try:
            while True:
                task = self.queue.get()
                command, file_name, user, user_key, password = task
                LOG.info("dispatch: %s, %s, %s", command, file_name, user.sha1)
                if command == ImportNote:
                    processer = self.mapping.get("note")
                    task_key = get_key(file_name, user)
                    for job in processer.iter(file_name, user, user_key, password):
                        self.task_queue.put(job)
                        self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= 1
                    LOG.info("dispatch notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == ImportRich:
                    processer = self.mapping.get("rich")
                    task_key = get_key(file_name, user)
                    for job in processer.iter(file_name, user, user_key, password):
                        self.task_queue.put(job)
                        self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= 1
                    LOG.info("dispatch rich notes over: %s, %s, %s", command, file_name, user.sha1)
        except Exception, e:
            LOG.exception(e)
        self.task_queue.put(StopSignal)
        LOG.info("Dispatcher exit")

class Collector(StoppableThread):
    def __init__(self, pid, tasks, result_queue, mapping):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid
        self.result_queue = result_queue
        self.mapping = mapping
        self.tasks = tasks
        for _, processer in self.mapping.iter():
            processer.init()

    def run(self):
        LOG = logging.getLogger("manager")
        LOG.info("Collector(%03d) start", self.pid)
        try:
            while True:
                if not self.stopped():
                    task = self.result_queue.get()
                    LOG.debug("collect: %s", task)
                    if task != StopSignal:
                        flag = False
                        if self.tasks.has_key(task[1]):
                            self.tasks[task[1]]["tasks"], flag = self.mapping.get(task[0]).reduce(self.tasks[task[1]]["tasks"], task[2])
                        else:
                            self.tasks[task[1]]["tasks"], flag = self.mapping.get(task[0]).reduce(0, task[2])
                        if flag and self.tasks[task[1]]["flag"] is False:
                            self.tasks[task[1]]["flag"] = True
                    else:
                        break
                else:
                    LOG.info("Collector(%03d) exit by signal!", self.pid)
                    break
        except Exception, e:
            LOG.exception(e)
        LOG.info("Collector(%03d) exit", self.pid)

class Manager(Process):
    def __init__(self, pipe_client, task_queue, result_queue, mapping):
        Process.__init__(self)
        self.pipe_client = pipe_client
        self.queue = Queue(100)
        self.tasks = {}
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.mapping = mapping
        self.stop = False

    def sig_handler(self, sig, frame):
        LOG.warning("Manager Caught signal: %s", sig)
        self.stop = True

    def run(self):
        logger.config_logging(file_name = CONFIG["LOG_FILE_NAME"],
                              log_level = CONFIG['LOG_LEVEL'],
                              dir_name = "logs",
                              day_rotate = False,
                              when = "D",
                              interval = 1,
                              max_size = 20,
                              backup_count = 5,
                              console = True)
        logger.config_logging(logger_name = "manager",
                              file_name = "manager.log",
                              log_level = CONFIG["LOG_LEVEL"],
                              dir_name = "logs",
                              day_rotate = False,
                              when = "D",
                              interval = 1,
                              max_size = 20,
                              backup_count = 5,
                              console = True)
        LOG = logging.getLogger("manager")
        LOG.propagate = False
        LOG.info("Manager start")
        try:
            threads = []
            dispatcher = Dispatcher(0, self.tasks, self.queue, self.task_queue, self.mapping)
            dispatcher.daemon = True
            threads.append(dispatcher)
            collector = Collector(0, self.tasks, self.result_queue, self.mapping)
            collector.daemon = True
            threads.append(collector)

            for t in threads:
                t.start()

            while True:
                command, file_name, user, user_key, password = self.pipe_client.recv()
                if command == ImportNote:
                    task_key = get_key(file_name, user)
                    LOG.debug("Manager import note %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == ImportRich:
                    task_key = get_key(file_name, user)
                    LOG.debug("Manager import rich %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == GetRate:
                    task_key = get_key(file_name, user)
                    LOG.debug("Manager get rate %s[%s]", user.sha1, user.user_name)
                    if self.tasks.has_key(task_key):
                        self.pipe_client.send((command, self.tasks[task_key]))
                        if self.tasks[task_key]["flag"] == True:
                            del self.tasks[task_key]
                    else:
                        self.pipe_client.send((command, None))
                elif command == Exit:
                    self.task_queue.put(StopSignal)
                    self.result_queue.put(StopSignal)
                    LOG.info("Manager exit by EXIT command!")
                    break

        except Exception, e:
            LOG.exception(e)
        self.task_queue.put(StopSignal)
        LOG.info("Manager exit")

class ManagerClient(object):
    PROCESS_LIST = []
    PROCESS_DICT = {}
    WRITE_LOCK = None
    _instance = None

    def __init__(self, process_num = 1):
        if ManagerClient._instance == None:
            self.process_num = process_num
            pipe_master, pipe_client = Pipe()
            ManagerClient.WRITE_LOCK = toro.Lock()
            mapping = Mapping()
            mapping.add(NoteImportProcesser())
            mapping.add(RichImportProcesser())
            p = Manager(pipe_client, TaskQueue, ResultQueue, mapping)
            p.daemon = True
            ManagerClient.PROCESS_LIST.append(p)
            ManagerClient.PROCESS_DICT["manager"] = [p, pipe_master]
            p.start()
            for i in xrange(process_num):
                p = Worker(i, TaskQueue, ResultQueue, mapping)
                p.daemon = True
                ManagerClient.PROCESS_LIST.append(p)
                p.start()
            ManagerClient._instance = self
        else:
            self.process_num = ManagerClient._instance.process_num

    @gen.coroutine
    def import_notes(self, file_name, user, user_key, password):
        """
        file_name: is uploaded file's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start import notes %s[%s]", file_name, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get import notes Lock %s[%s]", file_name, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((ImportNote, file_name, user, user_key, password))
            LOG.debug("Send import notes %s[%s] end", file_name, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV import notes %s[%s]", file_name, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End import notes %s[%s]", file_name, user.user_name)
        LOG.info("import notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def import_rich_notes(self, file_name, user, user_key, password):
        """
        file_name: is uploaded file's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start import rich notes %s[%s]", file_name, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get import rich notes Lock %s[%s]", file_name, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((ImportRich, file_name, user, user_key, password))
            LOG.debug("Send import rich notes %s[%s] end", file_name, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV import rich notes %s[%s]", file_name, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End import rich notes %s[%s]", file_name, user.user_name)
        LOG.info("import rich notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def get_rate_of_progress(self, file_name, user):
        """
        file_name: is uploaded file's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start get rate %s[%s]", file_name, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get rate Lock %s[%s]", file_name, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((GetRate, file_name, user, "", ""))
            LOG.debug("Send get rate %s[%s] end", file_name, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV get rate %s[%s]", file_name, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End get rate %s[%s]", file_name, user.user_name)
        LOG.info("get rate result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    def close(self):
        try:
            ManagerClient.PROCESS_DICT["manager"][1].send(("EXIT", None, None, None, None))
            for p in ManagerClient.PROCESS_LIST[1:]:
                    p.terminate()
            for p in ManagerClient.PROCESS_LIST:
                while p.is_alive():
                    time.sleep(0.5)
            LOG.info("All Processer Process Exit!")
        except Exception, e:
            LOG.exception(e)
