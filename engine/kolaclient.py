#! /usr/bin/python3
# -*- coding: utf-8 -*-

import json
import re
import sys
import traceback

import tornado.escape

from kola import GetUrl, GetCacheUrl, PostUrl


HOST = 'http://127.0.0.1:9992'
#HOST = 'http://192.168.188.135:9991'
#HOST = 'http://121.199.20.175'
#HOST = 'http://www.kolatv.com'

MAX_TRY = 3

class KolaClient:
    def __init__(self, Debug=False):
        self.menuList = []
        self.key = ''
        self.Debug = Debug

    def GetUrl(self, url, cached=False):
        if cached:
            return GetCacheUrl(url)
        else:
            return GetUrl(url)

    def PostUrl(self, url, body):
        return PostUrl(url, body, self.key)

    def RegularMatchUrl(self, url, regular):
        response,_,_ = self.GetUrl(url, True)
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
        cached = True
        cache_file = ''
        found = False

        if times > MAX_TRY or type(cmd) != dict:
            return False
        try:
            if 'text' in cmd:
                response = cmd['text']
            else:
                if 'source' in cmd:
                    if 'cache' in cmd:
                        cached = cmd['cache'] or self.Debug
                        response, cache_file, found = self.GetUrl(cmd['source'], cached)

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
                print("[WARNING] Data is empty", cmd['source'])

            body = json.dumps(cmd) #, ensure_ascii = False)
            ret = self.PostUrl(dest, body) != None
        except:
            print(data)
            t, v, tb = sys.exc_info()
            print("ProcessCommand playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
            return self.ProcessCommand(cmd, dest, times + 1)

        if 'source' in cmd:
            print((ret == True and "OK:" or "ERROR:"), (found and "[IN CACHE]" or ''), cache_file, cmd['source'])

        return ret

    def Login(self):
        ret = False

        playurl = HOST + '/login?user_id=000001'

        try:
            data, _,_ = self.GetUrl(playurl, False)
            if data:
                data = tornado.escape.json_decode(data)
                self.key = data['key']
                if 'command' in data:
                    dest = data['dest']
                    for cmd in data['command']:
                        self.ProcessCommand(cmd, dest)
                    ret = True
            else:
                ret = True
        except:
            t, v, tb = sys.exc_info()
            print("KolaClient:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return ret

