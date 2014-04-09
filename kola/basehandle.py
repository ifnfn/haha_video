#! /usr/bin/python3
# -*- coding: utf-8 -*-

import base64
from urllib.parse import unquote
import zlib

import redis
import tornado.web


key_db = redis.Redis(host='127.0.0.1', port=6379, db=1)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        key = self.get_secure_cookie('user_id', None, 1)
        if key_db.exists(key) and key_db.get(key).decode() == self.request.remote_ip and True:
            return key

    def prepare(self):
        if self.request.method == "POST" and self.request.body:
            body = unquote(self.request.body.decode())           # URLDecode
            body = base64.decodebytes(body.encode())             # BASE64_Decode
            if int(body[0]) == 0x5A and int(body[1]) == 0xA5:
                decompress = zlib.decompressobj(-zlib.MAX_WBITS)     # ZLIB Decompress
                self.request.body = decompress.decompress(body[2:])
                self.request.body += decompress.flush()
            else:
                self.request.body = body
