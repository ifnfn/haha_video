#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import traceback
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options
# from tornado import gen
# from tornado import httpclient
# from tornado.escape import json_encode

from pymongo import Connection
import redis
import json
import logging
import random
import hashlib
# import re
from basehandle import BaseHandler#, JSONPHandler
from kolatv import Kolatv


MAINSERVER_HOST = 'http://127.0.0.1:9991'


logging.basicConfig()
log = logging.getLogger("crawler")
tv = Kolatv()

def getlist(menuName, argument):
    data = {}
    m = tv.FindMenu(menuName)
    if m:
        data = m.GetAlbumList(argument)
    return data

class VideoListHandler(BaseHandler):
    def get(self):
        js = {}
        page = self.get_argument('page', 0)
        size = self.get_argument('size', 20)
        menu = self.get_argument('menu', '')

        js['result'] = getlist(menu, int(page), int(size))
        self.finish(json.dumps(js, indent=4, ensure_ascii=False))

    def post(self):
        argument = {}
        menu = self.get_argument('menu', '')

        argument['page'] = int(self.get_argument('page', 0))
        argument['size'] = int(self.get_argument('size', 20))

        if self.request.body:
            body = self.request.body.decode()
            try:
                umap = json.loads(body)
#                 argument['filter'] = {}
#                 argument['fields'] = {}
#                 argument['sort'] = {}
                argument.update(umap)
            except:
                t, v, tb = sys.exc_info()
                log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
                raise tornado.web.HTTPError(400)

        argument['result'] = getlist(menu, argument)
        self.finish(json.dumps(argument, indent=4, ensure_ascii=False))

class UrlMapHandler(BaseHandler):
    def post(self):
        body = self.request.body.decode()
        if body and len(body) > 0:
            try:
                umap = json.loads(body)
                tv.engine.command.AddUrlMap(umap['source'], umap['dest'])
            except:
                raise tornado.web.HTTPError(400)
            self.finish('OK')
        else:
            raise tornado.web.HTTPError(404)

class GetPlayerHandler(BaseHandler):
    def get(self):
        pass
    def post(self):
        body = self.request.body.decode()
        if body and len(body) > 0:
            step = self.get_argument('step', "1",)
            text = tv.GetRealPlayer(body, step)
            self.finish(text)
        else:
            raise tornado.web.HTTPError(404)

# http://xxxxx/video/getmenu?cid=1,2
# http://xxxxx/video/getmenu
# http://xxxxx/video/getmenu?name=电影,电视剧
# http://xxxxx/video/getmenu?name=
class GetMenuHandler(BaseHandler):
    def get(self):
        ret = []
        cid = self.get_argument('cid', '')
        name  = self.get_argument('name', '')
        if cid != '':
            cid = cid.split(',')
            ret = tv.GetMenuJsonInfoByCid(cid)
        elif name != '':
            name = name.split(',')
            ret =  tv.GetMenuJsonInfoByName(name)
        else:
            ret =  tv.GetMenuJsonInfoByName([])

        self.finish(json.dumps(ret, indent=4, ensure_ascii=False))

class UploadHandler(BaseHandler):
    def get(self):
        print('Upload get')
        pass

    def post(self):
        body = self.request.body.decode()
        if body and len(body) > 0:
            tv.AddTask(body)

def getRandomStr(n):
    st = ''
    while len(st) < n:
        temp = chr(97 + random.randint(0,25))
        st = st.join(['',temp])
    return st

class LoginHandler(BaseHandler):
    def check_user_id(self):
        self.user_id = ''
        self.status = 'NO'
        self.con = Connection('localhost', 27017)
        self.db = self.con.kola
        user_table = self.db.users
        db = redis.Redis(host='127.0.0.1', port=6379, db=1)

        user_id = self.get_argument('user_id')

        json = user_table.find_one({'user_id' : user_id})
        if json:
            self.user_id = json['user_id']
            self.status = json['status']
        else:
            user_table.insert({'user_id' : user_id, 'status' : 'YES'})

        if self.status == 'NO':
            raise tornado.web.HTTPError(401, "Missing key %s" % self.user_id)

        if not db.exists(self.user_id): # 如果没有登录，生成随机 KEY
            key = (self.user_id + getRandomStr(32) + self.client_ip).encode()
            key = hashlib.md5(key).hexdigest().upper()
            db.set(self.user_id, key)
            db.set(key, self.client_ip)
#            db.expire(self.user_id, 60) # 十秒过期
#            db.expire(key, 60) # 十秒过期
        else:
            key = db.get(self.user_id).decode()

        return key
    def prepare(self):
        pass

    def get(self):
        key = self.check_user_id()
        ret = {
            'key': 'None',
            'command': [],
            'server' : MAINSERVER_HOST,
            'next': 10   # 下次登录时间
        }

        ret['key'] = key
        cmd = tv.engine.command.GetCommandNext()
        if cmd:
            ret['command'].append(cmd)

        self.finish(json.dumps(ret))

    def post(self):
        self.finish('OK')

define('port', default=9991, help='run on the given port', type=int)
class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            debug = False,
            gzip = True,
            login_url = "/login",
            cookie_secret = 'z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To=',
            #xsrf_cookies = True,
            autoescape = None,
        )

        handlers = [
            (r'/video/list',              VideoListHandler),
            (r'/video/upload',            UploadHandler),          # 接受客户端上网的需要解析的网页文本
            (r'/video/getplayer',         GetPlayerHandler),       # 得到下载地位
            (r'/video/urlmap',            UrlMapHandler),          # 后台管理，增加网址映射
            (r'/video/getmenu',           GetMenuHandler),         # 后台管理，增加网址映射
            (r'/login',                   LoginHandler),           # 登录认证
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()
#    tv.UpdateAlbumList()

    tornado.options.parse_command_line()
    http_server = Application()
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
