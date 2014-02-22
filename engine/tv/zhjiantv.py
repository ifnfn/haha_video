#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from xml.etree import ElementTree

from kola import utils, LivetvMenu

from .common import PRIOR_HZTV, PRIOR_ZJTV
from .livetvdb import LivetvParser, LivetvDB
from .tvielivetv import ParserTVIELivetv


# 杭州电视台
class ParserHangZhouLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '杭州电视台'
        self.order = PRIOR_HZTV

        #self.cmd['text'] = 'OK'
        self.Alias = {}
        self.ExcludeName = ('交通918', 'FM1054', 'FM89')
        self.area = '中国,浙江,杭州'

    def Execute(self):
        for i in (1, 2, 3, 5, 13, 14, 15):
            self.cmd['source'] = 'http://api1.hoolo.tv/player/live/channel_xml.php?id=%d' % i
            self.cmd['channel_id'] = i
            self.command.AddCommand(self.cmd)

        self.cmd = None
        self.command.Execute()

    def CmdParser(self, js):
        url = js['source']
        text = js['data']
        root = ElementTree.fromstring(text)

        name = root.attrib['name']
        if name == '':
            return

        ok = False
        for p in root:
            if p.tag == 'video':
                for item in p.getchildren():
                    if 'url' in item.attrib:
                        ok = True
                        break

        if ok == False:
            return

        album  = self.NewAlbum(name)

        v = album.NewVideo()
        v.order = self.order
        v.name  = self.tvName

        v.vid   = utils.getVidoId(url)
        v.SetVideoUrlScript('default', 'hztv', [url])

        chid = utils.autostr(js['channel_id'])
        v.info = utils.GetScript('hztv', 'get_channel',[chid])

        album.videos.append(v)
        LivetvDB().SaveAlbum(album)

# 浙江电视台
class ParserZJLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.cztv.com')
        self.tvName = '浙江电视台'
        self.order = PRIOR_ZJTV

        self.Alias = {
            "频道101" : "浙江卫视",
            "频道102" : "钱江频道",
            "频道103" : "浙江经视",
            "频道104" : "教育科技",
            "频道105" : "浙江影视",
            "频道106" : "6频道",
            "频道107" : "公共新农村",
            "频道108" : "浙江少儿",
            #"频道109" : "留学世界",
            #"频道110" : "浙江国际",
            #"频道111" : "好易购"
        }
        self.ExcludeName = ('频道109', '频道1[1,2,3]\w*', '频道[23].*')
        self.area = '中国,浙江'

# 宁波电视台
class ParserNBLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('ming-api.nbtv.cn')
        self.tvName = '宁波电视台'

        self.Alias = {
            'nbtv1直播' : '宁波-新闻综合',
            'nbtv2直播' : '宁波-社会生活',
            'nbtv3直播' : '宁波-都市文体',
            'nbtv4直播' : '宁波-影视剧',
            'nbtv5直播' : '宁波-少儿',
        }
        self.ExcludeName = ('.*广播', '阳光调频', 'sunhotline')
        self.area = '中国,浙江,宁波'

# 义乌电视台
class ParserYiwuLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('live-01.ywcity.cn')
        self.tvName = '义乌电视台'
        self.Alias = {
            "新闻综合" : '义乌-新闻综合',
            "商贸频道" : '义乌-商贸频道',
        }
        self.ExcludeName = ('FM')
        self.area = '中国,浙江,金华,义乌'

# 绍兴电视台
class ParserShaoxinLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('115.239.168.72')
        self.tvName = '绍兴电视台'
        self.Alias = {
            "新闻综合频道" : '绍兴-新闻综合频道',
            "公共频道"     : '绍兴-公共频道',
            "文化影视频道" : '绍兴-文化影视频道',
        }
        self.ExcludeName = ('.*广播', '直播')
        self.area = '中国,浙江,绍兴'

# 温州电视台
class ParserWenZhouLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '温州电视台'

        self.cmd['source'] = 'http://tv.dhtv.cn'
        self.cmd['regular'] = ['(<a href=.* data-source=.*</a>)']
        self.Alias = {}
        self.ExcludeName = ()
        self.area = '中国,浙江,温州'

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('data-source="(.*?)" .*?>(.*?)<i>', js['data'])
        for source, name in ch_list:
            name = '温州-' + name
            album  = self.NewAlbum(name)

            v = album.NewVideo()
            v.vid      = utils.getVidoId(js['source'] + '/' + source)
            v.order = 2
            v.name     = self.tvName

            v.SetVideoUrlScript('default', 'wztv', ['http://www.dhtv.cn/static/js/tv.js?acm', source])
            v.info = utils.GetScript('wztv', 'get_channel',[source])

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
