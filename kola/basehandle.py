#! /usr/bin/python3
# -*- coding: utf-8 -*-

import base64
from urllib.parse import unquote
import zlib

import tornado.web

from .kolaserver import kolas


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        chipid  = self.get_argument('chipid', None)
        serial  = self.get_argument('serial', None)
        key = self.get_secure_cookie('user_id', None, 1)
        return kolas.CheckUser(key, self.request.remote_ip, chipid, serial)

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
