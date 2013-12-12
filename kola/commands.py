#! /usr/bin/python3
# -*- coding: utf-8 -*-

import threading
import time

import redis
import tornado.escape

from .singleton import Singleton


# 命令管理器
class KolaCommand(Singleton):
    db = redis.Redis(host='127.0.0.1', port=6379, db=1)
    mutex = threading.Lock()
    def __init__(self):
        self.time = time.time()

    def GetCommand(self, timeout = 0, count=1):
        if time.time() - self.time > timeout: # 命令不要拿得太快，否则几百万个客户端同时跑来，服务器受不了
            ret = []
            print(time.time() - self.time)
            self.time = time.time()
            KolaCommand.mutex.acquire()
            for _ in range(count):
                cmd = KolaCommand.db.lpop('command')
                if cmd:
                    ret.append(tornado.escape.json_decode(cmd))
                else:
                    break
            KolaCommand.mutex.release()

            return ret
        return None
