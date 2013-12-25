#! /usr/bin/python3
# -*- coding: utf-8 -*-

import logging

from kola import KolaCommand, ThreadPool, element, utils
import kola


POOLSIZE = 10

log = logging.getLogger('crawler')

class KolatvServer:
    def __init__(self):
        self.thread_pool = ThreadPool(POOLSIZE)
        self.db = kola.DB()
        self.command = KolaCommand()
        self.MenuList = {}
        self.UpdateAlbumFlag = False
        self.MenuList['直播']   = element.LivetvMenu('直播')
        self.MenuList['电影']   = element.MovieMenu('电影')
        self.MenuList['电视剧'] = element.TVMenu('电视剧')

    def GetVideoSource(self):
        return {
            'source' : ['乐视', '搜狐', '爱奇艺'],
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
            return self.db.GetAlbumListJson(argument, menu.cid)

        return [], 0

    def GetMenuAlbumListByVidList(self, vids, argument):
        if 'filter' not in argument:
            argument['filter'] = {}
        argument['filter']['vids'] = vids
        return self.db.GetAlbumListJson(argument)

    def GetMenuAlbumListByName(self, menuName, argument):
        menu = self.FindMenu(menuName)
        return self._GetMenuAlbumList(menu, argument)

    def GetMenuAlbumListByCid(self, cid, argument):
        cid = utils.autoint(cid)
        menu = self.FindMenuById(cid)
        return self._GetMenuAlbumList(menu, argument)

    def GetVideoByVid(self, vid):
        video = self.db.FindVideoJson(vid=vid)

        return video

    def GetVideoListByPid(self, pid, argument):
        return self.db.GetVideoListJson(pid=pid, arg=argument)

    # 得到真实播放地址
    def GetRealPlayer(self, text, cid, definition, step, url=''):
        menu = self.FindMenuById(utils.autoint(cid))
        if menu == None:
            return {}

        return menu.GetRealPlayer(text, definition, step, url)

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

    def _get_album(self, All=False):
        argument = {}
        argument['fields'] = {'engineList' : True,
                              'albumName': True,
                              'private': True,
                              'vid': True,
                              'playlistid': True}

        albumList = []
        data, _ = self.db.GetAlbumListJson(argument, disablePage=True, full=True)
        for p in data:
            for (name, engine) in list(self.engines.items()):
                if 'engineList' in p and name in p['engineList']:
                    albumList.append(engine.NewAlbum(p))
                    break

        return albumList

    def CommandEmptyMessage(self):
        if self.UpdateAlbumFlag == True:
            self.UpdateAlbumFlag = False

