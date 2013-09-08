#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os

import traceback
import json
import redis
from utils.fetchTools import fetch_httplib2 as fetch
import base64
import re
from utils.ThreadPool import ThreadPool
from pymongo import Connection

#log = logging.getLogger("crawler")
MAINSERVER_HOST = 'http://127.0.0.1:9990'
#MAINSERVER_HOST = 'http://121.199.20.175:9990'
HOST = 'http://127.0.0.1:9991'
PARSER_HOST  = HOST + '/video/upload'
MAX_TRY = 3

def AddUrlMap(old_url, new_url):
    self.con = Connection('localhost', 27017)
    self.db = self.con.kola
    self.map_table = self.db.urlmap

if __name__ == "__main__":
    #test()
    main_thread()
    #main_one()
    #main()

