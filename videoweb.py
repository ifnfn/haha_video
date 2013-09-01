#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado import gen
from tornado import httpclient
from tornado.options import define, options
from tornado.escape import json_encode

import redis
import json
import random
import re
import time
import base64, zlib
import threading
import Queue
from jsonphandler import JSONPHandler
from datetime import timedelta, date
from kolatv import tv

class ImgHandler(tornado.web.RequestHandler):
    def get(self,id):
        c = redis.Redis(host='127.0.0.1', port=6379, db=4)
        d = redis.Redis(host='127.0.0.1', port=6379, db=3)
        e = redis.Redis(host='127.0.0.1', port=6379, db=5)
        if id.startswith("singer") or id.startswith("show"):
            img = e.hget("id:%s"%id,"img")
            self.redirect(img, permanent=True)
            return
        elif c.exists("id:%s"%id):
            img = c.hget("id:%s"%id,"img")
            self.redirect(img, permanent=True)
            return
        elif d.exists("id:%s"%id):
            data = d.hgetall("id:%s"%id)
            item = json.loads(data.values()[0])
            img = item['img']
            self.redirect(img, permanent=True)
            return
        else:
            raise tornado.web.HTTPError(404)
            self.finish()
            return


def getlist(page, size, setname, flag, type):
    c = redis.Redis(host='127.0.0.1', port=6379, db=4)
    print c.keys()

    m = (int(page) - 1) * int(size)
    n = int(page) * int(size)
    length = c.llen(setname)
    print "length: ", length
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
    for id in ids:
        # c.expire(id, 10)
        # print "TTL: ", c.ttl(id)
        if not c.exists(id):
            continue
        item = c.hgetall(id)
        items.append(item)
    data = {}
    data['total'] = length
    data['next']  = nexts
    data['items'] = items
    return data

class TvnewHandler(JSONPHandler):
    def get(self):
        page = self.get_argument("page")
        size = self.get_argument("size")
        setname = "new:tv"
        type = "tv"
        flag = False
        data = getlist(page,size,setname,flag,type)
        self.finish(json.dumps(data, indent=4, ensure_ascii=False))
        return


class TvhotHandler(JSONPHandler):
    def get(self):
        page = self.get_argument("page")
        size = self.get_argument("size")
        setname = "title:tv"
        type = "tv"
        flag = False
        data = getlist(page, size, setname, flag, type)
        self.finish(json.dumps(data, indent=4, ensure_ascii=False))
        return

class VideoListHandler(tornado.web.RequestHandler):
    def get(self):
        c = redis.Redis(host='127.0.0.1', port=6379, db=4)
#        print c.keys()
        ids = c.lrange('title:tv', 0, -1)
        items = []
        for id in ids:
            if not c.exists(id):
                continue
            item = {}
            item['title'] = c.hgetall(id)['title']
#            self.finish(c.hgetall(id)['title']
            items.append(item)
        self.finish(json.dumps(items, sort_keys=True, indent=4, ensure_ascii=False))

        return

class UploadHandler(tornado.web.RequestHandler):
    def get(self):
        print("Upload get")
        pass

    def post(self):
        body = self.request.body
        if body and len(body) > 0:
            tv.AddTask(body)
#            js = json.loads(body)
#            if js == None:
#                return
#
#            text =base64.decodestring(js['data'])
#            if text:
#                js['data'] = text
#                tv.AddTask(js)
        return

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()

    define("port", default=9991, help="run on the given port", type=int)
    settings = {"debug": False, "template_path": "templates",
           "cookie_secret": "z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To="}
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/video/tv/new",            TvnewHandler),
        (r"/video/tv/hot",            TvhotHandler),
        (r"/video/list",              VideoListHandler),
        (r"/video/img/(.*)",          ImgHandler),
        (r"/video/upload",            UploadHandler),
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
