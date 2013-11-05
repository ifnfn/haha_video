#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import traceback
import sys
import json
import re
import redis
import base64
import tornado.escape

from bs4 import BeautifulSoup as bs
from engine import VideoBase, AlbumBase, VideoMenuBase, VideoEngine, Template
from utils import autostr, autoint, json_get, log

#================================= 以下是搜狐视频的搜索引擎 =======================================
SOHU_HOST = 'tv.sohu.com'
MAX_TRY = 3

# 搜狐节目列表
class TemplateVideoAll(Template):
    def __init__(self, menu):
        cmd = {
            'name' : 'sohu_videoall',
            'source': menu.homePage
        }
        super().__init__(menu.command, cmd)

# 搜狐节目列表
class TemplateVideoList(Template):
    def __init__(self, menu, url):
        cmd = {
            'name': 'sohu_videolist',
            'source': url,
            'regular': [
                '<p class="tit tit-p"><a target="_blank"\s*(.+)>.*</a>'
            ]
        }
        super().__init__(menu.command, cmd)

# 搜狐节目
class TemplateAlbumPage(Template):
    def __init__(self, album):
        cmd = {
            'name'    : 'sohu_album',
            'source'  : album.albumPageUrl,
            'regular' : [
                'var ((playlistId|pid|vid|PLAYLIST_ID|cid|playAble)\s*=\W*([\d,]+))'
            ],
            'cache' : True
        }
        super().__init__(album.command, cmd)

# 搜狐节目指数
class TemplateAlbumScore(Template):
    def __init__(self, album):
        cmd = {
            'name'    : 'sohu_album_score',
            'source'  : 'http://index.tv.sohu.com/index/switch-aid/%s' % album.playlistid,
            'json'    : [
                'attachment.album',
                'attachment.index'
            ],
            'cache' : False
        }
        super().__init__(album.command, cmd)

# 总播放次数，(如果没有指数的话）
class TemplateAlbumTotalPlayNum(Template):
    def __init__(self, album):
        cmd = {
            'name'    : 'sohu_album_total_playnum',
            'source'  : 'http://count.vrs.sohu.com/count/query.action?videoId=%s,' % album.vid,
            'cache' : False
        }
        super().__init__(album.command, cmd)

# http://count.vrs.sohu.com/count/query.action?videoId=1268037
# 更新热门节目信息
class TemplateAlbumHotList(Template):
    def __init__(self, menu, url):
        cmd = {
            'name'    : 'sohu_albumlist_hot',
            'source'  : url,
        }
        super().__init__(menu.command, cmd)

# 更新节目的完整信息
class TemplateAlbumFullInfo(Template):
    def __init__(self, album):
        cmd = {
            'name' : 'sohu_album_fullinfo',
            'source' : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s&vid=%s' % (album.playlistid, album.vid),
            'cache' : True
        }
        super().__init__(album.command, cmd)

# 更新节目的完整信息
class TemplateAlbumMvInfo(Template):
    def __init__(self, album, source_url):
        cmd = {
            'name'    : 'sohu_album_mvinfo',
            'source'  : 'http://search.vrs.sohu.com/mv_i%s.json' % album.vid,
            'homePage': source_url,
            'regular' : ['var video_album_videos_result=(\{.*.\})'],
            'cache' : False
        }
        super().__init__(album.command, cmd)

# 更新节目的完整信息, 只是通过vid 拿到 playlistid
class TemplateAlbumMvInfoMini(Template):
    def __init__(self, album, source_url):
        cmd = {
            'name'    : 'sohu_album_mvinfo_mini',
            'source'  : 'http://search.vrs.sohu.com/mv_i%s.json' % album.vid,
            'homePage': source_url,
            'regular' : ['("playlistId":\w+)'],
            'cache' : False
        }
        super().__init__(album.command, cmd)

# 更新节目的播放信息
class TemplateAlbumPlayInfo(Template):
    def __init__(self, album, url):
        cmd = {
            'name'   : 'sohu_album_playinfo',
            'source' : url, #'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s',
            'json' : [
                'data.highVid',
                'data.norVid',
                'data.oriVid',
                'data.superVid',
                'data.relativeId',
                'id'
            ],
            'cache' : False
        }
        super().__init__(album.command, cmd)

# 更新节目的播放信息
class TemplateLiveTVInfo(Template):
    def __init__(self, menu):
        cmd = {
            'name'   : 'sohu_livetv_list',
            'source' : 'http://tvimg.tv.itc.cn/live/top.json'
        }
        super().__init__(menu.command, cmd)

class SohuVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

    def GetVideoPlayUrl(self, definition=0):
        vid = self.GetVid(definition)
        if vid:
            return 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s' % vid
        else:
            return ''

class SohuAlbum(AlbumBase):
    def __init__(self, parent):
        AlbumBase.__init__(self, parent)
        self.VideoClass = SohuVideo

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        if self.albumPageUrl:
            if self.playlistid:
                TemplateAlbumFullInfo(self)
            #if self.vid:
            #    TemplateAlbumMvInfo(self, self.albumPageUrl)

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        if self.playlistid:
            TemplateAlbumScore(self).Execute()

    # 更新节目主页
    def UpdateAlbumPageCommand(self):
        if self.albumPageUrl:
            TemplateAlbumPage(self).Execute()

    # 更新节目播放信息
    def UpdateAlbumPlayInfoCommand(self):
        url = self.GetVideoPlayUrl()
        if url != '':
            TemplateAlbumPlayInfo(self, url)

class SohuVideoMenu(VideoMenuBase):
    def __init__(self, name, engine):
        VideoMenuBase.__init__(self, name, engine)
        self.homePage = ''
        self.HomeUrlList = []
        if hasattr(self, 'number'):
            self.HomeUrlList = ['http://so.tv.sohu.com/list_p1%d_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html' % self.number]

        self.albumClass = SohuAlbum
        self.filter_year = {
            '2013' : '',
            '2012' : '',
            '2011' : '',
            '2010' : '',
            '00年代': '',
            '90年代': '',
            '80年代': '',
            '更早'  : ''
        }
        self.key = {
            '类型' : 'p2',
            '产地' : 'p3',
            '地区' : 'p3',
            '年份' : 'p4',
            '篇幅' : 'p5',
            '年龄' : 'p6',
            '排序' : 'p7',
            '状态' : 'p9',
            '页号' : 'p10',
            '语言' : 'p11',
        }
        self.sort = {
            '周播放最多' : 7,
            '日播放最多' : 5,
            '总播放最多' : 1,
            '最新发布'   : 3,
            '评分最高'   : 4
        }
        self.quickFilter = {
            '热门电影' : {
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '最新电影' :{
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '推荐电影' :{
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '港台电影' : {
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            }
        }

    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        for url in self.HomeUrlList:
            TemplateVideoList(self, url).Execute()
        #if self.homePage != "":
        #    TemplateVideoAll(self).Execute()

    def UpdateHotList(self):
        # http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3&encode=GBK
        fmt = 'http://so.tv.sohu.com/iapi?v=%d&c=%d&sc=%s&o=3'
        v = 4
        if self.number == 100:
            v = 2
        sc = ''
        if '类型' in self.filter:
            for (_, v) in list(self.filter['类型'].items()):
                sc = sc + v + '_'
        url = fmt % (v, self.number, sc)

        TemplateAlbumHotList(self, url).Execute()

    def UpdateHotList2(self):
        # http://so.tv.sohu.com/jsl?c=100&area=5&cate=100102_100122&o=1&encode=GBK
        fmt = 'http://so.tv.sohu.com/jsl?c=%d&cate=%s&o=1'
        sc = ''
        if '类型' in self.filter:
            for (_, v) in list(self.filter['类型'].items()):
                sc += v + '_'
        url = fmt % (v, self.number, sc)

        TemplateAlbumHotList(self, url).Execute()

    def GetRealPlayer(self, text, definition, step):
        if step == '1':
            res = self._ParserRealUrlStep1(text)
        else:
            res = self._ParserRealUrlStep2(text)

        return json.dumps(res, indent=4, ensure_ascii=False)

    def _ParserRealUrlStep1(self, text):
        res = {}
        try:
            jdata = tornado.escape.json_decode(text)
            if 'data' not in jdata:
                return res

            host = jdata['allot']
            prot = jdata['prot']
            vid = jdata['id']

            urls = []
            data = jdata['data']
            if data == None:
                return {}

            if 'totalBytes' in data:
                res['totalBytes'] = data['totalBytes']

            if 'totalBlocks' in data:
                res['totalBlocks'] = data['totalBlocks']

            if 'totalDuration' in data:
                res['totalDuration'] = data['totalDuration']
            if 'clipsDuration' in data:
                res['clipsDuration'] = data['clipsDuration']
            if 'height' in data:
                res['height'] = data['height']
            if 'width' in data:
                res['width'] = data['width']

            if 'fps' in data:
                res['fps'] = data['fps']

            if 'scap' in jdata: # 字幕
                res['scap'] = jdata['scap']

            for tfile, new, duration, byte in zip(data['clipsURL'], data['su'], data['clipsDuration'], data['clipsBytes']):
                x = {}
                x['duration'] = duration
                x['size'] = byte
                x['new'] = new
                x['url'] = 'http://%s/?prot=%s&file=%s&new=%s' % (host, prot, tfile, new)
                urls.append(x)

            res['sets'] = urls
            res['vid'] = vid

            # TODO
            self.engine._UpdateVideoVid(jdata, res)

            return res
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep1: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return res;

    def _ParserRealUrlStep2(self, text):
        ret = {}
        try:
            ret = tornado.escape.json_decode(text)

            if 'sets' in ret:
                urls = []
                for url in ret['sets']:
                    new = url['new']
                    text = base64.decodebytes(url['url'].encode()).decode()

                    start, _, _, key, _, _, _, _ = text.split('|')
                    u = '%s%s?key=%s' % (start[:-1], new, key)
                    urls.append(u)

                ret['sets'] = urls
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ret

# 电影
class SohuMovie(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 100
        SohuVideoMenu.__init__(self, name, engine)
#        self.HomeUrlList = [
#            'http://so.tv.sohu.com/list_p1100_p20_p3_p40_p5_p6_p73_p80_p9_2d1_p101_p11.html',
#        ]
        self.cid = 1
        self.homePage = 'http://tv.sohu.com/movieall/'
        self.filter = {
            '年份' :  self.filter_year,
            '类型' : {
                '爱情片' : '100100',
                '战争片' : '100101',
                '喜剧片' : '100102',
                '科幻片' : '100103',
                '恐怖片' : '100104',
                '动画片' : '100105',
                '动作片' : '100106',
                '风月片' : '100107',
                '剧情片' : '100108',
                '歌舞片' : '100109',
                '纪录片' : '100110',
                '魔幻片' : '100111',
                '灾难片' : '100112',
                '悬疑片' : '100113',
                '传记片' : '100114',
                '警匪片' : '100116',
                '伦理片' : '100117',
                '惊悚片' : '100118',
                '谍战片' : '100119',
                '历史片' : '100120',
                '武侠片' : '100121',
                '青春片' : '100122',
                '文艺片' : '100123'
            },
            '产地' : {
                '内地'  : '5',
                '香港'  : '27',
                '台湾'  : '28',
                '日本'  : '3',
                '韩国'  : '4',
                # '欧洲' : '2',
                '美国'  : '12',
                '英国'  : '17',
                '法国'  : '18',
                '德国'  : '19',
                '意大利': '20',
                '西班牙': '21',
                '俄罗斯': '24',
                '加拿大': '25',
                '印度'  : '22',
                '泰国'  : '23',
                '其他'  : ''
            }
        }
        self.quickFilter = {
            '热门电影' :{
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '最新电影' :{
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '推荐电影' :{
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '国产电影' : {
                    'filter': {
                        '地区' : '内地'
                    },
                    'sort' : '日播放最多'
            },
            '欧美大片' : {
                    'filter': {
                        '地区' : '美国,英国,法国,德国,意大利,西班牙,俄罗斯'
                    },
                    'sort' : '日播放最多'
            },
            '港台电影' : {
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '日韩电影' : {
                    'filter': {
                        '地区' : '日本,韩国'
                    },
                    'sort' : '日播放最多'
            },
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 电视
class SohuTV(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 101
        SohuVideoMenu.__init__(self, name, engine)
        self.cid = 2

        self.homePage = 'http://tv.sohu.com/tvall/'
        self.filter = {
            '年份' : self.filter_year,
            '类型' : {
                '偶像片'   : '101100',
                '家庭片'   : '101101',
                '历史片'   : '101102',
                '年代片'   : '101103',
                '言情片'   : '101104',
                '武侠片'   : '101105',
                '古装片'   : '101106',
                '都市片'   : '101107',
                '农村片'   : '101108',
                '军旅片'   : '101109',
                '刑侦片'   : '101110',
                '喜剧片'   : '101111',
                '悬疑片'   : '101112',
                '情景片'   : '101113',
                '传记片'   : '101114',
                '科幻片'   : '101115',
                '动画片'   : '101116',
                '动作片'   : '101117',
                '真人秀片' : '101118',
                '栏目片'   : '101119',
                '谍战片'   : '101120',
                '伦理片'   : '101121',
                '战争片'   : '101122',
                '神话片'   : '101123',
                '惊悚片'   : '101124',
            },
            '产地' : {
                '内地' : '5',
                '港剧' : '6',
                '台剧' : '7',
                '美剧' : '9',
                '韩剧' : '8',
                '英剧' : '10',
                '泰剧' : '11',
                '日剧' : '15',
                '其他' : ''
            }
        }
        self.quickFilter = {
            '热播剧' :{
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '最新更新' :{
                    'sort' : '最新发布'
            },
            '推荐' :{
                    'sort' : '评分最高'
            },
            '国内剧' : {
                    'filter': {
                        '地区' : '内地'
                    },
                    'sort' : '日播放最多'
            },
            '韩剧' : {
                    'filter': {
                        '地区' : '韩国'
                    },
                    'sort' : '日播放最多'
            },
            '港台剧' : {
                    'filter': {
                        '地区' : '香港,台湾'
                    },
                    'sort' : '日播放最多'
            },
            '美剧' : {
                    'filter': {
                        '地区' : '美国'
                    },
                    'sort' : '日播放最多'
            },
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 动漫
class SohuComic(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 115
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = 'http://tv.sohu.com/comicall/'
        self.filter = {
            '年份' : self.filter_year,
            '篇幅' : {
                '剧场版' : '1',
                'TV版'   : '2',
                '花絮'   : '3',
                'OVA'    : '5',
                '其他'   : '3'
            },
            '类型' : {
                '历史'   : '115100',
                '搞笑'   : '115101',
                '战斗'   : '115102',
                '冒险'   : '115103',
                '魔幻'   : '115104',
                '励志'   : '115105',
                '益智'   : '115106',
                '童话'   : '115107',
                '体育'   : '115108',
                '神话'   : '115110',
                '青春'   : '115111',
                '悬疑'   : '115112',
                '真人'   : '115113',
                '亲子'   : '115114',
                '恋爱'   : '115118',
                '科幻'   : '115123',
                '治愈'   : '115124',
                '日常'   : '115125',
                '神魔'   : '115126',
                '百合'   : '115127',
                '耽美'   : '115128',
                '校园'   : '115129',
                '后宫'   : '115130',
                '美少女' : '115131',
                '竞技'   : '115132',
                '机战'   : '1151233',
            },
            '产地' : {
                '大陆' : '1',
                '日本' : '2',  # 7
                '美国' : '3',
                '韩国' : '5',
                '香港' : '6',
                '欧洲' : '',  # 英国8 加拿大 11 俄罗期 13
                '其他' : '',
            },
            '年龄' : {
                '5岁以下'   : '0',
                '5岁-12岁'  : '1',
                '13岁-18岁' : '2',
                '18岁以上'  : '3',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 综艺
class SohuShow(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 106
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = ''
        self.filter = {
            '类型' : {
                '访谈'     : '106100',
                '时尚'     : '106101',
                '游戏竞技' : '106102',
                'KTV'      : '106103',
                '交友'     : '106104',
                '选秀'     : '106105',
                '音乐'     : '106106',
                '曲艺'     : '106107',
                '养生'     : '106109',
                '脱口秀'   : '106110',
                '歌舞'     : '106111',
                '娱乐节目' : '106112',
                '真人秀'   : '106113',
                '其他'     : '106118'
            },
            '产地' : {
                '内地' : '5',
                '港台' : '14',
                '欧美' : '',  # 15?
                '日韩' : '16',
                '其他' : '',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 记录片
class SohuDocumentary(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 107
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = ''
        self.filter = {
            '类型': {
                  '人物' : '107100',
                  '历史' : '107101',
                  '自然' : '107102',
                  '军事' : '107103',
                  '社会' : '107104',
                  '幕后' : '107105',
                  '财经' : '107106',
                  '搜狐视频大视野' : '107107',
                  '剧情' : '107108',
                  '旅游' : '107109',
                  '科技' : '107110',
                  '文化' : '107111',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 教育
class SohuEdu(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 119
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = ''
        self.filter = {
            '类型': {
                '公开课':'119100',
                '考试辅导':'119101',
                '职业培训':'119102',
                '外语学习':'119103',
                '幼儿教育':'119104',
                '乐活':'119105',
                '职场管理':'119106',
                '中小学教育':'119107'
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 新闻
class SohuNew(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 122
        SohuVideoMenu.__init__(self, name, engine)
        self.filter = {
            '类型':{
                '国内':'122204',
                '国际':'122205',
                '军事':'122101',
                '科技':'122106',
                '财经':'122104',
                '社会':'122102',
                '生活':'122999',
            },
            '范围': {
                '今天':'86400',
                '本周':'604800',
                '本月':'2592000',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 娱乐
class SohuYule(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 112
        SohuVideoMenu.__init__(self, name, engine)
        self.filter = {
            '类型':{
                '明星':'112103',
                '电影':'112100',
                '电视':'112101',
                '音乐':'112102',
                '戏剧':'112202',
                '动漫':'112201',
                '其他':'112203',
            },
            '范围':{
                '今天':'86400',
                '本周':'604800',
                '本月':'2592000',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 旅游
class SohuTour(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 131
        SohuVideoMenu.__init__(self, name, engine)
        self.filter = {
            '类型': {
                '自驾游' : '131100',
                '攻略' : '131101',
                '交通住宿' : '131102',
                '旅游资讯' : '131103',
                '国内游' : '131104',
                '境外游' : '131105',
                '自然' : '131106',
                '人文' : '131107',
                '户外' : '131108',
                '美食' : '131109',
                '节庆活动' : '131110',
            }
        }

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

# 直播电视
class SohuLiveTV(SohuVideoMenu):
    def __init__(self, name, engine):
        self.number = 200
        SohuVideoMenu.__init__(self, name, engine)
        self.homePage = 'http://tv.sohu.com/live/'
        self.cid = 200
        self.filter = {
            '类型': {
                '卫视台':1,
                '地方台':2,
                '央视台':3,
                '境外台':4,
            }
        }
    # 更新该菜单下所有节目列表
    def UpdateAlbumList(self):
        if self.homePage != "":
            TemplateLiveTVInfo(self).Execute()

    # 更新热门电影信息
    def UpdateHotInfo(self):
        pass

    def _ParserRealUrlStep1(self, text):
        res = {}
        jdata = tornado.escape.json_decode(text)
        if 'data' in jdata:
            data = jdata['data']
            if 'live' in data:
                res['live'] = data['live']
                urls = []
                x = {}
                x['url'] = res['live']
                urls.append(x)

                res['sets'] = urls
                res['vid'] = jdata['lid']
        return res

    def _ParserRealUrlStep2(self, text):
    # {"code":"000000","msg":"OK","url":"http://122.228.223.139:80/live/31?key=H7mpogs3o-c84CTkTvx7PB6ME-QWypUS&ver=seg&n=1&a=1012&cip=115.236.90.218","cid":"31","nid":"347","cip":"115.236.90.218","key":"H7mpogs3o-c84CTkTvx7PB6ME-QWypUS","sp":"0"}
        ret = {}
        try:
            ret = tornado.escape.json_decode(text)

            if 'sets' in ret:
                urls = []
                for url in ret['sets']:
                    text = base64.decodebytes(url['url'].encode()).decode()
                    jdata = tornado.escape.json_decode(text)
                    if jdata['msg'] == 'OK':
                        u = jdata['url']
                        urls.append(u)

                ret['sets'] = urls
        except:
            t, v, tb = sys.exc_info()
            log.error('SohuEngine._ParserRealUrlStep2: %s,%s,%s' % (t, v, traceback.format_tb(tb)))

        return ret

# Sohu 搜索引擎
class SohuEngine(VideoEngine):
    def __init__(self, db, command):
        VideoEngine.__init__(self, db, command)

        self.engine_name = 'SohuEngine'
        self.albumClass = SohuAlbum
        self.videoClass = SohuVideo

        # 引擎主菜单
        self.menu = {
            '电影'   : SohuMovie,
            '电视剧' : SohuTV,
           # '综艺'   : SohuShow,
           # '娱乐'   : SohuYule,
           # '动漫'   : SohuComic,
           # '纪录片' : SohuDocumentary,
           # '教育'   : SohuEdu,
           # '旅游'   : SohuTour,
           # '新闻'   : SohuNew,
           # '直播'   : SohuLiveTV
        }

        self.parserList = {
                   'sohu_videolist'           : self._CmdParserVideoList,
                   'sohu_album'               : self._CmdParserAlbumPage,
                   'sohu_album_score'         : self._CmdParserAlbumScore,
                   'sohu_videoall'            : self._CmdParserAlbumList,
                   'sohu_albumlist_hot'       : self._CmdParserHotInfoByIapi,
                   'sohu_album_fullinfo'      : self._CmdParserAlbumFullInfo,
                   'sohu_album_mvinfo'        : self._CmdParserAlbumMvInfo,
                   'sohu_album_mvinfo_mini'   : self._CmdParserAlbumMvInfo,
                   'sohu_album_playinfo'      : self._CmdParserAlbumPlayInfo,
                   'sohu_album_total_playnum' : self._CmdParserAlbumTotalPlayNum,
                   'sohu_livetv_list'         : self._CmdParserLiveTVList,
        }

    # 解析热门节目
    # http://so.tv.sohu.com/iapi?v=4&c=115&t=1&sc=115101_115104&o=3
    # sohu_albumlist_hot
    def _CmdParserHotInfoByIapi(self, js):
        ret = []
        try:
            js = tornado.escape.json_decode(js['data'])

            tv = None
            if 'r' in js:
                for p in js['r']:
                    if 'url' in p:
                        tv = self.GetAlbumFormDB(albumPageUrl = p['url'])
                    elif 'aurl' in p:
                        tv = self.GetAlbumFormDB(albumPageUrl = p['aurl'])
            self._save_update_append(ret, tv)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserHotInfoByIapi  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

    # 通过 vid 获得节目更多的信息
    # http://search.vrs.sohu.com/mv_i1268037.json
    # sohu_album_mvinfo
    # sohu_sohu_album_mvinfo_mini
    def _CmdParserAlbumMvInfo(self, js):
        ret = []
        try:
            text = tornado.escape.to_basestring(js['data'])
            if js['name'] == 'sohu_album_mvinfo_mini':
                text = '{' + text + '}'
            json = tornado.escape.json_decode(text)

            if 'homePage' in js:
                album = self.NewAlbum()
                album.albumPageUrl = js['homePage']
            else:
                return []

            if 'playlistId' in json :
                album.playlistid = autostr(json['playlistId'])

            if 'videos' in json and json['videos']:
                video = json['videos'][0]

                if 'isHigh' in video          : album.isHigh = str(video['isHigh'])
                if 'videoScore' in video      : album.videoScore = str(video['videoScore'])

#                 for video in json['videos']:
#                     v = tv.VideoClass()
#                     v.playlistid = tv.playlistid
#                     v.pid = tv.pid
#                     v.LoadFromJson(video)
#
#                     tv.videos.append(v)
            if album.playlistid:
                self._save_update_append(ret, album, upsert=False)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumMvInfo: %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目的完全信息
    # http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=5112241
    # sohu_album_fullinfo
    def _CmdParserAlbumFullInfo(self, js):
        ret = []
        try:
            json = tornado.escape.json_decode(js['data'])

            album = self.NewAlbum()

            if 'cid' in json            : album.cid            = autoint(json['cid'])
            if 'playlistid' in json     : album.playlistid     = autostr(json['playlistid'])
            if 'pid' in json            : album.pid            = autostr(json['pid'])
            if 'vid' in json            : album.vid            = autostr(json['vid'])

            if 'isHigh' in json         : album.isHigh         = json['isHigh']
            if 'area' in json           : album.area           = json['area']
            if 'categories' in json     : album.categories     = json['categories']
            if 'publishYear' in json    : album.publishYear    = json['publishYear']
            if 'updateTime' in json     : album.updateTime     = json['updateTime']

            # 图片
            if 'largeHorPicUrl' in json : album.largeHorPicUrl = json['largeHorPicUrl']
            if 'smallHorPicUrl' in json : album.smallHorPicUrl = json['smallHorPicUrl']
            if 'largeVerPicUrl' in json : album.largeVerPicUrl = json['largeVerPicUrl']
            if 'smallVerPicUrl' in json : album.smallVerPicUrl = json['smallVerPicUrl']
            if 'largePicUrl' in json    : album.largePicUrl    = json['largePicUrl']
            if 'smallPicUrl' in json    : album.smallPicUrl    = json['smallPicUrl']

            if 'albumDesc' in json      : album.albumDesc      = json['albumDesc']
            if 'totalSet' in json       : album.totalSet       = json['totalSet']

            if 'mainActors' in json     : album.mainActors     = json['mainActors']
            if 'directors' in json      : album.directors      = json['directors']

            if 'videos' in json:
                for video in json['videos']:
                    if 'vid' in video and video['vid'] == autostr(album.vid) and album.vid:
                        if 'playLength' in video  : album.playLength =  video['playLength']
                        if 'publishTime' in video : album.publishTime = video['publishTime']

                    v = album.VideoClass()
                    v.playlistid = album.playlistid
                    v.pid = album.vid
                    v.cid = album.cid
                    v.LoadFromJson(video)
                    album.videos.append(v)
            if album.vid:
                self._save_update_append(ret, album, {'vid' : album.vid}, upsert=False)
            else:
                print(album.vid)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumFullInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析所有节目列表：
    # 拿到菜单下所有节目的 albumName、albumPageUrl
    # http://tv.sohu.com/tvall/
    # sohu_videoall
    def _CmdParserAlbumList(self, js):
        ret = []

        try:
            text = js['data']
            soup = bs(text)#, from_encoding = 'GBK')
            playlist = soup.findAll('li')
            for a in playlist:
                text = re.findall('<a href="(\S*)"\s+target="_blank">\s*(\S*)\s*</a>', a.prettify())
                if text:
                    (url, album) = text[0]

                    if url and album:
                        tv = self.NewAlbum()
                        if tv.albumName == '':
                            tv.albumName = album

                        tv.albumPageUrl = url
                        self._save_update_append(ret, tv)

                        # 访问该节目主页，获取playlistid 和 vid等重要信息
                        #TODO
                        #tv.UpdateAlbumPageCommand().Execute()
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserTVAll:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目基本信息：
    # 主要要拿到节目的playlistid、vid、pid，如果没有找到playlistid，则通过 mv_i继续找
    # http://tv.sohu.com/20120517/n343417005.shtml
    # sohu_album
    def _CmdParserAlbumPage(self, js):
        ret = []
        try:
            text = tornado.escape.to_basestring(js['data'])

            tv = self.NewAlbum()
            tv.albumPageUrl = js['source']
            t = re.findall('(playlistId|pid|vid|PLAYLIST_ID|cid|playAble)\s*=\W*([\d,]+)', text)
            if t:
                for u in t:
                    if u[0] == 'pid':
                        tv.pid = autostr(u[1])
                    elif u[0] == 'vid':
                        if u[1] in ['-1', '', '1']:
                            return ret
                        tv.vid = autostr(u[1])
                    elif u[0] == 'playlistId' or u[0] == 'PLAYLIST_ID':
                        tv.playlistid = autostr(u[1])
                    elif u[0] == 'cid':
                        tv.cid = autoint(u[1])
                    elif u[0] == 'playAble':
                        if u[1] == 0:
                            return []

                self._save_update_append(ret, tv, _filter={'albumPageUrl' : tv.albumPageUrl})#, False)

                #TODO
                # 如果得不到 playlistId 的话
                if tv.playlistid == '':
                    TemplateAlbumMvInfoMini(tv, js['source']).Execute()
                #tv.UpdateFullInfoCommand().Execute()
                #tv.UpdateScoreCommand().Execute()

            else:
                db = redis.Redis(host='127.0.0.1', port=6379, db=2) # 出错页
                db.rpush('urls', js['source'])

                print("ERROR: ", js['source'])
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbum:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # album_total_playnum
    def _CmdParserAlbumTotalPlayNum(self, js):
        ret = []
        try:
            data = tornado.escape.to_basestring(js['data'])
            text = re.findall('var count=(\S+?);', data)
            if text:
                data = tornado.escape.json_decode(text[0])
                for v in data['videos']:
                    vid = autostr(v['videoid'])
                    tv = self.GetAlbumFormDB(vid=vid, auto=False)
                    if tv == None:
                        return []

                    tv.totalPlayNum = tv['count']
                    self._save_update_append(ret, tv)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu._CmdParserAlbumTotalPlayNum:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 解析节目指数信息
    # http://index.tv.sohu.com/index/switch-aid/1012657
    # album_score
    def _CmdParserAlbumScore(self, js):
        ret = []
        try:
            data = tornado.escape.json_decode(js['data'])
            if 'album' in data:
                album = data['album']
                if album:
                    tv = self.NewAlbum()
                    if 'id' in album:
                        tv.playlistid = autostr(album['id'])
                        if not tv.playlistid:
                            return []

                    if 'index' in data:
                        index = data['index']
                        if index:
                            if 'dailyPlayNum' in index:
                                tv.dailyPlayNum    = index['dailyPlayNum']    # 每日播放次数
                            if 'weeklyPlayNum' in index:
                                tv.weeklyPlayNum   = index['weeklyPlayNum']   # 每周播放次数
                            if 'monthlyPlayNum' in index:
                                tv.monthlyPlayNum  = index['monthlyPlayNum']  # 每月播放次数
                            if 'totalPlayNum' in index:
                                tv.totalPlayNum    = index['totalPlayNum']    # 总播放资料
                            if 'dailyIndexScore' in index:
                                tv.dailyIndexScore = index['dailyIndexScore'] # 每日指数

                    self._save_update_append(ret, tv, upsert=False)
        except:
            print(js['source'])
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserAlbumScore:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    def _UpdateVideoVid(self, js, res=[]):
        if 'id' not in js or 'data' not in js:
            return

        try:
            video = self.NewVideo()
            video.vid = autostr(js['id'])
            data = js['data']

            if 'highVid' in data:    video.highVid    = autostr(data['highVid'])
            if 'norVid' in data:     video.norVid     = autostr(data['norVid'])
            if 'oriVid' in data:     video.oriVid     = autostr(data['oriVid'])
            if 'superVid' in data:   video.superVid   = autostr(data['superVid'])
            if 'relativeId' in data: video.relativeId = autostr(data['relativeId'])

            video.originalData = res
            self.db.SaveVideo(video)
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.UpdateVideoPid:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

    # 解析节目播放信息
    # 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s
    # album_playinfo
    def _CmdParserAlbumPlayInfo(self, js):
        ret = []
        try:
            data = tornado.escape.json_decode(js['data'])
            self._UpdateVideoVid(data)
        except:
            print(js['source'])
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu._CmdParserAlbumPlayInfo:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))

        return ret

    # 从分页的页面上解析该页上的节目
    # videolist
    def _CmdParserVideoList(self, js):
        ret = []
        try:
            if not js['data']:
                return ret
            g = re.search('p10(\d+)', js['source'])
            if g:
                current_page = int(g.group(1))
                link = re.compile('p10\d+')
                newurl = re.sub(link, 'p10%d' % (current_page + 1), js['source'])
                TemplateVideoList(self, newurl).Execute()

            playlist = js['data'].split("\n")

            for text in playlist:
                if text:
                    tv = self.NewAlbum()

                    urls = re.findall('(href|title)="([\s\S]*?)"', text)
                    for u in urls:
                        if u[0] == 'href':
                            tv.albumPageUrl = self.command.GetUrl(u[1])
                        elif u[0] == 'title':
                            tv.albumName = u[1]

                    if tv.albumPageUrl and tv.albumName:
                        self._save_update_append(ret, tv, _filter={'albumPageUrl' : tv.albumPageUrl})

                        # 访问该节目主页，获取更多的信息
                        #TODO
                        #tv.UpdateAlbumPageCommand().Execute()
        except:
            t, v, tb = sys.exc_info()
            log.error("SohuVideoMenu.CmdParserVideoList:  %s,%s, %s" % (t, v, traceback.format_tb(tb)))
        return ret

    # 从分页的页面上解析该页上的节目
    # videolist
    def _CmdParserLiveTVList(self, js):
        ret = []

        '''
        {'cu': 249, 'id': 147,
            'programaId': 76372, 'percentage': 0.1530424093423479,
            'enName': 'zjtv', 'name': '浙江卫视',
            'ico': 'http://i2.itc.cn/20120119/2cea_d8216f64_5ba9_b7dd_4b3d_f2ea360e895f_17.png',
            'videoId': 136573770, 'videoName': '浙江新闻联播'}
        '''
        tvlist = tornado.escape.json_decode(js['data'])
        for v in tvlist['attachment']:
            album  = self.NewAlbum()
            album.cid         = 200
            album.pid         = json_get(v, 'programaId', '')
            album.vid         = json_get(v, 'videoId', '')
            album.playlistid  = json_get(v, 'id', '')
            album.albumName   = json_get(v, 'name', '')
            album.enAlbumName = json_get(v, 'enName', '')
            album.smallPicUrl = json_get(v, 'ico', '')
            album.albumDesc   = json_get(v, 'VideoName', '')

            v = album.VideoClass()
            v.playlistid = album.playlistid
            v.pid = album.vid
            v.cid = album.cid
            v.vid = album.vid
            v.playUrl = 'http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1' % album.playlistid
            album.videos.append(v)
            self._save_update_append(ret, album)

    def _save_update_append(self, sets, tv, _filter={}, upsert=True):
        if tv:
            self.db.SaveAlbum(tv, _filter, upsert)
            sets.append(tv)
