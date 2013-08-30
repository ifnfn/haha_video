#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
reload(sys)
sys.setdefaultencoding("utf-8")
f_path = os.path.dirname(__file__)
if len(f_path) < 1: f_path = "."
sys.path.append(f_path)
sys.path.append(f_path + "/..")

from utils.dataSaver import DataSaver
from Queue import PriorityQueue
from time import sleep
from utils.mylogger import logging
import time
import threading
import traceback
import json
import random
from utils.BeautifulSoup import BeautifulSoup as bs
#import BeautifulSoup as bs
import urllib
from utils.fetchTools import fetch_httplib2 as fetch
import base64, zlib
import re
import redis
from random import randint
from urllib2 import HTTPError
from urlparse import urlparse
from xml.dom.minidom import parseString


log = logging.getLogger("crawler")

class HahaClient:
    def __init__(self):
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=4)

    def StartUpdate(self):
        self.db.flushdb()

    def EndUpdate(self):
        self.db.save()

    def Login(self):
        #playurl = 'http://121.199.20.175:9990/video/login'
        playurl = 'http://127.0.0.1:9990/video/login'

        try:
            _, _, _, response = fetch(playurl)

            data = json.loads(response)

            if data:
                for cmd in data['command']:
                    print cmd['dest']
                    _, _, _, response = fetch(cmd['source'])
                    base = base64.encodestring(response)
                    js = {}
                    js['menu'] = cmd['menu']
                    js['data'] = base
                    _, _, _, response = fetch(cmd['dest'], 'POST', \
                                              json.dumps(js, ensure_ascii = False))

                    return True

        except:
            t, v, tb = sys.exc_info()
            log.error("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return False

def main():
    haha = HahaClient()
    while True:
        if haha.Login() == False:
            break

if __name__ == "__main__":
    main()

