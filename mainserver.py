#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options
#from tornado import gen
#from tornado import httpclient
#from tornado.escape import json_encode

import redis
import json
import hashlib
from jsonphandler import JSONPHandler


MAINSERVER_HOST = 'http://127.0.0.1:9990'

class LoginHandler(JSONPHandler):
    def get(self):
        user_id = self.get_argument('user_id')
        print self.request.remote_ip, user_id
        db = redis.Redis(host='127.0.0.1', port=6379, db=1)

        ret = {
            'key': 'None',
            'command': [],
            'next': 100   # 下次登录时间
        }
        if not db.exists(user_id):
            key = hashlib.md5(user_id + self.request.remote_ip).hexdigest().upper()
            db.set(user_id, key)
        else:
            key = db.get(user_id)

        ret['key'] = key
        cmd = db.lpop('command')
        if cmd:
            data =json.loads(cmd)
            ret['command'].append(data)
        self.finish(json.dumps(ret))

class AddCommandHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        body = self.request.body
        if body:
            db = redis.Redis(host='127.0.0.1', port=6379, db=1)
            db.rpush('command', body)
            data =json.loads(body)
            print 'add: ', data['source']

        return

class GetMainMenuHandler(JSONPHandler):
    def get(self):
        pass

class GetAlbumListHandler(JSONPHandler):
    def get(self):
        pass

def main():
    define('port', default=9990, help='run on the given port', type=int)
    settings = {'debug': False, 'template_path': 'templates',
           'cookie_secret': 'z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To='}
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r'/video/login',             LoginHandler),            # 登录认证
        (r'/video/addcommand',        AddCommandHandler),       # 增加命令
        (r'/video/getmenu',           GetMainMenuHandler),      # 得到一级菜单
        (r'/video/programemlist',     GetAlbumListHandler),     # 得到节目列表
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
