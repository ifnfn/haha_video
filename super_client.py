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

#log = logging.getLogger("crawler")
MAINSERVER_HOST = 'http://127.0.0.1:9990'
#MAINSERVER_HOST = 'http://121.199.20.175:9990'

class HahaClient:
    def __init__(self):
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=4)

    def StartUpdate(self):
        self.db.flushdb()

    def EndUpdate(self):
        self.db.save()

    def Login(self):
        playurl = MAINSERVER_HOST + '/video/login'

        try:
            _, _, _, response = fetch(playurl)

            data = json.loads(response)

            if data:
                for cmd in data['command']:
                    print cmd['dest']
#                    cmd['source'] = 'http://index.tv.sohu.com/index/switch-aid/5161139'
#                    cmd['name'] = 'programme_score'
#                    del cmd['regular']
                    _, _, _, response = fetch(cmd['source'])
                    if cmd.has_key('regular'):
                        x = []
                        for regular in cmd['regular']:
                            res = re.findall(regular, response)
                            if (res):
                                x.extend(res)
                        response = str(x)

                    if response:
                        base = base64.encodestring(str(response))
                        cmd['data'] = base
                        body = json.dumps(cmd) #, ensure_ascii = False)
                        print cmd['source']
                        _, _, _, response = fetch(cmd['dest'], 'POST', body)

                    return True

        except:
            t, v, tb = sys.exc_info()
            print ("GetSoHuRealUrl playurl:  %s, %s,%s,%s" % (playurl, t, v, traceback.format_tb(tb)))

        return False

def main():
    haha = HahaClient()
    while True:
        if haha.Login() == False:
            break
        break

if __name__ == "__main__":
    main()

