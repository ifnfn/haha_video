#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import traceback
import tornado.ioloop
import tornado.web
import tornado.options
import redis
import json
import logging
import uuid
import hashlib

from tornado.options import define, options
from pymongo import Connection
from basehandle import BaseHandler
from kolatv import Kolatv

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
        argument = {}
        argument['page'] = int(self.get_argument('page', 0))
        argument['size'] = int(self.get_argument('size', 20))
        menu = self.get_argument('menu', '')

        argument['result'] = getlist(menu, argument)
        self.finish(json.dumps(argument, indent=4, ensure_ascii=False))

    def post(self):
        argument = {}
        menu = self.get_argument('menu', '')

        argument['page'] = int(self.get_argument('page', 0))
        argument['size'] = int(self.get_argument('size', 20))

        if self.request.body:
            try:
                umap = tornado.escape.json_decode(self.request.body)
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
        try:
            umap = tornado.escape.json_decode(self.request.body)
            if umap:
                tv.engine.command.AddUrlMap(umap['source'], umap['dest'])
        except:
            raise tornado.web.HTTPError(400)
        self.finish('OK')

class GetPlayerHandler(BaseHandler):
    def get(self):
        pass
    def post(self):
        body = self.request.body.decode()
        if body and len(body) > 0:
            step = self.get_argument('step', "1",)
            definition = self.get_argument('hd', '0')
            text = tv.engine.GetRealPlayer(body, definition, step)
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
            ret = tv.GetMenuJsonInfoById(cid)
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
            tv.ParserHtml(body)
            #tv.AddTask(body)

class UpdateCommandHandle(BaseHandler):
    def initialize(self):
        pass

    def get(self):
        command = self.get_argument('user_id', '')
        if command == 'score':
            tv.UpdateAllScore()
        elif command == 'fullinfo':
            tv.UpdateAllFullInfo()
        elif command == 'playinfo':
            tv.UpdateAllPlayInfo()
        elif command == 'all':
            tv.UpdateAllAlbumList()

        self.finish('OK')

    def post(self):
        pass

class LoginHandler(BaseHandler):
    def initialize(self):
        pass

    def check_user_id(self):
        user_id = self.get_argument('user_id')
        status = 'YES'
        con = Connection('localhost', 27017)
        user_table = con.kola.users

        json = user_table.find_one({'user_id' : user_id})
        if json:
            status = json['status']
        else:
            user_table.insert({'user_id' : user_id, 'status' : 'YES'})

        if status == 'NO' or user_id == None or user_id == '':
            raise tornado.web.HTTPError(401, 'Missing key %s' % user_id)

        # 登录检查，生成随机 KEY
        redis_db = redis.Redis(host='127.0.0.1', port=6379, db=1)
        if not redis_db.exists(user_id):
            key = (user_id + uuid.uuid4().__str__() + self.request.remote_ip).encode()
            key = hashlib.md5(key).hexdigest().upper()
            redis_db.set(user_id, key)
            redis_db.set(key, self.request.remote_ip)
        else:
            key = redis_db.get(user_id).decode()
        #redis_db.expire(user_id, 60) # 一分钟过期
        #redis_db.expire(key, 60) # 一分钟过期

        return key

    def get(self):
        ret = {
            'key': self.check_user_id(),
            'command': [],
            'server' : self.request.protocol + '://' + self.request.host,
            'next': 30   # 下次登录时间
        }

        cmd = tv.engine.command.GetCommandNext()
        if cmd:
            cmd['dest'] =  self.request.protocol + '://' + self.request.host + '/video/upload'
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
            autoreload = True
        )

        handlers = [
            (r'/video/list',              VideoListHandler),
            (r'/video/upload',            UploadHandler),          # 接受客户端上网的需要解析的网页文本
            (r'/video/getplayer',         GetPlayerHandler),       # 得到下载地位
            (r'/video/urlmap',            UrlMapHandler),          # 后台管理，增加网址映射
            (r'/video/getmenu',           GetMenuHandler),         # 后台管理，增加网址映射
            (r'/login',                   LoginHandler),           # 登录认证
            (r'/manage/update',           UpdateCommandHandle)
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()

    tornado.options.parse_command_line()
    http_server = Application()
    http_server.listen(options.port, xheaders = True)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
