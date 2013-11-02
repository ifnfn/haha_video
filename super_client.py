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
import utils

HOST = 'http://127.0.0.1:9991'
#HOST = 'http://192.168.188.135:9991'
#HOST = 'http://121.199.20.175'
#HOST = 'http://www.kolatv.com'

MAX_TRY = 3

class KolaClient:
    def __init__(self):
        self.menuList = []
        self.key = ''

    def GetUrl(self, url):
        return utils.GetUrl(url)

    def GetCacheUrl(self, url):
        response = ''

        key = hashlib.md5(url.encode('utf8')).hexdigest().upper()

        filename = './cache/' + key
        if os.path.exists(filename):
            f = open(filename, 'rb')
            response = f.read()
            f.close()
        else:
            print("Download: ", url)
            response = self.GetUrl(url)
            if response:
                f = open(filename, 'wb')
                f.write(response)
                f.close()

        return response

    def PostUrl(self, url, body):
        return utils.PostUrl(url, body, self.key)

    def RegularMatchUrl(self, url, regular):
        response = self.GetCacheUrl(url)
        return self.RegularMatch([regular], response)

    def RegularMatch(self, regular, text):
        x = ''
        for r in regular:
            res = re.finditer(r, text)
            if (res):
                for i in res:
                    if type(i.group(1)) == bytes:
                        x += i.group(1).decode("GB18030") + '\n'
                    else:
                        x += i.group(1) + '\n'
        return x

    def ProcessCommand(self, cmd, dest, times = 0):
        ret = False
        if times > MAX_TRY or type(cmd) != dict:
            return False
        try:
            cached = False
            if 'cache' in cmd:
                cached = cmd['cache']
            if ('name' in cmd and cmd['name'] == 'videolist') or (cached == False):
                response = self.GetUrl(cmd['source'])
            else:
                response = self.GetCacheUrl(cmd['source'])

            coding = 'utf8'
            try:
                if type(response) == bytes:
                    response = response.decode(coding)
            except:
                coding = 'GB18030'
                if type(response) == bytes:
                    response = response.decode(coding)

            if 'regular' in cmd:
                response = self.RegularMatch(cmd['regular'], response).encode(coding)

            if 'json' in cmd:
                data = tornado.escape.json_decode(response)

                ret = {}
                for kv in  cmd['json']:
                    if kv == '':
                        break
                    d = data
                    for v in kv.split('.'):
                        if v in d: d = d[v]
                        else: d = None
                        if d == None:
                            break
                    if d:
                        ret[v] = d
                response = json.dumps(ret).encode()

            if response:
                if type(response) == bytes:
                    response = response.decode(coding)
                cmd['data'] = response
            else:
                print("[WARNING] Data is empty: ", cmd['source'])

            body = json.dumps(cmd) #, ensure_ascii = False)
            ret = self.PostUrl(dest, body) != None
        except:
            t, v, tb = sys.exc_info()
            print("ProcessCommand playurl: %s %s, %s, %s" % (cmd['source'], t, v, traceback.format_tb(tb)))
            return self.ProcessCommand(cmd, dest, times + 1)

        print((ret == True and "OK:" or "ERROR:"), cmd['source'],  '-->', dest)
        return ret

    def Login(self):
        ret = False

        playurl = HOST + '/login?user_id=000001'

        try:
            data = self.GetUrl(playurl)
            if data:
                data = tornado.escape.json_decode(data)
                self.key = data['key']
                if 'command' in data:
                    dest = data['dest']
                    for cmd in data['command']:
                        self.ProcessCommand(cmd, dest)
                    ret = True
        except:
            t, v, tb = sys.exc_info()
            print("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return ret

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

if __name__ == "__main__":
    haha = KolaClient()
    #a = haha.RegularMatchUrl('http://www.letvlive.com',
    #                         '(<a href="tv.php.*</a>)'.encode())
    #                         '<h1 class="lm_1">(.*)</h1>'.encode())
    #print(a)

    #a = haha.RegularMatchUrl("http://search.vrs.sohu.com/mv_i1268037.json",
    #                         '("playlistId":\w+)'.encode())
    #print(a)
    #a = haha.RegularMatchUrl('http://so.tv.sohu.com/list_p1100_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html',
    #                         '<p class="tit tit-p"><a target="_blank"\s*(.+)>.*</a>'.encode())
    #                         #'var video_album_videos_result=(\{.*.\})'.encode())
    #print(a)
    #main_thread()
    #main_one()
    main()
    #main_loop()
