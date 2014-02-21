#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from engine import City
from kola import utils, LivetvMenu

from .common import PRIOR_SMGBB
from .livetvdb import LivetvParser, LivetvDB


# 东方卫视
class ParserSmgbbLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '东方卫视'
        self.order = PRIOR_SMGBB
        self.area = '中国,上海'
        self.Alias = {
            '生活时尚' : '上海-生活时尚',
            '第一财经' : '上海-第一财经',
            '纪实频道' : '上海-纪实频道',
            '艺术人文' : '上海-艺术人文',
            '外语频道' : '上海-外语频道',
            '新闻综合' : '上海-新闻综合',
            '娱乐频道' : '上海-娱乐频道',
        }

        self.cmd['source'] = 'http://l.smgbb.cn/'
        self.cmd['regular'] = ['(<ul id="channels" class="ul_l_m">[\s\S]*</ul>)']

    def CmdParser(self, js):
        db = LivetvDB()
        city = City()

        channel = re.findall('<a href="\?channel=(.*?)" class="channel_name">(.*?)</a>', js['data'])
        for pid, name in channel:
            album  = self.NewAlbum(name)
            album.area = city.GetCity(album.albumName)

            v = album.NewVideo()
            v.order = self.order
            v.name     = self.tvName

            playUrl    = 'http://l.smgbb.cn/channelurl.ashx?starttime=0&endtime=0&channelcode=%s' % pid
            v.vid      = utils.getVidoId(playUrl)

            v.SetVideoUrl('default', {
                'script' : 'smgbbtv',
                'parameters' : [pid]
            })

            v.info = {
                'script' : 'smgbbtv',
                'function' : 'get_channel',
                'parameters' : [pid],
            }
            print(pid)
            print(v.info)

            album.videos.append(v)
            db.SaveAlbum(album)

class SmgbbLivetv(LivetvMenu):
    '''
    东方卫视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserSmgbbLivetv]
