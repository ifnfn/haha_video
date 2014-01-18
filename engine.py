#! /usr/bin/python3
# -*- coding: utf-8 -*-

import redis
import tornado.ioloop

from engineweb import EngineApplication
#from viewweb import ViewApplication

def main():
    db = redis.Redis(host='127.0.0.1', port=6379, db=4)
    db.flushdb()

    tornado.options.parse_command_line()
    EngineApplication().listen(9992, xheaders = True)
#    ViewApplication().listen(9991, xheaders = True)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
