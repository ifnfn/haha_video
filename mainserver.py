#!/usr/bin/python3
# -*- coding: utf-8 -*-

import redis
import json
import hashlib
import base64
from Crypto.PublicKey import RSA
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options

from fetchTools import fetch_httplib2 as fetch
from basehandle import BaseHandler#, JSONPHandler

MAINSERVER_HOST = 'http://127.0.0.1:9990'

privatekey_text = '''-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA8uLLcUH6pVt4qyiUgU+KN/dFVIZOZinZ2YnsydbEMhwAUW6g
Q1wUGPr4B9eAeEKBWCB6PKEJkzQC7Fmmu2WPcs67bqvcoRmFMbiMN2n+faczL2Pd
7Je8iUO9nUWU4hfn4HyG2fUdVXf3J/cz7OZ1OCFHPS0JI7UnN4a8WE41tYbMuAJA
9uaVs4WqPtZ/GBvNub/kkf9Ltf0sDGa4quTdu+cRkLMQBnRTDGalmI3Wx6C9WGPO
iNUYK1+KS9UMyyGP9hwBvcWAvgy7WmarxR8gTxrIguRPcnciPi9aIoE8Xe3vxQ7S
ddFQdee8ua2IsgRy4g4+o7LMK2b2hn2lIXJOUwIDAQABAoIBAQDStLk0+b4NMXtP
UJb0TyJjRtoYZ6MfsfLRa3vF5dCyf+QuwL+7b+fne+EsPGGw8lDvOM2SR0ndL+PR
Ujz4mTSGrp2fduyhvVf1OFo7wHIMY75dwE9H7qKame+mvjRYp9B6yMzbzG60NKxv
OV8MhyjtlsEMa0NgfMkWvIYsPT0Oyb+rXZpgwLM+a1caLx/qVTDN6TO4+y1BWIRu
XrdAO2yHwqJP77zpFgtQ7ZkRTAkG7Rt69PNrHWHD40TA5zhnM+IyS1Js3Xr7u4hc
8ZoAcXde+qjj32ASFRyGjUZUKp1d4nU1IUKnrwgtNLyjl6XtOYWmL/HbFpZOhQV3
HXTM+kSxAoGBAPsh53PvNOuQWocourUa7+8nqMDfoz+GgQd4Ki+X1YqT/1oDKSYy
xbMBhFzkKRypprqb8QzKRVPf6awLtmmuzqSLUE/TUh3wllU4Nn+uVRWuakEJp2tT
a4X+3jtjMomYKwLMScrDfvYua8GpVL1W1HE6mF4NK794aCHoESyfWbevAoGBAPeX
+Nw4hGA3CoMflyDSmOc2BJSpQor7HB41STwlHzUG7kEzIc5EKnME/8uNBn3kkNek
+Au+EloWQEqaqUxeFwbNWrMPBcfI+bVDT4ZzQqTxv4YjbEvipiRyyMpgh29q/tyM
K4E/tbYSSydJ2tYWPBaDIk5MMacoLaZ7oZg939idAoGBALQDFIZs4/Eq80lI77Sb
z3sNYZCHfdwuTNUO1KZy3rXL6lEaTOe9oyryHm/7eGC8VvASkdIKN3Gs4jHZ33KX
xDX8SqA9qPIfH5OMjLwvOXwmHrHp+qEbFcrh62iEbZhlhAcoaoi2Y46RrdoOx9hE
ollbmBZquH4yD+qmD5F90/CvAoGBAMQV4KqQPA5zKOkl2KvO/feHKWOPFTs6mk82
RlTS1X9KiOCsHSbdh3zmRasweia0IR4X8bZjBue/3ZT4HgJ0NepWMnHDAQHzogez
UkUZ/XriVptmbHtA+fG90lWs0zYjV8rVXBMVoNScclagQCbzHw15N28pGt3WjSjf
muAWiLRlAoGAQtYOFx/sxMPZGLLl5AYJVYu7ygSjDcSepkFjXbHX2QbABhmkcI5r
SqeJ/rm7yOdi4f66W40yjflLA1tZtuaefvjFF3QVhQEXTD7G01b5Ul6zXpOLjwNZ
ZBB65WO1zc7h8xq6nssyaR1vruGt41dhV+CLSnTxU3g3eDWNOtYBios=
-----END RSA PRIVATE KEY-----'''

class R:
    def __init__(self):
        #self.privateRSAKey = RSA.generate(4096)
        #self.publicRSAKey = self.privateRSAKey.publickey()
        self.privateRSAKey = RSA.importKey(privatekey_text)
        self.publicRSAKey = self.privateRSAKey.publickey()
        #print(self.privateRSAKey.publickey().exportKey())
        #print("private:")
        #self.printf(self.privateRSAKey)
        #print("public:")
        #self.printf(self.publicRSAKey)

    def exportKey(self):
        return self.publicRSAKey.exportKey()

    def printf(self, key):
        print("Can Encrypt:", key.can_encrypt())
        print("Can sign:", key.can_sign())
        print("Has private:", key.has_private())

    def RSAEncrypt(self, text):
        bits = ""
        pos = 0
        size = len(text)
        chuncklen = self.publicRSAKey.size() // 8 + 1
        print(chuncklen)
        while pos <size:
            a = text[pos : pos + chuncklen].encode()
            cipheredText = self.publicRSAKey.encrypt(a, "")
            x = [chr(v) for v in cipheredText[0]]
            bits += ''.join(x)
            pos += chuncklen

        print(len(bits))

#        return self.publicRSAKey.encrypt(text, len(text))

    def RSADecrypt(self, text):
        return self.privateRSAKey.decrypt(text)
        #return rsa.decrypt(text)


def test():
    a = R()
    t = a.RSAEncrypt('text')
    print(t)
    print(a.RSADecrypt(t))

class KeyHandler(BaseHandler):
    def get(self):
        self.finish(R().exportKey())

class LoginHandler(BaseHandler):
    def get(self):
        user_id = self.get_argument('user_id')
        #print(self.request.remote_ip, user_id)
        db = redis.Redis(host='127.0.0.1', port=6379, db=1)

        ret = {
            'key': 'None',
            'command': [],
            'server' : MAINSERVER_HOST,
            'next': 10   # 下次登录时间
        }
        if not db.exists(user_id):
            key = (user_id + self.request.remote_ip).encode()
            key = hashlib.md5(key).hexdigest().upper()
            db.set(user_id, key)
        else:
            key = db.get(user_id).decode()

        ret['key'] = key
        cmd = db.lpop('command')
        if cmd:
            cmd = cmd.decode()
            data =json.loads(cmd)
            ret['command'].append(data)
        self.finish(json.dumps(ret))

    def post(self):
        self.finish('OK')

class AddCommandHandler(BaseHandler):
    def get(self):
        pass

    def post(self):
        body = self.request.body.decode()
        if body:
            db = redis.Redis(host='127.0.0.1', port=6379, db=1)
            db.rpush('command', body)
            data =json.loads(body)

        return

class SohuCacheHandler(BaseHandler):
    def get(self):
        response = ''
        db = redis.Redis(host='127.0.0.1', port=6379, db=8)
        url = self.get_argument('url')
        if not db.exists(url):
            _, _, _, response = fetch(url)
            db.set(url, response)
        else:
            response = db.get(url)

        self.finish(response)

define('port', default=9990, help='run on the given port', type=int)

class Application(tornado.web.Application):
    def __init__(self):
        settings = dict(
            debug = False,
            login_url = "/login",
            cookie_secret = 'z1DAVh+WTvyqpWGmOtJCQLETQYUznEuYskSF062J0To=',
            #xsrf_cookies = True,
            autoescape = None,
        )

        handlers = [
            (r'/key',               KeyHandler),           # 取得public key
            (r'/login',             LoginHandler),         # 登录认证
            (r'/addcommand',        AddCommandHandler),    # 增加命令
            (r'/cache',             SohuCacheHandler),     # 得到节目列表
        ]

        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    tornado.options.options.logging = "debug"
    tornado.options.parse_command_line()
    http_server = Application()
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    #main()
    test()
