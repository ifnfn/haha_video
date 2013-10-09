#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback, time
import logging
import json
import configparser
import tornado.escape
import redis
import pymongo

logging.basicConfig()
log = logging.getLogger("crawler")

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
            for _ in range(count):
                cmd = self.db.lpop('command')
                if cmd:
                    ret.append(tornado.escape.json_decode(cmd))
                else:
                    break
            return ret
        return None

def autostr(i):
    if type(i) == int:
        return str(i)
    else:
        return i

def autoint(i):
    if type(i) == str:
        return i and int(i) or 0
    else:
        return i

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
            "videoDesc": "多年以来，雪祭的画面一直在齐远脑海里浮现，可是现实中却不是这个样子，他在心里向安琪道歉，因为安琪是那样全心全意的对待自己，而自己却负了她。家丁向齐远说早安，齐远吩咐他们，要注意的事情一定要注意，有事给自己的打招呼。",
            "isHigh": 1,

            "videoPlayCount": 18435401,
            "videoScore": 9.385957,

            "largePicUrl": "http://photocdn.sohu.com/20130806/vrsb924544.jpg",
            "smallPicUrl": "http://photocdn.sohu.com/20130806/vrss924544.jpg",
            "pageUrl": "http://tv.sohu.com/20130806/n383534504.shtml",
        }
        '''

        self.name = ''
        self.playlistid = 0  # 所属 ablum
        self.pid = 0
        self.vid = 0
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
        self.pageUrl = ''
        if js:
            self.LoadFromJson(js)

    def SaveToJson(self):
        ret = {}

        if self.playlistid      : ret['playlistid'] = self.playlistid
        if self.pid             : ret['pid'] = self.pid
        if self.name            : ret['name'] = self.name
        if self.vid             : ret['vid'] = self.vid
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
        if self.pageUrl         : ret['pageUrl'] = self.pageUrl

        return ret

    def LoadFromJson(self, json):
        if 'playlistid' in json     : self.playlistid = autoint(json['playlistid'])
        if 'pid' in json            : self.pid = autoint(json['pid'])
        if 'vid' in json            : self.vid = autoint(json['vid'])
        if 'name' in json           : self.name = json['name']
        if 'videoName' in json      : self.name = json['videoName']
        if 'order' in json          : self.order = json['order']
        if 'playLength' in json     : self.playLength = json['playLength']
        if 'showName' in json       : self.showName = json['showName']
        if 'publishTime' in json    : self.publishTime = json['publishTime']
        if 'videoDesc' in json      : self.videoDesc = json['videoDesc']
        if 'isHigh' in json         : self.isHigh = json['isHigh']
        if 'videoPlayCount' in json : self.videoPlayCount = json['videoPlayCount']
        if 'videoScore' in json     : self.videoScore = json['videoScore']
        if 'largePicUrl' in json    : self.largePicUrl = json['largePicUrl']
        if 'smallPicUrl' in json    : self.smallPicUrl = json['smallPicUrl']
        if 'pageUrl' in json        : self.pageUrl = json['pageUrl']

# 一个节目，表示一部电影、电视剧集
class AlbumBase:
    def __init__(self, engine):
        self.engine = engine
        self.command = engine.command
        self.VideoClass = VideoBase
        self.cid = 0

        self.albumName = ''
        self.albumPageUrl = ''
        self.pid = 0
        self.playlistid = 0
        self.vid = 0
        self.norVid = 0
        self.highVid = 0
        self.supverVid = 0
        self.oriVid = 0
        self.relativeId = 0
        self.area = ''            # 地区
        self.categories  = []     # 类型
        self.publishYear = ''     # 发布年份
        self.isHigh      = 0      # 是否是高清

        self.largePicUrl = ''     # 大图片网址
        self.smallPicUrl = ''     # 小图片网址
        self.largeHorPicUrl = ''
        self.smallHorPicUrl = ''
        self.largeVerPicUrl = ''
        self.smallVerPicUrl = ''

        self.playLength = 0.0
        self.publishTime = ''
        self.updateTime = 0
        self.videoPlayUrl = ''

        self.albumDesc = ''
        self.videoScore = ''

        self.defaultPageUrl  = '' # 当前播放集
        self.filmType        = '' # "TV" or ""
        self.totalSet        = 0  # 总集数
        self.updateSet       = 0  # 当前更新集
        self.dailyPlayNum    = 0  # 每日播放次数
        self.weeklyPlayNum   = 0  # 每周播放次数
        self.monthlyPlayNum  = 0  # 每月播放次数
        self.totalPlayNum    = 0  # 总播放资料
        self.dailyIndexScore = 0  # 每日指数

        self.mainActors = []
        self.actors = []
        self.directors = []

        self.videos = []

    def SaveToJson(self):
        ret = {}
        if self.cid :        ret['cid'] = self.cid
        if self.playlistid : ret['playlistid'] = self.playlistid
        if self.vid :        ret['vid'] = self.vid
        if self.norVid :     ret['norVid'] = self.norVid
        if self.highVid :    ret['highVid'] = self.highVid
        if self.supverVid :  ret['supverVid'] = self.supverVid
        if self.oriVid :     ret['oriVid'] = self.oriVid
        if self.relativeId:  ret['relativeId'] = self.relativeId

        url = self.GetVideoPlayUrl()
        if url != '':
            ret['videoPlayUrl'] = url

        if self.albumName       : ret['albumName']      = self.albumName
        if self.albumPageUrl    : ret['albumPageUrl']   = self.albumPageUrl
        if self.pid             : ret['pid']            = self.pid
        if self.isHigh          : ret['isHigh']         = self.isHigh

        if self.area            : ret['area']           = self.area
        if self.categories      : ret['categories']     = self.categories
        if self.publishYear     : ret['publishYear']    = self.publishYear

        if self.defaultPageUrl  : ret['defaultPageUrl'] = self.defaultPageUrl
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
        if self.actors          : ret['actors']         = self.actors
        if self.directors       : ret['directors']      = self.directors

        if self.playLength :      ret['playLength']     = self.playLength
        if self.publishTime :     ret['publishTime']    = self.publishTime
        if self.updateTime :      ret['updateTime']     = self.updateTime

        if self.dailyPlayNum :    ret['dailyPlayNum']   = self.dailyPlayNum     # 每日播放次数
        if self.weeklyPlayNum :   ret['weeklyPlayNum']  = self.weeklyPlayNum    # 每周播放次数
        if self.monthlyPlayNum :  ret['monthlyPlayNum'] = self.monthlyPlayNum   # 每月播放次数
        if self.totalPlayNum :    ret['totalPlayNum']   = self.totalPlayNum     # 总播放资料
        if self.dailyIndexScore : ret['dailyIndexScore']= self.dailyIndexScore  # 每日指数

        return ret

    def LoadFromJson(self, json):
        # From DataBase
        if 'cid' in json            : self.cid        = json['cid']
        if 'albumName' in json      : self.albumName  = json['albumName']

        if 'pid' in json            : self.pid        = autoint(json['pid'])
        if 'playlistid' in json     : self.playlistid = autoint(json['playlistid'])
        if 'vid' in json            : self.vid        = autoint(json['vid'])

        if 'norVid' in json         : self.norVid     = autoint(json['norVid'])
        if 'highVid' in json        : self.highVid    = autoint(json['highVid'])
        if 'supverVid' in json      : self.supverVid  = autoint(json['supverVid'])
        if 'oriVid' in json         : self.oriVid     = autoint(json['oriVid'])
        if 'relativeId' in json     : self.relativeId = autoint(json['relativeId'])

        if 'videoPlayUrl' in json   : self.videoPlayUrl = json['videoPlayUrl']
        if 'albumPageUrl' in json   : self.albumPageUrl = json['albumPageUrl']

        if 'isHigh' in json         : self.isHigh = json['isHigh']

        if 'area' in json           : self.area = json['area']
        if 'categories' in json     : self.categories  = json['categories']
        if 'publishYear' in json    : self.publishYear = json['publishYear']

        if 'defaultPageUrl' in json : self.defaultPageUrl = json['defaultPageUrl']

        if 'playLength' in json     : self.playLength  = json['playLength']
        if 'publishTime' in json    : self.publishTime = json['publishTime']
        if 'updateTime' in json     : self.updateTime  = json['updateTime']

        # 图片
        if 'largeHorPicUrl' in json : self.largeHorPicUrl = json['largeHorPicUrl']
        if 'smallHorPicUrl' in json : self.smallHorPicUrl = json['smallHorPicUrl']
        if 'largeVerPicUrl' in json : self.largeVerPicUrl = json['largeVerPicUrl']
        if 'smallVerPicUrl' in json : self.smallVerPicUrl = json['smallVerPicUrl']
        if 'largePicUrl' in json    : self.largePicUrl    = json['largePicUrl']
        if 'smallPicUrl' in json    : self.smallPicUrl    = json['smallPicUrl']

        if 'albumDesc' in json      : self.albumDesc  = json['albumDesc']
        if 'videoScore' in json     : self.videoScore = json['videoScore']
        if 'totalSet' in json       : self.totalSet   = json['totalSet']

        if 'actors' in json         : self.actors     = json['actors']
        if 'mainActors' in json     : self.mainActors = json['mainActors']
        if 'directors' in json      : self.directors  = json['directors']

        if 'dailyPlayNum' in json   : self.dailyPlayNum    = json['dailyPlayNum']    # 每日播放次数
        if 'weeklyPlayNum' in json  : self.weeklyPlayNum   = json['weeklyPlayNum']   # 每周播放次数
        if 'monthlyPlayNum' in json : self.monthlyPlayNum  = json['monthlyPlayNum']  # 每月播放次数
        if 'totalPlayNum' in json   : self.totalPlayNum    = json['totalPlayNum']    # 总播放资料
        if 'dailyIndexScore' in json: self.dailyIndexScore = json['dailyIndexScore'] # 每日指数

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
    def __init__(self, name, engine):
        self.engine = engine
        self.command = engine.command
        self.filter = {}
        self.name = name
        self.homePage = ''
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
        ret['count'] = self.engine.db.GetMenuAlbumCount(self.cid)
        ret['filter'] = self.GetFilterJson()
        ret['sort'] = self.GetSortJson()

        return ret

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        pass

    # 更新热门节目表
    def UpdateHotList(self):
        pass

class DB:
    def __init__(self):
        self.con = pymongo.Connection('localhost', 27017)
        self.db = self.con.kola
        self.album_table  = self.db.album
        self.videos_table = self.db.videos
        self.map_table    = self.db.urlmap
        self.album_table.drop_indexes()
#         self.album_table.create_index([('albumPageUrl', pymongo.ASCENDING)])
#         self.album_table.create_index([('vid', pymongo.ASCENDING)])
#         self.album_table.create_index([('cid', pymongo.ASCENDING)])

    def SaveVideo(self, video):
        if video.pid or video.vid or video.playlistid:
            js = video.SaveToJson()
            upert = []
            if video.playlistid:
                upert.append({'playlistid' : video.playlistid})
            if video.pid:
                upert.append({'pid' : video.pid})
            if video.vid:
                upert.append({'vid' : video.vid})

            self.videos_table.update(
                      {'$or' : upert},
                      {'$set' : js},
                      upsert=True, multi=True)

    def SaveAlbum(self, album, key={}, upsert=True):
        album.playlistid = autoint(album.playlistid)
        album.vid        = autoint(album.vid)
        if album.albumName or album.albumPageUrl or album.playlistid or album.vid:
            js = album.SaveToJson()

            if not key:
                if album.vid:
                    key = {'vid' : album.vid}
                elif album.albumPageUrl:
                    key = {'albumPageUrl': album.albumPageUrl}
                elif album.albumName:
                    key = {'albumName': album.albumName}
                elif album.playlistid:
                    key = {'playlistid' : album.playlistid}

            if key:
                self.album_table.update(key,
                                        {"$set" : js},
                                        upsert=upsert, multi=True)

                for v in album.videos:
                    self.SaveVideo(v)

    # 从数据库中找到album
    def FindAlbumJson(self, playlistid=0, albumName='', albumPageUrl='', vid=0, auto=False):
        playlistid = autoint(playlistid)
        vid = autoint(vid)
        if playlistid == 0 and albumName == '' and albumPageUrl == '' and vid == '':
            return None

        f = []
        if playlistid :   f.append({'playlistid'   : playlistid})
        if albumName :    f.append({'albumName'    : albumName})
        if albumPageUrl : f.append({'albumPageUrl' : albumPageUrl})
        if vid :          f.append({'vid'          : vid})

        return self.album_table.find_one({"$or" : f})

    # 得到节目列表
    # arg参数：
    # {
    #    "page" : 0,
    #    "size" : 20,
    #    "filter" : {                 # 过滤字段
    #        "cid":2,
    #        "playlistid":123123,
    #    },
    #    "fields" : {                 # 显示字段
    #        "albumName" : True,
    #        "playlistid" : True
    #    },
    #    "sort" : {                   # 排序字段
    #        "albumName": 1,
    #        "vid": -1
    #    }
    def GetAlbumListJson(self, arg, cid=-1,All=False):
        ret = []
        try:
            _filter = {}
            if cid != -1:
                _filter['cid']        = cid
            if All == False:
                _filter['playlistid'] = {'$ne' : ''}
                _filter['vid']        = {'$ne' : ''}

            if 'filter' in arg:
                _filter.update(arg['filter'])

            if 'fields' in arg:
                fields = arg['fields']
            else:
                fields = None

            cursor = self.album_table.find(_filter, fields = fields)

            if 'sort' in arg:
                cursor = cursor.sort(arg['sort'])

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

    def FindVideoJson(self, playlistid=0, pid=0, vid=0):
        playlistid = autoint(playlistid)
        pid        = autoint(pid)
        vid        = autoint(vid)
        if pid == 0 and vid == 0 and playlistid == 0:
            return None

        f = []
        if playlistid : f.append({'playlistid' : playlistid})
        if pid        : f.append({'pid' : pid})
        if vid        : f.append({'vid' : vid})

        return self.videos_table.find_one({"$or" : f})

    def GetVideoListJson(self, playlistid, pid=0, arg={}):
        ret = []
        playlistid = autoint(playlistid)
        pid        = autoint(pid)
        try:
            _filter = {}
            if pid:
                _filter['pid'] = pid

            if playlistid:
                _filter['playlistid'] = playlistid

            if 'filter' in arg:
                _filter.update(arg['filter'])

            if 'fields' in arg:
                fields = arg['fields']
            else:
                fields = None

            cursor = self.videos_table.find(_filter, fields = fields)

            if 'sort' in arg:
                cursor = cursor.sort(arg['sort'])
            else:
                cursor = cursor.sort([('order', 1)])

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

    def GetMenuAlbumCount(self, cid):
        return self.db.album_table.find({'cid': cid}).count()

class VideoEngine:
    def __init__(self):
        self.fieldMapping = {}
        self.engine_name = 'EngineBase'
        self.config = configparser.ConfigParser()

        self.db = DB()
        self.command = Commands(self.db.map_table)

    def ConvertJson(self, arg):
        if 'filter' in arg:
            arg['filter'] = self._ConvertFilterJson(arg['filter'])
        if 'sort' in arg:
            arg['sort'] = self._ConvertSortJson(arg['sort'])

        return arg

    def _ConvertFilterJson(self, f):
        for key in f:
            if key in self.fieldMapping:
                newkey = self.fieldMapping[key]
                f[newkey] = { "$in" : [f[key]]}
                del f[key]
        return f

    def _ConvertSortJson(self, v):
        if v in self.fieldMapping:
            newkey = self.fieldMapping[v]
            return [(newkey, -1)]
        else:
            return [(v, -1)]

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self, times=0):
        return []

    # 解析菜单网页解析
    def ParserHtml(self, js):
        pass

    # 得到真实播放地址
    def GetRealPlayer(self, text, definition, step):
        return ''

    # 转换 Filter 及 Sort 字段
    def GetAlbumListJson(self, arg, cid=-1,All=False):
        self.ConvertJson(arg)

        return self.db.GetAlbumListJson(arg, cid, All)

    # 从数据库中找到album
    def GetAlbumFormDB(self, playlistid=0, albumName='', albumPageUrl='', vid=0, auto=False):
        tv = None
        json = self.db.FindAlbumJson(playlistid, albumName, albumPageUrl, vid, auto)
        if json:
            tv = self.albumClass(self)
            tv.LoadFromJson(json)
        elif auto:
            tv = self.albumClass(self)

        if tv:
            if playlistid   : tv.playlistid = playlistid
            if albumName    : tv.albumName = albumName
            if albumPageUrl : tv.albumPageUrl = albumPageUrl

        return tv
