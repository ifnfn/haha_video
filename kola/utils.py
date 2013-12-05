#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .fetchTools import fetch_httplib2 as fetch
import logging, sys
import traceback
import json
import base64, zlib

def autostr(i):
    if type(i) == int:
        return str(i)
    else:
        return i

def autoint(i):
    if type(i) == str:
        return i and int(i) or 0
    else:
        return i

def json_get(sets, key, default):
    if key in sets:
        return sets[key]
    else:
        return default

MAX_TRY = 3
def GetUrl(url, times = 0):
    if times > MAX_TRY:
        return ''
    try:
        status, _, _, response = fetch(url)
        if status != '200':
            print(response)
            return ''
        return response
    except:
        t, v, tb = sys.exc_info()
        print("KolaClient.GetUrl: %s %s, %s, %s" % (url, t, v, traceback.format_tb(tb)))
        return GetUrl(url, times + 1)

def PostUrl(url, body, key=""):
    try:
        compress = zlib.compressobj(9,
                                    zlib.DEFLATED,
                                    - zlib.MAX_WBITS,
                                    zlib.DEF_MEM_LEVEL,
                                    0)
        body = b"\x5A\xA5" + compress.compress(body.encode())
        body += compress.flush()
        body = base64.encodebytes(body).decode()

        ret, _, _, response = fetch(url, 'POST', body, cookies = "key=" + key)
        if ret != "200":
            print(response)
            return None
        return response
    except:
        t, v, tb = sys.exc_info()
        print("PostUrl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
        return None

base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]
def dec2hex(string_num):
    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num,rem = divmod(num, 16)
        mid.append(base[rem])

    return ''.join([str(x) for x in mid[::-1]])

def GetNameByUrl(url):
    maps = {
           '乐视': 'letv.com',
           '腾讯视频' : ('qq.com', 'qqlive.dnion.com'),
           '视讯中国' : 'cnlive.com',
           '凤凰网'   : 'ifeng.com',
    }
    order = {
           '乐视'    : 1,
           '腾讯视频' : 2,
           '视讯中国' : 3,
           '凤凰网'   : 4,
    }

    for k, v in list(maps.items()):
        if type(v) == str:
            if v in url:
                return k, order[k]
        elif type(v) == tuple:
            for vv in v:
                if vv in url:
                    return k, order[k]
    return '', 5

def GetQuickFilter(name, default):
    filename = name + '.json'
    try:
        io = open(filename)
        return json.load(io)
    except:
        return default

logging.basicConfig()
log = logging.getLogger("crawler")
