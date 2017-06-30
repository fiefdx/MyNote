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

from utils.tasks import get_key, get_index_key, get_export_key, get_archive_key
from utils.tasks import NoteImportProcesser, RichImportProcesser, NoteIndexProcesser, RichIndexProcesser, NoteExportProcesser, RichExportProcesser, NoteArchiveProcesser, RichArchiveProcesser
from models.mapping import Mapping
from models.task import StopSignal, StartSignal
from config import CONFIG
import logger

LOG = logging.getLogger(__name__)


TaskQueues = [Queue(CONFIG["PROCESS_NUM"] * CONFIG["THREAD_NUM"] * 2) for _ in xrange(CONFIG["PROCESS_NUM"])]
ResultQueue = Queue(CONFIG["PROCESS_NUM"] * CONFIG["THREAD_NUM"] * 2)
ImportRich = "IMPORT_RICH"
ImportNote = "IMPORT_NOTE"
IndexNote = "INDEX_NOTE"
IndexRich = "INDEX_RICH"
ExportNote = "EXPORT_NOTE"
ExportRich = "EXPORT_RICH"
ArchiveNote = "ARCHIVE_NOTE"
ArchiveRich = "ARCHIVE_RICH"
Exit = "EXIT"
GetRate = "GET_RATE"
GetIndexRate = "GET_INDEX_RATE"
GetExportRate = "GET_EXPORT_RATE"
GetArchiveRate = "GET_ARCHIVE_RATE"

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
    def __init__(self, pid, task_queue, result_queue):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.mapping = Mapping()
        self.mapping.add(NoteImportProcesser())
        self.mapping.add(RichImportProcesser())
        self.mapping.add(NoteExportProcesser())
        self.mapping.add(NoteArchiveProcesser())
        self.mapping.add(RichExportProcesser())
        self.mapping.add(RichArchiveProcesser())

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
                            LOG.debug("processing task: %s", task[:-1])
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
    def __init__(self, wid, task_queue, result_queue):
        Process.__init__(self)
        self.wid = wid
        self.task_queue = task_queue
        self.result_queue = result_queue

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
                t = Processer(i, self.task_queue, self.result_queue)
                threads.append(t)

            for t in threads:
                t.start()

            for t in threads:
                t.join()
        except Exception, e:
            LOG.exception(e)
        LOG.info("Worker(%03d) exit", self.wid)

class Dispatcher(StoppableThread):
    def __init__(self, pid, tasks, queue, task_queues):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid
        self.tasks = tasks
        self.queue = queue
        self.task_queues = task_queues
        self.mapping = Mapping()
        self.mapping.add(NoteImportProcesser())
        self.mapping.add(RichImportProcesser())
        self.mapping.add(NoteExportProcesser())
        self.mapping.add(NoteArchiveProcesser())
        self.mapping.add(RichExportProcesser())
        self.mapping.add(RichArchiveProcesser())

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
                    for n, job in enumerate(processer.iter(file_name, user, user_key, password)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == ImportRich:
                    processer = self.mapping.get("rich")
                    task_key = get_key(file_name, user)
                    for n, job in enumerate(processer.iter(file_name, user, user_key, password)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch rich notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == IndexNote:
                    processer = self.mapping.get("index_note")
                    task_key = get_index_key(file_name, user)
                    for n, job in enumerate(processer.iter(file_name, user, user_key)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch index notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == IndexRich:
                    processer = self.mapping.get("index_rich")
                    task_key = get_index_key(file_name, user)
                    for n, job in enumerate(processer.iter(file_name, user, user_key)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch index rich notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == ExportNote:
                    processer = self.mapping.get("export_note")
                    task_key = get_export_key(file_name, user)
                    for n, job in enumerate(processer.iter(file_name, user, user_key, password)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch export notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == ExportRich:
                    processer = self.mapping.get("export_rich")
                    task_key = get_export_key(file_name, user)
                    for n, job in enumerate(processer.iter(file_name, user, user_key, password)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch export rich notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == ArchiveNote:
                    processer = self.mapping.get("archive_note")
                    task_key = get_archive_key(file_name, user)
                    for n, job in enumerate(processer.iter(file_name, user, user_key, password)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch archive notes over: %s, %s, %s", command, file_name, user.sha1)
                elif command == ArchiveRich:
                    processer = self.mapping.get("archive_rich")
                    task_key = get_archive_key(file_name, user)
                    for n, job in enumerate(processer.iter(file_name, user, user_key, password)):
                        if job[2] == StartSignal:
                            self.tasks[task_key]["predict_total"] = job[3]
                        else:
                            self.task_queues[n % CONFIG["PROCESS_NUM"]].put(job)
                            self.tasks[task_key]["total"] += 1
                    self.tasks[task_key]["total"] -= CONFIG["PROCESS_NUM"]
                    LOG.info("dispatch archive rich notes over: %s, %s, %s", command, file_name, user.sha1)
        except Exception, e:
            LOG.exception(e)
        for i in xrange(CONFIG["PROCESS_NUM"]):
            self.task_queues[i].put(StopSignal)
        LOG.info("Dispatcher exit")

class Collector(StoppableThread):
    def __init__(self, pid, tasks, result_queue):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.pid = pid
        self.result_queue = result_queue
        self.mapping = Mapping()
        self.mapping.add(NoteImportProcesser())
        self.mapping.add(RichImportProcesser())
        self.mapping.add(NoteExportProcesser())
        self.mapping.add(NoteArchiveProcesser())
        self.mapping.add(RichExportProcesser())
        self.mapping.add(RichArchiveProcesser())
        self.tasks = tasks

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
                            self.tasks[task[1]]["tasks"], flag, self.tasks[task[1]]["finish"] = self.mapping.get(task[0]).reduce(self.tasks[task[1]]["tasks"], task[2], self.tasks[task[1]]["finish"])
                        else:
                            self.tasks[task[1]]["tasks"], flag, self.tasks[task[1]]["finish"] = self.mapping.get(task[0]).reduce(0, task[2], 0)
                        if len(task) >= 4 and self.tasks[task[1]].has_key("package_name"): # for archive notes processer
                            self.tasks[task[1]]["package_name"] = task[3]
                        if flag and self.tasks[task[1]]["finish"] == CONFIG["PROCESS_NUM"] and self.tasks[task[1]]["flag"] is False:
                            self.tasks[task[1]]["flag"] = True
                            self.tasks[task[1]]["predict_total"] = self.tasks[task[1]]["total"]
                    else:
                        break
                else:
                    LOG.info("Collector(%03d) exit by signal!", self.pid)
                    break
        except Exception, e:
            LOG.exception(e)
        LOG.info("Collector(%03d) exit", self.pid)

class Manager(Process):
    def __init__(self, pipe_client, task_queues, result_queue):
        Process.__init__(self)
        self.pipe_client = pipe_client
        self.queue = Queue(100)
        self.tasks = {}
        self.task_queues = task_queues
        self.result_queue = result_queue
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
            dispatcher = Dispatcher(0, self.tasks, self.queue, self.task_queues)
            dispatcher.daemon = True
            threads.append(dispatcher)
            collector = Collector(0, self.tasks, self.result_queue)
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
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == ImportRich:
                    task_key = get_key(file_name, user)
                    LOG.debug("Manager import rich %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0}
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
                elif command == IndexNote:
                    task_key = get_index_key(file_name, user)
                    LOG.debug("Manager index note %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == IndexRich:
                    task_key = get_index_key(file_name, user)
                    LOG.debug("Manager index rich %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == GetIndexRate:
                    task_key = get_index_key(file_name, user)
                    LOG.debug("Manager get index rate %s[%s]", user.sha1, user.user_name)
                    if self.tasks.has_key(task_key):
                        self.pipe_client.send((command, self.tasks[task_key]))
                        if self.tasks[task_key]["flag"] == True:
                            del self.tasks[task_key]
                    else:
                        self.pipe_client.send((command, None))
                elif command == ExportNote:
                    task_key = get_export_key(file_name, user)
                    LOG.debug("Manager export note %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == ExportRich:
                    task_key = get_export_key(file_name, user)
                    LOG.debug("Manager export rich note %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == GetExportRate:
                    task_key = get_export_key(file_name, user)
                    LOG.debug("Manager get export rate %s[%s]", user.sha1, user.user_name)
                    if self.tasks.has_key(task_key):
                        self.pipe_client.send((command, self.tasks[task_key]))
                        if self.tasks[task_key]["flag"] == True:
                            del self.tasks[task_key]
                    else:
                        self.pipe_client.send((command, None))
                elif command == ArchiveNote:
                    task_key = get_archive_key(file_name, user)
                    LOG.debug("Manager archive note %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0, "package_name": ""}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == ArchiveRich:
                    task_key = get_archive_key(file_name, user)
                    LOG.debug("Manager archive rich note %s[%s]", user.sha1, user.user_name)
                    if not self.tasks.has_key(task_key):
                        self.tasks[task_key] = {"total": 0, "tasks": 0, "flag": False, "finish": 0, "predict_total": 0, "package_name": ""}
                    self.queue.put((command, file_name, user, user_key, password))
                    self.pipe_client.send((command, self.tasks[task_key]))
                elif command == GetArchiveRate:
                    task_key = get_archive_key(file_name, user)
                    LOG.debug("Manager get archive rate %s[%s]", user.sha1, user.user_name)
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
            p = Manager(pipe_client, TaskQueues, ResultQueue)
            p.daemon = True
            ManagerClient.PROCESS_LIST.append(p)
            ManagerClient.PROCESS_DICT["manager"] = [p, pipe_master]
            p.start()
            for i in xrange(process_num):
                p = Worker(i, TaskQueues[i], ResultQueue)
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

    @gen.coroutine
    def index_notes(self, file_name, user, user_key):
        """
        file_name: is uploaded file's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start index notes %s[%s]", file_name, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get index notes Lock %s[%s]", file_name, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((IndexNote, file_name, user, user_key, ""))
            LOG.debug("Send index notes %s[%s] end", file_name, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV index notes %s[%s]", file_name, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End index notes %s[%s]", file_name, user.user_name)
        LOG.info("index notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def index_rich_notes(self, file_name, user, user_key):
        """
        file_name: is uploaded file's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start index rich notes %s[%s]", file_name, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get index rich notes Lock %s[%s]", file_name, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((IndexRich, file_name, user, user_key, ""))
            LOG.debug("Send index rich notes %s[%s] end", file_name, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV index rich notes %s[%s]", file_name, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End index rich notes %s[%s]", file_name, user.user_name)
        LOG.info("index rich notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def get_index_rate_of_progress(self, file_name, user):
        """
        file_name: is uploaded file's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start get index rate %s[%s]", file_name, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get index rate Lock %s[%s]", file_name, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((GetIndexRate, file_name, user, "", ""))
            LOG.debug("Send get index rate %s[%s] end", file_name, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV get index rate %s[%s]", file_name, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End get index rate %s[%s]", file_name, user.user_name)
        LOG.info("get index rate result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def export_notes(self, note_category, user, user_key, password):
        """
        note_category: is a note category's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start export notes %s[%s]", note_category, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get export notes Lock %s[%s]", note_category, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((ExportNote, note_category, user, user_key, password))
            LOG.debug("Send export notes %s[%s] end", note_category, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV export notes %s[%s]", note_category, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End export notes %s[%s]", note_category, user.user_name)
        LOG.info("export notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def export_rich_notes(self, note_category, user, user_key, password):
        """
        note_category: is a note category's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start export rich notes %s[%s]", note_category, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get export rich notes Lock %s[%s]", note_category, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((ExportRich, note_category, user, user_key, password))
            LOG.debug("Send export rich notes %s[%s] end", note_category, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV export rich notes %s[%s]", note_category, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End export rich notes %s[%s]", note_category, user.user_name)
        LOG.info("export rich notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)


    @gen.coroutine
    def get_export_rate_of_progress(self, note_category, user):
        """
        note_category: is a note category's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start get export rate %s[%s]", note_category, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get export rate Lock %s[%s]", note_category, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((GetExportRate, note_category, user, "", ""))
            LOG.debug("Send get export rate %s[%s] end", note_category, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV get export rate %s[%s]", note_category, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End get export rate %s[%s]", note_category, user.user_name)
        LOG.info("get export rate result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def archive_notes(self, note_category, user, user_key, password):
        """
        note_category: is a note category's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start archive notes %s[%s]", note_category, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get archive notes Lock %s[%s]", note_category, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((ArchiveNote, note_category, user, user_key, password))
            LOG.debug("Send archive notes %s[%s] end", note_category, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV archive notes %s[%s]", note_category, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End archive notes %s[%s]", note_category, user.user_name)
        LOG.info("archive notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def archive_rich_notes(self, note_category, user, user_key, password):
        """
        note_category: is a note category's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start archive rich notes %s[%s]", note_category, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get archive rich notes Lock %s[%s]", note_category, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((ArchiveRich, note_category, user, user_key, password))
            LOG.debug("Send archive rich notes %s[%s] end", note_category, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV archive rich notes %s[%s]", note_category, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End archive rich notes %s[%s]", note_category, user.user_name)
        LOG.info("archive rich notes result: %s", r[1])
        if r[1]:
            result = r[1]
        raise gen.Return(result)

    @gen.coroutine
    def get_archive_rate_of_progress(self, note_category, user):
        """
        note_category: is a note category's name
        user: is user object from models.item.USER
        """
        result = False
        # acquire write lock
        LOG.debug("Start get archive rate %s[%s]", note_category, user.user_name)
        with (yield ManagerClient.WRITE_LOCK.acquire()):
            LOG.debug("Get archive rate Lock %s[%s]", note_category, user.user_name)
            ManagerClient.PROCESS_DICT["manager"][1].send((GetArchiveRate, note_category, user, "", ""))
            LOG.debug("Send get archive rate %s[%s] end", note_category, user.user_name)
            while not ManagerClient.PROCESS_DICT["manager"][1].poll():
                yield gen.moment
            LOG.debug("RECV get archive rate %s[%s]", note_category, user.user_name)
            r = ManagerClient.PROCESS_DICT["manager"][1].recv()
            LOG.debug("End get archive rate %s[%s]", note_category, user.user_name)
        LOG.info("get archive rate result: %s", r[1])
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
