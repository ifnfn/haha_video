#! env /usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
reload(sys)
f_path = os.path.dirname(__file__)
if len(f_path) < 1: f_path = "."
sys.path.append(f_path)
sys.path.append(f_path + "/..")

import traceback
import json
from utils.fetchTools import fetch_httplib2 as fetch
import base64
import re
import redis
from utils.ThreadPool import ThreadPool

#log = logging.getLogger("crawler")
MAINSERVER_HOST = 'http://127.0.0.1:9990'
#MAINSERVER_HOST = 'http://121.199.20.175:9990'
PARSER_HOST  = 'http://127.0.0.1:9991/video/upload'

cmd_list = [
    {
        'name'    : 'videoall',
        'source'  : 'http://tv.sohu.com/movieall',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album',
        'source'  : 'http://tv.sohu.com/s2011/ajyh/',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\s*"(.+?)";'
        ]
    },
    {
        'name'    : 'album',
        'source'  : 'http://tv.sohu.com/s2012/zlyeye/',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\s*"(.+?)";'
        ]
    },
    {
        'name'    : 'album',
        'source'  : 'http://store.tv.sohu.com/view_content/movie/5008825_704321.html',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\s*"(.+?)";'
        ]
    },
    {
        'name'    : 'album',
        'source'  : 'http://tv.sohu.com/20120517/n343417005.shtml',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\s*"(.+?)";'
        ]
    },
    {
        'name'    : 'album_mvinfo',
        'source'  : 'http://search.vrs.sohu.com/mv_i4746.json', # http://tv.sohu.com/s2011/ajyh/
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album_mvinfo',
        'source'  : 'http://search.vrs.sohu.com/mv_i704321.json', # http://store.tv.sohu.com/view_content/movie/5008825_704321.html
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album_mvinfo',
        'source'  : 'http://search.vrs.sohu.com/mv_i662182.json', # http://tv.sohu.com/20120517/n343417005.shtml
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album_full',
        'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=1012657', # http://tv.sohu.com/20120517/n343417005.shtml
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album_full',
        'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=228', # http://tv.sohu.com/s2011/ajyh/
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album_score',
        'source'  : 'http://index.tv.sohu.com/index/switch-aid/1012657',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            '({"index":\S+?),"asudIncomes'
        ]
    },
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

    def ProcessCommand(self, cmd):
        try:
            _, _, _, response = fetch(cmd['source'])
            if cmd.has_key('regular'):
                x = ""
                for regular in cmd['regular']:
                    res = re.findall(regular, response)
                    if (res):
                        for i in res:
                            x += str(i)
                response = x

            if response:
                base = base64.encodestring(str(response))
                cmd['data'] = base
                body = json.dumps(cmd) #, ensure_ascii = False)
                print "OK: ", cmd['source']
                _, _, _, response = fetch(cmd['dest'], 'POST', body)

                return True
        except:
            t, v, tb = sys.exc_info()
            print ("GetSoHuRealUrl playurl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))

        print "ERROR: ", cmd['source']
        return False

    def Login(self):
        ret = False
        playurl = MAINSERVER_HOST + '/video/login'

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

def test():
    haha = KolaClient()
    for cmd in cmd_list:
        haha.ProcessCommand(cmd)
#    haha.ProcessCommand(cmd_test4)

def main():
    haha = KolaClient()
    while True:
        if haha.Login() == False:
            print "exit"
            break
        #break

def main_thread():
    thread_pool = ThreadPool(10)
    for _ in range(10):
        thread_pool.add_job(main)

if __name__ == "__main__":
    test()
    #main_thread()

