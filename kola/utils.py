#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import json
import logging

from .pytable import Pinyin

def autostr(i):
    if i == None:
        return ''
    if type(i) == int:
        return str(i)
    else:
        return i

def autoint(i):
    if i == None:
        return 0

    if type(i) == str:
        return i and int(i) or 0
    else:
        return i

def autofloat(i):
    if i == None:
        return 0.0

    if type(i) == str:
        return i and float(i) or 0.0
    else:
        return i;

def json_get(sets, key, default):
    if key in sets:
        return sets[key]
    else:
        return default

def genAlbumId(name):
    if type(name) == str:
        name = name.encode()

    return hashlib.md5(name).hexdigest()[22:]

def getVidoId(name):
    if type(name) == str:
        name = name.encode()

    return hashlib.md5(name).hexdigest()[24:]


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
           '乐视'     : 1,
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

py = Pinyin()

def GetPinYin(text):
    return py.get_initials(text, '')

logging.basicConfig()
log = logging.getLogger("crawler")
