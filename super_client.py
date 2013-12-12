#! /usr/bin/python3
# -*- coding: utf-8 -*-

import json
import time

from engine.kolaclient import KolaClient
from kola.ThreadPool import ThreadPool


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

def GetURL(xid):
    haha = KolaClient()
    url = 'http://59.175.153.182/api/getCDNByChannelId/' + xid
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
    main()
    #main_loop()
