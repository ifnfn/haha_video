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

def getlist(menuName, argument):
    data = {}
    m = tv.FindMenu(menuName)
    if m:
        data = m.GetAlbumList(argument)
    return data

class VideoListHandler(JSONPHandler):
    def get(self):
        js = {}
        page = self.get_argument('page', 0)
        size = self.get_argument('size', 20)
        menu = self.get_argument('menu', u'电影')

        js['result'] = getlist(menu, int(page), int(size))
        self.finish(json.dumps(js, indent=4, ensure_ascii=False))

    def post(self):
        argument = {}
        menu = self.get_argument('menu', u'电影')

        argument['page'] = int(self.get_argument('page', 0))
        argument['size'] = int(self.get_argument('size', 20))
        if self.request.body:
            try:
                umap = json.loads(self.request.body)
#                 argument['filter'] = {}
#                 argument['fields'] = {}
#                 argument['sort'] = {}
                argument.update(umap)
            except:
                raise tornado.web.HTTPError(400)

        argument['result'] = getlist(menu, argument)
        self.finish(json.dumps(argument, indent=4, ensure_ascii=False))

class UrlMapHandler(tornado.web.RequestHandler):
    def post(self):
        body = self.request.body
        if body and len(body) > 0:
            try:
                umap = json.loads(body)
                tv.engine.command.AddUrlMap(umap['source'], umap['dest'])
            except:
                raise tornado.web.HTTPError(400)
            self.finish('OK')
        else:
            raise tornado.web.HTTPError(404)

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
        (r'/video/urlmap',            UrlMapHandler),          # 后台管理，增加网址映射

    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
