#! /usr/bin/python3
# -*- coding: utf-8 -*-

from engine import VideoEngine

from .cntv import CntvLiveTV
from .cutv import CuLiveTV
from .letv import LetvLiveTV
from .livetvdb import *
from .pptv import PPtvLiveTV
from .qqtv import QQLiveTV
from .sohutv import SohuLiveTV
from .textv import TextLiveTV
from .tvielivetv import ParserTVIELivetv
from .wasu import WasuLiveTV
from .wolidou import WolidouTV
from .vst import VstLiveTV

from .上海 import SmgbbLivetv
from .云南 import YunNanLiveTV
from .北京 import BtvLiveTV
from .吉林 import JilingLiveTV
from .安徽 import AnHuiLiveTV
from .山东 import ShangDongLiveTV
from .广西 import GuangXiLiveTV
from .新疆 import XinJianLiveTV
from .江西 import JianXiLiveTV
from .河北 import HeBeiLiveTV
from .浙江 import ZheJianLiveTV
from .湖北 import HuBeiLiveTV
from .辽宁 import LiaoNingLiveTV
from .黑龙江 import HeiLongJiangLiveTV

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'LivetvEngine'
        self.albumClass = LivetvAlbum

        self.LiveEngines = {
            'VST' : VstLiveTV,
            #===================================================================
            'Sohu'  : SohuLiveTV,
            '腾讯'  : QQLiveTV,
            '浙江'  : ZheJianLiveTV,
            '上海'  : SmgbbLivetv,
            '辽宁'  : LiaoNingLiveTV,
            '湖北'  : HuBeiLiveTV,
            '河北'  : HeBeiLiveTV,
            '云南'  : YunNanLiveTV,
            '山东'  : ShangDongLiveTV,
            # '黑龙江' : HeiLongJiangLiveTV, # VST 中已有
            # '安徽'  : AnHuiLiveTV,  # VST 中已有
            # '吉林'  : JilingLiveTV,  # VST 中已有
            #'CNTV'  : CntvLiveTV,  # VST 中已有
            # '江西'  : JianXiLiveTV,   # VST 中已有
            # '文本'  : TextLiveTV,
            #===================================================================

            # '北京'  : BtvLiveTV,
            # '广西'  : GuangXiLiveTV,
            # '新疆'  : XinJianLiveTV,
            # 'Letv' : LetvLiveTV,
            # 'CuTV'  : CuLiveTV,
            # 'PPTV'  : PPtvLiveTV,
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