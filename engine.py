#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import traceback
import sys
import json
from utils.fetchTools import fetch_httplib2 as fetch
from pymongo import Connection
import ConfigParser

logging.basicConfig()
log = logging.getLogger("crawler")

COMMAND_HOST = 'http://127.0.0.1:9990/video/addcommand'
PARSER_HOST = 'http://127.0.0.1:9991/video/upload'

# 命令管理器
class Commands:
    def __init__(self, host):
        self.cmdlist = {}
        self.urlmap = {}
        self.commandHost = host

        self.con = Connection('localhost', 27017)
        self.db = self.con.kola
        self.map_table = self.db.urlmap

        maps = self.map_table.find()
        for url in maps:
            self.AddUrlMap(url['source'], url['dest'])

        #self.AddUrlMap('http://tv.sohu.com/s2011/fengsheng/', 'http://tv.sohu.com/20121109/n268282527.shtml')
        #self.AddUrlMap('http://tv.sohu.com/s2011/nrb/', 'http://tv.sohu.com/20111023/n323122692.shtml')

    def AddUrlMap(self, oldurl, newurl):
        self.urlmap[oldurl] = newurl
        self.map_table.update({'source': oldurl}, {"$set" : {'dest': newurl}}, upsert=True, multi=True)

    def GetUrl(self, url):
        if self.urlmap.has_key(url):
            print "Map: %s --> %s" % (url, self.urlmap[url])
            return self.urlmap[url]
        else:
            return url

    # 注册解析器
    def AddTemplate(self, m):
        self.cmdlist[m['name']] = m

    def SendCommand(self, name, menu, url, *private_data):
        if self.cmdlist.has_key(name):
            #print "Add Command: ", url
            cmd = self.cmdlist[name]
            cmd['source'] = self.GetUrl(url)
            cmd['menu'] = menu
            if private_data:
                cmd['privdate_data'] = private_data
            _, _, _, response = fetch(self.commandHost + '?' + name, 'POST', json.dumps(cmd))
            return response == ""
        return False

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

    # 获得播放视频源列表，返回m3u8
    def GetRealUrl(self, playurl):
        return ""

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

        if self.albumName != ''   : ret['albumName'] = self.albumName
        if self.albumPageUrl != '': ret['albumPageUrl'] = self.albumPageUrl
        if self.pid != ''         : ret['pid'] = self.pid
        if self.vid != ''         : ret['vid'] = self.vid
        if self.playlistid != ''  : ret['playlistid'] = self.playlistid
        if self.isHigh != ''      : ret['isHigh'] = self.isHigh

        if self.area != ''        : ret['area'] = self.area
        if self.categories != []  : ret['categories'] = self.categories
        if self.publishYear != '' : ret['publishYear'] = self.publishYear

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
        if self.actors != []         : ret['actors'] = self.actors
        if self.directors != []      : ret['directors'] = self.directors

        ret['index'] = {
            'dailyPlayNum'  : self.dailyPlayNum,     # 每日播放次数
            'weeklyPlayNum' : self.weeklyPlayNum,    # 每周播放次数
            'monthlyPlayNum': self.monthlyPlayNum,   # 每月播放次数
            'totalPlayNum'  : self.totalPlayNum,     # 总播放资料
            'totalPlayNum'  : self.dailyIndexScore,  # 每日指数
        }

        return ret

    def LoadFromJson(self, json):
        # From DataBase
        if json.has_key('vid')            : self.vid = autostr(json['vid'])
        if json.has_key('cid')            : self.cid = json['cid']
        if json.has_key('albumName')      : self.albumName = json['albumName']

        if json.has_key('albumPageUrl') and json['albumPageUrl'] != '':
            self.albumPageUrl = json['albumPageUrl']

        if json.has_key('pid'):
                self.pid = autostr(json['pid'])
        elif json.has_key('PId'):
                self.pid = autostr(json['PId'])

        if json.has_key('playlist_id'):
            self.playlistid = autostr(json['playlist_id'])
        elif json.has_key('playlistid'):
            self.playlistid = autostr(json['playlistid'])

        if json.has_key('isHigh')         : self.isHigh = json['isHigh']

        if json.has_key('area')           : self.area = json['area']
        if json.has_key('categories')     : self.categories = json['categories']
        if json.has_key('publishYear')    : self.publishYear = json['publishYear']

        if json.has_key('defaultPageUrl') : self.defaultPageUrl = json['defaultPageUrl']

        # 图片
        if json.has_key('largeHorPicUrl') : self.largeHorPicUrl = json['largeHorPicUrl']
        if json.has_key('smallHorPicUrl') : self.smallHorPicUrl = json['smallHorPicUrl']
        if json.has_key('largeVerPicUrl') : self.largeVerPicUrl = json['largeVerPicUrl']
        if json.has_key('smallVerPicUrl') : self.smallVerPicUrl = json['smallVerPicUrl']

        if json.has_key('albumDesc')      : self.albumDesc = json['albumDesc']
        if json.has_key('videoScore')     : self.videoScore = json['videoScore']
        if json.has_key('totalSet')       : self.totalSet = json['totalSet']

        if json.has_key('mainActors')     : self.mainActors = json['mainActors']
        if json.has_key('actors')         : self.actors = json['actors']
        if json.has_key('directors')      : self.directors = json['directors']

        if json.has_key('index'):
            index = json['index']
            if index:
                if index.has_key('dailyPlayNum')   : self.dailyPlayNum    = index['dailyPlayNum']    # 每日播放次数
                if index.has_key('weeklyPlayNum')  : self.weeklyPlayNum   = index['weeklyPlayNum']   # 每周播放次数
                if index.has_key('monthlyPlayNum') : self.monthlyPlayNum  = index['monthlyPlayNum']  # 每月播放次数
                if index.has_key('totalPlayNum')   : self.totalPlayNum    = index['totalPlayNum']    # 总播放资料
                if index.has_key('dailyIndexScore'): self.dailyIndexScore = index['dailyIndexScore'] # 每日指数

        # 如果有视频数据
        if json.has_key('videos'):
            self.videos = []
            for v in json['videos']:
                video = self.VideoClass(v)
                self.videos.append(video)
            del json['videos']
        self.data.update(json)

    # 发送节目信息更新命令
    def UpdateAllCommand(self):
        pass

    def SaveToDB(self, db):
        if self.albumName != "" and self.albumPageUrl != "":
            js = self.SaveToJson()
            db.update({'albumName': self.albumName},
                      {"$set" : js},
                      upsert=True, multi=True)

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
            page = arg['page']
            size = arg['size']

            _filter = {}
            _filter['cid'] = self.cid
            if arg.has_key('filter'):
                _filter.update(arg['filter'])

            if arg.has_key('fields'):
                fields = arg['fields']
            else:
                fields = None

            cursor = self.engine.album_table.find(_filter, fields = fields)

            if arg.has_key('sort'):
                cursor = cursor.sort(arg['sort'])

            for x in cursor.skip( page * size).limit(size):
                del x['_id']
                ret.append(x)
        except:
            pass

        return ret

    # 更新该菜单下所有节目完全信息
    def UpdateAllAlbumFullInfo(self):
        pgs = self.engine.album_table.find({'cid': self.cid},
                                                    fields = {'albumName': True,
                                                              'albumPageUrl': True,
                                                              'PId': True,
                                                              'vid': True,
                                                              'playlistid': True}
                                                    )
        for p in pgs:
            album = self.albumClass(self)
            album.LoadFromJson(p)
            album.UpdateAllCommand()

    # 更新热门节目表
    def UpdateHotList(self):
        self.HotList = []
        self.engine.UpdateHotList(self)

    # 更新本菜单节目网址，并提交命令服务器
    def UploadAlbumList(self):
        pass

    # 解析菜单网页解析
    def ParserHtml(self, name, js):
        ret = []
        if self.parserList.has_key(name):
            ret = self.parserList[name](js)

        return ret

    def GetAlbum(self, playlistid = '', albumName = '', albumPageUrl= '', auto = False):
        tv = None
        f = {}
        if playlistid != '':
            f['playlistid'] = playlistid
        if albumName != '':
            f['albumName'] = albumName
        if albumPageUrl != '':
            f['albumPageUrl'] = albumPageUrl

        json = self.engine.album_table.find_one({"#or" : f})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)
            tv.playlistid = playlistid
            tv.albumName = albumName
            tv.albumPageUrl = albumPageUrl

        return tv

    # 根据 ID 从数据库中加载节目
    def GetAlbumById(self, playlistid, auto = False):
        tv = None
        if type(playlistid) == int:
            playlistid = str(playlistid)
        json = self.engine.album_table.find_one({'playlistid': playlistid})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)
            tv.playlistid = playlistid

        return tv

    def GetAlbumByUrl(self, url, auto = False):
        tv = None
        json = self.engine.album_table.find_one({'albumPageUrl': url})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)
            tv.albumPageUrl = url

        return tv

    def GetAlbumByName(self, albumName, auto = False):
        tv = None
        json = self.engine.album_table.find_one({'albumName': albumName})
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)
            tv.albumName = albumName

        return tv

class VideoEngine:
    def __init__(self):
        self.engine_name = 'EngineBase'
        self.config = ConfigParser.ConfigParser()
        self.cmd_host = COMMAND_HOST
        self.parser_host = PARSER_HOST
        try:
            self.config.read("/etc/engine.conf")
            if self.config.has_section('global'):
                if self.config.has_option('global', 'command_host'):
                    host = self.config.get('global', 'command_host')
                    if host != '':
                        self.cmd_host = host

                if self.config.has_option('global', 'parser_host'):
                    host = self.config.get('global', 'parser_host')
                    if host == '':
                        self.parser_host = host
        except:
            t, v, tb = sys.exc_info()
            log.error("VideoEngine.__init__:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        self.command = Commands(self.cmd_host)
        self.con = Connection('localhost', 27017)
        self.db = self.con.kola
        self.album_table = self.db.album

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self, times = 0):
        return []

    # 生成所有分页网址, 返回网址列表
    def GetHtmlList(self, playurl, times = 0):
        return []

    # 获取真实播放节目源地址
    def GetRealPlayUrl(self, playurl, times = 0):
        return []

    # 更新一级菜单首页热门节目表
    def UpdateHotList(self, menu, times = 0):
        pass

    # 获取节目的播放列表
    def GetAlbumPlayList(self, album, times = 0):
        pass

    # 将 BeautifulSoup的节目 tag 转成节目单
    def ParserAlbum(self, tag, album):
        return False

