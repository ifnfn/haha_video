#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from engine import KolaParser
from kola import VideoBase, AlbumBase, DB, utils, City

from .common import PRIOR_COMMON
from .tvorder import GetOrder, GetNumber


class TVCategory:
    def __init__(self):
        self.Outside = '凤凰|越南|半岛|澳门|东森|澳视|亚洲|良仔|朝鲜| TV|KP|Yes|HQ|NASA|Poker|Docu|Channel|Neotv|fashion|Sport|sport|Power|FIGHT|Pencerahan|UK|GOOD|Kontra|Rouge|Outdoor|Divine|Europe|DaQu|Teleromagna|Alsharqiya|Playy|Boot Movie|Runway|Bid|LifeStyle|CBN|HSN|BNT|NTV|Virgin|Film|Smile|Russia|NRK|VIET|Gulli|Fresh'
        self.filter = {
            '类型' : {
                '央视台' : 'cctv|CCTV',
                '卫视台' : '卫视|卡酷少儿|炫动卡通',
                '体育台' : '体育|足球|网球|cctv-5|CCTV5|cctv5|CCTV-5',
                '综合台' : '综合|财|都市|经济|旅游',
                '少儿台' : '动画|卡通|动漫|少儿',
                '地方台' : '^(?!.*?(cctv|CCTV|卫视|测试|卡酷少儿|炫动卡通' + self.Outside + ')).*$',
                '境外台' : self.Outside
            }
        }

    def GetCategories(self, name):
        ret = []
        for k, v in self.filter['类型'].items():
            x = re.findall(v, name)
            if x:
                ret.append(k)
        return ret

class LivetvDB(DB):
    def SaveAlbum(self, album, upsert=True):
        self._save_update_append(None, album)

class LivetvVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

class LivetvPrivate:
    def __init__(self):
        self.name =  '直播'
        self.videoListUrl = {}

    def Json(self):
        json = {'name' : self.name}
        if self.videoListUrl : json['videoListUrl'] = self.videoListUrl

        return json

    def Load(self, js):
        if 'name' in js         : self.name         = js['name']
        if 'videoListUrl' in js : self.videoListUrl = js['videoListUrl']

class LivetvAlbum(AlbumBase):
    def __init__(self):
        self.engineName = 'LivetvEngine'
        super().__init__()
        self.cid =  200
        self.albumPageUrl = ''
        self.livetv = LivetvPrivate()
        self.videoClass = LivetvVideo

    def SaveToJson(self):
        if self.livetv:
            self.private[self.engineName] = self.livetv.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.livetv.Load(self.private[self.engineName])

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        pass

class LivetvParser(KolaParser):
    city = City()
    def __init__(self):
        super().__init__()
        self.tvCate = TVCategory()
        self.Alias = {}
        self.ExcludeName = []
        self.tvName = ''
        self.order = PRIOR_COMMON
        self.area = ''

    def NewAlbum(self, name, epgInfo=None):
        album = None
        albumName = self.GetAliasName(name)
        if albumName:
            album  = LivetvAlbum()
            album.albumName = albumName
            album.Number    = GetNumber(album.albumName)
            vid   = utils.genAlbumId(album.albumName)
            order = GetOrder(album.albumName)

            album.vid = order + vid
            album.categories  = self.tvCate.GetCategories(album.albumName)

            album.enAlbumName = self.tvName
            if epgInfo:
                album.epgInfo = epgInfo
            if self.area:
                album.area = self.area
            else:
                album.area = self.city.GetCity(album.albumName)

        return album

    def GetAliasName(self, name):
        for p in list(self.ExcludeName):
            if re.findall(p, name):
                return None

        if name in self.ExcludeName:
            return None

        if name in self.Alias:
            return self.Alias[name]

        return name


