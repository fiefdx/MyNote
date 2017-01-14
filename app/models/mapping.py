# -*- coding: utf-8 -*-
'''
Created on 2016-01-09
@summary: mapping
@author: YangHaitao
'''

class Mapping(object):
    def __init__(self):
        self.mapping = {}

    def add(self, task_processer):
        self.mapping[task_processer.name] = task_processer

    def delete(self, name):
        if self.mapping.has_key(name):
            del self.mapping[name]

    def get(self, name):
        result = None
        if self.mapping.has_key(name):
            result = self.mapping[name]
        return result

    def iter(self):
        for name in self.mapping:
            yield (name, self.mapping[name])