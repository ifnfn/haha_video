#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os
import traceback
import json
import re
import hashlib
import tornado.escape
import kola

HOST = 'http://127.0.0.1:9992'
#HOST = 'http://192.168.188.135:9991'
#HOST = 'http://121.199.20.175'
#HOST = 'http://www.kolatv.com'

MAX_TRY = 3

class KolaClient:
    def __init__(self):
        self.menuList = []
        self.key = ''

    def GetUrl(self, url):
        print("Download: ", url)
        return kola.utils.GetUrl(url)

    def GetCacheUrl(self, url):
        response = ''

        key = hashlib.md5(url.encode('utf8')).hexdigest().upper()

        filename = './cache/' + key
        if os.path.exists(filename):
            f = open(filename, 'rb')
            response = f.read()
            f.close()
        else:
            response = self.GetUrl(url)
            if response:
                try:
                    f = open(filename, 'wb')
                    f.write(response)
                    f.close()
                except:
                    pass

        return response

    def PostUrl(self, url, body):
        return kola.utils.PostUrl(url, body, self.key)

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
                text = x
        if x:
            x = x[0:len(x)-1]
        return x

    def ProcessCommand(self, cmd, dest, times = 0):
        ret = False
        if times > MAX_TRY or type(cmd) != dict:
            return False
        try:
            if 'text' in cmd:
                response = cmd['text']
            else:
                cached = False
                if 'cache' in cmd and 'source' in cmd:
                    cached = cmd['cache']
                    if cached:
                        response = self.GetCacheUrl(cmd['source'])
                    else:
                        response = self.GetUrl(cmd['source'])

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
                print("[WARNING] Data is empty")

            body = json.dumps(cmd) #, ensure_ascii = False)
            ret = self.PostUrl(dest, body) != None
        except:
            t, v, tb = sys.exc_info()
            print("ProcessCommand playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
            return self.ProcessCommand(cmd, dest, times + 1)

        if 'source' in cmd:
            print((ret == True and "OK:" or "ERROR:"), cmd['source'],  '-->', dest)
        else:
            print((ret == True and "OK:" or "ERROR:"), '-->', dest)

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

