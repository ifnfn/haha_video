#! /usr/bin/python3
# -*- coding: utf-8 -*-

from engine import VideoEngine

from .cntv import CntvLiveTV
from .iqilu import IQiluLiveTV
from .livetvdb import *
from .m2oplayer import M2OLiveTV
from .pptv import PPtvLiveTV
from .qqtv import QQLiveTV
from .sohutv import SohuLiveTV
from .textv import TextLiveTV
from .tvielivetv import TvieLiveTV
from .vst import VstLiveTV
from .wasu import WasuLiveTV
from .wolidou import WolidouTV
from .yy import YYLiveTV


from .上海 import SmgbbLivetv
from .北京 import BtvLiveTV
from .吉林 import JilingLiveTV
from .广西 import GuangXiLiveTV
from .江西 import JianXiLiveTV
from .浙江 import ZheJianLiveTV
from .辽宁 import LiaoNingLiveTV

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'LivetvEngine'
        self.albumClass = LivetvAlbum

        self.LiveEngines = {
            #===================================================================
            'VST' : VstLiveTV,
            'Sohu'  : SohuLiveTV,
            '腾讯'  : QQLiveTV,
            'PPTV'  : PPtvLiveTV,
            '浙江'  : ZheJianLiveTV,
            '上海'  : SmgbbLivetv,
            '辽宁'  : LiaoNingLiveTV,
            'TVIE' : TvieLiveTV,
            'M2O'  : M2OLiveTV,
            '文本'  : TextLiveTV,
            #'YY'    : YYLiveTV,
            'Qilu'  : IQiluLiveTV
            #===================================================================
            # '吉林'  : JilingLiveTV,  # VST 中已有
            # 'CNTV'  : CntvLiveTV,  # VST 中已有
            # '江西'  : JianXiLiveTV,   # VST 中已有
            # '文本'  : TextLiveTV,

            # '北京'  : BtvLiveTV,
            # '广西'  : GuangXiLiveTV,
            # '华数'   : WasuLiveTV,
            # '私有'  : WolidouLiveTV,
        }

        for name, e  in self.LiveEngines.items():
            self.AddMenu(e(name))

    def AddMenu(self, menu):
        self.menu.append(menu)
        menu.RegisterParser(self.parserList)

    def Update(self):
        pass

class Live2Engine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'Livetv2Engine'
        self.albumClass = LivetvAlbum

        self.LiveEngines = {
            'JSON'  : WolidouTV,
        }

        for name, e  in self.LiveEngines.items():
            self.AddMenu(e(name))

    def AddMenu(self, menu):
        self.menu.append(menu)
        menu.RegisterParser(self.parserList)

    def Update(self):
        pass