#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os
f_path = os.path.dirname(__file__)
if len(f_path) < 1: f_path = "."
sys.path.append(f_path)
sys.path.append(f_path + "/..")

from pymongo import Connection
import traceback
import json
import base64
import re
from Crypto.PublicKey import RSA
import hashlib

from fetchTools import fetch_httplib2 as fetch
from ThreadPool import ThreadPool

MAINSERVER_HOST = 'http://127.0.0.1:9990'
#MAINSERVER_HOST = 'http://121.199.20.175:9990'
HOST = 'http://127.0.0.1:9991'
#HOST = 'http://121.199.20.175'
PARSER_HOST  = HOST + '/video/upload'
MAX_TRY = 3

class R:
    def __init__(self, key):
        self.key = RSA.importKey(key)

    def Encrypt(self, text):
        return self.key.encrypt(text, len(text))

    def Decrypt(self, text):
        return self.key.decrypt(text)

class KolaMenu:
    def __init__(self, client, js):
        self.client = client
        self.filter = js['filter']
        self.cid = js['cid']
        self.name = js['name']
        self.pageSize = 20
        self.pageId = 0
        self.Show()

    def GetFilter(self, key):
        if key in self.filter:
            return self.filter[key]
        else:
            return []

    def SetFilter(self, key, value):
        self.filter[key] = value

    def SetSort(self, key):
        pass

    def SetFields(self, fields):
        pass
    def NextPage(self):
        url = '%s/video/list?page=%d&size=%d&menu=%s' % (HOST, self.pageId, self.pageSize, self.name)
        body = {
                #'filter': {},
                #'fields': {},
                #'sort': {},
                }
        print(self.client.PostUrl(url, json.dumps(body)).decode())
        self.pageId += 1

    def Show(self):
        print("Name:", self.name, "CID:", self.cid)

class KolaClient:
    def __init__(self):
        self.rsa_public_key = ''
        self.rsa = None
        self.menuList = []

    def GenKolaMenu(self):
        print (HOST + '/video/getmenu')
        res = self.GetUrl(HOST + '/video/getmenu').decode()
        try:
            js = json.loads(res)
            for x in js:
                self.menuList.append(KolaMenu(self, x))
        except:
            pass

        return self.menuList

    def GetUrl(self, url):
        status, _, _, response = fetch(url)
        #if self.rsa:
        #    response = self.rsa.Decrypt(response)
        if status != '200':
            pass
        return response

    def GetCacheUrl(self, url):
#         url = MAINSERVER_HOST + '/video/cache?url=' + urllib.quote(url)
#         return self.GetUrl(url)

        response = ''

        key = hashlib.md5(url.encode('utf8')).hexdigest().upper()
        filename = f_path + '/cache/' + key
        if os.path.exists(filename):
            f = open(filename, 'rb')
            response = f.read()
            f.close()
        else:
            _, _, _, response = fetch(url)
            f = open(filename, 'wb')
            f.write(response)
            f.close()

        return response

    def PostUrl(self, url, body):
        #if self.rsa:
        #    body = self.rsa.Encrypt(body)
        try:
            _, _, _, response = fetch(url, 'POST', body)
            return response
        except:
            return None

    def GetRealPlayer(self, url, times = 0):
        if times > MAX_TRY:
            return ''
        try:
            response = self.GetUrl(url)
            return self.PostUrl(HOST + '/video/getplayer', response)
        except:
            t, v, tb = sys.exc_info()
            print("GetSoHuRealUrl playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
            return self.GetRealPlayer(url, times + 1)

        return ''

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
            codingg = 'utf8'
            if 'regular' in cmd:
                try:
                    text = response.decode(coding)
                except:
                    coding = 'GBK'
                    text = response.decode(coding)

                response = self.RegularMatch(cmd['regular'], text)
                response = response.encode(coding)

            if response:
                base = base64.encodebytes(response)
                cmd['data'] = base.decode()
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

    def GetKey(self):
        playurl = MAINSERVER_HOST + '/key'
        try:
            _, _, _, response = fetch(playurl)
            self.rsa = R(response)

        except:
            t, v, tb = sys.exc_info()
            print("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return ''

    def Login(self):
        ret = False

        #if self.rsa == None:
        #    self.GetKey()

        playurl = MAINSERVER_HOST + '/login?user_id=000000'

        try:
            data = json.loads(self.GetUrl(playurl).decode("utf8"))

            if data:
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

def main_thread():
    thread_pool = ThreadPool(10)
    for _ in range(10):
        thread_pool.add_job(main)

def main_getmenu():
    haha = KolaClient()
    haha.GenKolaMenu()
    for menu in haha.menuList:
        menu.NextPage()
        print("==============================\n")
        menu.NextPage()
        print("==============================\n")
        menu.NextPage()

if __name__ == "__main__":
    #main_thread()
    main_one()
    #main()
    #main_getmenu()

