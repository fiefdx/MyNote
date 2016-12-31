# -*- coding: utf-8 -*-
'''
Created on 2013-10-26 21:29
@summary:  import yaml configuration
@author: YangHaitao

Modified on 2014-10-25
@summary: simplify the configuration.yml
@author: YangHaitao
''' 
try:
    import yaml
except ImportError:
    raise ImportError("Config module requires pyYAML package, please check if pyYAML is installed!")

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import os
#
# default config
cwd = '.'
configpath = os.path.join(cwd, "configuration.yml")

def update(**kwargs):
    config = load(stream = file(configpath), Loader = Loader)
    for k in kwargs:
        if k in config:
            config[k] = kwargs[k]
    fp = open(configpath, "wb")
    dump(config, fp, default_flow_style = False)
    fp.close()

CONFIG = {}
try:
    # script in the app dir
    # cwd = os.path.split(os.path.realpath(__file__))[0]
    localConf = load(stream = file(configpath), Loader = Loader)
    CONFIG.update(localConf)
    if CONFIG["USB_MODE"] == True:
        datapath = os.path.join("../..", "MyNoteData")
    else:
        datapath = CONFIG["DATA_PATH"]
    CONFIG["APP_PATH"] = cwd
    CONFIG["SOURCE_PATH"] = os.path.join(datapath, "source")
    CONFIG["INDEX_ROOT_PATH"] = os.path.join(datapath, "index")
    CONFIG["STORAGE_ROOT_PATH"] = os.path.join(datapath, "storage")
    CONFIG["STORAGE_STATIC_PATH"] = os.path.join(datapath, "static")
    CONFIG["STORAGE_USERS_PATH"] = os.path.join(datapath, "users")
    CONFIG["STORAGE_PICTURES_PATH"] = os.path.join(datapath, "pictures")
    CONFIG["STORAGE_DB_PATH"] = os.path.join(datapath, "db")
    CONFIG["PID_PATH"] = cwd
    CONFIG["SCRIPTS_PATH"] = os.path.join(cwd, "scripts")
except Exception, e:
    print e

if __name__ == "__main__":
    print "cwd: %s"%cwd
    print "configpath: %s"%configpath
    print "CONFIG: %s"%CONFIG



