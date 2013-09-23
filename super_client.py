#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os
import traceback
import json
import base64, zlib
import re
import time
import hashlib
import tornado.escape

from fetchTools import fetch_httplib2 as fetch
from ThreadPool import ThreadPool

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
        status, _, _, response = fetch(url)
        if status != '200':
            print(response)
            return ""
        return response

    def GetCacheUrl(self, url):
        response = ''

        key = hashlib.md5(url.encode('utf8')).hexdigest().upper()

        filename = './cache/' + key
        if os.path.exists(filename):
            f = open(filename, 'rb')
            response = f.read()
            f.close()
        else:
            ret, _, _, response = fetch(url)
            if ret == '200':
                f = open(filename, 'wb')
                f.write(response)
                f.close()

        return response

    def PostUrl(self, url, body):
        try:
            compress = zlib.compressobj(9,
                                        zlib.DEFLATED,
                                        - zlib.MAX_WBITS,
                                        zlib.DEF_MEM_LEVEL,
                                        0)
            body = compress.compress(body.encode())
            body += compress.flush()
            body = base64.encodebytes(body).decode()

            ret, _, _, response = fetch(url, 'POST', body, cookies = "key=" + self.key)
            if ret != "200":
                print(response)
                return None
            return response
        except:
            t, v, tb = sys.exc_info()
            print("PostUrl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
            return None

    def RegularMatchUrl(self, url, regular):
        response = self.GetUrl(url)
        return self.RegularMatch([regular], response)

    def RegularMatch(self, regular, text):
        x = ''
        for r in regular:
            res = re.finditer(r, text)
            if (res):
                for i in res:
                    x += i.group(0) + '\n'
        return x

    def ProcessCommand(self, cmd, times = 0):
        ret = False
        if times > MAX_TRY:
            return False
        try:
            response = self.GetCacheUrl(cmd['source'])
            coding = 'utf8'
            if 'regular' in cmd:
                try:
                    text = response.decode(coding)
                except:
                    coding = 'GBK'
                    text = response.decode(coding)

                response = self.RegularMatch(cmd['regular'], text).encode(coding)
            if 'json' in cmd:
                data = tornado.escape.json_decode(response)

                ret = {}
                for kv in  cmd['json']:
                    if kv == "":
                        break
                    d = data
                    for v in kv.split('.'):
                        d = d[v]
                    if d:
                        ret[v] = d
                response = json.dumps(ret).encode()

            if response:
                cmd['data'] = base64.encodebytes(response).decode()
            else:
                print("[WARNING] Data is empty: ", cmd['source'])
            body = json.dumps(cmd) #, ensure_ascii = False)
            ret = self.PostUrl(cmd['dest'], body) != None
        except:
            t, v, tb = sys.exc_info()
            print("ProcessCommand playurl: %s %s, %s, %s" % (cmd['source'], t, v, traceback.format_tb(tb)))
            return self.ProcessCommand(cmd, times + 1)

        print((ret == True and "OK:" or "ERROR:"), cmd['source'],  '-->', cmd['dest'])
        return ret

    def Login(self):
        ret = False

        playurl = HOST + '/login?user_id=000001'

        try:
            data = self.GetUrl(playurl)
            if data:
                data = tornado.escape.json_decode(data)
                self.key = data['key']
                #print(self.key)
                if len(data['command']) > 0:
                    for cmd in data['command']:
                        self.ProcessCommand(cmd)
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
    #main_thread()
    #main_one()
    main_loop()
