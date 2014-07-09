#! /usr/bin/python3
# -*- coding: utf-8 -*-

import posixpath
import re

import tornado.escape

from engine import KolaParser
from kola import VideoBase, AlbumBase, DB, utils, City

from .common import PRIOR_COMMON
from .epg import GetEPGScript
from .tvorder import GetOrder, GetNumber


class TVAlias:
    def __init__(self):
        self.Update()

    def Update(self):
        try:
            fn = posixpath.abspath('alias.json')
            self.alias_list = tornado.escape.json_decode(open(fn, encoding='utf8').read())
            #try:
            #    for v, x in self.alias_list.items():
            #        if x == v:
            #            self.alias_list[v] = ''
            #    s = json.dumps(self.alias_list, indent=4, ensure_ascii=False, sort_keys=True)
            #    print(s)
            #except Exception as e:
            #    print(e)
        except Exception as e:
            print(e)

    def GetAliasName(self, albumName, engineName=None):
        for k, v in self.alias_list.items():
            if albumName == k:
                return albumName
            if type(v) == str:
                nameList = v.split("$")
            else:
                nameList = v

            for n in nameList:
                if engineName in n:
                    tmp_name = n.replace("@" + engineName, "")
                    if albumName == tmp_name:
                        return k
                elif albumName == n:
                    return k

        print('"%s" : "%s",' % (albumName, albumName))
        return albumName

    def Show(self):
        return

tvalias = TVAlias()

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
                '境外台' : self.Outside,
                '高清台' : 'HD|hd|高清'
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

    def SetUrl(self, url, album):
        urlScript = utils.GetScript('livetv', 'get_video_url', [url, album.albumName, album.vid])
        self.SetVideoUrl('default', urlScript)

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

    def NewVideo(self, videoUrl=None):
        v = self.videoClass()
        v.pid = self.vid
        v.cid = self.cid
        v.order = self.order
        v.name  = self.tvName

        if videoUrl:
            v.vid = utils.getVidoId(videoUrl)
            v.SetUrl(videoUrl, self)

        return v

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
            album.albumName  = albumName
            album.Number     = GetNumber(album.albumName)
            album.tvName     = self.tvName
            album.order      = self.order
            album.vid        = GetOrder(album.albumName) + utils.genAlbumId(album.albumName)
            album.categories = self.tvCate.GetCategories(album.albumName)

            album.enAlbumName = self.tvName

            if album.cid == 200: # 直播
                if epgInfo == None:
                    album.epgInfo = GetEPGScript(albumName)
                else:
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
            name = self.Alias[name]

        return tvalias.GetAliasName(name, self.__class__.__name__)
