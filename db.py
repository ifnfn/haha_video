#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, traceback
import pymongo
import redis
from utils import autostr, autoint, log

class DB:
    def __init__(self):
        self.video_cachedb = redis.Redis(host='127.0.0.1', port=6379, db=3)
        self.con = pymongo.Connection('localhost', 27017)
        mongodb = self.con.kola
        self.album_table  = mongodb.album
        self.videos_table = mongodb.videos
        self.map_table    = mongodb.urlmap

        self.videos_table.drop_indexes()
        self.videos_table.create_index([('pid', pymongo.ASCENDING)])
        self.videos_table.create_index([('vid', pymongo.ASCENDING)])
        self.videos_table.create_index([('pid', pymongo.ASCENDING), ('vid', pymongo.ASCENDING)])

        self.album_table.drop_indexes()
        self.album_table.create_index([('albumName', pymongo.ASCENDING)])
        self.album_table.create_index([('albumPageUrl', pymongo.ASCENDING)])
        self.album_table.create_index([('vid', pymongo.ASCENDING)])
        self.album_table.create_index([('cid', pymongo.ASCENDING)])
        self.album_table.create_index([('playlistid', pymongo.ASCENDING)])

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
            'vids'     : 'vid'
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
        album.playlistid = autostr(album.playlistid)
        album.vid        = autostr(album.vid)
        key = ''
        js = {}
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

    # 从数据库中找到 album
    def FindAlbumJson(self, playlistid='', albumName='', vid='', auto=False):
        playlistid = autostr(playlistid)
        vid = autostr(vid)
        if playlistid == '' and albumName == '' and vid == '':
            return None

        f = []
        if playlistid :   f.append({'playlistid'   : playlistid})
        if albumName :    f.append({'albumName'    : albumName})
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

    def FindVideoJson(self, playlistid='', pid='', vid=''):
        playlistid = autostr(playlistid)
        pid        = autostr(pid)
        vid        = autostr(vid)
        if pid == '' and vid == '' and playlistid == '':
            return None

        f = []
        if playlistid : f.append({'playlistid' : playlistid})
        if pid        : f.append({'pid' : pid})
        if vid        : f.append({'vid' : vid})

        return self.videos_table.find_one({"$or" : f})

    def GetVideoListJson(self, playlistid='', pid='', arg={}):
        ret = []
        playlistid = autostr(playlistid)
        pid        = autostr(pid)
        count = 0
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
