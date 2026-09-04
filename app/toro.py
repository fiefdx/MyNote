# -*- coding: utf-8 -*-
'''
Created on 2024-01-01
@summary: Python 3 / Tornado 6 compatibility shim for the legacy "toro"
          library. The upstream ``toro`` package is Python 2 only (it relies
          on ``use_2to3`` and cannot be installed on modern Python).

This module only provides the small slice of the toro API that MyNote uses:
an async ``Lock`` whose ``acquire()`` returns a coroutine that resolves to an
async context manager, matching the original toro semantics:

    with (yield lock.acquire()):
        ...
'''

import logging

import tornado.gen
import tornado.locks

LOG = logging.getLogger(__name__)


class _LockContext(object):
    def __init__(self, lock):
        self._lock = lock

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        return False


class Lock(object):
    def __init__(self):
        self._lock = tornado.locks.Lock()

    @tornado.gen.coroutine
    def acquire(self):
        yield self._lock.acquire()
        raise tornado.gen.Return(_LockContext(self._lock))
