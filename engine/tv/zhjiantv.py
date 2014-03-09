#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu

from .common import PRIOR_HZTV, PRIOR_ZJTV
from .livetvdb import LivetvParser, LivetvDB
from .tvielivetv import ParserTVIELivetv
from .m2oplayer import M2OLivetvParser


# 杭州电视台
class ParserHangZhouLivetv(M2OLivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '杭州电视台'
        self.area = '中国,浙江,杭州'
        self.order = PRIOR_HZTV

        self.Alias = {}
        self.ExcludeName = ('交通918', 'FM1054', 'FM89')

        self.Alias = {
        }

        self.ExcludeName = ()
        self.baseUrl = 'www.hoolo.tv'
        self.channelIds = (1, 2, 3, 5, 13, 30, 31)

# 浙江电视台
class ParserZJLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.cztv.com')
        self.tvName = '浙江电视台'
        self.area = '中国,浙江'
        self.order = PRIOR_ZJTV

        self.Alias = {
            "频道101" : "浙江卫视",
            "频道102" : "浙江台-钱江频道",
            "频道103" : "浙江台-经视",
            "频道104" : "浙江台-教育科技",
            "频道105" : "浙江台-影视",
            "频道106" : "浙江台-6频道",
            "频道107" : "浙江台-公共新农村",
            "频道108" : "浙江台-少儿",
            #"频道109" : "留学世界",
            #"频道110" : "浙江国际",
            #"频道111" : "好易购"
        }
        self.ExcludeName = ('频道109', '频道1[1,2,3]\w*', '频道[23].*')

# 宁波电视台
class ParserNBLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('ming-api.nbtv.cn')
        self.tvName = '宁波电视台'
        self.area = '中国,浙江,宁波'

        self.Alias = {
            'nbtv1直播' : '宁波台-新闻综合',
            'nbtv2直播' : '宁波台-社会生活',
            'nbtv3直播' : '宁波台-都市文体',
            'nbtv4直播' : '宁波台-影视',
            'nbtv5直播' : '宁波台-少儿',
        }
        self.ExcludeName = ('.*广播', '阳光调频', 'sunhotline')

# 义乌电视台
class ParserYiwuLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('live-01.ywcity.cn')
        self.tvName = '义乌电视台'
        self.area = '中国,浙江,金华,义乌'
        self.Alias = {
            "新闻综合" : '义乌台-新闻综合',
            "商贸频道" : '义乌台-商贸频道',
        }
        self.ExcludeName = ('FM')

# 绍兴电视台
class ParserShaoxinLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('115.239.168.72')
        self.tvName = '绍兴电视台'
        self.area = '中国,浙江,绍兴'

        self.Alias = {
            "新闻综合频道" : '绍兴台-新闻综合',
            "公共频道"     : '绍兴台-公共频道',
            "文化影视频道" : '绍兴台-文化影视',
        }
        self.ExcludeName = ('.*广播', '直播')

# 温州电视台
class ParserWenZhouLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '温州电视台'
        self.area = '中国,浙江,温州'

        self.cmd['source'] = 'http://tv.dhtv.cn'
        self.cmd['regular'] = ['(<a href=.* data-source=.*</a>)']
        self.Alias = {}
        self.ExcludeName = ()

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('data-source="(.*?)" data-id="(.*?)">(.*?)<i>', js['data'])
        for source, data_id, name in ch_list:
            name = '温州台-' + name
            album  = self.NewAlbum(name)

            v = album.NewVideo()
            v.vid      = utils.getVidoId(js['source'] + '/' + source)
            v.order = 2
            v.name     = self.tvName

            v.SetVideoUrlScript('default', 'wztv', ['http://www.dhtv.cn/static/js/tv.js?acm', source])
            v.info = utils.GetScript('wztv', 'get_channel',[data_id])

            album.videos.append(v)
            db.SaveAlbum(album)

class ZheJianLiveTV(LivetvMenu):
    '''
    浙江省内所有电视台
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [
            ParserZJLivetv,      # 浙江省台
            ParserNBLivetv,      # 宁波
            ParserYiwuLivetv,    # 义乌
            ParserShaoxinLivetv, # 绍兴
            ParserHangZhouLivetv,# 杭州台
            ParserWenZhouLivetv, # 温州
        ]
