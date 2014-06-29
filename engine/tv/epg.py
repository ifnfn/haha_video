#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import utils


def GetEPGScript(albumName):
    info = get_channel_tvmao(albumName)
    if info == None:
        info = get_channel_wasu(albumName)

    if info == None:
        info = utils.GetScript('epg', 'get_channel', [albumName])

    return info

def get_channel_wasu(albumName):
    name_key = {}
    if albumName in name_key:
        return utils.GetScript('epg', 'get_channel_wasu', [albumName, name_key[albumName]])

    return None

def get_channel_tvmao(albumName):
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
    name_key['沈阳-经济频道'] = 'lnsy2'
    name_key['沈阳-公共频道'] = 'lnsy3'
    name_key['沈阳-生活频道'] = 'lnsy5'


    #name_key['吉林-东北戏曲'] = ''
    #name_key['吉林-家有购物'] = ''
    name_key['吉林卫视']     = 'jilin1'
    name_key['吉林-都市频道'] = 'jilin2'
    name_key['吉林-生活频道'] = 'jilin3'
    name_key['吉林-影视频道'] = 'jilin4'
    name_key['吉林-乡村频道'] = 'jilin5'
    name_key['吉林-公共新闻'] = 'jilin6'
    name_key['吉林-综艺文化'] = 'jilin7'

    name_key['河南-都市频道'] = 'hntv2'
    name_key['河南-民生频道'] = 'hntv3'
    name_key['河南-政法频道'] = 'hntv4'
    name_key['河南-电视剧频道'] = 'hntv5'
    name_key['河南-新闻频道'] = 'hntv6'
    name_key['河南-公共频道'] = 'hntv8'
    name_key['河南-新农村频道'] = 'hntv9'
    name_key['河南-国际频道'] = 'hngj'

    name_key['福建-综合频道'] = 'FJTV1',
    name_key['福建-公共频道'] = 'FJTV3',
    name_key['福建-新闻频道'] = 'FJTV4',
    name_key['福建-电视剧频道'] = 'FJTV5',
    name_key['福建-都市频道'] = 'FJTV6',
    name_key['福建-经济频道'] = 'FJTV7',
    name_key['福建-体育频道'] = 'FJTV8',
    name_key['福建-少儿频道'] = 'FJTV9',

    name_key['天津-新闻频道'] = 'TJTV2'
    name_key['天津-文艺频道'] = 'TJTV3'
    name_key['天津-影视频道'] = 'TJTV4'
    name_key['天津-都市频道'] = 'TJTV5'
    name_key['天津-体育频道'] = 'TJTV6'
    name_key['天津-科教频道'] = 'TJTV7'
    name_key['天津-少儿频道'] = 'TJTV8'
    name_key['天津-公共频道'] = 'TJTV9'

    name_key['北京-文艺频道'] = 'BTV2'
    name_key['北京-科教频道'] = 'BTV3'
    name_key['北京-影视频道'] = 'BTV4'
    name_key['北京-财经频道'] = 'BTV5'
    name_key['北京-体育频道'] = 'BTV6'
    name_key['北京-生活频道'] = 'BTV7'
    name_key['北京-青年频道'] = 'BTV8'
    name_key['北京-新闻频道'] = 'BTV9'

    if albumName in name_key:
        return utils.GetScript('epg', 'get_channel_tvmao', [albumName, name_key[albumName]])

    return None

def get_channel_qq(albumName):
    return None
