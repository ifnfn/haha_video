#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import json
import uuid

from pymongo import Connection
import redis
import tornado.ioloop
import tornado.options
import tornado.web

from engine import QiyiEngine, LetvEngine, SohuEngine, LiveEngine, \
    EngineCommands
from kola import BaseHandler, DB, ThreadPool


POOLSIZE = 10

class KolaEngine:
    def __init__(self):
        self.thread_pool = ThreadPool(POOLSIZE)
        self.db = DB()
        self.command = EngineCommands()
        self.engines = []
        self.UpdateAlbumFlag = False

        self.AddEngine(LetvEngine)
        self.AddEngine(SohuEngine)
        self.AddEngine(QiyiEngine)
        self.AddEngine(LiveEngine)

    def AddEngine(self, egClass):
        self.engines.append(egClass())

    def ParserHtml(self, data):
        js = tornado.escape.json_decode(data)
        if (js == None) or ('data' not in js):
            db = redis.Redis(host='127.0.0.1', port=6379, db=2) # 出错页
            db.rpush('urls', js['source'])
            print("Error:", js['source'])
            return False

        for eg in self.engines:
            if eg.ParserHtml(js):
                break

        return True

    def UpdateNewest(self): # 更新最新节目
        print("UpdateNewest")

    def UpdateAllHotList(self):
        print("UpdateAllHotList")

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")
        for eg in self.engines:
            eg.UpdateAllScore()

    # 更新所有节目
    def UpdateAllAlbumList(self):
        for eg in self.engines:
            eg.UpdateAllAlbumList()

    def CommandEmptyMessage(self):
        if self.UpdateAlbumFlag == True:
            self.UpdateAlbumFlag = False

    def AddTask(self, data):
        self.thread_pool.add_job(self.ParserHtml, [data])

tv = KolaEngine()

class UploadHandler(BaseHandler):
    def get(self):
        print('Upload get')
        pass

    def post(self):
        try:
            if type(self.request.body) == bytes:
                body = self.request.body.decode()
            else:
                body = self.request.body
            if body and len(body) > 0:
                tv.ParserHtml(body)
                #tv.AddTask(body)
        except:
            pass

class RandomVideoUrlHandle(BaseHandler):
    def get(self, name):
        self.finish(tv.db.GetVideoCache(name))

    def post(self, name):
        if name == '':
            body = self.request.body
            name = hashlib.md5(body).hexdigest().upper()
            self.db.set(name, body.decode())
            self.db.expire(name, 60) # 1 分钟有效
            self.finish(name)

class UpdateCommandHandle(BaseHandler):
    def initialize(self):
        pass

    def get(self):
        cmdlist = {}
        cmdlist['list']      = tv.UpdateAllAlbumList
        cmdlist['score']     = tv.UpdateAllScore

        command = self.get_argument('cmd', '')
        for cmd in command.split(','):
            if cmd in cmdlist:
                cmdlist[cmd]()

        self.finish('OK\n')

    def post(self):
        pass

class LoginHandler(BaseHandler):
    redis_db = redis.Redis(host='127.0.0.1', port=6379, db=1)
    def initialize(self):
        pass

    def check_user_id(self):
        self.user_id = self.get_argument('user_id')
        status = 'YES'
        con = Connection('localhost', 27017)
        user_table = con.kola.users

        json = user_table.find_one({'user_id' : self.user_id})
        if json:
            status = json['status']
        else:
            user_table.insert({'user_id' : self.user_id, 'status' : 'YES'})

        if status == 'NO' or self.user_id == None or self.user_id == '':
            raise tornado.web.HTTPError(401, 'Missing key %s' % self.user_id)

        # 登录检查，生成随机 KEY
        if not self.redis_db.exists(self.user_id):
            key = (self.user_id + uuid.uuid4().__str__() + self.request.remote_ip).encode()
            key = hashlib.md5(key).hexdigest().upper()
            self.redis_db.set(self.user_id, key)
            self.redis_db.set(key, self.request.remote_ip)
        else:
            key = self.redis_db.get(self.user_id).decode()
            self.redis_db.set(key, self.request.remote_ip)
        self.redis_db.expire(self.user_id, 60) # 一分钟过期
        self.redis_db.expire(key, 60) # 一分钟过期

        return key

    def get(self):
        ret = {
            'key'    : self.check_user_id(),
            'server' : self.request.protocol + '://' + self.request.host,
            'next'   : 60,   # 下次登录时间
        }

        cmd = self.get_argument('cmd', '1')
        if cmd == '1':
            if self.user_id == '000001':
                timeout = 0
            else:
                timeout = 0.3
            count = self.get_argument('count', 1)

            cmd = tv.command.GetCommand(timeout, count)
            if cmd:
                ret['dest'] =  self.request.protocol + '://' + self.request.host + '/video/upload'
                ret['command'] = cmd
                if self.user_id == '000001':
                    ret['next'] = 0
            else:
                tv.CommandEmptyMessage()

        self.finish(json.dumps(ret))

    def post(self):
        self.finish('OK')

class EngineApplication(tornado.web.Application):
    def __init__(self):
        settings = dict(
            debug = False,
            gzip = True,
            login_url = "/login",
            template_path = "templates",
            cookie_secret = 'z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To=',
            #xsrf_cookies = True,
            autoescape = None,
            autoreload = True
        )

        handlers = [
            (r'/video/upload',     UploadHandler),          # 接受客户端上网的需要解析的网页文本
            (r'/video/urls(.*)',   RandomVideoUrlHandle),
            (r'/login',            LoginHandler),           # 登录认证
            (r'/manage/update',    UpdateCommandHandle),
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()

    tornado.options.parse_command_line()
    EngineApplication().listen(9992, xheaders = True)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
