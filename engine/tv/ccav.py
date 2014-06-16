#! /usr/bin/python3
# -*- coding: utf-8 -*-

from .wolidou import WolidouDirectParser, WolidouBaseMenu
from .common import PRIOR_DEFTV
from kola import utils

# CCTV
class CCTVLivetvWolidouParser(WolidouDirectParser):
    def __init__(self, albumName=None, url=None):
        super().__init__(albumName, url)
        self.tvName = 'CCTV'
        self.order = PRIOR_DEFTV

    def NewEpgScript(self, albumName):
        return utils.GetScript('epg', 'get_channel_cntv', [albumName])

class CCTVLiveTV(WolidouBaseMenu):
    '''
    湖南省内所有电视台
    '''
    def __init__(self, name):
        self.Parser = CCTVLivetvWolidouParser
        super().__init__(name)
        self.AlbumPage = [
            ('CCTV-1 综合',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv1',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv1', # 很慢
              'rtmp://live.asbctv.com/livepkgr/_definst_/20asUBiNYsYoats8AbvqT0mfBclSk246JHoLj0TIibO37R3zdi14',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv1'
              ]),
            ('CCTV-2 财经',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv2',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv2',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv2'
              ]),
            ('CCTV-3 综艺',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv3',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv3',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv3'
              ]),
            ('CCTV-4 中文国际',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv4',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv4',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv4'
              ]),
            ('CCTV-5 体育',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv5',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv5',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv5',
              'http://61.55.175.79:81/youkulive/204/400/0/wolidou.com.flv',
              ]),
            ('CCTV-6 电影',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv6',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv6', # 没有
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv6',
              ]),
            ('CCTV-7 军事农业',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv7',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv7',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv7',
              ]),
            ('CCTV-8 电视剧',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv8',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv8',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv8',
              ]),
            ('CCTV-9 记录',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv9',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv9',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv9',
              ]),
            ('CCTV-10 科教',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv10',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv10',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv10',
              ]),
            ('CCTV-11 戏曲',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv11',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv11',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv11',
              ]),
            ('CCTV-12 社会与法',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv12',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv12',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv12',
              ]),
            ('CCTV-13 新闻',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv13',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv13',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv13',
              ]),
            ('CCTV-14 少儿',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv14',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv14',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv14',
              ]),
            ('CCTV-15 音乐',
             ['http://www.wolidou.com/x/?s=jstv&f=flv&u=cctv15',
              #'http://www.wolidou.com/x/?s=cx2tv_hls&f=m3u8&u=cctv15',
              #'http://www.wolidou.com/x/?s=alllook&f=m3u8&u=cctv15',
              ]),
        ]
