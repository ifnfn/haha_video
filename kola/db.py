#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import pymongo
import redis
from .utils import autostr, autoint, log, GetQuickFilter

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
        self.vid = ''
        self.cid = 0

#        self.highVid = ''
#        self.norVid = ''
#        self.oriVid = ''
#        self.superVid = ''
#        self.relativeId = ''

        self.order = -1
        self.playLength = 0.0
        self.showName = ''
        self.publishTime = ''
        self.videoDesc = ''
        self.isHigh = -1
        self.priority = 100

        self.videoPlayCount = 0
        self.videoScore = 0.0

        self.smallPicUrl = ''
        self.largePicUrl = ''
        self.playUrl = ''
        self.private = {}

        self.videos = {}
        self.script = {}

        if js:
            self.LoadFromJson(js)

    def GetVideoPlayUrl(self):
        pass

    def GetVideoResolution(self):
        ret = []
        for _,v in list(self.videos.items()):
            ret.append(v['name'])

        return ret

    def SaveToJson(self):
        ret = {}

        if self.cid             : ret['cid'] = self.cid
        if self.pid             : ret['pid'] = self.pid
        if self.vid             : ret['vid'] = self.vid
        if self.name            : ret['name'] = self.name

#        if self.highVid         : ret['highVid'] = self.highVid
#        if self.norVid          : ret['norVid'] = self.norVid
#        if self.oriVid          : ret['oriVid'] = self.oriVid
#        if self.superVid        : ret['superVid'] = self.superVid
#        if self.relativeId      : ret['relativeId'] = self.relativeId

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
        if self.videos          : ret['videos'] = self.videos
        if self.script          : ret['script'] = self.script

        if self.priority        : ret['priority'] = self.priority
        if self.private         : ret['private']  = self.private

        resolution = self.GetVideoResolution()
        if resolution:
            ret['resolution'] = resolution

        return ret

    def LoadFromJson(self, json):
        if 'cid' in json            : self.cid            = autoint(json['cid'])
        if 'pid' in json            : self.pid            = autostr(json['pid'])
        if 'vid' in json            : self.vid            = autostr(json['vid'])

#        if 'highVid' in json        : self.highVid        = autostr(json['highVid'])
#        if 'norVid' in json         : self.norVid         = autostr(json['norVid'])
#        if 'oriVid' in json         : self.oriVid         = autostr(json['oriVid'])
#        if 'superVid' in json       : self.superVid       = autostr(json['superVid'])
#        if 'relativeId' in json     : self.relativeId     = autostr(json['relativeId'])

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
        if 'videos' in json         : self.videos         = json['videos']
        if 'script' in json         :  self.script        = json['script']
        if 'priority' in json       : self.priority       = json['priority']
        if 'private' in json        : self.private        = json['private']

class AlbumBase:
    def __init__(self):
        self.VideoClass = VideoBase
        self.cid = 0

        self.sources = {}        # 直接节目    [*]
        self.albumName = ''      # 名称       [*]
        self.enAlbumName = ''    # 英文名称    [*]
        self.vid = ''             #           [*]
        self.area = ''            # 地区       [*]
        self.categories  = []     # 类型       [*]
        self.publishYear = ''     # 发布年份    [*]
        self.isHigh      = 0      # 是否是高清  [*]
        self.albumPageUrl = ''    # 节目主页

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
        self.private = {}
        self.engineList = {}

    def NewVideo(self, js=None):
        v = self.videoClass(js)
        v.pid = self.vid
        v.cid = self.cid

        return v

    def SaveToJson(self):
        ret = {}
        if self.cid             : ret['cid']            = self.cid
        if self.engineList      : ret['engineList']     = self.engineList

        if self.albumName       : ret['albumName']      = self.albumName
        if self.vid             : ret['vid']            = self.vid
        if self.isHigh          : ret['isHigh']         = self.isHigh

        if self.area            : ret['area']           = self.area
        if self.categories      : ret['categories']     = self.categories
        if self.publishYear     : ret['publishYear']    = self.publishYear

        if self.albumDesc       : ret['albumDesc']      = self.albumDesc
        if self.videoScore      : ret['videoScore']     = self.videoScore
        if self.totalSet        : ret['totalSet']       = self.totalSet
        if self.updateSet       : ret['updateSet']      = self.updateSet

        if self.albumPageUrl    : ret['albumPageUrl']   = self.albumPageUrl
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
        if self.private :         ret['private']        = self.private

        return ret

    def LoadFromJson(self, json):
        # From DataBase
        if 'cid' in json            : self.cid             = json['cid']
        if 'albumName' in json      : self.albumName       = json['albumName']
        if 'engineList' in json     : self.engineList      = json['engineList']

        if 'vid' in json            : self.vid             = autostr(json['vid'])

        if 'isHigh' in json         : self.isHigh          = json['isHigh']

        if 'area' in json           : self.area            = json['area']
        if 'categories' in json     : self.categories      = json['categories']
        if 'publishYear' in json    : self.publishYear     = json['publishYear']

        if 'playLength' in json     : self.playLength      = json['playLength']
        if 'publishTime' in json    : self.publishTime     = json['publishTime']
        if 'updateTime' in json     : self.updateTime      = json['updateTime']
        if 'albumPageUrl' in json   : self.albumPageUrl    = json['albumPageUrl']

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
        if 'private' in json        : self.private         = json['private']

# 一级分类菜单
class VideoMenuBase:
    def __init__(self, name):
        self.db = DB()
        self.filter = {}
        self.quickFilter = {}
        self.sort = {}
        self.name = name
        self.homePage = ''
        self.parserList = {}
        self.albumClass = AlbumBase
        self.cid = 0

    def NewAlbum(self, js=None):
        album = self.albumClass()
        if js and album:
            album.LoadFromJson(js)

        return album

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
        ret['count']        = self.db.GetMenuAlbumCount(self.cid)
        ret['filter']       = self.GetFilterJson()
        ret['quickFilters'] = self.GetQuickFilterJson()
        ret['sort']         = self.GetSortJson()

        return ret

class DB:
    video_cachedb = redis.Redis(host='127.0.0.1', port=6379, db=3)
    con = pymongo.Connection('localhost', 27017)
    mongodb = con.kola
    album_table  = mongodb.album
    videos_table = mongodb.videos
    map_table    = mongodb.urlmap
    menu_table   = mongodb.menu
    videos_table.drop_indexes()
    videos_table.create_index([('pid', pymongo.ASCENDING)])
    videos_table.create_index([('vid', pymongo.ASCENDING)])
    videos_table.create_index([('pid', pymongo.ASCENDING), ('vid', pymongo.ASCENDING)])

    album_table.drop_indexes()
    album_table.create_index([('albumName', pymongo.ASCENDING)])
    album_table.create_index([('albumPageUrl', pymongo.ASCENDING)])
    album_table.create_index([('vid', pymongo.ASCENDING)])
    album_table.create_index([('cid', pymongo.ASCENDING)])

    def __init__(self):
        self.fieldMapping = {
            '类型' : 'categories',
            '产地' : 'area',
            '地区' : 'area', # Music
            '年份' : 'publishYear',
            '篇幅' : '',
            '年龄' : '',
            '范围' : '',
            '语言' : '',
            '周播放最多' : 'weeklyPlayNum',
            '日播放最多' : 'dailyPlayNum',
            '总播放最多' : 'totalPlayNum',
            '最新发布'   : 'publishTime',
            '评分最高'   : 'videoScore',
            'vids'      : 'vid'
        }

    def SetVideoCache(self, key, value):
        self.video_cachedb.set(key, value)
        self.video_cachedb.expire(key, 600) # 10 分钟有效

    def GetVideoCache(self, key):
        return self.video_cachedb.get(key)

    def SaveVideo(self, video):
        if video.vid:
            js = video.SaveToJson()
            upert = {}

            upert['vid'] = video.vid
            if video.pid:
                upert['pid'] = video.pid

            self.videos_table.update(
                       upert,
                       {'$set' : js},
                       upsert=True, multi=True)

    def _GetKeyAndJson(self, album, key):
        album.vid        = autostr(album.vid)
        key = ''
        js = {}
        if album.albumName or album.albumPageUrl or album.vid:
            js = album.SaveToJson()

            if not key:
                if album.vid:
                    key = {'vid' : album.vid}
                elif album.albumPageUrl:
                    key = {'albumPageUrl': album.albumPageUrl}
                elif album.albumName:
                    key = {'albumName': album.albumName}

        return key, js

    def DeleteAlbum(self, album, key={}):
        key, _ = self._GetKeyAndJson(album, key)
        if key:
            self.album_table.remove(key)

    def SaveAlbum(self, album, key={}, upsert=True):
        key, js = self._GetKeyAndJson(album, key)

        if key:
            self.album_table.update(key, {"$set" : js}, upsert=upsert, multi=True)

            for v in album.videos:
                self.SaveVideo(v)

    def FindAlbumJson(self, albumName='', vid=''):
        vid = autostr(vid)
        if albumName == '' and vid == '':
            return None

        f = []
        if albumName :    f.append({'albumName'  : albumName})
        if vid :          f.append({'vid'        : vid})

        return self.album_table.find_one({"$or" : f})

    # 得到节目列表
    # arg参数：
    # {
    #    "page" : 0,
    #    "size" : 20,
    #    "filter" : {                 # 过滤字段
    #        "cid":2,
    #        "pid":123123,
    #    },
    #    "fields" : {                 # 显示字段
    #        "albumName" : True,
    #        "pid" : True
    #    },
    #    "sort" : {                   # 排序字段
    #        "albumName": 1,
    #        "vid": -1
    #    }
    # disablePage 为Ture时，页的大小不能为 0
    def GetAlbumListJson(self, arg, cid=-1, disablePage=False, full=False):
        self.ConvertJson(arg)
        ret = []
        count = 0
        try:
            _filter = {}
            if cid != -1:
                _filter['cid'] = cid
            if 'filter' in arg:
                _filter.update(arg['filter'])

            if 'fields' in arg:
                fields = arg['fields']
            else:
                fields = None
            if 'full' in arg:
                full = arg['full']

            cursor = self.album_table.find(_filter, fields = fields)
            count = cursor.count()

            if 'sort' in arg:
                cursor = cursor.sort(arg['sort'])

            size = 0
            if 'page' in arg and 'size' in arg:
                page = autoint(arg['page'])
                size = autoint(arg['size'])
            if size:
                cursor = cursor.skip(page * size).limit(size)
            if size or disablePage:
                for x in cursor:
                    del x['_id']
                    if not full:
                        if 'private' in x:
                            del x['private']
                        if 'engineList' in x:
                            del x['engineList']

                    ret.append(x)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserHotInfoByIapi  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret, count

    def FindVideoJson(self, pid='', vid=''):
        pid        = autostr(pid)
        vid        = autostr(vid)
        if pid == '' and vid == '':
            return None

        f = []
        if pid        : f.append({'pid' : pid})
        if vid        : f.append({'vid' : vid})

        return self.videos_table.find_one({"$or" : f})

    def GetVideoListJson(self, pid='', arg={}):
        ret = []
        pid        = autostr(pid)
        count = 0
        try:
            _filter = {}
            if pid:
                _filter['pid'] = pid

            if 'filter' in arg:
                _filter.update(arg['filter'])

            if 'fields' in arg:
                fields = arg['fields']
            else:
                fields = None

            if not _filter:
                return ret, 0

            cursor = self.videos_table.find(_filter, fields = fields)

            if 'sort' in arg:
                cursor = cursor.sort(arg['sort'])
            else:
                cursor = cursor.sort([('priority', 1)])

            count = cursor.count()

            if 'sort' in arg:
                cursor = cursor.sort(arg['sort'])
            else:
                cursor = cursor.sort([('order', 1)])

            allVideo = False
            if 'page' in arg and 'size' in arg:
                page = autoint(arg['page'])
                size = autoint(arg['size'])
            else:
                allVideo = True
                size = 0

            if size or allVideo:
                if size:
                    cursor = cursor.skip(page * size).limit(size)
                for x in cursor:
                    del x['_id']
                    ret.append(x)
            elif size == 0 and page == 0:
                pass
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserHotInfoByIapi  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret, count

    def GetMenuAlbumCount(self, cid):
        return self.album_table.find({'cid': cid}).count()

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
                f[newkey] = { "$in" : f[key].split(',')}
                del f[key]
        return f

    def _ConvertSortJson(self, v):
        if v in self.fieldMapping:
            newkey = self.fieldMapping[v]
            return [(newkey, -1)]
        else:
            return [(v, -1)]

    def _save_update_append(self, sets, album, key={}, upsert=True):
        if album:
            self.SaveAlbum(album, key, upsert)
            sets.append(album)

