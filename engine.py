#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import json
import configparser
import tornado.escape
import redis
import threading
from utils import autostr, autoint, GetQuickFilter

class Template:
    def __init__(self, command=None, cmd=None):
        self.command = command
        command.AddCommand(cmd)

    def Execute(self):
        if self.command:
            self.command.Execute()

# 命令管理器
class Commands:
    def __init__(self, map_table):
        self.time = time.time()
        self.urlmap = {}
        self.pipe = None
        self.mutex = threading.Lock()

        self.map_table = map_table
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=1)

        maps = self.map_table.find()
        for url in maps:
            self.AddUrlMap(url['source'], url['dest'])

        # self.AddUrlMap('http://tv.sohu.com/s2011/fengsheng/', 'http://tv.sohu.com/20121109/n268282527.shtml')
        # self.AddUrlMap('http://tv.sohu.com/s2011/nrb/', 'http://tv.sohu.com/20111023/n323122692.shtml')
        self.AddUrlMap('http://tv.sohu.com/s2010/tctyjxl/', 'http://tv.sohu.com/20090930/n267111286.shtml')

    def AddUrlMap(self, oldurl, newurl):
        self.urlmap[oldurl] = newurl
        self.map_table.update({'source': oldurl}, {"$set" : {'dest': newurl}}, upsert=True, multi=True)

    def GetUrl(self, url):
        if url in self.urlmap:
            print(("Map: %s --> %s" % (url, self.urlmap[url])))
            return self.urlmap[url]
        else:
            return url

    def AddCommand(self, cmd):
        if 'source' in cmd and 'name' in cmd:
            cmd['source'] = self.GetUrl(cmd['source'])
            if self.pipe == None:
                self.pipe = self.db.pipeline()
            self.pipe.rpush('command', json.dumps(cmd))
        return self

    def Execute(self):
        if self.pipe:
            self.pipe.execute()
            self.pipe = None

    def GetCommand(self, timeout = 0, count=1):
        if time.time() - self.time > timeout: # 命令不要拿得太快，否则几百万个客户端同时跑来，服务器受不了
            ret = []
            print(time.time() - self.time)
            self.time = time.time()
            self.mutex.acquire()
            for _ in range(count):
                cmd = self.db.lpop('command')
                if cmd:
                    ret.append(tornado.escape.json_decode(cmd))
                else:
                    break
            self.mutex.release()

            return ret
        return None

# 每个 Video 表示一个可以播放视频
class VideoBase:
    def __init__(self, js=None):
        '''
        self.data = {
            'pid' : '371214851',
            "name": "花非花雾非雾第1集",
            "vid": 1268037,
            "order": "1",
            "playLength": 1935.051,
            "showName": "第1集",
            "publishTime": "2013-08-06",
            "videoDesc": "事情一定要注意，有事给自己的打招呼。",
            "isHigh": 1,

            "videoPlayCount": 18435401,
            "videoScore": 9.385957,

            "largePicUrl": "http://photocdn.sohu.com/20130806/vrsb924544.jpg",
            "smallPicUrl": "http://photocdn.sohu.com/20130806/vrss924544.jpg",

            'highVid' :
            'norVid' :
            'oriVid' :
            'superVid' :
            'relativeId' :
        }
        '''

        self.pid = ''
        self.name = ''
        self.playlistid = ''  # 所属 ablum
        self.vid = ''
        self.cid = 0

        self.highVid = ''
        self.norVid = ''
        self.oriVid = ''
        self.superVid = ''
        self.relativeId = ''

        self.order = -1
        self.playLength = 0.0
        self.showName = ''
        self.publishTime = ''
        self.videoDesc = ''
        self.isHigh = -1

        self.videoPlayCount = 0
        self.videoScore = 0.0

        self.smallPicUrl = ''
        self.largePicUrl = ''
        self.playUrl = ''

        self.originalData = []
        if js:
            self.LoadFromJson(js)

    def GetVid(self, definition=0):
        vid = self.vid
        maplist = self.vid,self.norVid,self.highVid,self.superVid,self.oriVid,self.relativeId
        if definition < len(maplist):
            vid = maplist[definition]
            if vid == '':
                vid = self.vid

        return vid

    def GetVideoPlayUrl(self, definition=0):
        pass

    def SaveToJson(self):
        ret = {}

        if self.playlistid      : ret['playlistid'] = self.playlistid
        if self.pid             : ret['pid'] = self.pid
        if self.name            : ret['name'] = self.name
        if self.vid             : ret['vid'] = self.vid
        if self.cid             : ret['cid'] = self.cid

        if self.highVid         : ret['highVid'] = self.highVid
        if self.norVid          : ret['norVid'] = self.norVid
        if self.oriVid          : ret['oriVid'] = self.oriVid
        if self.superVid        : ret['superVid'] = self.superVid
        if self.relativeId      : ret['relativeId'] = self.relativeId

        if self.order != -1     : ret['order'] = self.order
        if self.playLength      : ret['playLength'] = self.playLength
        if self.showName        : ret['showName'] = self.showName
        if self.publishTime     : ret['publishTime'] = self.publishTime
        if self.videoDesc       : ret['videoDesc'] = self.videoDesc
        if self.isHigh != -1    : ret['isHigh'] = self.isHigh
        if self.videoPlayCount  : ret['videoPlayCount'] = self.videoPlayCount
        if self.videoScore      : ret['videoScore'] = self.videoScore
        if self.largePicUrl     : ret['largePicUrl'] = self.largePicUrl
        if self.smallPicUrl     : ret['smallPicUrl'] = self.smallPicUrl
        if self.originalData    : ret['originalData'] = self.originalData

        if self.playUrl:
            ret['playUrl'] = self.playUrl
        else:
            ret['playUrl'] = self.GetVideoPlayUrl()

        return ret

    def LoadFromJson(self, json):
        if 'playlistid' in json     : self.playlistid     = autostr(json['playlistid'])
        if 'pid' in json            : self.pid            = autostr(json['pid'])
        if 'vid' in json            : self.vid            = autostr(json['vid'])
        if 'cid' in json            : self.cid            = autoint(json['cid'])

        if 'highVid' in json        : self.highVid        = autostr(json['highVid'])
        if 'norVid' in json         : self.norVid         = autostr(json['norVid'])
        if 'oriVid' in json         : self.oriVid         = autostr(json['oriVid'])
        if 'superVid' in json       : self.superVid       = autostr(json['superVid'])
        if 'relativeId' in json     : self.relativeId     = autostr(json['relativeId'])

        if 'order' in json          : self.order          = autoint(json['order'])
        if 'name' in json           : self.name           = json['name']
        if 'videoName' in json      : self.name           = json['videoName']
        if 'playLength' in json     : self.playLength     = json['playLength']
        if 'showName' in json       : self.showName       = json['showName']
        if 'publishTime' in json    : self.publishTime    = json['publishTime']
        if 'videoDesc' in json      : self.videoDesc      = json['videoDesc']
        if 'isHigh' in json         : self.isHigh         = autoint(json['isHigh'])
        if 'videoPlayCount' in json : self.videoPlayCount = json['videoPlayCount']
        if 'videoScore' in json     : self.videoScore     = json['videoScore']
        if 'largePicUrl' in json    : self.largePicUrl    = json['largePicUrl']
        if 'smallPicUrl' in json    : self.smallPicUrl    = json['smallPicUrl']
        if 'originalData' in json   : self.originalData   = json['originalData']

class AlbumBase:
    def __init__(self, engine):
        self.engine = engine
        self.command = engine.command
        self.VideoClass = VideoBase
        self.cid = 0

        self.engineList = []
        self.engineList.append(engine.engine_name)

        self.sources = {}        # 直接节目    [*]
        self.albumName = ''      # 名称       [*]
        self.enAlbumName = ''    # 英文名称    [*]
        self.albumPageUrl = ''
        self.pid = ''
        self.playlistid = ''
        self.vid = ''             #           [*]
        self.area = ''            # 地区       [*]
        self.categories  = []     # 类型       [*]
        self.publishYear = ''     # 发布年份    [*]
        self.isHigh      = 0      # 是否是高清  [*]

        self.largePicUrl = ''     # 大图片网址  [*]
        self.smallPicUrl = ''     # 小图片网址  [*]
        self.largeHorPicUrl = ''  # [*]
        self.smallHorPicUrl = ''  # [*]
        self.largeVerPicUrl = ''  # [*]
        self.smallVerPicUrl = ''  # [*]

        self.playLength = 0.0     # [*]
        self.publishTime = ''     # [*]
        self.updateTime = 0       # [*]

        self.albumDesc = ''       # [*]
        self.videoScore = ''      # [*]

        self.totalSet        = 0  # 总集数      [*]
        self.updateSet       = 0  # 当前更新集   [*]
        self.dailyPlayNum    = 0  # 每日播放次数 [*]
        self.weeklyPlayNum   = 0  # 每周播放次数 [*]
        self.monthlyPlayNum  = 0  # 每月播放次数 [*]
        self.totalPlayNum    = 0  # 总播放次数   [*]
        self.dailyIndexScore = 0  # 每日指数    [*]

        self.mainActors = []      # [*]
        self.directors = []       # [*]

        self.videos = []

    def SaveToJson(self):
        ret = {}
        if self.cid             : ret['cid']            = self.cid
        if self.vid             : ret['vid']            = self.vid
        if self.playlistid      : ret['playlistid']     = self.playlistid
        if self.engineList      : ret['engineList']     = self.engineList

        if self.albumName       : ret['albumName']      = self.albumName
        if self.albumPageUrl    : ret['albumPageUrl']   = self.albumPageUrl
        if self.pid             : ret['pid']            = self.pid
        if self.isHigh          : ret['isHigh']         = self.isHigh

        if self.area            : ret['area']           = self.area
        if self.categories      : ret['categories']     = self.categories
        if self.publishYear     : ret['publishYear']    = self.publishYear

        if self.albumDesc       : ret['albumDesc']      = self.albumDesc
        if self.videoScore      : ret['videoScore']     = self.videoScore
        if self.totalSet        : ret['totalSet']       = self.totalSet
        if self.updateSet       : ret['updateSet']      = self.updateSet

        # 图片
        if self.largeHorPicUrl  : ret['largeHorPicUrl'] = self.largeHorPicUrl
        if self.smallHorPicUrl  : ret['smallHorPicUrl'] = self.smallHorPicUrl
        if self.largeVerPicUrl  : ret['largeVerPicUrl'] = self.largeVerPicUrl
        if self.smallVerPicUrl  : ret['smallVerPicUrl'] = self.smallVerPicUrl
        if self.largePicUrl     : ret['largePicUrl']    = self.largePicUrl
        if self.smallPicUrl     : ret['smallPicUrl']    = self.smallPicUrl

        if self.mainActors      : ret['mainActors']     = self.mainActors
        if self.directors       : ret['directors']      = self.directors

        if self.playLength :      ret['playLength']     = self.playLength
        if self.publishTime :     ret['publishTime']    = self.publishTime
        if self.updateTime :      ret['updateTime']     = self.updateTime

        if self.dailyPlayNum :    ret['dailyPlayNum']   = self.dailyPlayNum     # 每日播放次数
        if self.weeklyPlayNum :   ret['weeklyPlayNum']  = self.weeklyPlayNum    # 每周播放次数
        if self.monthlyPlayNum :  ret['monthlyPlayNum'] = self.monthlyPlayNum   # 每月播放次数
        if self.totalPlayNum :    ret['totalPlayNum']   = self.totalPlayNum     # 总播放资料
        if self.dailyIndexScore : ret['dailyIndexScore']= self.dailyIndexScore  # 每日指数

        if self.sources :         ret['sources']        = self.sources

        return ret

    def LoadFromJson(self, json):
        # From DataBase
        if 'cid' in json            : self.cid             = json['cid']
        if 'albumName' in json      : self.albumName       = json['albumName']
        if 'engineList' in json     : self.engineList      = json['engineList']

        if 'pid' in json            : self.pid             = autostr(json['pid'])
        if 'playlistid' in json     : self.playlistid      = autostr(json['playlistid'])
        if 'vid' in json            : self.vid             = autostr(json['vid'])

        if 'albumPageUrl' in json   : self.albumPageUrl    = json['albumPageUrl']

        if 'isHigh' in json         : self.isHigh          = json['isHigh']

        if 'area' in json           : self.area            = json['area']
        if 'categories' in json     : self.categories      = json['categories']
        if 'publishYear' in json    : self.publishYear     = json['publishYear']

        if 'playLength' in json     : self.playLength      = json['playLength']
        if 'publishTime' in json    : self.publishTime     = json['publishTime']
        if 'updateTime' in json     : self.updateTime      = json['updateTime']

        # 图片
        if 'largeHorPicUrl' in json : self.largeHorPicUrl  = json['largeHorPicUrl']
        if 'smallHorPicUrl' in json : self.smallHorPicUrl  = json['smallHorPicUrl']
        if 'largeVerPicUrl' in json : self.largeVerPicUrl  = json['largeVerPicUrl']
        if 'smallVerPicUrl' in json : self.smallVerPicUrl  = json['smallVerPicUrl']
        if 'largePicUrl' in json    : self.largePicUrl     = json['largePicUrl']
        if 'smallPicUrl' in json    : self.smallPicUrl     = json['smallPicUrl']

        if 'albumDesc' in json      : self.albumDesc       = json['albumDesc']
        if 'videoScore' in json     : self.videoScore      = json['videoScore']
        if 'totalSet' in json       : self.totalSet        = json['totalSet']
        if 'updateSet' in json      : self.updateSet       = json['updateSet']

        if 'mainActors' in json     : self.mainActors      = json['mainActors']
        if 'directors' in json      : self.directors       = json['directors']

        if 'dailyPlayNum' in json   : self.dailyPlayNum    = json['dailyPlayNum']    # 每日播放次数
        if 'weeklyPlayNum' in json  : self.weeklyPlayNum   = json['weeklyPlayNum']   # 每周播放次数
        if 'monthlyPlayNum' in json : self.monthlyPlayNum  = json['monthlyPlayNum']  # 每月播放次数
        if 'totalPlayNum' in json   : self.totalPlayNum    = json['totalPlayNum']    # 总播放资料
        if 'dailyIndexScore' in json: self.dailyIndexScore = json['dailyIndexScore'] # 每日指数

        if 'sources' in json        : self.sources         = json['sources']

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        pass

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        pass

    # 更新节目主页
    def UpdateAlbumPageCommand(self):
        pass

    # 更新节目播放信息
    def UpdateAlbumPlayInfoCommand(self):
        pass

# 一级分类菜单
class VideoMenuBase:
    def __init__(self, name, engine):
        self.engine = engine
        self.command = engine.command
        self.filter = {}
        self.quickFilter = {}
        self.sort = {}
        self.name = name
        self.homePage = ''
        self.parserList = {}
        self.albumClass = AlbumBase
        self.cid = 0

    def CheckQuickFilter(self, argument):
        if 'quickFilter' in argument:
            qf = GetQuickFilter(self.name, self.quickFilter)

            name = argument['quickFilter']
            if name in qf:
                js = qf[name]
                if 'filter' in js:
                    argument['filter'] = js['filter']
                if 'sort' in js:
                    argument['sort'] = js['sort']
            del argument['quickFilter']

    def GetQuickFilterJson(self):
        return [x for x in self.quickFilter]

    def GetFilterJson(self):
        ret = {}
        for k,v in list(self.filter.items()):
            ret[k] = [x for x in v]

        return ret

    def GetSortJson(self):
        ret = []
        for k in self.sort:
            ret.append(k)

        return ret

    def GetJsonInfo(self):
        ret = {}

        ret['name']         = self.name
        ret['cid']          = self.cid
        ret['count']        = self.engine.db.GetMenuAlbumCount(self.cid)
        ret['filter']       = self.GetFilterJson()
        ret['quickFilters'] = self.GetQuickFilterJson()
        ret['sort']         = self.GetSortJson()

        return ret

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        pass

    # 更新热门节目表
    def UpdateHotList(self):
        pass

    # 得到真实播放地址
    def GetRealPlayer(self, text, definition, step, url=''):
        return ''

class VideoEngine:
    def __init__(self, db, command):
        self.engine_name = 'EngineBase'
        self.config = configparser.ConfigParser()

        self.albumClass = AlbumBase
        self.videoClass = VideoBase
        self.db = db
        self.command = command
        self.parserList = {}

    def NewVideo(self, js=None):
        return self.videoClass(js)

    def NewAlbum(self, js=None):
        album = self.albumClass(self)
        if js and album:
            album.LoadFromJson(js)

        return album

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self, MenuList):
        for m, cls in list(self.menu.items()):
            if cls:
                MenuList[m] = cls(m, self)

    # 解析菜单网页解析
    def ParserHtml(self, js):
        name = js['name']
        if name in self.parserList:
            return self.parserList[name](js)
        return None

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid='', albumName='', albumPageUrl='', vid='', auto=False):
        tv = None
        json = self.db.FindAlbumJson(playlistid, albumName, albumPageUrl, vid, auto)
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)

        if tv:
            if playlistid   : tv.playlistid   = playlistid
            if albumName    : tv.albumName    = albumName
            if albumPageUrl : tv.albumPageUrl = albumPageUrl

        return tv

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")

    # 更新所有节目的完全信息
    def UpdateAllFullInfo(self):
        print("UpdateAllFullInfo")

    # 更新所有节目的播放信息
    def UpdateAllPlayInfo(self):
        print("UpdateAllPlayInfo")

    # 更新所有节目主页
    def UpdateAllAlbumPage(self):
        print("UpdateAllAlbumPage")

    # 更新热门节目信息
    def UpdateAllHotList(self):
        print("UpdateAllHotList")

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        print("UpdateAllAlbumList")
