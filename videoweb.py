#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options
# from tornado import gen
# from tornado import httpclient
# from tornado.escape import json_encode

import redis
import json
# import re
from jsonphandler import JSONPHandler
from kolatv import Kolatv

tv = Kolatv()

def getlist(menuName, page, size):
    data = {}
    m = tv.FindMenu(menuName)
    if m:
        return data

class VideoListHandler(JSONPHandler):
    # list?page=2&size=10&menu="电影"
    def get(self):
        page = self.get_argument('page')
        size = self.get_argument('size')
        menu = self.get_argument('menu')
        data = getlist(menu, page, size)
        self.finish(json.dumps(data, indent=4, ensure_ascii=False))

class GetPlayerHandler(tornado.web.RequestHandler):
    def post(self):
        body = self.request.body
        if body and len(body) > 0:
            self.finish(tv.GetRealPlayer(body))
        else:
            raise tornado.web.HTTPError(404)

class UploadHandler(tornado.web.RequestHandler):
    def get(self):
        print('Upload get')
        pass

    def post(self):
#         user_id = self.get_argument('user_id')
#         user_key = self.get_argument('user_key')
#         print self.request.remote_ip, user_id, user_key
#
#         db = redis.Redis(host='127.0.0.1', port=6379, db=1)
#         if not db.exists(user_id):
#             raise tornado.web.HTTPError(400, "Timeout user_key %s" % user_key)
#         elif db.get(user_id) != user_key:
#             raise tornado.web.HTTPError(400, "Missing user_key %s" % user_key)

        body = self.request.body
        if body and len(body) > 0:
            tv.AddTask(body)

        return

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()
    tv.UpdateAlbumList()

    define('port', default=9991, help='run on the given port', type=int)
    settings = {'debug': False, 'template_path': 'templates',
           'cookie_secret': 'z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To='}
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r'/video/list',              VideoListHandler),
        (r'/video/upload',            UploadHandler),          # 接受客户端上网的需要解析的网页文本
        (r'/video/getplayer',         GetPlayerHandler),       # 得到下载地位

    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
