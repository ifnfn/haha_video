#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import uuid
import time
import redis

from .utils import autoint
from .commands import KolaCommand
from .element import LivetvMenu, MovieMenu, TVMenu, ComicMenu, DocumentaryMenu, ShowMenu
from .db import DB

class KolatvServer:    
    def __init__(self):
        self.db = DB()
        self.kdb = redis.Redis(host='127.0.0.1', port=6379, db=1)
        self.command = KolaCommand()
        self.MenuList = {}
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


    def Login(self, chipid, serial, remote_ip):
        status = 'NO'

        if serial in ['000001', '000002', '000003', '000004']:
            status = 'YES'
        elif chipid and serial and chipid not in ['0000000000000000']: # 默认的测试号
            json = self.db.user_table.find_one({'serial' : serial})
            if json and (json['chipid'] == '' or json['chipid'] == chipid):
                status = 'YES'
                self.db.user_table.update({'serial' : serial}, {'$set' : {'chipid': chipid, 'updateTime' : time.time()}})

        if status == 'YES':
            # 登录检查，生成随机 KEY
            if not self.kdb.exists(chipid):
                key = (chipid + uuid.uuid4().__str__() + remote_ip).encode()
                key = hashlib.md5(key).hexdigest().upper()
                self.kdb.set(chipid, key)
                self.kdb.set(key, remote_ip)
            else:
                key = self.kdb.get(chipid).decode()
                self.kdb.set(key, remote_ip)
            self.kdb.expire(chipid, 120) # 一分钟过期
            self.kdb.expire(key, 120)    # 一分钟过期

            return key
        else:
            return ''

    def CheckUser(self, key, remote_ip, chipid=None, serial=None):
        if not kolas.kdb.exists(key) and chipid and serial:
            return self.Login(chipid, serial, remote_ip)
        elif kolas.kdb.get(key).decode() == remote_ip:
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

    def GetVideoByVid(self, vid):
        video = self.db.FindVideoJson(vid=vid)

        return video

    def GetVideoListByPid(self, pid, argument):
        return self.db.GetVideoListJson(pid=pid, arg=argument)

    def FindMenuById(self, cid):
        for _, menu in list(self.MenuList.items()):
            if menu.cid == cid:
                return menu

        return None

    def FindMenu(self, name):
        if name in self.MenuList:
            return self.MenuList[name]
        else:
            return None

    def CommandEmptyMessage(self):
        if self.UpdateAlbumFlag == True:
            self.UpdateAlbumFlag = False

kolas = KolatvServer()
