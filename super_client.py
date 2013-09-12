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
PARSER_HOST  = HOST + '/video/upload'
MAX_TRY = 3

cmd_list = [
    {
        'name'    : 'album_score',
        'source'  : 'http://index.tv.sohu.com/index/switch-aid/1012657',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            '({"index":\S+?),"asudIncomes'
        ]
    },
    {
        'name'    : 'videoall',
        'source'  : 'http://tv.sohu.com/movieall/',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album',
        'source'  : 'http://store.tv.sohu.com/view_content/movie/1008522_577560.html',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
        ]
    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2011/ajyh/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2011/ajyh/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2012/zlyeye/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/20120517/n343417005.shtml',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://store.tv.sohu.com/5009508/706684_1772.html',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album_mvinfo',
#        'source'  : 'http://search.vrs.sohu.com/mv_i4746.json', # http://tv.sohu.com/s2011/ajyh/
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_mvinfo',
#        'source'  : 'http://search.vrs.sohu.com/mv_i704321.json', # http://store.tv.sohu.com/view_content/movie/5008825_704321.html
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_mvinfo',
#        'source'  : 'http://search.vrs.sohu.com/mv_i662182.json', # http://tv.sohu.com/20120517/n343417005.shtml
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_fullinfo',
#        'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=1012657', # http://tv.sohu.com/20120517/n343417005.shtml
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_fullinfo',
#        'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=228', # http://tv.sohu.com/s2011/ajyh/
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_score',
#        'source'  : 'http://index.tv.sohu.com/index/switch-aid/1012657',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            '({"index":\S+?),"asudIncomes'
#        ]
#    },
]

cmd_test1 = {
    'name'    : 'albumlist_hot',
    'source'  : 'http://so.tv.sohu.com/iapi?v=2&c=100&o=3',
    'menu'    : '电影',
    'dest'    : PARSER_HOST,
}

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

    def NextPage(self):
        url = '%s/video/list?page=%d&size=%d&menu=%s' % (HOST, self.pageId, self.pageSize, self.name)
        body = {
                #'filter': {},
                #'fields': {},
                #'sort': {},
                }
        print(self.client.PostUrl(url, json.dumps(body)))

    def Show(self):
        print("Name:", self.name, "CID:", self.cid)

class KolaClient:
    def __init__(self):
        self.rsa_public_key = ''
        self.rsa = None
        self.menuList = []

    def GenKolaMenu(self):
        res = self.GetUrl(HOST + '/video/getmenu')
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

def test_album():
    con = Connection('localhost', 27017)
    db = con.kola
    album_table = db.album
    haha = KolaClient()
    regular = [
        'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)',
        'content="text/html; charset=(\S*?)"'
    ]

    url = [
        'http://tv.sohu.com/s2011/bjdyj/',
        'http://tv.sohu.com/s2011/1663/s322643386/',
        'http://tv.sohu.com/s2012/zlyeye/',
        'http://tv.sohu.com/s2012/zlyeye/',
        'http://store.tv.sohu.com/view_content/movie/5008825_704321.html',
        'http://tv.sohu.com/20120517/n343417005.shtml',
        'http://store.tv.sohu.com/5009508/706684_1772.html',
        'http://tv.sohu.com/20110718/n313760898.shtml',
        'http://tv.sohu.com/20110328/n304983620.shtml'
    ]
    for u in  url:
        print(u)
        x = haha.RegularMatchUrl(u, regular)
        print(x)

    return

    url = album_table.find({}, fields = {'albumPageUrl': True})
    for u in  url:
        print(u['albumPageUrl'])
        x = haha.RegularMatchUrl(u['albumPageUrl'], regular)
        print(x)

    return

def test():
    haha = KolaClient()
#    haha.GetRealPlayer('')
    for cmd in cmd_list:
        haha.ProcessCommand(cmd)
#    haha.ProcessCommand(cmd_test4)

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

if __name__ == "__main__":
    #test()
    #main_thread()
    #test_album()
    #main_one()
    main()
    #main_getmenu()

