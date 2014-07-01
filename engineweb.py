#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import uuid

from pymongo import Connection
import redis
import tornado.ioloop
import tornado.options
import tornado.web

import engine
from kola import BaseHandler


tv = engine.KolaEngine()

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

class UpdateCommandHandle(BaseHandler):
    def initialize(self):
        pass

    def get(self):
        engine = self.get_argument('engine')
        if engine:
            engine = engine.split(',')

        command = self.get_argument('cmd', '')
        for cmd in command.split(','):
            if cmd == 'list':
                tv.UpdateAllAlbumList(engine)
            elif cmd == 'score':
                tv.UpdateAllScore(engine)

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

        self.finish(tornado.escape.json_encode(ret))

    def post(self):
        self.finish('OK')

class UploadFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('loadtv.html')

    def post(self):
        ret = {}

        try:
            upload_path=os.path.join(os.path.dirname(__file__), 'files')  #文件的暂存路径

            file_metas=self.request.files['myfile']    #提取表单中‘name’为‘file’的文件元数据
            ret['files'] = []
            for meta in file_metas:
                filepath=os.path.join(upload_path,'tv.json')
                with open(filepath,'wb') as up:      #有些文件需要已二进制的形式存储，实际中可以更改
                    up.write(meta['body'])
                tv.UpdateAllAlbumList('Livetv2Engine')
                self.finish('OK')
                break
        except:
            self.finish('Error!')
            pass

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
            #autoreload = True
        )

        handlers = [
            (r'/video/upload',     UploadHandler),          # 接受客户端上网的需要解析的网页文本
            (r'/login',            LoginHandler),           # 登录认证
            (r'/upload',           UploadFileHandler),
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
