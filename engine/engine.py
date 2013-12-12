#! /usr/bin/python3
# -*- coding: utf-8 -*-

import configparser
import json
import sys
import traceback

from kola import DB, KolaCommand


global Debug
Debug = True

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
        if ('source' in cmd or 'text' in cmd) and 'name' in cmd:
            if 'source' in cmd:
                cmd['source'] = self.GetUrl(cmd['source'])
            if self.pipe == None:
                self.pipe = self.db.pipeline()
            self.pipe.rpush('command', json.dumps(cmd))
        return self

    def Execute(self):
        if self.pipe:
            self.pipe.execute()
            self.pipe = None

class KolaParser:
    def __init__(self):
        self.command = EngineCommands()
        self.name = self.__class__.__name__

        self.cmd = {}
        self.cmd['engine'] = self.__class__.__name__
        self.cmd['cache']  = False or Debug

    def AddCommand(self):
        if self.cmd:
            self.command.AddCommand(self.cmd)
            self.cmd = None

    def Execute(self):
        self.AddCommand()
        self.command.Execute()

class VideoEngine:
    def __init__(self):
        self.engine_name = 'EngineBase'
        self.config = configparser.ConfigParser()

        self.albumClass = None
        self.parserList = {}

    def NewAlbum(self, js=None):
        album = self.albumClass()
        if js and album:
            album.LoadFromJson(js)

        return album

    # 获取节目一级菜单, 返回分类列表
    def GetMenu(self, MenuList):
        for m, menu in list(self.menu.items()):
            if type(menu) == type:
                menu = menu(m)
            if m not in MenuList:
                MenuList[m] = menu

    # 解析菜单网页解析
    def ParserHtml(self, js):
        try:
            for engine in self.parserList:
                if engine.name == js['engine']:
                    return engine.CmdParser(js)

        except:
            t, v, tb = sys.exc_info()
            print("SohuVideoMenu._CmdParserAlbumPlayInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return None

    # 更新所有节目的排名数据
    def UpdateAllScore(self):
        print("UpdateAllScore")

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

    # 更新所有节目（增加新的节目）
    def UpdateAllAlbumList(self):
        print("UpdateAllAlbumList")

