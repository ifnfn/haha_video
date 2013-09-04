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

cmd_test1 = {
    'name'    : 'videolist',
    'source'  : 'http://so.tv.sohu.com/list_p1100_p20_p3_p41_p5_p6_p73_p80_p9_2d0_p103_p11.html',
    'menu'    : '电影',
    'dest'    : PARSER_HOST,
    'regular' : [
        '(<a class="pic" target="_blank" title=".+/></a>)',
        '(<p class="tit tit-p">.+</a>)'
    ]
}

cmd_test2 = {
    'name'    : 'album',
    'source'  : 'http://tv.sohu.com/20120517/n343417005.shtml',
    'menu'    : '电影',
    'dest'    : PARSER_HOST,
    'regular' : [
        'var (playlistId|pid|vid|tag)\s*=\s*"(.+)";'
    ]
}

cmd_test3 = {
    'name'    : 'album_score',
    'source'  : 'http://index.tv.sohu.com/index/switch-aid/1012657',
    'menu'    : '电影',
    'dest'    : PARSER_HOST,
    'regular' : [
        '({"index":\S+?),"asudIncomes'
    ]
}

cmd_test4 = {
    'name'    : 'albumlist_hot',
    'source'  : 'http://so.tv.sohu.com/iapi?v=2&c=100&o=3',
    'menu'    : '电影',
    'dest'    : PARSER_HOST,
}

cmd_test5 = {
    'name'    : 'album_full',
    'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241',
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
        playurl = MAINSERVER_HOST + '/video/login'

        try:
            _, _, _, response = fetch(playurl)

            data = json.loads(response)

            if data:
                for cmd in data['command']:
                    self.ProcessCommand(cmd)
            return True

        except:
            t, v, tb = sys.exc_info()
            print ("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return False

def test():
    haha = KolaClient()
#    haha.ProcessCommand(cmd_test1)
#    haha.ProcessCommand(cmd_test2)
#    haha.ProcessCommand(cmd_test3)
    haha.ProcessCommand(cmd_test5)

def main():
    haha = KolaClient()
    while True:
        if haha.Login() == False:
            break
        #break

def main_thread():
    thread_pool = ThreadPool(10)
    for _ in range(10):
        thread_pool.add_job(main)
    thread_pool.shutdown()

if __name__ == "__main__":
    #test()
    main_thread()

