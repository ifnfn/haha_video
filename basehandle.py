# coding=utf-8

import tornado.web
import tornado.escape
import redis
import zlib
import base64
from urllib.parse import unquote

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.client_ip = self.request.remote_ip
        print(self.request.headers)
        if 'X-Real-IP' in self.request.headers:
            self.client_ip = self.request.headers['X-Real-IP']
        elif 'Host' in self.request.headers:
            host = self.request.headers['Host'].split(':')
            if len(host) > 0:
                self.client_ip = host[0]

    def get_current_user(self):
        user = self.get_secure_cookie('user')
        if not user:
            return
        return tornado.escape.json_decode(user)

    def prepare(self):
        self.check_cookie()
        if self.request.method == "POST" and self.request.body:
            body = unquote(self.request.body.decode())           # URLDecode
            body = base64.decodebytes(body.encode())             # BASE64_Decode
            decompress = zlib.decompressobj(-zlib.MAX_WBITS)     # ZLIB Decompress
            self.request.body = decompress.decompress(body)

    def check_cookie(self):
        key = self.get_cookie('key')
        #print(self.request.remote_ip, user_id)
        db = redis.Redis(host='127.0.0.1', port=6379, db=1)
        if not db.exists(key) or db.get(key).decode() != self.request.remote_ip:
            raise tornado.web.HTTPError(401, "Missing key %s" % key)
