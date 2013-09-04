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
#import re
from jsonphandler import JSONPHandler
from kolatv import Kolatv

tv = Kolatv()

def getlist(page, size, setname, flag):
    c = redis.Redis(host='127.0.0.1', port=6379, db=4)
    print c.keys()

    m = (int(page) - 1) * int(size)
    n = int(page) * int(size)
    length = c.llen(setname)
    print 'length: ', length
    nexts = length - n
    if n > length:
        n = length - 1
        if m > length:
            m = n - int(size) +1
        nexts = 0
    else:
        n = n -1
    if m < 0:
        m = 0

    ids = c.lrange(setname, m, n)
    items = []
    for i in ids:
        # c.expire(i, 10)
        # print 'TTL: ', c.ttl(i)
        if not c.exists(i):
            continue
        item = c.hgetall(i)
        items.append(item)
    data = {}
    data['total'] = length
    data['next']  = nexts
    data['items'] = items
    return data

class TvnewHandler(JSONPHandler):
    def get(self):
        page = self.get_argument('page')
        size = self.get_argument('size')
        setname = 'new:tv'
        flag = False
        data = getlist(page,size,setname,flag)
        self.finish(json.dumps(data, indent=4, ensure_ascii=False))
        return


class TvhotHandler(JSONPHandler):
    def get(self):
        page = self.get_argument('page')
        size = self.get_argument('size')
        setname = 'title:tv'
        flag = False
        data = getlist(page, size, setname, flag)
        self.finish(json.dumps(data, indent=4, ensure_ascii=False))
        return

class VideoListHandler(tornado.web.RequestHandler):
    def get(self):
        c = redis.Redis(host='127.0.0.1', port=6379, db=4)
#        print c.keys()
        ids = c.lrange('title:tv', 0, -1)
        items = []
        for i in ids:
            if not c.exists(i):
                continue
            item = {}
            item['title'] = c.hgetall(i)['title']
#            self.finish(c.hgetall(i)['title']
            items.append(item)
        self.finish(json.dumps(items, sort_keys=True, indent=4, ensure_ascii=False))

        return

class UploadHandler(tornado.web.RequestHandler):
    def get(self):
        print('Upload get')
        pass

    def post(self):
        body = self.request.body
        if body and len(body) > 0:
            tv.AddTask(body)
        return

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()
    tv.UpdateMainMenu()

    define('port', default=9991, help='run on the given port', type=int)
    settings = {'debug': False, 'template_path': 'templates',
           'cookie_secret': 'z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To='}
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r'/video/tv/new',            TvnewHandler),
        (r'/video/tv/hot',            TvhotHandler),
        (r'/video/list',              VideoListHandler),
        (r'/video/upload',            UploadHandler),          # 接受客户端上网的需要解析的网页文本
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
