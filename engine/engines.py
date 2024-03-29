#! /usr/bin/python3
# -*- coding: utf-8 -*-

import configparser
import sys
import traceback

import tornado.escape

from kola import DB, KolaCommand, VideoMenuBase


global Debug
Debug = True

class KolaAlias:
    def __init__(self):
        self.alias = {}

    def Get(self, v):
        if v in self.alias:
            return self.alias[v]
        else:
            return v

    def GetList(self, v):
        ret = []
        for i in v:
            if i in self.alias:
                ret.append(self.alias[i])
            else:
                ret.append(i)
        return ret

    def GetStrings(self, v, sp):
        v = v.split(sp)

        return self.GetList(v)

# 命令管理器
class EngineCommands(KolaCommand):
    def __init__(self):
        super().__init__()
        self.urlmap = {}
        self.pipe = None

    def AddUrlMap(self, oldurl, newurl):
        self.urlmap[oldurl] = newurl
        DB().map_table.update({'source': oldurl}, {"$set" : {'dest': newurl}}, upsert=True, multi=True)

    def GetUrl(self, url):
        if not self.urlmap:
            maps = DB().map_table.find()
            for m in maps:
                self.AddUrlMap(m['source'], m['dest'])

            # self.AddUrlMap('http://tv.sohu.com/s2011/fengsheng/', 'http://tv.sohu.com/20121109/n268282527.shtml')
            # self.AddUrlMap('http://tv.sohu.com/s2011/nrb/', 'http://tv.sohu.com/20111023/n323122692.shtml')
            self.AddUrlMap('http://tv.sohu.com/s2010/tctyjxl/', 'http://tv.sohu.com/20090930/n267111286.shtml')

        if url in self.urlmap:
            print(("Map: %s --> %s" % (url, self.urlmap[url])))
            return self.urlmap[url]
        else:
            return url

    def AddCommand(self, cmd):
        if 'source' in cmd or 'text' in cmd:
            if 'source' in cmd:
                cmd['source'] = self.GetUrl(cmd['source'])
            if self.pipe == None:
                self.pipe = self.db.pipeline()
            self.pipe.rpush('command', tornado.escape.json_encode(cmd))
        return self

    def Execute(self):
        if self.pipe:
            self.pipe.execute()
            self.pipe = None

class KolaParser:
    def __init__(self):
        self.command = EngineCommands()
        self.name = self.__class__.__module__ + '.' + self.__class__.__name__

        self.cmd = {}
        self.cmd['engine'] = self.name
        self.cmd['cache']  = True

    def AddCommand(self):
        if self.cmd:
            self.command.AddCommand(self.cmd)
            self.cmd = None

    def Execute(self):
        self.AddCommand()
        self.command.Execute()

class EngineVideoMenu(VideoMenuBase):
    def __init__(self, name):
        super().__init__(name)
        self.DBClass = DB

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        pass

    # 更新排名数据
    def UpdateAllScore(self):
        for album in self.DBClass().GetMenuAlbumList(self.cid):
            album.UpdateScoreCommand()

        EngineCommands().Execute()

class VideoEngine:
    def __init__(self):
        self.engine_name = 'EngineBase'
        self.config = configparser.ConfigParser()

        self.albumClass = None
        self.parserList = []
        self.menu = []

    def NewAlbum(self, js=None):
        album = self.albumClass()
        if js and album:
            album.LoadFromJson(js)

        return album

    # 解析菜单网页解析
    def ParserHtml(self, js):
        try:
            for engine in self.parserList:
                if engine.name == js['engine']:
                    engine.CmdParser(js)
                    return True

        except:
            t, v, tb = sys.exc_info()
            print("VideoEngine.ParserHtml:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return False

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        self.UpdateAlbumFlag = True
        for m in self.menu:
            m.UpdateAlbumList()

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")
        for m in self.menu:
            m.UpdateAllScore()

    # 更新所有节目的完全信息
    def UpdateAllFullInfo(self):
        print("UpdateAllFullInfo")

    # 更新所有节目的播放信息
    def UpdateAllPlayInfo(self):
        print("UpdateAllPlayInfo")

    # 更新所有节目主页
    def UpdateAllAlbumPage(self):
        print("UpdateAllAlbumPage")

    # 更新热门节目信息
    def UpdateAllHotList(self):
        print("UpdateAllHotList")
