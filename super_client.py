#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
reload(sys)
f_path = os.path.dirname(__file__)
if len(f_path) < 1: f_path = "."
sys.path.append(f_path)
sys.path.append(f_path + "/..")

from pymongo import Connection
import traceback
import json
from utils.fetchTools import fetch_httplib2 as fetch
import base64
import re
from utils.ThreadPool import ThreadPool

#log = logging.getLogger("crawler")
MAINSERVER_HOST = 'http://127.0.0.1:9990'
#MAINSERVER_HOST = 'http://121.199.20.175:9990'
HOST = 'http://127.0.0.1:9991'
PARSER_HOST  = HOST + '/video/upload'
MAX_TRY = 3

cmd_list = [
#    {
#        'name'    : 'videoall',
#        'source'  : 'http://tv.sohu.com/movieall/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2011/ajyh/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2012/zlyeye/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://store.tv.sohu.com/view_content/movie/5008825_704321.html',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
    {
        'name'    : 'album',
        'source'  : 'http://tv.sohu.com/s2011/nrb/',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'
        ]
    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/20120517/n343417005.shtml',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://store.tv.sohu.com/5009508/706684_1772.html',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'
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

class KolaClient:
    def __init__(self):
        pass

    def PostUrl(self, url, body):
        _, _, _, response = fetch(url, 'POST', body)
        return response

    def GetRealPlayer(self, url, times = 0):
        if times > MAX_TRY:
            return ''
        try:
            _, _, _, response = fetch(url)
            return self.PostUrl(HOST + '/video/getplayer', response)
        except:
            t, v, tb = sys.exc_info()
            print ("GetSoHuRealUrl playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
            return self.GetRealPlayer(url, times + 1)

        return ''

    def RegularMatchUrl(self, url, regular):
        _, _, _, response = fetch(url)
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
        if times > MAX_TRY:
            return False
        try:
            _, _, _, response = fetch(cmd['source'])
            if cmd.has_key('regular'):
                response = self.RegularMatch(cmd['regular'], response)

            if response != '':
                base = base64.encodestring(str(response))
                cmd['data'] = base
                print "OK: ", cmd['source'], "--->", cmd['dest']
            else:
                print "ERROR: Data is empty: ", cmd['source']
            body = json.dumps(cmd) #, ensure_ascii = False)
            self.PostUrl(cmd['dest'], body)

            return True
        except:
            t, v, tb = sys.exc_info()
            print ("ProcessCommand playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
            return self.ProcessCommand(cmd, times + 1)

        print "ERROR: ", cmd['source']
        return False

    def Login(self):
        ret = False
        playurl = MAINSERVER_HOST + '/video/login?user_id=000000'

        try:
            _, _, _, response = fetch(playurl)

            data = json.loads(response)

            if data:
                if len(data['command']) > 0:
                    for cmd in data['command']:
                        self.ProcessCommand(cmd)
                    ret = True
        except:
            t, v, tb = sys.exc_info()
            print ("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return ret

def test_album():
    con = Connection('localhost', 27017)
    db = con.kola
    album_table = db.album
    haha = KolaClient()
    regular = 'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)'

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
        print u
        x = haha.RegularMatchUrl(u, regular)
        print x
        print "======================="
        print re.findall(regular, x)
        print "\n"

    return

    url = album_table.find({}, fields = {'albumPageUrl': True})
    for u in  url:
        print u['albumPageUrl']
        x = haha.RegularMatchUrl(u['albumPageUrl'], regular)
        print x

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

if __name__ == "__main__":
    #test()
    #main_thread()
    test_album()
    #main_one()
    #main()

