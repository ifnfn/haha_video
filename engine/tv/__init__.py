#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .livetvdb import TVCategory, LivetvDB, LivetvVideo, LivetvAlbum, LivetvParser
from .tvielivetv import ParserTVIELivetv

from .anhuitv import AnHuiLiveTV
from .zhjiantv import ZheJianLiveTV
from .jiansutv import JianSuLiveTV
from .cutv import CuLiveTV
from .xinjiangtv import XinJianLiveTV
from .guanxitv import GuangXiLiveTV
from .sohutv import SohuLiveTV
from .letv import LetvLiveTV
from .cntv import CntvLiveTV
from .jinlingtv import JilingLiveTV
from .textv import TextLiveTV
from engine import VideoEngine

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'LivetvEngine'
        self.albumClass = LivetvAlbum

        self.parserList = []
        # 引擎菜单
        self.menu = []

        #self.AddMenu(JianSuLiveTV ('江苏'))
        #self.AddMenu(ZheJianLiveTV('浙江'))
        #self.AddMenu(AnHuiLiveTV  ('安徽'))
        #self.AddMenu(XinJianLiveTV('新疆'))
        #self.AddMenu(GuangXiLiveTV('广西'))
        #self.AddMenu(JilingLiveTV ('吉林'))
        #self.AddMenu(CuLiveTV     ('CuTV'))
        self.AddMenu(CntvLiveTV   ("CNTV"))
        #self.AddMenu(SohuLiveTV   ('Sohu'))
        self.AddMenu(LetvLiveTV   ('Letv'))

    def AddMenu(self, menu):
        self.menu.append(menu)
        menu.RegisterParser(self.parserList)
