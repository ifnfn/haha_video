#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os
import traceback
import json
import re
import time
import hashlib
import tornado.escape

from ThreadPool import ThreadPool
from kolaclient import KolaClient

def main_one():
    haha = KolaClient()
    haha.Login()

def main():
    haha = KolaClient()
    while True:
        if haha.Login() == False:
            break

def main_loop():
    haha = KolaClient()
    while True:
        while True:
            if haha.Login() == False:
                break
        time.sleep(10)
        print("Loop")

def main_thread():
    thread_pool = ThreadPool(10)
    for _ in range(10):
        thread_pool.add_job(main)


def GetURL(id):
    haha = KolaClient()
    url = 'http://59.175.153.182/api/getCDNByChannelId/' + id
    text = haha.GetCacheUrl(url)
    try:
        js = json.loads(text.decode())

        for k, v in js['streams'].items():
            url = 'http://%s/channels/%s/%s/flv:%s/live' % (v['cdnlist'][0],
                                                            js['customer_name'],
                                                            js['channel_name'],
                                                            k)

            print(url)
    except:
        #print(text.decode(), url)
        pass

if __name__ == "__main__":
    haha = KolaClient()

    ids = ['210', '211', '212', '213', '214', '215', '216', '216', '217',
           '218', '219', '232', '513', '220', '221', '222', '223', '514',
           '1181']

    for id in ids:
        GetURL(id)

    #text = haha.GetCacheUrl('http://59.175.153.182/api/getChannels')
    #js = json.loads(text.decode())
    #print(json.dumps(js, indent=4, ensure_ascii=False))
    #print(len(js['result']))


    # regular = [ '(<div id="pplist">[\s\S]*.?)<div class="ddes">' ]
    # url = 'http://www.wolidou.com/tvc/weishi/204.html'
    # text = haha.GetCacheUrl(url)
    # text = text.decode("GBK")
    # x = haha.RegularMatch(regular, text)
    # print(x)

    #regular = [ '(<li>\s*<div class="left">[\s\S]*.?</div>\s*</li>|<option value=.*html\'>)' ]
    #url = 'http://www.wolidou.com/tvz/cctv/70_1.html'
    #text = haha.GetCacheUrl(url)
    #text = text.decode("GBK")
    #x = haha.RegularMatch(regular, text)
    #print(x)

    #main_thread()
    #main_one()
    #main()
    #main_loop()
