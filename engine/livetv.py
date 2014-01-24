#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re
from urllib.parse import urljoin
from xml.etree import ElementTree

import tornado.escape

from kola import VideoBase, AlbumBase, DB, json_get, GetNameByUrl, utils
from kola.element import LivetvMenu

from .city import City
from .engines import VideoEngine, KolaParser
from .fetchTools import GetUrl


global Debug
Debug = True

class TVCategory:
    def __init__(self):
        self.Outside = '凤凰|越南|半岛|澳门|东森|澳视|亚洲|良仔|朝鲜| TV|KP|Yes|HQ|NASA|Poker|Docu|Channel|Neotv|fashion|Sport|sport|Power|FIGHT|Pencerahan|UK|GOOD|Kontra|Rouge|Outdoor|Divine|Europe|DaQu|Teleromagna|Alsharqiya|Playy|Boot Movie|Runway|Bid|LifeStyle|CBN|HSN|BNT|NTV|Virgin|Film|Smile|Russia|NRK|VIET|Gulli|Fresh'
        self.filter = {
            '类型' : {
                '央视台' : 'cctv|CCTV',
                '卫视台' : '卫视|卡酷少儿|炫动卡通',
                '体育台' : '体育|足球|网球|cctv-5|CCTV5|cctv5|CCTV-5',
                '综合台' : '综合|财|都市|经济|旅游',
                '少儿台' : '动画|卡通|动漫|少儿',
                '地方台' : '^(?!.*?(cctv|CCTV|卫视|测试|卡酷少儿|炫动卡通' + self.Outside + ')).*$',
                '境外台' : self.Outside
            }
        }

    def GetCategories(self, name):
        ret = []
        for k, v in self.filter['类型'].items():
            x = re.findall(v, name)
            if x:
                ret.append(k)
        return ret

class LivetvDB(DB):
    def SaveAlbum(self, album, upsert=True):
        self._save_update_append(None, album)

class LivetvVideo(VideoBase):
    def __init__(self, js = None):
        super().__init__(js)

class LivetvPrivate:
    def __init__(self):
        self.name =  '直播'
        self.videoListUrl = {}

    def Json(self):
        json = {'name' : self.name}
        if self.videoListUrl : json['videoListUrl'] = self.videoListUrl

        return json

    def Load(self, js):
        if 'name' in js         : self.name         = js['name']
        if 'videoListUrl' in js : self.videoListUrl = js['videoListUrl']

class LivetvAlbum(AlbumBase):
    def __init__(self):
        self.engineName = 'LivetvEngine'
        super().__init__()
        self.cid =  200
        self.albumPageUrl = ''
        self.livetv = LivetvPrivate()
        self.videoClass = LivetvVideo

    def SaveToJson(self):
        if self.livetv:
            self.private[self.engineName] = self.livetv.Json()
        ret = super().SaveToJson()

        return ret

    def LoadFromJson(self, json):
        super().LoadFromJson(json)
        if self.engineName in self.private:
            self.livetv.Load(self.private[self.engineName])

    # 更新节目完整信息
    def UpdateFullInfoCommand(self):
        pass

    # 更新节目指数信息
    def UpdateScoreCommand(self):
        pass

class SohuLiveTV(LivetvMenu):
    '''
    搜狐电视
    '''
    def UpdateAlbumList(self):
        ParserSohuLivetv().Execute()

class LetvLiveTV(LivetvMenu):
    '''
    乐视电视
    '''
    def UpdateAlbumList(self):
        ParserLetvLivetv().Execute()

class CuLiveTV(LivetvMenu):
    '''
    联合电视台
    '''
    def UpdateAlbumList(self):
        ParserCutvLivetv('all').Execute()

class JilingLiveTV(LivetvMenu):
    '''
    吉林所有电视台
    '''
    def UpdateAlbumList(self):
        ParserJLntvLivetv().Execute()

class GuangXiLiveTV(LivetvMenu):
    '''
    广西所有电视台
    '''
    def UpdateAlbumList(self):
        ParserNNLivetv().Execute()

class XinJianLiveTV(LivetvMenu):
    '''
    新疆所有电视台
    '''
    def UpdateAlbumList(self):
        ParserUCLivetv().Execute()


class ZheJianLiveTV(LivetvMenu):
    '''
    浙江省内所有电视台
    '''
    def UpdateAlbumList(self):
        ParserZJLivetv().Execute()           # 浙江省台
        ParserHangZhouLivetv().Execute()     # 杭州市台
        ParserNBLivetv().Execute()           # 宁波
        ParserWenZhouLivetv().Execute()      # 温州
        ParserYiwuLivetv().Execute()         # 义乌
        ParserShaoxinLivetv().Execute()      # 绍兴

class JianSuLiveTV(LivetvMenu):
    '''
    江苏省内所有电视台
    '''
    def UpdateAlbumList(self):
        ParserJiansuLivetv().Execute()           # 江苏省台

class AnHuiLiveTV(LivetvMenu):
    '''
    安徽省内所有电视台
    '''
    def UpdateAlbumList(self):
        ParserAnhuiLivetv().Execute()           # 安徽省台

class LivetvParser(KolaParser):
    def __init__(self):
        super().__init__()
        self.tvCate = TVCategory()
        self.Alias = {}
        self.ExcludeName = ()
        self.tvName = ''
        self.area = ''

    def NewAlbum(self):
        album  = LivetvAlbum()
        album.enAlbumName = self.tvName
        album.area        = self.area
        return album

    def GetAliasName(self, name):
        for p in list(self.ExcludeName):
            if re.findall(p, name):
                return ""

        if name in self.ExcludeName:
            return ""

        if name in self.Alias:
            return self.Alias[name]

        return name

# 乐视直播电视
class ParserLetvLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '乐视'

        #self.cmd['source']  = 'http://www.leshizhibo.com/channel/index.php'
        self.cmd['source']  = 'http://www.leshizhibo.com/'
        self.cmd['regular'] = ['<p class="channelimg">(.*)</p>']

    def CmdParser(self, js):
        db = LivetvDB()

        playlist = js['data'].split("</a>")

        for t in playlist:
            #print(t)
            x = re.findall('<a href=".*/channel/(.*)" target="_blank"><img src="(.*)" alt="(.*)" width', t)
            if x:
                vid = x[0][0]
                name = x[0][2]
                image = urljoin(js['source'], x[0][1])
                #print(name, vid, image)

                if name in ['中国教育一台', '中国教育三台', '中国教育二台', '游戏风云一套', '优漫卡通', '延边卫视', '星空卫视',
                            '五星体育', 'TVB翡翠台', '三沙卫视', '厦门卫视', 'NEOTV综合频道', '嘉佳卡通', '华娱卫视',
                            '湖北体育', '广东体育', 'CCTV女性时尚', 'CCTV电视指南', 'CCTV-5体育频道', '兵团卫视', '澳亚卫视',
                            ]:
                    continue
                album  = self.NewAlbum()
                album.vid         = utils.genAlbumId(name)
                album.albumName   = name
                album.largePicUrl = image
                album.categories  = self.tvCate.GetCategories(name)

                v = album.NewVideo()
                playUrl     = 'http://live.gslb.letv.com/gslb?stream_id=%s&ext=m3u8&sign=live_tv&format=1' % vid
                v.vid         = utils.getVidoId(playUrl)
                v.largePicUrl = x[0][2]
                v.priority    = 1
                v.name        = "乐视"

                v.SetVideoUrl('default', {
                    'script' : 'letvlive',
                    'parameters' : [playUrl]
                })

                v.info = {
                          'script' : 'letvlive',
                          'function' : 'get_channel',
                          'parameters' : [vid]}

                album.videos.append(v)
                db.SaveAlbum(album)

# 搜狐直播电视
class ParserSohuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '搜狐'

        self.cmd['source'] = 'http://tvimg.tv.itc.cn/live/top.json'

    def CmdParser(self, js):
        db = LivetvDB()
        city = City()

        tvlist = tornado.escape.json_decode(js['data'])
        for v in tvlist['attachment']:
            name = json_get(v, 'name', '')
            pid = json_get(v, 'id', '')
            vid = utils.genAlbumId(name)

            album  = self.NewAlbum()
            album.albumName   = json_get(v, 'name', '')
            album.categories  = self.tvCate.GetCategories(album.albumName)
            album.vid         = vid
            album.smallPicUrl = json_get(v, 'ico', '')
            album.area = city.GetCity(album.albumName)

            v = album.NewVideo()
            playUrl    = 'http://live.tv.sohu.com/live/player_json.jhtml?encoding=utf-8&lid=%s&type=1' % pid
            v.vid      = utils.getVidoId(playUrl)
            v.priority = 2
            v.name     = "搜狐"

            v.SetVideoUrl('default', {
                'script' : 'sohulive',
                'parameters' : [playUrl]
            })

            v.info = {
                'script' : 'sohulive',
                'function' : 'get_channel',
                'parameters' : [pid],
            }

            album.videos.append(v)
            db.SaveAlbum(album)

# 吉林电视台
class ParserJLntvLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '吉林电视台'

        self.cmd['source']  = 'http://live.jlntv.cn/index.php?option=default,live&ItemId=86&type=record&channelId=6'
        self.cmd['regular'] = ['(<li id="T_Menu_.*</a></li>)']

        self.Alias = {}
        self.ExcludeName = ('交通918', 'FM1054', 'FM89')
        self.area = '中国,吉林'

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('<li id="T_Menu_(\d*)"><a href="(.*)">(.*)</a></li>', js['data'])

        for _, u, n in ch_list:
            album  = self.NewAlbum()
            album.vid        = utils.genAlbumId(n)
            album.albumName  = n
            album.categories = self.tvCate.GetCategories(n)

            v = album.NewVideo()
            playUrl     = 'http://live.jlntv.cn/' + u
            v.vid         = utils.getVidoId(playUrl)
#            v.largePicUrl = x[0][2]
            v.priority    = 1
            v.name        = "JLNTV"

            v.SetVideoUrl('default', {
                'script' : 'jlntv',
                'parameters' : [playUrl]
            })

            v.info = {
                      'script' : 'jlntv',
                      'function' : 'get_channel',
                      'parameters' : []}

            album.videos.append(v)
            db.SaveAlbum(album)

class ParserCutvLivetv(LivetvParser):
    def __init__(self, station=None, tv_id=None):
        super().__init__()
        self.area = ''

        if station == 'all':
            self.cmd['step'] = 1
            self.cmd['source'] = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=tv_live'
        elif station and id:
            self.tvName = station

            self.cmd['step'] = 2
            self.cmd['station'] = station
            self.cmd['id'] = tv_id
            self.cmd['source'] = 'http://ugc.sun-cam.com/api/tv_live_api.php?action=channel_prg_list&tv_id=' + utils.autostr(tv_id)

    def CmdParser(self, js):
        if js['step'] == 1:
            self.CmdParserAll(js)
        elif js['step'] == 2:
            self.CmdParserTV(js)


    def CmdParserAll(self, js):
        text = js['data']
        root = ElementTree.fromstring(text)
        for p in root.findall('tv'):
            ParserCutvLivetv(p.findtext('tv_name'), p.findtext('tv_id')).Execute()

    def CmdParserTV(self, js):
        db = LivetvDB()
        text = js['data']
        city = City()
        self.area = city.GetCity(js['station'])
        root = ElementTree.fromstring(text)
        for p in root.findall('channel'):
                album  = self.NewAlbum()
                album.albumName  = p.findtext('channel_name')
                album.categories = self.tvCate.GetCategories(album.albumName)
                album.area       = self.area
                album.vid        = utils.genAlbumId(album.area + album.albumName)

                album.channel_id  = p.findtext('channel_id')
                album.largePicUrl = p.findtext('thumb')

                url = p.findtext('mobile_url')
                v = album.NewVideo()
                v.priority = 2
                v.name     = "CUTV"
                v.SetVideoUrl('default', {'text' : url})

                x = url.split('/')
                if len(x) > 4:
                    v.vid  = x[4]
                    v.info = {
                        'script' : 'cutv',
                        'function' : 'get_channel',
                        'parameters' : [v.vid],
                    }

                album.videos.append(v)
                db.SaveAlbum(album)

# 安徽电视台
class ParserAnhuiLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '安徽电视台'
        self.cmd['source'] = 'http://www.ahtv.cn/m2o/player/channel_xml.php?first=1&id=7'
        self.cmd['step']   = 1
        self.area = '中国,安徽'

    def CmdParser(self, js):
        ChannelMap = {
            '安徽卫视' : 2,
            '安徽公共' : 3,
            '安徽-科教频道' : 4,
            '安徽-综艺频道' : 5,
            '安徽-影视频道' : 6,
            '安徽-经济生活' : 7,
            '安徽国际'     : 8,
            '安徽-人物频道' : 9
        }

        db = LivetvDB()
        for k,v in ChannelMap.items():
            #url = 'http://www.ahtv.cn/m2o/player/channel_xml.php?first=1&id=%d' % v
            album  = self.NewAlbum()
            album.albumName  = k
            album.categories = self.tvCate.GetCategories(album.albumName)
            album.area       = self.area
            album.vid        = utils.genAlbumId(album.area + album.albumName)
            album.livetv.videoListUrl = {
                'script': 'ahtv',
                'function' : 'get_videolist',
                'parameters' : [album.cid, album.vid, v]
            }
            db.SaveAlbum(album)

# 南宁电视台
class ParserNNLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '南宁电视台'
        self.cmd['source'] = 'http://user.nntv.cn/nnplatform/index.php?mod=api&ac=player&m=getLiveUrlXml&inajax=2&cid=104'
        self.area = '中国,广西,南宁'

    def CmdParser(self, js):
        db = LivetvDB()
        count = 0
        for i in ('101', '105', '104', '103', '106', '117', '109'): #  新闻综合 都市生活 影视娱乐 公共频道 广电购物 老友LIVE CCTV-1
            url = 'http://user.nntv.cn/nnplatform/index.php?mod=api&ac=player&m=getLiveUrlXml&inajax=2&cid=' + i
            text = GetUrl(url).decode()
            root = ElementTree.fromstring(text)

            album = None
            for p in root:
                if p.tag == 'title':
                    album  = self.NewAlbum()
                    album.albumName  = p.text
                    album.categories = self.tvCate.GetCategories(album.albumName)
                    album.area       = self.area
                    album.vid        = utils.genAlbumId(album.area + album.albumName)

            if album == None:
                return

            v = album.NewVideo()
            v.vid      = utils.getVidoId(url)
            v.priority = 2
            v.name     = "NNTV"

            for p in root:
                if p.tag == 'url':
                    print(p.text)

                    if count == 0:
                        v.SetVideoUrl('default', {'text' : p.text})
                    else:
                        v.SetVideoUrl('url_%d' % count, {'text' : p.text})

                    count += 1

            if count == 0:
                return

            v.info = {
                'script' : 'nntv',
                'function' : 'get_channel',
                'parameters' : [i],
            }

            album.videos.append(v)
            db.SaveAlbum(album)

# 杭州电视台
class ParserHangZhouLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '杭州电视台'

        self.cmd['text'] = 'OK'
        self.Alias = {}
        self.ExcludeName = ('交通918', 'FM1054', 'FM89')
        self.area = '中国,浙江,杭州'

    def CmdParser(self, js):
        db = LivetvDB()

        #for i in range(1, 60):
        for i in (1, 2, 3, 5, 13, 14, 15):
            url = 'http://api1.hoolo.tv/player/live/channel_xml.php?id=%d' % i
            text = GetUrl(url).decode()
            root = ElementTree.fromstring(text)

            name = self.GetAliasName(root.attrib['name'])
            if name == '':
                continue

            ok = False
            for p in root:
                if p.tag == 'video':
                    for item in p.getchildren():
                        if 'url' in item.attrib:
                            ok = True
                            break

            if ok == False:
                continue

            album  = self.NewAlbum()
            album.albumName  = name
            album.categories = self.tvCate.GetCategories(album.albumName)
            album.vid        = utils.genAlbumId(name)
            album.area       = self.area

            v = album.NewVideo()
            v.vid      = utils.getVidoId(url)
            v.priority = 2
            v.name     = "HZTV"

            v.SetVideoUrl('default', {
                'script' : 'hztv',
                'parameters' : [url]
            })

            v.info = {
                'script' : 'hztv',
                'function' : 'get_channel',
                'parameters' : [utils.autostr(i)],
            }

            album.videos.append(v)
            db.SaveAlbum(album)

# 江苏电视台
class ParserJiansuLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '江苏电视台'

        #self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_1.html'
        self.cmd['source'] = 'http://newplayerapi.jstv.com/rest/getplayer_2.html'
        self.Alias = {}
        self.ExcludeName = ()
        self.area = '中国,江苏'

    def CmdParser(self, js):
        db = LivetvDB()

        tvlist = tornado.escape.json_decode(js['data'])

        if tvlist['status'] == 'ok':
            for stations in tvlist['paramz']['stations']:
                for ch in stations['channels']:
                    album  = self.NewAlbum()
                    album.albumName = ch['name']
                    album.vid = utils.genAlbumId(album.albumName)
                    album.categories = self.tvCate.GetCategories(album.albumName)
                    album.largePicUrl = 'http://newplayer.jstv.com' + ch['logo']

                    v = album.NewVideo()
                    v.vid      = utils.getVidoId('http://streamabr.jstv.com' + ch['name'])
                    v.priority = 2
                    v.name     = "JSTV"

                    videoUrl = 'http://streamabr.jstv.com'

                    v.SetVideoUrl('default', {
                        'text' : videoUrl + ch['auto']
                    })

                    v.SetVideoUrl('super', {
                        'text' : videoUrl + ch['supor']
                    })

                    v.SetVideoUrl('high', {
                        'text' : videoUrl + ch['high']
                    })

                    v.SetVideoUrl('normal', {
                        'text' : videoUrl + ch['fluent']
                    })

                    v.info = {
                        'script'     : 'jstv',
                        'function'   : 'get_channel',
                        'parameters' : [ch['id']],
                    }
                    album.videos.append(v)
                    db.SaveAlbum(album)

# 温州电视台
class ParserWenZhouLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = '温州电视台'

        self.cmd['source'] = 'http://tv.dhtv.cn'
        self.cmd['regular'] = ['<li class="on">(.*)</li>']
        self.Alias = {}
        self.ExcludeName = ()
        self.area = '中国,浙江,温州'

    def CmdParser(self, js):
        db = LivetvDB()

        ch_list = re.findall('data-source="(.*?)" .*?>(.*?)<i>', js['data'])
        for source, name in ch_list:
            name = '温州-' + name
            vid = utils.genAlbumId(name)
            album  = self.NewAlbum()
            album.albumName  = name
            album.categories = self.tvCate.GetCategories(album.albumName)
            album.vid        = vid

            v = album.NewVideo()
            v.vid      = utils.getVidoId(js['source'] + '/' + source)
            v.priority = 2
            v.name     = "WZTV"

            v.SetVideoUrl('default', {
                'script' : 'wztv',
                'parameters' : ['http://www.dhtv.cn/static/js/tv.js?acm', source]
            })

            v.info = {
                'script'     : 'wztv',
                'function'   : 'get_channel',
                'parameters' : [source],
            }
            album.videos.append(v)
            db.SaveAlbum(album)

#
class ParserTVIELivetv(LivetvParser):
    def __init__(self, url):
        super().__init__()
        self.base_url = url
        self.cmd['source'] = 'http://' + self.base_url + '/api/getChannels'
        self.area = ''

    def CmdParser(self, js):
        db = LivetvDB()

        jdata = tornado.escape.json_decode(js['data'])

        for x in jdata['result']:
            #if 'group_names' in x and x['group_names'] == '':
            #    continue
            name = ''
            if 'name' in x: name = x['name']
            if 'display_name' in x: name = x['display_name']

            name = self.GetAliasName(name)
            if name == '':
                continue

            album = self.NewAlbum()
            album.albumName  = name
            album.categories = self.GetCategories(album.albumName)
            album.vid        = utils.genAlbumId(name)
            album.area       = self.area

            v = album.NewVideo()
            playUrl = 'http://' + self.base_url + '/api/getCDNByChannelId/' + x['id']
            if self.base_url in ['api.cztv.com']:
                playUrl += '?domain=' + self.base_url

            v.vid = utils.getVidoId(playUrl)

            v.priority = 2
            v.name = "TVIE"

            v.SetVideoUrl('default', {
                'script' : 'tvie',
                'parameters' : [playUrl]
            })

            v.info = {
                'script' : 'tvie',
                'function' : 'get_channel',
                'parameters' : ['http://%s/api/getEPGByChannelTime/%s' % (self.base_url, x['id'])]
            }

            album.videos.append(v)
            db.SaveAlbum(album)

    def GetCategories(self, name):
        return self.tvCate.GetCategories(name)

# 浙江电视台
class ParserZJLivetv(ParserTVIELivetv):
    def __init__(self):
        super().__init__('api.cztv.com')
        self.tvName = '浙江电视台'

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

# 新疆电视台
class ParserUCLivetv(ParserTVIELivetv):
    class UCTVCategory(TVCategory):
        def __init__(self):
            super().__init__()
            self.filter = {
                '类型' : {
                    '体育台' : '体育|足球|网球|cctv-5|CCTV5|cctv5|CCTV-5|中央电视台五套',
                    '综合台' : '综合|财|都市|经济|旅游',
                    '少儿台' : '动画|卡通|动漫|少儿',
                    '地方台' : '.*',
                }
            }

    def __init__(self):
        super().__init__('epgsrv01.ucatv.com.cn')
        self.tvCate = self.UCTVCategory()
        self.tvName = '新疆电视台'

        self.ExcludeName = ('.*广播', '106点5旅游音乐', '天山云LIVE')
        self.area = '中国,新疆'

# 文本导入
class ParserTextLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.cmd['source'] = 'http://files.cloudtv.bz/media/20130927.txt'

    def CmdParser(self, js):
        db = LivetvDB()
        text = js['data']
        text = text.replace('（华侨直播）', '')
        text = text.replace('【夜猫】', '')
        text = text.replace('[腾讯]', '')
        playlist = text.split('\n')

        tv = {}
        for t in playlist:
            t = t.strip()
            if t[0:1] != '#':
                v = re.findall('(.*)((http://|rtmp://|rtsp://).*)', t)
                if v and len(v[0]) >= 2:
                    key = v[0][0].strip()
                    value = v[0][1].strip()
                    if key not in tv:
                        tv[key] = []
                    x = {}
                    x['name'], x['order'] = GetNameByUrl(value)
                    x['directPlayUrl'] = value

                    if x not in tv[key]:
                        tv[key].append(x)
        for k,v in list(tv.items()):
            if k and v:
                v.sort(key=lambda x:x['order'])
                album  = self.NewAlbum()
                album.vid         = k
                album.playlistid  = k
                album.pid         = k
                album.albumName   = k
                album.categories  = self.tvCate.GetCategories(album.albumName)
                album.sources     = v
                album.totalSet    = len(v)
                db.SaveAlbum(album)

# LiveTV 搜索引擎
class LiveEngine(VideoEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = 'LivetvEngine'
        self.albumClass = LivetvAlbum

        # 引擎菜单
        self.menu = [
            JianSuLiveTV('江苏'),
            ZheJianLiveTV('浙江'),
            AnHuiLiveTV('安徽'),
            XinJianLiveTV('新疆'),
            GuangXiLiveTV('广西'),
            JilingLiveTV('吉林'),
            CuLiveTV('CuTV'),
            SohuLiveTV('Sohu'),
            LetvLiveTV('Letv'),
        ]

        self.parserList = [
            ParserLetvLivetv(),
            ParserSohuLivetv(),
            ParserTextLivetv(),
            ParserZJLivetv(),
            ParserNBLivetv(),
            ParserYiwuLivetv(),
            ParserShaoxinLivetv(),
            ParserHangZhouLivetv(),
            ParserUCLivetv(),
            ParserWenZhouLivetv(),
            ParserJLntvLivetv(),
            ParserNNLivetv(),
            ParserCutvLivetv(),
            ParserJiansuLivetv(),
            ParserAnhuiLivetv(),
        ]
