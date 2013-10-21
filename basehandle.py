# coding=utf-8

import tornado.web
import redis
import zlib
import base64
from urllib.parse import unquote

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        return
        self.client_ip = self.request.remote_ip
        key = self.get_cookie('key')
        db = redis.Redis(host='127.0.0.1', port=6379, db=1)
        if not db.exists(key) or db.get(key).decode() != self.request.remote_ip:
            raise tornado.web.HTTPError(401, "Missing key %s" % key)

    def get_current_user(self):
        return self.get_secure_cookie('user_id', 0)

    def prepare(self):
        if self.request.method == "POST" and self.request.body:
            body = unquote(self.request.body.decode())           # URLDecode
            body = base64.decodebytes(body.encode())             # BASE64_Decode
            decompress = zlib.decompressobj(-zlib.MAX_WBITS)     # ZLIB Decompress
            self.request.body = decompress.decompress(body)
            self.request.body += decompress.flush()
