#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from urllib.parse import quote

import tornado.escape

from kola.element import LivetvMenu

from .common import PRIOR_DEFTV
from .livetvdb import LivetvParser


class ParserTVIELivetv(LivetvParser):
    def __init__(self, url):
        super().__init__()
        self.base_url = url
        self.order = PRIOR_DEFTV
        self.area = ''

        self.cmd['source'] = 'http://' + self.base_url + '/api/getChannels'
        self.Referer = ''

    def CmdParser(self, js):
        jdata = tornado.escape.json_decode(js['data'])

        for x in jdata['result']:
            if 'group_names' in x and x['group_names'] == 'audio':
                continue

            albumName = ''
            if 'name' in x: albumName = x['name']
            if 'display_name' in x: albumName = x['display_name']

            videoUrl = 'http://' + self.base_url + '/api/getCDNByChannelId/' + x['id']
            if self.base_url in ['api.cztv.com']:
                videoUrl += '?domain=' + self.base_url

            videoUrl = re.sub('^http://', 'tvie://', videoUrl)

            if self.Referer:
                if videoUrl.find("?", 0) > 0:
                    videoUrl += "&referer=" + quote(self.Referer)
                else:
                    videoUrl += "?referer=" + quote(self.Referer)

            album, _ = self.NewAlbumAndVideo(albumName, videoUrl)
            self.db.SaveAlbum(album)

    def GetCategories(self, name):
        return self.tvCate.GetCategories(name)

# 河北省电视台
class ParserHeBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.hebtv.com')
        self.tvName = '河北电视台'
        self.area = '中国,河北'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '河北卫视-标清' : '河北卫视',
            #'河北卫视-高清' : '河北卫视-高清',
            '河北经视' : '河北-经济频道',
            '河北都市' : '河北-都市频道',
            '河北影视' : '河北-影视频道',
            '河北公共' : '河北-公共频道',
            '河北购物' : '河北-购物频道',
            '农民频道' : '河北-农民频道',
            '少儿科教' : '河北-少儿科教',
        }
        self.ExcludeName = []

# 黑龙江省电视台
class ParserHLJLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.hljtv.com')
        self.tvName = '黑龙江电视台'
        self.area = '中国,黑龙江'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '卫视' : '黑龙江卫视',
            '第七' : '黑龙江-第七频道',
            '公共' : '黑龙江-公共频道',
            '考试' : '黑龙江-考试频道',
            '导视' : '黑龙江-导视频道',
        }
        self.ExcludeName = []

# 湖北省电视台
class ParserHuBeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('59.175.153.182')
        self.tvName = '湖北台'
        self.area = '中国,湖北'
        self.order = PRIOR_DEFTV

        self.Alias = {
            'CCTV13' : 'CCTV-13 新闻',
            "湖北公共" : "湖北-公共频道",
            "湖北经视" : "湖北-经视频道",
            "湖北教育" : "湖北-教育频道",
            "湖北体育" : "湖北-体育生活",
            "垄上频道" : "湖北-垄上",
            "天天读网" : "湖北-天天读网",
            "美嘉购物" : "湖北-美嘉购物",
            "城市频道" : "湖北-城市",
            "孕育指南" : "湖北-孕育指南",
            "湖北影视" : "湖北-影视频道",
            "职业指南" : "湖北-职业指南",
            "长江TV"  : "湖北-长江TV",
            "碟市频道" : "湖北-碟市",
        }

        self.ExcludeName = ['.*广播', '卫视备份', '演播室.*', '湖北之声', 'CCTV-13-彩电', '网台直播', 'CCTV13', '湖北电视台',
                            '湖北场外直播', '联播湖北', '湖北卫视彩电备份', '手机电视', '网罗湖北', '虚拟直播', '钓鱼频道', '手机频道']

# 上海电视台
class ParserKksmgLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.kksmg.com')
        self.tvName = '看看'
        self.area = '中国,上海'
        self.order = PRIOR_DEFTV

        self.Alias = {
            "娱乐频道" : "上海-娱乐频道",
            "艺术人文" : "上海-艺术人文",
            "戏剧频道" : "上海-戏剧",
            "ICS"     : "上海-外语频道ICS",
            "星尚酷"   : "上海-星尚酷",
            "上海导视" : "上海-导视",
            "新闻综合" : "上海-新闻综合",
            "星尚"     : "上海-星尚",
            "第一财经" : "上海-第一财经",
            "纪实频道" : "上海-纪实频道",
        }
        self.ExcludeName = ['.*电台', '东广新闻', '动感101', '经典947', 'LoveRadio',
                            '第一财经音频', 'Sport', '.*广播'
        ]

# 新疆电视台
class ParserUCLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('epgsrv01.ucatv.com.cn')
        self.tvName = '新疆电视台'
        self.order = PRIOR_DEFTV

        self.ExcludeName = ['.*广播', '106点5旅游音乐', '天山云LIVE', 'CCTV']
        self.area = '中国,新疆'
        self.Alias = {
            'CCTV-1' : 'CCTV-1 综合',
            'CCTV-2' : 'CCTV-2 财经',
            'CCTV-3' : 'CCTV-3 综艺',
            'CCTV-4' : 'CCTV-3 国际',
            'CCTV-5' : 'CCTV-5 体育',
            'CCTV-6' : 'CCTV-6 电影',
            'CCTV-7' : 'CCTV-7 军事农业',
            'CCTV-8' : 'CCTV-8 电视剧',
            'CCTV-9' : 'CCTV-9 纪录',
            'CCTV-10' : 'CCTV-10 科教',
            'CCTV-11' : 'CCTV-11 戏曲',
            'CCTV-12' : 'CCTV-12 社会与法',
            'CCTV-13' : 'CCTV-13 新闻',
            'CCTV-少儿' : 'CCTV-14 少儿',
            'CCTV5-plus': 'CCTV5+ 体育赛事',
            '中央电视台五套' : 'CCTV-5 体育',
            '中央电视台十三套' : 'CCTV-13 新闻',
            'UTV-1' : '乌鲁木齐-新闻综合(汉)',
            'UTV-2' : '乌鲁木齐-新闻综合(维)',
            'UTV-3' : '乌鲁木齐-影视频道',
            'UTV-4' : '乌鲁木齐-生活服务',
            'UTV-5' : '乌鲁木齐-文体娱乐',
            'UTV-6' : '乌鲁木齐-妇女儿童',

            'XJTV-1' : '新疆-卫星频道(汉)',
            'XJTV-2' : '新疆-卫星频道(维)',
            'XJTV-3' : '新疆-卫星频道(哈)',
            'XJTV-4' : '新疆-综艺频道(汉)',
            'XJTV-5' : '新疆-综艺频道(维)',
            'XJTV-6' : '新疆-影视频道(汉)',
            'XJTV-7' : '新疆-经济生活(汉)',
            'XJTV-8' : '新疆-综艺频道(哈)',
            'XJTV-9' : '新疆-经济生活(维)',
            'XJTV-10': '新疆-体育健康(汉)',
            'XJTV-11': '新疆-法制信息频道',
            'XJTV-12': '新疆-少儿频道',
            '福建卫视' : '东南卫视',
        }

# 云南电视台
class ParserYunNanLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('mediamobile.yntv.cn')
        self.tvName = '云南电视台'
        self.area = '中国,云南'
        self.order = PRIOR_DEFTV

        self.Alias = {
            '卫视频道YNTV_1' : '云南卫视',
            '都市频道YNTV_2' : '云南-都市频道',
            '娱乐频道YNTV_3' : '云南-娱乐频道',
            '公共频道YNTV_6' : '云南-公共频道',
            '都市频道'       : '云南-都市频道',
            '国际频道'       : '云南-国际频道',
        }
        self.ExcludeName = ['云南卫视CDN']
        self.Referer = 'http://store1.yntv.cn/flash-player'

# 浙江电视台
class ParserZJLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.cztv.com')
        self.tvName = '浙江电视台'
        self.area = '中国,浙江'
        self.order = PRIOR_DEFTV

        self.Alias = {
            "频道101" : "浙江卫视",
            "频道102" : "浙江-钱江频道",
            "频道103" : "浙江-经视",
            "频道104" : "浙江-教育科技",
            "频道105" : "浙江-影视娱乐",
            "频道106" : "浙江-6频道",
            "频道107" : "浙江-公共新农村",
            "频道108" : "浙江-少儿频道",
            # "频道109" : "留学世界",
            # "频道110" : "浙江国际",
            # "频道111" : "好易购"
        }
        self.ExcludeName = ['频道109', '频道1[1,2,3]\w*', '频道[23].*']

# 宁波电视台
class ParserNBLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('ming-api.nbtv.cn')
        self.tvName = '宁波电视台'
        self.area = '中国,浙江,宁波'

        self.Alias = {
            'nbtv1直播' : '宁波-新闻综合',
            'nbtv2直播' : '宁波-社会生活',
            'nbtv3直播' : '宁波-都市文体',
            'nbtv4直播' : '宁波-影视剧',
            'nbtv5直播' : '宁波-少儿频道',
        }
        self.ExcludeName = ['.*广播', '阳光调频', 'sunhotline']

# 义乌电视台
class ParserYiwuLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('live-01.ywcity.cn')
        self.tvName = '义乌电视台'
        self.area = '中国,浙江,金华,义乌'
        self.Alias = {
            "公共文艺" : '义乌-公共文艺',
            "新闻综合" : '义乌-新闻综合',
            "商贸频道" : '义乌-商贸频道',
        }
        self.ExcludeName = ['FM']

# 绍兴电视台
class ParserShaoxinLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('115.239.168.72')
        self.tvName = '绍兴电视台'
        self.area = '中国,浙江,绍兴'

        self.Alias = {
            "新闻综合频道" : '绍兴-新闻综合',
            "公共频道"    : '绍兴-公共频道',
            "文化影视频道" : '绍兴-文化影视',
        }
        self.ExcludeName = ['.*广播', '直播']

# 南京电视台
class ParserNanJinLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('live.xwei.tv')
        self.tvName = '南京电视台'
        self.area = '中国,江苏,南京'
        self.Alias = {
            "新闻综合频道" : "南京-新闻综合",
            "教科频道" : "南京-教科频道",
            "生活频道" : "南京-生活频道",
            "娱乐频道" : "南京-娱乐频道",
            "少儿频道" : "南京-少儿频道",
            "十八频道" : "南京-十八频道"
        }
        self.ExcludeName = ['测试']

# 遂宁电视台
class ParserSuilinLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('mid.sngdxsn.com')
        self.tvName = '遂宁电视台'
        self.area = '中国,四川,遂宁'
        self.Alias = {
            "新闻综合" : "遂宁-新闻",
            "公共公益" : "遂宁-公共",
            "互动频道" : "遂宁-影视",
            "直播频道" : "遂宁-直播",
        }
        self.ExcludeName = ['FM']

# 合肥电视台
class ParserHeFeiLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('live2.hfbtv.com')
        self.tvName = '合肥电视台'
        self.area = '中国,安徽,合肥'
        self.Alias = {
            "新闻" : "合肥-新闻频道",
            "生活" : "合肥-生活频道",
            "财经" : "合肥-财经频道",
            "法制" : "合肥-教育法制",
            "文体" : "合肥-文体博览",
        }

# 石家庄电视台
class ParserSJZLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.2300sjz.com')
        self.tvName = '石家庄电视台'
        self.area = '中国,河北,石家庄'
        self.Alias = {
            "雪梨TV" : "石家庄-雪梨TV",
            "新闻" : "石家庄-新闻综合",
            "娱乐" : "石家庄-娱乐",
            "生活" : "石家庄-生活",
            "都市" : "石家庄-都市",
        }
        self.ExcludeName = ['广播', '绿色之声', 'linshi']

# 巴东电视台
class ParserBaDongLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('vod.bdntv.cn')
        self.tvName = '巴东电视台'
        self.area = '中国,湖北,恩施,巴东'
        self.Alias = {
            "巴东新闻" : "巴东-新闻综合"
        }
        self.ExcludeName = ['广播']

# 芜湖电视台
class ParserWuhubLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('live.wuhubtv.com')
        self.tvName = '芜湖电视台'
        self.area = '中国,安徽,芜湖'
        self.Alias = {
            "新闻综合": "芜湖-新闻综合",
            "生活频道": "芜湖-生活频道",
            "徽商频道": "芜湖-徽商频道",
            "教育频道": "芜湖-教育频道"
        }

        self.ExcludeName = ['广播']

class TvieLiveTV(LivetvMenu):
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserHeBeiLivetv,
                                ParserHLJLivetv,
                                ParserHuBeiLivetv,
                                ParserKksmgLivetv,
                                ParserUCLivetv,
                                ParserYunNanLivetv,
                                ParserZJLivetv,
                                ParserNBLivetv,
                                ParserYiwuLivetv,
                                ParserShaoxinLivetv,
                                ParserNanJinLivetv,
                                ParserSuilinLivetv,
                                ParserHeFeiLivetv,
                                ParserSJZLivetv,
                                ParserBaDongLivetv,
                                ParserWuhubLivetv
                            ]


