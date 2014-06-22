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
from .wolidou import WolidouLiveTV
from .wolidou_json import JsonLiveTV


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
from .香港 import HongKongLiveTV
from .黑龙江 import HeiLongJiangLiveTV

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'LivetvEngine'
        self.albumClass = LivetvAlbum

        self.LiveEngines = {
            'CNTV'  : CntvLiveTV,
            'Sohu'  : SohuLiveTV,
            '黑龙江' : HeiLongJiangLiveTV,
            '浙江'  : ZheJianLiveTV,
            '安徽'  : AnHuiLiveTV,
            '吉林'  : JilingLiveTV,
            '腾讯'  : QQLiveTV,
            '上海'  : SmgbbLivetv,
            '辽宁'  : LiaoNingLiveTV,
            '江西'  : JianXiLiveTV,
            '湖北'  : HuBeiLiveTV,
            '河北'  : HeBeiLiveTV,
            '云南'  : YunNanLiveTV,
            '山东'  : ShangDongLiveTV,
            '香港'  : HongKongLiveTV,
            #'JSON'  : JsonLiveTV,

            # '北京'  : BtvLiveTV,
            # '文本'  : TextLiveTV,
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
            'JSON'  : JsonLiveTV,
        }

        for name, e  in self.LiveEngines.items():
            self.AddMenu(e(name))

    def AddMenu(self, menu):
        self.menu.append(menu)
        menu.RegisterParser(self.parserList)

    def Update(self):
        pass