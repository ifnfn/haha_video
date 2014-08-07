#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import time
import uuid

import tornado.escape
from tornado.log import access_log, app_log, gen_log

from .cached import RedisCached, MemcachedCached, AliyunCached
from .commands import KolaCommand
from .db import DB
from .element import LivetvMenu, MovieMenu, TVMenu, ComicMenu, DocumentaryMenu, \
    ShowMenu
from .utils import autoint


class KolatvServer:
    def __init__(self):
        self.hit_count = 0     # 页面缓冲命中次数
        self.misses_count = 0  # 页面未缓冲命中次数
        self.db = DB()
        self.command = KolaCommand()
        self.UserCache = RedisCached()

        #self.cached = MemcachedCached()
        self.cached = AliyunCached()
        #self.cached = RedisCached()

        self.MenuList = {}
        self.ActiveTime = 60 # 客户端重新登录时长
        self.UpdateAlbumFlag = False
        self.MenuList['直播']   = LivetvMenu('直播')           # 200
        self.MenuList['电影']   = MovieMenu('电影')            # 1
        self.MenuList['电视剧'] = TVMenu('电视剧')              # 2
        self.MenuList['动漫']   = ComicMenu('动漫')            # 3
        self.MenuList['记录片'] = DocumentaryMenu('记录片')     # 4
        self.MenuList['综艺']   = ShowMenu('综艺')             # 5
        #self.MenuList['教育']   = EduMenu('教育')              # 6
        #self.MenuList['娱乐']   = YuleMenu('娱乐')             # 7
        #self.MenuList['旅游']   = TourMenu('旅游')             # 8

    def GetOnline(self):
        ret = []

        i = 1
        for key in self.UserCache.Keys('????????????????'):
            js = tornado.escape.json_decode(self.UserCache.Get(key))
            js['id'] = i
            js['updateTimeStr'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(js['updateTime']))
            ret.append(js)
            i += 1

        return ret

    def GetAllUser(self):
        ret = []
        _filter = {'chipid' : {'$ne' : '', "$exists": True}, 'number': {"$exists": True}}
        cursor = self.db.user_table.find(_filter).sort([('number', 1)])
        for x in cursor:
            del x['_id']
            if 'updateTime' in x:
                x['updateTimeStr'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x['updateTime']))
            else:
                x['updateTimeStr'] = ''
            if 'registerTime' in x:
                x['registerTimeStr'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x['registerTime']))
            else:
                x['registerTimeStr'] = ''
            ret.append(x)
        return ret

    def LoginFromCache(self, chipid, serial):
        js = self.UserCache.Get(chipid)
        if js:
            js = tornado.escape.json_decode(js)

            if js['serial'] == serial:
                return js['key']

    def Login(self, chipid, serial, remote_ip, area=None):
        status = 'NO'
        key = ''

        if serial in ['000001', '000002', '000003', '000004']:
            status = 'YES'
        elif chipid and serial and chipid not in ['0000000000000000']: # 默认的测试号
            key = self.LoginFromCache(chipid, serial)
            if key:
                status = 'YES'
            else:
                while status == 'NO':
                    json = self.db.user_table.find_one({'chipid' : chipid})
                    if json:
                        if json['serial'] == serial:
                            status = 'YES'
                            break
                        elif json['serial'] != '': # 已经注册过的话，源序列号失效
                            self.db.user_table.update({'serial' : json['serial']}, {'$set' : {'chipid': ''}})
                        else:
                            break
                    else:
                        json = self.db.user_table.find_one({'serial' : serial})
                        if not json:
                            break

                    self.db.user_table.update({'serial' : serial}, {'$set' : {'chipid': chipid, 'registerTime': time.time()}})

        userinfo = {
                    'chipid'    : chipid,
                    'serial'    : serial,
                    'remote_ip' : remote_ip,
                    'updateTime': time.time(),
                    'area'      : area
                    }

        if status == 'YES' and not key:
            js = self.UserCache.Get(chipid)

            if js:
                key = tornado.escape.json_decode(js)['key']
            if not key:
                key = (chipid + uuid.uuid4().__str__() + remote_ip).encode()
                key = hashlib.md5(key).hexdigest().upper()

        if key:
            userinfo['key'] = key

            userinfo = tornado.escape.json_encode(userinfo)
            self.UserCache.Set(chipid, userinfo, self.ActiveTime + 30)
            self.UserCache.Set(key, userinfo, self.ActiveTime + 30)

            return key

    def CheckUser(self, key, remote_ip, chipid=None, serial=None):
        if key:
            js = self.UserCache.Get(key)
        else:
            js = None
        if js:
            userinfo = tornado.escape.json_decode(js)
            if userinfo['key'] == key and userinfo['remote_ip'] == remote_ip:
                return key
        else:
            if chipid and serial:
                return self.Login(chipid, serial, remote_ip)

    def GetVideoSource(self):
        return {
            'source' : ['腾讯', '搜狐', '爱奇艺'],
            'resolution' : ['1080P', '原画质', '720P', '超清', '高清', '标清', '默认']
        }

    def SetCache(self, key, value, timeout=None):
        self.cached.Set(key, value, timeout)

    def GetCache(self, key):
        return self.cached.Get(key)

    def CleanUrlCache(self):
        self.cached.Clean('album_*')
        self.cached.Clean('video_*')
        self.cached.Clean('allmenu')
        self.cached.Clean('list_*')

    def GeJsontData(self, args):
        value = None
        if args['cache'] != 0:
            if 'cid' in args and args['cid'] != '200':
                key_js = args.copy()
                del key_js['area']
                key = tornado.escape.json_encode(key_js)
            else:
                key = tornado.escape.json_encode(args)
            key = 'album_' + hashlib.sha1(key.encode()).hexdigest()

            value = self.cached.Get(key)

        if not value:
            self.misses_count += 1
            if 'cid' in args:
                albumlist, args['total'] = self.GetMenuAlbumListByCid(args['cid'], args)
            elif 'menu' in args:
                albumlist, args['total'] = self.GetMenuAlbumListByName(args['menu'], args)
            elif 'vid' in args:
                albumlist, args['total'] = self.GetMenuAlbumListByVidList(args['vid'], args)

            if albumlist:
                args['result'] = albumlist

            value = tornado.escape.json_encode(args)
            if args['cache'] != 0:
                self.cached.Set(key, value)
        else:
            self.hit_count += 1

        app_log.info("albume page hit: %2.2f%%, hit: %d, misses: %d" % (self.hit_count * 100.0 / (self.hit_count + self.misses_count), self.hit_count, self.misses_count))
        return value

    def GetMenuJsonInfoById(self, cid_list):
        ret = []
        count = len(cid_list)
        for _, menu in list(self.MenuList.items()):
            if count == 0 or str(menu.cid) in cid_list:
                ret.append(menu.GetJsonInfo())

        return ret

    def GetMenuJsonInfoByName(self, name_list):
        ret = []
        count = len(name_list)
        for name, menu in list(self.MenuList.items()):
            if count == 0 or name in name_list:
                ret.append(menu.GetJsonInfo())

        return ret

    def _GetMenuAlbumList(self, menu, argument):
        if menu:
            menu.CheckQuickFilter(argument)
            menu.FixArgument(argument)
            return self.db.GetAlbumListJson(argument, menu.cid)

        return [], 0

    def GetAlbumFailure(self, vids):
        return self.db.GetAlbumFailure(vids)

    def GetMenuAlbumListByVidList(self, vids, argument):
        if 'filter' not in argument:
            argument['filter'] = {}
        argument['filter']['vids'] = vids
        return self.db.GetAlbumListJson(argument)

    def GetMenuAlbumListByName(self, menuName, argument):
        menu = self.FindMenu(menuName)
        return self._GetMenuAlbumList(menu, argument)

    def GetMenuAlbumListByCid(self, cid, argument):
        cid = autoint(cid)
        menu = self.FindMenuById(cid)
        return self._GetMenuAlbumList(menu, argument)

    def GetVideoList(self, argument):
        return self.db.GetVideoListJson(argument)

    def FindMenuById(self, cid):
        for _, menu in list(self.MenuList.items()):
            if menu.cid == cid:
                return menu

    def FindMenu(self, name):
        if name in self.MenuList:
            return self.MenuList[name]

    def CommandEmptyMessage(self):
        if self.UpdateAlbumFlag == True:
            self.UpdateAlbumFlag = False
