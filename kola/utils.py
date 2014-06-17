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

def GetScript(script, function, param):
    return {
        'script' : script,
        'function' : function,
        'parameters' : param
    }

def GetTvmaoEpgScript(albumName):
    name_key = {}
    name_key['江苏-城市频道'] = 'jstv3'
    name_key['江苏-综艺频道'] = 'jstv2'
    name_key['江苏-公共频道'] = 'jstv8'
    name_key['江苏-影视频道'] = 'jstv4'
    name_key['江苏-休闲频道'] = 'jstv6'
    name_key['江苏-国际频道'] = 'jstv10'
    name_key['江苏-教育频道'] = 'jstv9'
    name_key['江苏-学习频道'] = ''
    name_key['江苏-好享购物'] = ''

    name_key['湖南卫视']     = 'hunantv1'
    name_key['沈阳-新闻频道'] = 'lnsy1'

    #name_key['吉林-东北戏曲'] = ''
    #name_key['吉林-家有购物'] = ''
    name_key['吉林卫视']     = 'jilin1'
    name_key['吉林-都市频道'] = 'jilin2'
    name_key['吉林-生活频道'] = 'jilin3'
    name_key['吉林-影视频道'] = 'jilin4'
    name_key['吉林-乡村频道'] = 'jilin5'
    name_key['吉林-公共新闻'] = 'jilin6'
    name_key['吉林-综艺文化'] = 'jilin7'

    #name_key['沈阳-经济频道'] = 'lnsy2'
    #name_key['沈阳-公共频道'] = 'lnsy3'
    #name_key['沈阳-生活频道'] = 'lnsy5'

    name_key['河南-都市频道'] = 'hntv2'
    name_key['河南-民生频道'] = 'hntv3'
    name_key['河南-政法频道'] = 'hntv4'
    name_key['河南-电视剧频道'] = 'hntv5'
    name_key['河南-新闻频道'] = 'hntv6'
    name_key['河南-公共频道'] = 'hntv8'
    name_key['河南-新农村频道'] = 'hntv9'
    name_key['河南-国际频道'] = 'hngj'

    if albumName in name_key:
        return GetScript('epg', 'get_channel_tvmao', [albumName, name_key[albumName]])

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
           '乐视'     : 'letv.com',
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

def GetPinYin(text, full=False):
    return py.get_initials(text, '', full)

logging.basicConfig()
log = logging.getLogger("crawler")
