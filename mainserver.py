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
from jsonphandler import JSONPHandler


MAINSERVER_HOST = 'http://127.0.0.1:9990'

cmd_1 ={
    'source'  : 'http://so.tv.sohu.com/list_p11_p2_p3_p4-1_p5_p6_p70_p80_p9_2d2_p101_p11.html',
    'dest'    : MAINSERVER_HOST + '/video/upload',
    'name'    : 'videolist',
    'menu'    : '电影',
    'regular' : [
        '(<a class="pic" target="_blank" title=".+/></a>)',
        '(<p class="tit tit-p">.+</a>)'
    ],
}

cmd_2 = {
    'source'  : 'http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html',
    'dest'    : MAINSERVER_HOST + '/video/upload',
    'name'    : 'programme',
    'menu'    : '电影',
    'regular' : [
        'var (playlistId|pid|vid|tag)\s*=\s*"(.+)";',
        'h1 class="color3"><a href=.*>(.*)</a>'
    ],
}

cmd_3 = { # 搜狐节目指数
    'source'  : 'http://index.tv.sohu.com/index/switch-aid/5161139',
    'dest'    : MAINSERVER_HOST + '/video/upload',
    'name'    : 'programme_score',
    'menu'    : '电影',
    'dest'    : 'http://git.nationalchip.com:9990/video/upload',
}

class LoginHandler(JSONPHandler):
    def get(self):
        print self.request.remote_ip
        db = redis.Redis(host='127.0.0.1', port=6379, db=1)

#        db.rpush('command', json.dumps(cmd_1));
#        db.rpush('command', json.dumps(cmd_2));
#        db.rpush('command', json.dumps(cmd_3));
        ret = {
            'key': 'None',
            'command': []
        }
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

class GetProgrammeListHandler(JSONPHandler):
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
        (r'/video/programemlist',     GetProgrammeListHandler), # 得到节目列表
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
