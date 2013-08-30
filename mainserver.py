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
from jsonphandler import JSONPHandler
from datetime import timedelta, date

cmd_1 ={
    "source": "http://so.tv.sohu.com/list_p11_p2_p3_p4-1_p5_p6_p70_p80_p9_2d2_p101_p11.html",
    "dest" : "http://git.nationalchip.com:9990/video/upload"
}

cmd_2 = {
    "source": "http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html",
    "dest" : "http://git.nationalchip.com:9990/video/upload"
}

class LoginHandler(JSONPHandler):
    def get(self):
        print self.request.remote_ip
        db = redis.Redis(host='127.0.0.1', port=6379, db=1)

#        db.lpush('command', json.dumps(cmd_1));
#        db.lpush('command', json.dumps(cmd_2));
        ret = {
            'key': "None",
            'command': []
        }
        cmd = db.rpop('command')
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
            db.lpush("command", body)
            data =json.loads(body)
            print "add: ", data['source']

        return

def main():
    define("port", default=9990, help="run on the given port", type=int)
    settings = {"debug": False, "template_path": "templates",
           "cookie_secret": "z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To="}
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/video/login",             LoginHandler),
        (r"/video/addcommand",        AddCommandHandler),
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
