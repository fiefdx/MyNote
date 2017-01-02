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
    if not os.path.exists(datapath) or not os.path.isdir(datapath):
        os.makedirs(datapath)
    CONFIG["APP_PATH"] = cwd
    CONFIG["SOURCE_PATH"] = os.path.join(datapath, "source")
    if not os.path.exists(CONFIG["SOURCE_PATH"]) or not os.path.isdir(CONFIG["SOURCE_PATH"]):
        os.makedirs(CONFIG["SOURCE_PATH"])
    CONFIG["INDEX_ROOT_PATH"] = os.path.join(datapath, "index")
    if not os.path.exists(CONFIG["INDEX_ROOT_PATH"]) or not os.path.isdir(CONFIG["INDEX_ROOT_PATH"]):
        os.makedirs(CONFIG["INDEX_ROOT_PATH"])
    CONFIG["STORAGE_ROOT_PATH"] = os.path.join(datapath, "storage")
    if not os.path.exists(CONFIG["STORAGE_ROOT_PATH"]) or not os.path.isdir(CONFIG["STORAGE_ROOT_PATH"]):
        os.makedirs(CONFIG["STORAGE_ROOT_PATH"])
    CONFIG["STORAGE_STATIC_PATH"] = os.path.join(datapath, "static")
    if not os.path.exists(CONFIG["STORAGE_STATIC_PATH"]) or not os.path.isdir(CONFIG["STORAGE_STATIC_PATH"]):
        os.makedirs(CONFIG["STORAGE_STATIC_PATH"])
    CONFIG["STORAGE_USERS_PATH"] = os.path.join(datapath, "users")
    if not os.path.exists(CONFIG["STORAGE_USERS_PATH"]) or not os.path.isdir(CONFIG["STORAGE_USERS_PATH"]):
        os.makedirs(CONFIG["STORAGE_USERS_PATH"])
    CONFIG["STORAGE_PICTURES_PATH"] = os.path.join(datapath, "pictures")
    if not os.path.exists(CONFIG["STORAGE_PICTURES_PATH"]) or not os.path.isdir(CONFIG["STORAGE_PICTURES_PATH"]):
        os.makedirs(CONFIG["STORAGE_PICTURES_PATH"])
    CONFIG["STORAGE_DB_PATH"] = os.path.join(datapath, "db")
    if not os.path.exists(CONFIG["STORAGE_DB_PATH"]) or not os.path.isdir(CONFIG["STORAGE_DB_PATH"]):
        os.makedirs(CONFIG["STORAGE_DB_PATH"])
    CONFIG["PID_PATH"] = cwd
    if not CONFIG.has_key("FUNCTIONS"):
        CONFIG["FUNCTIONS"] = ["rich", "note", "help"] # ["home", "search", "note", "rich", "help"]
except Exception, e:
    print e

if __name__ == "__main__":
    print "cwd: %s"%cwd
    print "configpath: %s"%configpath
    print "CONFIG: %s"%CONFIG
