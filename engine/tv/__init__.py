#! /usr/bin/python3
# -*- coding: utf-8 -*-

from engine import VideoEngine

from .anhuitv import AnHuiLiveTV
from .btv import BtvLiveTV
from .cntv import CntvLiveTV
from .cutv import CuLiveTV
from .guanxitv import GuangXiLiveTV
from .hebtv import HeBeiLiveTV
from .hljtv import HeiLongJiangLiveTV
from .hubeitv import HuBeiLiveTV
from .jiansutv import JianSuLiveTV
from .jianxitv import JianXiLiveTV
from .jinlingtv import JilingLiveTV
from .letv import LetvLiveTV
from .livetvdb import *
from .lntv import LiaoNingLiveTV
from .pptv import PPtvLiveTV
from .qqtv import QQLiveTV
from .smgbb import SmgbbLivetv
from .sohutv import SohuLiveTV
from .textv import TextLiveTV
from .tvielivetv import ParserTVIELivetv
from .xinjiangtv import XinJianLiveTV
from .yntv import YunNanLiveTV
from .zhjiantv import ZheJianLiveTV
from .shangdongtv import ShangDongLiveTV
from .wolidou import WolidouLiveTV
from .hunantv import HuNanLiveTV

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'LivetvEngine'
        self.albumClass = LivetvAlbum

        self.menu = []
        self.parserList = []

        self.LiveEngines = {
            '浙江'  : ZheJianLiveTV,
            '安徽'  : AnHuiLiveTV,
            '吉林'  : JilingLiveTV,
            'CuTV'  : CuLiveTV,
            'CNTV'  : CntvLiveTV,
            'Sohu'  : SohuLiveTV,
            '腾讯'  : QQLiveTV,
            '上海'  : SmgbbLivetv,
            '北京'  : BtvLiveTV,
            'PPTV'  : PPtvLiveTV,
            '辽宁'  : LiaoNingLiveTV,
            '黑龙江': HeiLongJiangLiveTV,
            '江西'  : JianXiLiveTV,
            '湖北'  : HuBeiLiveTV,
            '湖南' : HuNanLiveTV,
            '河北'  : HeBeiLiveTV,
            '云南'  : YunNanLiveTV,
            '山东' :  ShangDongLiveTV,
            '文本'  : TextLiveTV,
            #'私有' : WolidouLiveTV,
            #'江苏'  : JianSuLiveTV,
            #'广西' : GuangXiLiveTV,
            #'新疆' : XinJianLiveTV,
            #'Letv' : LetvLiveTV,
        }

        for name, e  in self.LiveEngines.items():
            self.AddMenu(e(name))

    def AddMenu(self, menu):
        self.menu.append(menu)
        menu.RegisterParser(self.parserList)
