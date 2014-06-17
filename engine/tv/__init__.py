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
from .wolidou import WolidouLiveTV
from .wasu import WasuLiveTV
from .ccav import CCTVLiveTV

from .安徽 import AnHuiLiveTV
from .北京 import BtvLiveTV
from .广西 import GuangXiLiveTV
from .河北 import HeBeiLiveTV
from .黑龙江 import HeiLongJiangLiveTV
from .湖北 import HuBeiLiveTV
from .江苏 import JianSuLiveTV
from .江西 import JianXiLiveTV
from .吉林 import JilingLiveTV
from .辽宁 import LiaoNingLiveTV
from .上海 import SmgbbLivetv
from .新疆 import XinJianLiveTV
from .云南 import YunNanLiveTV
from .浙江 import ZheJianLiveTV
from .山东 import ShangDongLiveTV
from .湖南 import HuNanLiveTV
from .香港 import HongKongLiveTV
from .广东 import GuanDongLiveTV

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'LivetvEngine'
        self.albumClass = LivetvAlbum

        self.menu = []
        self.parserList = []

        self.LiveEngines = {
            'CCTV' : CCTVLiveTV,
            #'CuTV'  : CuLiveTV,
            'CNTV'  : CntvLiveTV,
            'Sohu'  : SohuLiveTV,
            #'PPTV'  : PPtvLiveTV,
            #'华数'   : WasuLiveTV,
            '黑龙江' : HeiLongJiangLiveTV,
            '浙江'  : ZheJianLiveTV,
            '安徽'  : AnHuiLiveTV,
            '吉林'  : JilingLiveTV,
            '腾讯'  : QQLiveTV,
            '上海'  : SmgbbLivetv,
            '北京'  : BtvLiveTV,
            '辽宁'  : LiaoNingLiveTV,
            '江西'  : JianXiLiveTV,
            '湖北'  : HuBeiLiveTV,
            '湖南'  : HuNanLiveTV,
            '河北'  : HeBeiLiveTV,
            '云南'  : YunNanLiveTV,
            '山东'  : ShangDongLiveTV,
            '香港'  : HongKongLiveTV,
            '湖南'  : HuNanLiveTV,
            '江苏'  : JianSuLiveTV,
            '广东'  : GuanDongLiveTV,

            #'文本'  : TextLiveTV,
            #'私有'  : WolidouLiveTV,
            #'广西'  : GuangXiLiveTV,
            #'新疆'  : XinJianLiveTV,
            #'Letv' : LetvLiveTV,
        }

        for name, e  in self.LiveEngines.items():
            self.AddMenu(e(name))

    def AddMenu(self, menu):
        self.menu.append(menu)
        menu.RegisterParser(self.parserList)

    def Update(self):
        pass