#! /usr/bin/python3
# -*- coding: utf-8 -*-

import posixpath
import re

import tornado.escape

from engine import KolaParser
from kola import AlbumBase, DB, utils, City, autostr, autoint

from .common import PRIOR_DEFTV
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

        #print('"%s" : "%s",' % (albumName, albumName))
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
                '体育台' : '棋|游戏|钓|体育|足球|网球|cctv-5|CCTV5|cctv5|CCTV-5',
                '综合台' : '综合|财|都市|经济|旅游',
                '少儿台' : '动画|卡通|动漫|少儿|宝贝',
                '地方台' : '^(?!.*?(cctv|CCTV|卫视|测试|卡酷少儿|炫动卡通' + self.Outside + ')).*$',
                '境外台' : self.Outside,
                '高清台' : 'HD|hd|高清',
                '网络台' : '乐视|VST|vst|全纪实|股票老左|大智慧财经|彩民在线|网络'
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
        if album and len(album.videos) > 0:
            self._save_update_append(None, album)

class LivetvVideo:
    def __init__(self, js = None):
        self.name = ''
        self.vid = ''
        self.order = -1
        self.isHigh = -1
        self.videoUrl = ''

        self.resolution = {}

        if js:
            self.LoadFromJson(js)

    def SetUrl(self, url, album):
        urlScript = utils.GetScript('livetv', 'get_video_url', [url, album.albumName, album.vid])
        self.resolution['default'] = urlScript

    def SaveToJson(self):
        ret = {}

        if self.vid             : ret['vid']          = self.vid
        if self.name            : ret['name']         = self.name
        if self.order != -1     : ret['order']        = self.order
        if self.isHigh != -1    : ret['isHigh']       = self.isHigh
        if self.resolution      : ret['resolution']   = self.resolution

        return ret

    def LoadFromJson(self, json):
        if 'vid' in json        : self.vid        = autostr(json['vid'])
        if 'order' in json      : self.order      = autoint(json['order'])
        if 'isHigh' in json     : self.isHigh     = autoint(json['isHigh'])
        if 'name' in json       : self.name       = json['name']
        if 'resolution' in json : self.resolution = json['resolution']

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
        self.videos = []
        self.livetv = LivetvPrivate()

    def NewVideo(self, videoUrl=None, isHigh=0):
        if len(self.videos) >= 10:
            return None
        video = LivetvVideo()
        video.order = self.order
        video.name  = self.tvName
        video.isHigh = isHigh
        video.videoUrl = videoUrl

        if videoUrl:
            video.vid = utils.getVidoId(videoUrl)
            video.SetUrl(videoUrl, self)

            for v in self.videos:
                if v.vid == video.vid:
                    return None

        self.videos.append(video)
        return video

    def SaveToJson(self):
        self.videoList = []
        for v in self.videos:
            js = v.SaveToJson()
            self.videoList.append(js)

        self.videos = []
        if self.livetv:
            self.private[self.engineName] = self.livetv.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)

        for js in json['videoList']:
            v = LivetvVideo()
            v.LoadFromJson(js)
            self.videos.append(v)

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
        self.order = PRIOR_DEFTV
        self.area = ''
        self.db = LivetvDB()

    def NewAlbumAndVideo(self, albumName, videoUrl):
        videos = []
        album = self.NewAlbum(albumName)
        if album:
            if type(videoUrl) == str:
                v = album.NewVideo(videoUrl, album.isHigh)
                videos.append(v)
            elif type(videoUrl) == list:
                for url in videoUrl:
                    v = album.NewVideo(url, album.isHigh)
                    if v:
                        videos.append(v)

        return album, videos

    def NewAlbum(self, name, epgInfo=None):
        album = None
#        if name in ['宁波文化娱乐']:
#            print(name)
        albumName = self.GetAliasName(name)
#        if albumName in ['宁波文化娱乐']:
#            print(albumName)
        if albumName:
            DisplayAlbumName = albumName
            isHigh = 0
            if re.findall('HD|hd|高清', albumName):
                isHigh = 1
                #DisplayAlbumName = re.sub('-高清', '', albumName)

            vid = GetOrder(DisplayAlbumName) + utils.genAlbumId(DisplayAlbumName)

            album = LivetvAlbum()
            js, count = self.db.GetAlbumListJson({"filter" : {"vids": vid,"cid":200}}, disablePage=True, full=True)
            if js and count == 1:
                album.LoadFromJson(js[0])

            album.isHigh      = isHigh
            album.albumName   = DisplayAlbumName
            album.Number      = GetNumber(album.albumName)
            album.tvName      = self.tvName
            album.order       = self.order
            album.vid         = vid
            album.categories  = self.tvCate.GetCategories(albumName)
            album.enAlbumName = self.tvName

            if album.cid == 200: # 直播
                if epgInfo == None:
                    album.epgInfo = GetEPGScript(album.albumName)
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
        else:
            for (k,v) in self.Alias.items():
                #if re.findall(k, name):
                nname = re.sub(k, v, name)
                if nname != name:
                    name = nname
                    break

        return tvalias.GetAliasName(name, self.__class__.__name__)
