#! /usr/bin/python3
# -*- coding: utf-8 -*-

import re

from kola import utils, LivetvMenu

from .common import PRIOR_PPTV
from .livetvdb import LivetvParser, LivetvDB
from bs4 import BeautifulSoup as bs, Tag
import tornado.escape


'http://web-play.pptv.com/web-m3u8-300162.m3u8?type=m3u8.web.pad&playback=0'

class ParserPPtvList(LivetvParser):
    def __init__(self, area_id=None):
        super().__init__()
        self.tvName = 'PPTV'
        self.order = PRIOR_PPTV

        self.Alias = {
            "cctv中学生" : "CCTV中学生",
            "武汉电视台科教生活" : "武汉-科教生活",
            "武汉电视台文艺频道" : "武汉-文艺频道",
            "武汉教育台" : "武汉-教育频道",
            "河北电视台农民频道" : "河北-农民频道",
            "河北公共" : "河北-公共频道",
            "河北少儿科教" : "河北-少儿科教",
            "河北都市" : "河北-都市频道",
            "河北影视" : "河北-影视频道",
            "河北经济" : "河北-经济频道",
            "广州电视台综合频道" : "广州-综合频道",
            "广州经济" : "广州-经济频道",
            "广州少儿" : "广州-少儿频道",
            "广州新闻" : "广州-新闻频道",
            "广州影视" : "广州-影视频道",
            "广西综艺频道" : "广西-综艺频道",
            "湖北公共" : "湖北-公共频道",
            "湖北经视" : "湖北-经视频道",
            "湖北教育" : "湖北-教育频道",
            "中国教育-1" : "中国教育一",
            "中国教育-2" : "中国教育二",
            "成都都市生活" : "成都-都市生活",
            "成都公共频道" : "成都-公共频道",
            "成都经济资讯" : "成都-经济资讯",
            "成都少儿频道" : "成都-少儿频道",
            "成都新闻综合" : "成都-新闻综合",
            "成都影视文艺" : "成都-影视文艺",
            "西安健康快乐" : "西安-健康快乐",
            "西安商务资讯" : "西安-商务资讯",
            "西安文化影视" : "西安-文化影视",
            "西安新闻综合" : "西安-新闻综合",
            "西安都市" : "西安-都市",
            '北京卫视[高清]' : '北京卫视-高清',
            '湖北卫视[高清]' : '湖北卫视-高清',
            '广东卫视[高清]' : '广东卫视-高清',
            '河北卫视[高清]' : '河北卫视-高清',
            '黑龙江卫视[高清]' : '黑龙江卫视-高清',
            '江苏卫视[高清]' : '江苏卫视-高清',
            '山东卫视[高清]' : '山东卫视-高清',
            '深圳卫视[高清]' : '深圳卫视-高清',
            '天津卫视[高清]' : '天津卫视-高清',
            '浙江卫视[高清]' : '浙江卫视-高清',
            '深圳卫视[高清]' : '深圳卫视-高清',
            '广东卫视[高清]' : '广东卫视-高清',
            '广东汽车·会展频道' : '广东-汽车会展',
            '广东现代教育' : '广东-现代教育'

        }
        if area_id:
            self.cmd['source'] = 'http://live.pptv.com/api/tv_list?area_id=%s&canBack=0' % area_id
            self.cmd['regular'] = ['\((.*)\)']

    def CmdParser(self, js):
        db = LivetvDB()
        json = tornado.escape.json_decode(js['data'])
        if 'html' in json:
            html = json['html']
            '''
            <table class=\"table_style_b\">\n
                <tr>\n
                    <td class=\"show_channel\">
                        <i class=\"ico ico_con_1\">
                            <a href=\"http://live.pptv.com/list/tv_program/300159.html\" target =\"_blank\">
                                <img src=\"http://img3.pplive.cn/images/2013/03/13/21352466993.png\" alt=\"\"></a>
                        </i>
                        <a href=\"http://live.pptv.com/list/tv_program/300159.html\" target =\"_blank\">河南卫视</a>
                    </td>\n
                    <td class=\"show_playing\">
                        <a  href=\"http://v.pptv.com/show/fymQDnbcTIrta9M.html\" target =\"_blank\">
                            <i class=\"ico_4\"></i>
                            <span class=\"titme\">08:00</span>
                            <span class = \"p_title\" title = \" 电视剧\">电视剧</span>
                        </a>
                    </td>\n
                    <td class=\"show_next\">
                        <a  href=\"#\" title =\"订阅提醒\" _siteyydata =\"%7B%22id%22%3A%22tvepg_300159_201403071130%22%2C%22title%22%3A%22%5Cu822a%5Cu7a7a%5Cu5927%5Cu90fd%5Cu5e02-%5Cu6211%5Cu4eec%5Cu672a%5Cu6765%5Cu7684%5Cu751f%5Cu6d3b%5Cu65b9%5Cu5f0f%22%2C%22start%22%3A%222014-03-07%2011%3A30%3A00%22%2C%22end%22%3A%222014-03-07%2012%3A30%3A00%22%2C%22link%22%3A%22http%3A%5C%2F%5C%2Fv.pptv.com%5C%2Fshow%5C%2FfymQDnbcTIrta9M.html%22%2C%22channel_id%22%3A%22300159%22%7D\"class=\"btn btn_book\">
                            <span><i class=\"ico_1\"></i>11:30</span>
                        </a>
                        <span class = \"p_title\" title = \" 航空大都市-我们未来的生活方式\">航空大都市-我们未来的生活方</span>
                    </td>\n
                </tr>\n
                <tr class = \"even\">\n
                    <td class=\"show_channel\">
                        <i class=\"ico ico_con_1\">
                            <a href=\"http://live.pptv.com/list/tv_program/301055.html\" target =\"_blank\">
                                <img src=\"http://sr1.pplive.com/mcms/zt/2013musiczt/midi/1/download/1380095716493.png\" alt=\"\"></a>
                        </i>
                        <a href=\"http://live.pptv.com/list/tv_program/301055.html\" target =\"_blank\">睛彩平顶山</a>
                    </td>\n
                    <td class=\"show_playing\">
                        <a  href=\"http://v.pptv.com/show/ic6YFgibtRwf9ia4Eg.html\" target =\"_blank\">
                            <i class=\"ico_4\"></i>
                            <span class=\"titme\">08:00</span>
                            <span class = \"p_title\" title = \"黄金剧场：乱世三义（18—20）\">黄金剧场：乱世三义（18—20</span>
                        </a>
                    </td>\n
                    <td class=\"show_next\">
                        <a  href=\"#\" title =\"订阅提醒\" _siteyydata =\"%7B%22id%22%3A%22tvepg_301055_201403071050%22%2C%22title%22%3A%22%5Cu597d%5Cu83b1%5Cu575e%5Cu5267%5Cu573a%5Cuff1a%5Cu62f3%5Cu97382%22%2C%22start%22%3A%222014-03-07%2010%3A50%3A00%22%2C%22end%22%3A%222014-03-07%2012%3A50%3A00%22%2C%22link%22%3A%22http%3A%5C%2F%5C%2Fv.pptv.com%5C%2Fshow%5C%2Fic6YFgibtRwf9ia4Eg.html%22%2C%22channel_id%22%3A%22301055%22%7D\"class=\"btn btn_book\">
                            <span><i class=\"ico_1\"></i>10:50</span>
                        </a>
                        <span class = \"p_title\" title = \"好莱坞剧场：拳霸2\">好莱坞剧场：拳霸2</span>
                    </td>\n
                </tr>\n
            </table>"
            '''
            soup = bs(html)  # , from_encoding = 'GBK')
            channells = soup.findAll('td', {'class' : 'show_channel'})
            for ch in channells:
                if type(ch) == Tag:
                    for t in ch.contents:
                        if t.name == 'a':
                            href = t.get('href')
                            channel_id = re.findall('/(\w*).html', href)
                            if channel_id:
                                channel_id = channel_id[0]
                            albumName = t.text

                            print(albumName, href, channel_id)

                            if not (albumName and channel_id):
                                continue

                            album  = self.NewAlbum(albumName)
                            if album == None:
                                continue

                            v = album.NewVideo()
                            v.order = self.order
                            v.name     = self.tvName

                            v.vid   = utils.getVidoId(albumName + channel_id)

                            v.SetVideoUrlScript('default', 'pptvlive', [channel_id])
                            v.info = utils.GetScript('pptvlive', 'get_channel', [channel_id])

                            album.videos.append(v)
                            db.SaveAlbum(album)


# PPTV 直播电视
class ParserPPtvLivetv(LivetvParser):
    def __init__(self):
        super().__init__()
        self.tvName = 'PPTV'
        self.order = PRIOR_PPTV

        self.cmd['source'] = 'http://live.pptv.com/list/tv_list'
        self.cmd['regular'] = ['(<a.*area_id ="\w*">.*</a>)']

    def CmdParser(self, js):
        soup = bs(js['data'])  # , from_encoding = 'GBK')
        albumTag = soup.findAll('a', { "href" : '#' })
        for a in albumTag:
            ParserPPtvList(a.get('area_id')).Execute()

class PPtvLiveTV(LivetvMenu):
    '''
    PPTV 电视
    '''
    def __init__(self, name):
        super().__init__(name)
        self.parserClassList = [ParserPPtvLivetv, ParserPPtvList]
