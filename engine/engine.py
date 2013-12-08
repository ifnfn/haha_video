#! /usr/bin/python3
# -*- coding: utf-8 -*-

import json, re
import configparser
from kola import DB
from kola import KolaCommand

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

class KolaParser:
    def __init__(self):
        self.cmd = {}
        self.name = self.__class__.__name__

        self.cmd['engine'] = self.__class__.__name__
        self.cmd['cache']  = False or Debug

        self.command = EngineCommands()

    def AddCommand(self):
        if self.cmd:
            self.command.AddCommand(self.cmd)
            self.cmd = None

    def Execute(self):
        self.AddCommand()
        self.command.Execute()

class VideoEngine:
    def __init__(self, command):
        self.engine_name = 'EngineBase'
        self.config = configparser.ConfigParser()

        self.albumClass = None
        self.db = DB()
        self.command = command
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
                # MenuList[self.engine_name + '-' + m] = cls(m)
            if m not in MenuList:
                MenuList[m] = menu
#            else:
#                MenuList[m].append(menu)

    # 解析菜单网页解析
    def ParserHtml(self, js):
        for engine in self.parserList:
            if engine.name == js['engine']:
                return engine.CmdParser(js)

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

class TVCategory:
    def __init__(self):
        self.Outside = '凤凰|越南|半岛|澳门|东森|澳视|亚洲|良仔|朝鲜| TV|KP|Yes|HQ|NASA|Poker|Docu|Channel|Neotv|fashion|Sport|sport|Power|FIGHT|Pencerahan|UK|GOOD|Kontra|Rouge|Outdoor|Divine|Europe|DaQu|Teleromagna|Alsharqiya|Playy|Boot Movie|Runway|Bid|LifeStyle|CBN|HSN|BNT|NTV|Virgin|Film|Smile|Russia|NRK|VIET|Gulli|Fresh'
        self.filter = {
            '类型' : {
                'CCTV' : 'cctv|CCTV',
                '卫视台' : '卫视|卡酷少儿|炫动卡通',
                '体育台' : '体育|足球|网球',
                '综合台' : '综合|财|都市|经济|旅游',
                '少儿台' : '动画|卡通|动漫|少儿',
                '地方台' : '^(?!.*?(cctv|CCTV|卫视|测试|卡酷少儿|炫动卡通' + self.Outside + ')).*$',
                '境外台' : self.Outside
            }
        }

    def GetCategories(self, name):
        ret = []
        for k, v in self.filter['类型'].items():
            x = re.findall(v, name)
            if x:
                ret.append(k)
        return ret

