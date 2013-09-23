#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import logging
import json
import configparser
import tornado.escape
import redis
from pymongo import Connection

logging.basicConfig()
log = logging.getLogger("crawler")

# 命令管理器
class Commands:
    def __init__(self):
        self.cmdlist = {}
        self.urlmap = {}
        self.pipe = None

        self.con = Connection('localhost', 27017)
        self.db = self.con.kola
        self.map_table = self.db.urlmap
        self.db = redis.Redis(host='127.0.0.1', port=6379, db=1)

        maps = self.map_table.find()
        for url in maps:
            self.AddUrlMap(url['source'], url['dest'])

        # self.AddUrlMap('http://tv.sohu.com/s2011/fengsheng/', 'http://tv.sohu.com/20121109/n268282527.shtml')
        # self.AddUrlMap('http://tv.sohu.com/s2011/nrb/', 'http://tv.sohu.com/20111023/n323122692.shtml')

    def AddUrlMap(self, oldurl, newurl):
        self.urlmap[oldurl] = newurl
        self.map_table.update({'source': oldurl}, {"$set" : {'dest': newurl}}, upsert=True, multi=True)

    def GetUrl(self, url):
        if url in self.urlmap:
            print(("Map: %s --> %s" % (url, self.urlmap[url])))
            return self.urlmap[url]
        else:
            return url

    # 注册解析器
    def AddTemplate(self, m):
        self.cmdlist[m['name']] = m

    def AddCommand(self, name, menu, url, *private_data):
        if name in self.cmdlist:
            # print("Add Command: ", url)
            cmd = self.cmdlist[name]
            cmd['source'] = self.GetUrl(url)
            cmd['menu'] = menu
            if private_data:
                cmd['privdate_data'] = private_data
            if self.pipe == None:
                self.pipe = self.db.pipeline()
            self.pipe.rpush('command', json.dumps(cmd))
        return self

    def Execute(self):
        if self.pipe:
            self.pipe.execute()
            self.pipe = None

    def GetCommandNext(self):
        cmd = self.db.lpop('command')
        if cmd:
            return tornado.escape.json_decode(cmd)

        return None

def autostr(i):
    if type(i) == int:
        return str(i)
    else:
        return i

# 每个 Video 表示一个可以播放视频
class VideoBase:
    def __init__(self):
        self.data = {
            "smallPicUrl": "http://photocdn.sohu.com/20121119/vrss671283.jpg",
            "name": "十诫",
            "vid": 871321,
            "singerName": "",
            "playLength": 5749.6,
            "largePicUrl": "http://photocdn.sohu.com/20121119/vrsb671283.jpg",
            "publishTime": "2013-08-28",
            "pageUrl": "http://tv.sohu.com/20130828/n385287051.shtml",
            "subName": "",
            "singerIds": "",
            "order": "1",
            "showName": "十诫",
            "showDate": ""
        }
        self.vid = ""

# 一个节目，表示一部电影、电视剧集
class AlbumBase:
    def __init__(self, parent):
        self.parent = parent
        self.command = parent.command
        self.VideoClass = VideoBase
        self.cid = parent.cid

        self.albumName = ""
        self.albumPageUrl = ""
        self.pid = ""
        self.vid = ""
        self.playlistid  = ""
        self.area = ""            # 地区
        self.categories = []      # 类型
        self.publishYear = ""     # 发布年份
        self.isHigh      = 0      # 是否是高清

        self.largePicUrl = ""     # 大图片网址
        self.smallPicUrl = ""     # 小图片网址
        self.largeHorPicUrl = ''
        self.smallHorPicUrl = ''
        self.largeVerPicUrl = ''
        self.smallVerPicUrl = ''

        self.playLength = 0.0
        self.publishTime = ''

        self.albumDesc = ""
        self.videoScore = ""

        self.defaultPageUrl  = "" # 当前播放集
        self.filmType        = "" # "TV" or ""
        self.totalSet        = "" # 总集数
        self.updateSet       = "" # 当前更新集
        self.dailyPlayNum    = 0  # 每日播放次数
        self.weeklyPlayNum   = 0  # 每周播放次数
        self.monthlyPlayNum  = 0  # 每月播放次数
        self.totalPlayNum    = 0  # 总播放资料
        self.dailyIndexScore = 0  # 每日指数

        self.mainActors = []
        self.actors = []
        self.directors = []

        self.data = {}
        self.videos = []

    def SaveToJson(self):
        ret = {}
        ret['cid'] = self.cid

        url = self.GetVideoPlayUrl()
        if url != '':
            ret['videoPlayUrl'] = url

        if self.playlistid != ''     : ret['playlistid'] = self.playlistid
        if self.albumName != ''      : ret['albumName'] = self.albumName
        if self.albumPageUrl != ''   : ret['albumPageUrl'] = self.albumPageUrl
        if self.pid != ''            : ret['pid'] = self.pid
        if self.vid != ''            : ret['vid'] = self.vid
        if self.isHigh != ''         : ret['isHigh'] = self.isHigh

        if self.area != ''           : ret['area'] = self.area
        if self.categories != []     : ret['categories'] = self.categories
        if self.publishYear != ''    : ret['publishYear'] = self.publishYear

        if self.defaultPageUrl != '' : ret['defaultPageUrl'] = self.defaultPageUrl
        if self.albumDesc != ''      : ret['albumDesc'] = self.albumDesc
        if self.videoScore != ''     : ret['videoScore'] = self.videoScore
        if self.totalSet != ""       : ret['totalSet'] = self.totalSet
        if self.updateSet != ""      : ret['updateSet'] = self.updateSet

        # 图片
        if self.largeHorPicUrl != '' : ret['largeHorPicUrl'] = self.largeHorPicUrl
        if self.smallHorPicUrl != '' : ret['smallHorPicUrl'] = self.smallHorPicUrl
        if self.largeVerPicUrl != '' : ret['largeVerPicUrl'] = self.largeVerPicUrl
        if self.smallVerPicUrl != '' : ret['smallVerPicUrl'] = self.smallVerPicUrl

        if self.mainActors != []     : ret['mainActors'] = self.mainActors
        if self.actors != []         : ret['actors']     = self.actors
        if self.directors != []      : ret['directors']  = self.directors

        ret['playLength'] = self.playLength
        ret['publishTime'] = self.publishTime

        ret['dailyPlayNum']   = self.dailyPlayNum     # 每日播放次数
        ret['weeklyPlayNum']  = self.weeklyPlayNum    # 每周播放次数
        ret['monthlyPlayNum'] = self.monthlyPlayNum   # 每月播放次数
        ret['totalPlayNum']   = self.totalPlayNum     # 总播放资料
        ret['dailyIndexScore']= self.dailyIndexScore  # 每日指数

        return ret

    def LoadFromJson(self, json):
        # From DataBase
        if 'vid' in json            : self.vid = autostr(json['vid'])
        if 'cid' in json            : self.cid = json['cid']
        if 'albumName' in json      : self.albumName = json['albumName']

        if 'albumPageUrl' in json and json['albumPageUrl'] != '':
            self.albumPageUrl = json['albumPageUrl']

        if 'pid' in json:
                self.pid = autostr(json['pid'])
        elif 'PId' in json:
                self.pid = autostr(json['PId'])

        if 'playlist_id' in json:
            self.playlistid = autostr(json['playlist_id'])
        elif 'playlistid' in json:
            self.playlistid = autostr(json['playlistid'])

        if 'isHigh' in json         : self.isHigh = json['isHigh']

        if 'area' in json           : self.area = json['area']
        if 'categories' in json     : self.categories = json['categories']
        if 'publishYear' in json    : self.publishYear = json['publishYear']

        if 'defaultPageUrl' in json : self.defaultPageUrl = json['defaultPageUrl']

        if 'playLength' in json : self.playLength = json['playLength']
        if 'publishTime' in json : self.publishTime = json['publishTime']

        # 图片
        if 'largeHorPicUrl' in json : self.largeHorPicUrl = json['largeHorPicUrl']
        if 'smallHorPicUrl' in json : self.smallHorPicUrl = json['smallHorPicUrl']
        if 'largeVerPicUrl' in json : self.largeVerPicUrl = json['largeVerPicUrl']
        if 'smallVerPicUrl' in json : self.smallVerPicUrl = json['smallVerPicUrl']

        if 'albumDesc' in json      : self.albumDesc = json['albumDesc']
        if 'videoScore' in json     : self.videoScore = json['videoScore']
        if 'totalSet' in json       : self.totalSet = json['totalSet']

        if 'mainActors' in json     : self.mainActors = json['mainActors']
        if 'actors' in json         : self.actors = json['actors']
        if 'directors' in json      : self.directors = json['directors']

        if 'dailyPlayNum' in json   : self.dailyPlayNum    = json['dailyPlayNum']    # 每日播放次数
        if 'weeklyPlayNum' in json  : self.weeklyPlayNum   = json['weeklyPlayNum']   # 每周播放次数
        if 'monthlyPlayNum' in json : self.monthlyPlayNum  = json['monthlyPlayNum']  # 每月播放次数
        if 'totalPlayNum' in json   : self.totalPlayNum    = json['totalPlayNum']    # 总播放资料
        if 'dailyIndexScore' in json: self.dailyIndexScore = json['dailyIndexScore'] # 每日指数

        self.data.update(json)

    def SaveToDB(self, db):
        if self.albumName != "" and self.albumPageUrl != "":
            js = self.SaveToJson()
            db.update({'albumName': self.albumName},
                      {"$set" : js},
                      upsert=True, multi=True)

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

    # 得到节目的地址
    def GetVideoPlayUrl(self):
        pass

# 一级分类菜单
class VideoMenuBase:
    def __init__(self, name, engine, url):
        self.command = engine.command
        self.filter = {}
        self.name = name
        self.url = url
        self.HotList = []
        self.engine = engine
        self.parserList = {}
        self.albumClass = AlbumBase
        self.cid = 0

    def GetFilterJson(self):
        pass

    def GetSortJson(self):
        pass

    def GetJsonInfo(self):
        ret = {}

        ret['name'] = self.name
        ret['cid'] = self.cid
        ret['count'] = self.engine.album_table.find({'cid': self.cid}).count()
        ret['filter'] = self.GetFilterJson()
        ret['sort'] = self.GetSortJson()

        return ret

    def ConvertFilterJson(self, f):
        return f

    def ConvertSortJson(self, f):
        return f

    def Reset(self):
        self.HotList = []

    # 得到节目列表
    # arg参数：
    # {
    #    "page" : 0,
    #    "size" : 20,
    #    "filter" : {                 # 过滤字段
    #        "cid":2,
    #        "playlistid":"123123",
    #    },
    #    "fields" : {                 # 显示字段
    #        "albumName" : True,
    #        "playlistid" : True
    #    },
    #    "sort" : {                   # 排序字段
    #        "albumName": 1,
    #        "vid": -1
    #    }
    def GetAlbumList(self, arg):
        ret = []
        try:
            _filter = {}
            _filter['cid']        = self.cid
            _filter['playlistid'] = {'$exists' : True}
            _filter['vid']        = {'$exists' : True}
            if 'filter' in arg:
                f = self.ConvertFilterJson(arg['filter'])
                _filter.update(f)

            if 'fields' in arg:
                fields = arg['fields']
            else:
                fields = None

            cursor = self.engine.album_table.find(_filter, fields = fields)

            if 'sort' in arg:
                s = self.ConvertSortJson(arg['sort'])
                if s:
                    cursor = cursor.sort(s)

            if 'page' in arg and 'size' in arg:
                page = arg['page']
                size = arg['size']
                cursor = cursor.skip(page * size).limit(size)

            for x in cursor:
                del x['_id']
                ret.append(x)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserHotInfoByIapi  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 更新该菜单下所有节目完全信息
    def UpdateAllFullInfo(self):
        argument = {}
        argument['fields'] = {'albumName': True,
                              'albumPageUrl': True,
                              'PId': True,
                              'vid': True,
                              'playlistid': True}
        pgs = self.GetAlbumList(argument)

        for p in pgs:
            album = self.albumClass(self)
            album.LoadFromJson(p)
            album.UpdateFullInfoCommand()
        self.command.Execute()

    # 更新所有节目的完全信息
    def UpdateAllScore(self):
        argument = {}
        argument['fields'] = {'albumName': True,
                              'albumPageUrl': True,
                              'PId': True,
                              'vid': True,
                              'playlistid': True}
        pgs = self.GetAlbumList(argument)

        for p in pgs:
            album = self.albumClass(self)
            album.LoadFromJson(p)
            album.UpdateScoreCommand()
        self.command.Execute()

    def UpdatePlayInfo(self):
        argument = {}
        argument['fields'] = {'albumName': True,
                              'albumPageUrl': True,
                              'PId': True,
                              'vid': True,
                              'playlistid': True}
        pgs = self.GetAlbumList(argument)

        for p in pgs:
            album = self.albumClass(self)
            album.LoadFromJson(p)
            album.UpdateAlbumPlayInfoCommand()
        self.command.Execute()

    # 更新热门节目表
    def UpdateHotList(self):
        self.HotList = []
        self.engine.UpdateHotList(self)

        # 解析菜单网页解析
    def ParserHtml(self, name, js):
        ret = []
        if name in self.parserList:
            ret = self.parserList[name](js)

        return ret

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid='', albumName='', albumPageUrl='', auto=False):
        playlistid = autostr(playlistid)
        if playlistid == '' and albumName == '' and albumPageUrl == '':
            return None

        tv = None
        f = []
        if playlistid != '':
            f.append({'playlistid' : playlistid})
        if albumName != '':
            f.append({'albumName' : albumName})
        if albumPageUrl != '':
            f.append({'albumPageUrl' : albumPageUrl})

        json = self.engine.album_table.find_one({"$or" : f})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)

        if playlistid != '':
            tv.playlistid = playlistid

        if albumName != '':
            tv.albumName = albumName

        if albumPageUrl != '':
            tv.albumPageUrl = albumPageUrl

        return tv

class VideoEngine:
    def __init__(self):
        self.engine_name = 'EngineBase'
        self.config = configparser.ConfigParser()

        self.command = Commands()
        self.con = Connection('localhost', 27017)
        self.db = self.con.kola
        self.album_table = self.db.album

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self, times=0):
        return []

    # 得到真实播放地址
    def GetRealPlayer(self, text, definition, step):
        return ''
