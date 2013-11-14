#!/usr/bin/python3
# -*- coding: utf-8 -*-


import sys, os
import traceback
import json
import re
import time
import hashlib
import tornado.escape
from urllib.parse import unquote

from ThreadPool import ThreadPool
import utils
from kolaclient import KolaClient


def GetURL():
    haha = KolaClient()
    url = 'http://api.cztv.com/api/getCDNByChannelId/%d?domain=api.cztv.com'

    for i in range(100, 199):
        u = url % i
        text = haha.GetCacheUrl(u)
        js = json.loads(text.decode())

        datarates = js['result']['datarates']
        if datarates != None:
            k, v = list(datarates.items())[0]
            timestamp = int(float(js['result']['timestamp']) / 1000) * 1000
            u = 'http://%s/channels/%d/%s.flv/live?%d' % (v[0], i, k, timestamp)
            print(u)


if __name__ == "__main__":
    GetURL()
