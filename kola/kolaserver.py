#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import time
import uuid

import redis
import tornado.escape

from .commands import KolaCommand
from .db import DB
from .element import LivetvMenu, MovieMenu, TVMenu, ComicMenu, DocumentaryMenu, \
    ShowMenu
from .utils import autoint


class KolatvServer:
    def __init__(self):
        self.db = DB()
        self.kdb = redis.Redis(host='127.0.0.1', port=6379, db=1)
        self.command = KolaCommand()
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
        for key in self.kdb.keys('????????????????'):
            js = tornado.escape.json_decode(self.kdb.get(key))
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
        js = self.kdb.get(chipid)
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
                    self.db.user_table.update({'serial' : serial}, {'$set' : {'chipid': chipid, 'registerTime': time.time()}})

        userinfo = {
                    'chipid'    : chipid,
                    'serial'    : serial,
                    'remote_ip' : remote_ip,
                    'updateTime': time.time(),
                    'area'      : area
                    }

        if status == 'YES' and not key:
            # 登录检查，生成随机 KEY
            if self.kdb.exists(chipid):
                js = self.kdb.get(chipid)
                key = tornado.escape.json_decode(js)['key']
            if not key:
                key = (chipid + uuid.uuid4().__str__() + remote_ip).encode()
                key = hashlib.md5(key).hexdigest().upper()

        userinfo['key'] = key

        userinfo = tornado.escape.json_encode(userinfo)
        self.kdb.set(chipid, userinfo)
        self.kdb.set(key, userinfo)

        self.kdb.expire(chipid, self.ActiveTime + 30) # 一分钟过期
        self.kdb.expire(key, self.ActiveTime + 30)    # 一分钟过期

        return key

    def CheckUser(self, key, remote_ip, chipid=None, serial=None):
        if not self.kdb.exists(key):
            if chipid and serial:
                return self.Login(chipid, serial, remote_ip)
        else:
            js = self.kdb.get(key)
            userinfo = tornado.escape.json_decode(js)
            if userinfo['key'] == key.decode() and userinfo['remote_ip'] == remote_ip:
                return key

    def GetVideoSource(self):
        return {
            'source' : ['腾讯', '搜狐', '爱奇艺'],
            'resolution' : ['1080P', '原画质', '720P', '超清', '高清', '标清', '默认']
        }

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

    def GetVideoListByPid(self, pid, argument):
        return self.db.GetVideoListJson(pid=pid, arg=argument)

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
