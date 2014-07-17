#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import traceback

import pymongo
import redis

from .utils import autostr, autoint, log, GetQuickFilter, GetPinYin


class AlbumBase:
    def __init__(self):
        self.cid = 0

        self.albumName       = ''  # 名称        [*]
        self.enAlbumName     = ''  # 英文名称    [*]
        self.vid             = ''  # [*]
        self.area            = ''  # 地区        [*]
        self.categories      = []  # 类型        [*]
        self.publishYear     = ''  # 发布年份    [*]
        self.publishTime     = 0   # 网站上线时间
        self.isHigh          = 0   # 是否是高清  [*]

        self.largePicUrl     = ''  # 大图片网址  [*]
        self.smallPicUrl     = ''  # 小图片网址  [*]
        self.largeHorPicUrl  = ''  # [*]
        self.smallHorPicUrl  = ''  # [*]
        self.largeVerPicUrl  = ''  # [*]
        self.smallVerPicUrl  = ''  # [*]

        self.playLength      = 0.0 # [*]
        self.updateTime      = 0   # [*]

        self.albumDesc       = ''  # [*]

        self.totalSet        = 0   # 总集数      [*]
        self.updateSet       = 0   # 当前更新集   [*]
        self.dailyPlayNum    = 0   # 每日播放次数 [*]
        self.weeklyPlayNum   = 0   # 每周播放次数 [*]
        self.monthlyPlayNum  = 0   # 每月播放次数 [*]
        self.totalPlayNum    = 0   # 总播放次数   [*]
        self.Score           = 0.0 # 得分        [*]
        self.Number          = 0

        self.mainActors      = []  # [*]
        self.directors       = []  # [*]

        self.videoListUrl    = ''

        self.epgInfo         = {}
        self.sources         = {}  # 直接节目    [*]
        self.videos          = []
        self.private         = {}
        self.engineList      = []
        self.videoList       = []

        if self.engineName:
            self.engineList.append(self.engineName)

    def SaveToJson(self):
        ret = {}
        if self.engineName and self.engineName not in self.engineList:
            self.engineList.append(self.engineName)
        if self.engineList      : ret['engineList']      = self.engineList

        if self.cid             : ret['cid']             = self.cid

        if self.albumName:
            ret['albumName'] = self.albumName
            ret['NamePy']    = GetPinYin(self.albumName)

        if self.enAlbumName     : ret['enAlbumName']     = self.enAlbumName

        if self.vid             : ret['vid']             = self.vid
        if self.isHigh          : ret['isHigh']          = self.isHigh

        if self.area            : ret['area']            = self.area
        if self.categories      : ret['categories']      = self.categories
        if self.publishYear     : ret['publishYear']     = self.publishYear
        if self.publishTime     : ret['publishTime']     = self.publishTime

        if self.albumDesc       : ret['albumDesc']       = self.albumDesc
        if self.totalSet        : ret['totalSet']        = self.totalSet
        if self.updateSet       : ret['updateSet']       = self.updateSet

        # 图片
        if self.largeHorPicUrl  : ret['largeHorPicUrl']  = self.largeHorPicUrl
        if self.smallHorPicUrl  : ret['smallHorPicUrl']  = self.smallHorPicUrl
        if self.largeVerPicUrl  : ret['largeVerPicUrl']  = self.largeVerPicUrl
        if self.smallVerPicUrl  : ret['smallVerPicUrl']  = self.smallVerPicUrl
        if self.largePicUrl     : ret['largePicUrl']     = self.largePicUrl
        if self.smallPicUrl     : ret['smallPicUrl']     = self.smallPicUrl

        if self.mainActors      : ret['mainActors']      = self.mainActors
        if self.directors       : ret['directors']       = self.directors

        if self.playLength      : ret['playLength']      = self.playLength

        if self.updateTime      : ret['updateTime']      = self.updateTime
        if self.dailyPlayNum    : ret['dailyPlayNum']    = self.dailyPlayNum     # 每日播放次数
        if self.weeklyPlayNum   : ret['weeklyPlayNum']   = self.weeklyPlayNum    # 每周播放次数
        if self.monthlyPlayNum  : ret['monthlyPlayNum']  = self.monthlyPlayNum   # 每月播放次数
        if self.totalPlayNum    : ret['totalPlayNum']    = self.totalPlayNum     # 总播放资料
        if self.Score           : ret['Score']           = self.Score

        if self.sources         : ret['sources']         = self.sources
        if self.epgInfo         : ret['epgInfo']         = self.epgInfo
        if self.videoList       : ret['videoList']       = self.videoList

        ret['private'] = self.private
        ret['Number']  = self.Number

        return ret

    def LoadFromJson(self, json):
        # From DataBase
        if 'cid' in json            : self.cid             = json['cid']
        if 'albumName' in json      : self.albumName       = json['albumName']
        if 'engineList' in json     : self.engineList      = json['engineList']
        if self.engineName and self.engineName not in self.engineList:
            self.engineList.append(self.engineName)

        if 'enAlbumName' in json    : self.enAlbumName     = json['enAlbumName']
        if 'vid' in json            : self.vid             = autostr(json['vid'])

        if 'isHigh' in json         : self.isHigh          = json['isHigh']

        if 'area' in json           : self.area            = json['area']
        if 'categories' in json     : self.categories      = json['categories']
        if 'publishYear' in json    : self.publishYear     = json['publishYear']
        if 'publishTime' in json    : self.publishTime     = json['publishTime']

        if 'playLength' in json     : self.playLength      = json['playLength']

        # 图片
        if 'largeHorPicUrl' in json : self.largeHorPicUrl  = json['largeHorPicUrl']
        if 'smallHorPicUrl' in json : self.smallHorPicUrl  = json['smallHorPicUrl']
        if 'largeVerPicUrl' in json : self.largeVerPicUrl  = json['largeVerPicUrl']
        if 'smallVerPicUrl' in json : self.smallVerPicUrl  = json['smallVerPicUrl']
        if 'largePicUrl' in json    : self.largePicUrl     = json['largePicUrl']
        if 'smallPicUrl' in json    : self.smallPicUrl     = json['smallPicUrl']

        if 'albumDesc' in json      : self.albumDesc       = json['albumDesc']
        if 'totalSet' in json       : self.totalSet        = json['totalSet']
        if 'updateSet' in json      : self.updateSet       = json['updateSet']

        if 'mainActors' in json     : self.mainActors      = json['mainActors']
        if 'directors' in json      : self.directors       = json['directors']

        if 'dailyPlayNum' in json   : self.dailyPlayNum    = json['dailyPlayNum']    # 每日播放次数
        if 'weeklyPlayNum' in json  : self.weeklyPlayNum   = json['weeklyPlayNum']   # 每周播放次数
        if 'monthlyPlayNum' in json : self.monthlyPlayNum  = json['monthlyPlayNum']  # 每月播放次数
        if 'totalPlayNum' in json   : self.totalPlayNum    = json['totalPlayNum']    # 总播放资料
        if 'Score' in json          : self.Score           = json['Score']
        if 'Number' in json         : self.Number          = json['Number']

        if 'updateTime' in json     : self.updateTime      = json['updateTime']
        if 'videoList' in json      : self.videoList       = json['videoList']

        if 'sources' in json        : self.sources         = json['sources']
        if 'epgInfo' in json        : self.epgInfo         = json['epgInfo']
        if 'private' in json        : self.private         = json['private']

# 一级分类菜单
class VideoMenuBase:
    def __init__(self, name):
        self.db          = DB()
        self.filter      = {}
        self.quickFilter = {}
        self.sort        = {}
        self.name        = name
        self.homePage    = ''
        self.parserList  = {}
        self.albumClass  = AlbumBase
        self.cid         = 0

    def NewAlbum(self, js=None):
        album = self.albumClass()
        if js and album:
            album.LoadFromJson(js)

        return album

    def FixArgument(self, argument):
        pass

    def CheckQuickFilter(self, argument):
        if 'quickFilter' in argument:
            qf = GetQuickFilter(self.name, self.quickFilter)

            name = argument['quickFilter']
            for js in qf:
                if js['title'] ==  name:
                    if 'filter' in js:
                        argument['filter'] = js['filter']
                    if 'sort' in js:
                        argument['sort'] = js['sort']
                    break
            del argument['quickFilter']

    def GetQuickFilterJson(self):
        return [x['title'] for x in self.quickFilter]

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
    kola = con.kola
    album_table  = kola.album
    videos_table = kola.videos
    map_table    = kola.urlmap
    menu_table   = kola.menu
    user_table   = kola.users
    videos_table.drop_indexes()
    videos_table.create_index([('pid', pymongo.ASCENDING)])
    videos_table.create_index([('vid', pymongo.ASCENDING)])
    videos_table.create_index([('pid', pymongo.ASCENDING), ('vid', pymongo.ASCENDING)])

    album_table.drop_indexes()
    album_table.create_index([('engineList'  , pymongo.ASCENDING)])
    album_table.create_index([('albumName'   , pymongo.ASCENDING)])
    album_table.create_index([('vid'         , pymongo.ASCENDING)])
    album_table.create_index([('cid'         , pymongo.ASCENDING)])

    user_table.drop_indexes()
    user_table.create_index([('serial'       , pymongo.ASCENDING)])
    user_table.create_index([('client_id'    , pymongo.ASCENDING)])

    fieldMapping = {
            '类型' : 'categories',
            '产地' : 'area',
            '地区' : 'area', # Music
            '年份' : 'publishYear',
            '篇幅' : '',
            '年龄' : '',
            '范围' : '',
            '语言' : '',
            '周热播'   : 'weeklyPlayNum',
            '昨日热播' : 'dailyPlayNum',
            '历史热播' : 'totalPlayNum',
            '最新发布' : 'publishTime',
            '最新更新' : 'updateTime',
            '评分最高' : 'Score',
            '名称'    : 'NamePy',
            'Name'   : 'NamePy',
            'vids'   : 'vid'
    }

    def __init__(self):
        self.albumNameAlias = {}   # 别名
        self.blackAlbumName = []   # 黑名单

    def GetAlbumName(self, name):
        if name in self.albumNameAlias:
            name = self.albumNameAlias[name]

        if name in self.blackAlbumName:
            return ''
        return name

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
        album.vid = autostr(album.vid)
        key = ''
        js = {}
        if album.albumName or album.vid:
            js = album.SaveToJson()

            if not key:
                if album.vid:
                    key = {'vid' : album.vid}
                elif album.albumName:
                    key = {'albumName': album.albumName}

        return key, js

    def _SaveAlbum(self, album, key={}, upsert=True):
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

    def GetAlbumFailure(self, vids):
        vids = vids.split(',')
        _filter = {
            'vid' : { "$in" : vids}
        }
        cursor = self.album_table.find(_filter, fields = {'vid'})
        for x in cursor:
            vid = x['vid']
            if vid in vids:
                vids.remove(vid)

        return vids

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

            if set(['key', 'value', 'size']).issubset(arg): # 查找指定名称的节目所在的页
                key = arg['key']
                value = arg['value']
                size = autoint(arg['size'])
                cursor = self.album_table.find(_filter, fields = fields)
                if 'sort' in arg:
                    cursor = cursor.sort(arg['sort'])

                c = 0
                for x in cursor:
                    if x[key] == value:
                        arg['page'] = c // size
                        break
                    c += 1

            size = 0
            if 'page' in arg and 'size' in arg:
                page = autoint(arg['page'])
                size = autoint(arg['size'])

            cursor = self.album_table.find(_filter, fields = fields)
            if 'sort' in arg:
                cursor = cursor.sort(arg['sort'])

            count = cursor.count()

            if size:
                cursor = cursor.skip(page * size).limit(size)

            if size or disablePage:
                #if 'engine' in arg:
                #    engine_name = arg['engine']
                #else:
                #    engine_name = ''
                for x in cursor:
                    engine_list = {}
                    del x['_id']
                    if 'private'in x:
                        for _, v in x['private'].items():
                            if 'videoListUrl' in v:
                                engine_list[v['name']] = v['videoListUrl']

                    x['engine'] = engine_list
                    if not full:
                        if 'private' in x:
                            del x['private']
                        if 'engineList' in x:
                            del x['engineList']
                        if 'NamePy' in x:
                            del x['NamePy']

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
        if pid: f.append({'pid' : pid})
        if vid: f.append({'vid' : vid})

        return self.videos_table.find_one({"$or" : f})

    def GetVideoListJson(self, pid='', arg={}):
        ret = []
        pid        = autostr(pid)
        allVideo = False
        if 'page' in arg and 'size' in arg:
            page = autoint(arg['page'])
            size = autoint(arg['size'])
        else:
            allVideo = True
            size = 0

        cursor = self.album_table.find({'vid' : pid}, fields = {'videoList': True})
        if cursor:
            for x in cursor:
                videoList = x['videoList']
                count = len(videoList)
                if size or allVideo:
                    videoList = sorted(videoList, key=lambda d:d['order'])
                else:
                    videoList = []

                return videoList, count

        return [], 0

        #################### 以下不要啦！###############################
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
                cursor = cursor.sort([('order', 1)])

            count = cursor.count()

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
        elif 'cid' in arg and arg['cid'] == '200':
            arg['sort'] = [('vid', pymongo.ASCENDING)]
        else:
            arg['sort'] = [('dailyPlayNum', pymongo.DESCENDING)]

        #print(arg['sort'])
        return arg

    def _ConvertFilterJson(self, f):
        ret = {}
        for key in f:
            if key.lower() == 'pinyin':
                ret['NamePy'] = {'$regex':f[key], '$options':'i'}
            elif key.lower() == 'local_area':
                ret['area'] = {'$regex':f[key], '$options':'i'}
            elif key in self.fieldMapping:
                newkey = self.fieldMapping[key]
                if newkey.lower() == 'publishyear':
                    value = f[key]
                    if value in ['2013', '2012', '2011', '2010']:
                        ret[newkey] = autoint(value)
                    elif value == '00年代':
                        ret[newkey] = {'$gte' : 2000, '$lte' : 2009}
                    elif value == '90年代':
                        ret[newkey] = {'$gte' : 1990, '$lte' : 1999}
                    elif value == '80年代':
                        ret[newkey] = {'$gte' : 1980, '$lte' : 1989}
                    elif value == '更早':
                        ret[newkey] = {'$lt' : 1980}
                else:
                    ret[newkey] = { "$in" : f[key].split(',')}
        return ret

    def _ConvertSortJson(self, v):
        if v.find(',') >= 0:
            v, style = v.split(',')
        else:
            style = "-1"
        if v in self.fieldMapping:
            newkey = self.fieldMapping[v]
            return [(newkey, int(style))]
        else:
            return [(v, int(style))]

    def _save_update_append(self, sets, album, key={}, upsert=True):
        if album:
            self._SaveAlbum(album, key, upsert)
            if sets:
                sets.append(album)

