#! /usr/bin/python3
# -*- coding: utf-8 -*-

from engine import VideoEngine

from .anhuitv import AnHuiLiveTV
from .cntv import CntvLiveTV
from .cutv import CuLiveTV
from .guanxitv import GuangXiLiveTV
from .jiansutv import JianSuLiveTV
from .jinlingtv import JilingLiveTV
from .letv import LetvLiveTV
from .livetvdb import TVCategory, LivetvDB, LivetvVideo, LivetvAlbum, \
    LivetvParser
from .qqtv import QQLiveTV
from .sohutv import SohuLiveTV
from .tvielivetv import ParserTVIELivetv
from .xinjiangtv import XinJianLiveTV
from .zhjiantv import ZheJianLiveTV
from .smgbb import SmgbbLivetv
from .btv import BtvLiveTV
from .pptv import PPtvLiveTV

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
        #self.AddMenu(JilingLiveTV ('吉林'))
        #self.AddMenu(CuLiveTV     ('CuTV'))
        #self.AddMenu(CntvLiveTV   ("CNTV"))
        #self.AddMenu(SohuLiveTV   ('Sohu'))
        #self.AddMenu(QQLiveTV     ('腾讯'))
        #self.AddMenu(SmgbbLivetv  ('东方卫视'))
        #self.AddMenu(BtvLiveTV    ('北京'))
        self.AddMenu(PPtvLiveTV   ('PPTV'))
        #self.AddMenu(LetvLiveTV   ('Letv'))
        #self.AddMenu(GuangXiLiveTV('广西'))
        #self.AddMenu(XinJianLiveTV('新疆'))

    def AddMenu(self, menu):
        self.menu.append(menu)
        menu.RegisterParser(self.parserList)
