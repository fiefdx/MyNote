# -*- coding: utf-8 -*-
'''
Created on 2016-01-09
@summary: task
@author: YangHaitao
'''

StopSignal = "mission_complete"

class TaskProcesser(object):
    name = ""

    def __init__(self):
        pass

    def init(self):
    	pass

    def iter(self):
        yield (self.name, None)

    def map(self, x):
        return (self.name, x)

    def reduce(self, x, y, z):
        return x
