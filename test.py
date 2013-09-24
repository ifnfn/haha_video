#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import json
from fetchTools import fetch_httplib2 as fetch
from bs4 import BeautifulSoup as bs
from pymongo import Connection
import re
from super_client import KolaClient

MAINSERVER_HOST = 'http://127.0.0.1:9990'
#MAINSERVER_HOST = 'http://121.199.20.175:9990'
HOST = 'http://127.0.0.1:9991'
HOST = 'http://121.199.20.175'
PARSER_HOST  = HOST + '/video/upload'
MAX_TRY = 3

cmd_list = [
    {
        'name'    : 'album_score',
        'source'  : 'http://index.tv.sohu.com/index/switch-aid/1012657',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            '({"index":\S+?),"asudIncomes'
        ]
    },
    {
        'name'    : 'videoall',
        'source'  : 'http://tv.sohu.com/movieall/',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
    },
    {
        'name'    : 'album',
        'source'  : 'http://store.tv.sohu.com/view_content/movie/1008522_577560.html',
        'menu'    : '电影',
        'dest'    : PARSER_HOST,
        'regular' : [
            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
        ]
    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2011/ajyh/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2011/ajyh/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/s2012/zlyeye/',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://tv.sohu.com/20120517/n343417005.shtml',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album',
#        'source'  : 'http://store.tv.sohu.com/5009508/706684_1772.html',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            'var (playlistId|pid|vid|PLAYLIST_ID)\s*=\W*([\d,]+)'
#        ]
#    },
#    {
#        'name'    : 'album_mvinfo',
#        'source'  : 'http://search.vrs.sohu.com/mv_i4746.json', # http://tv.sohu.com/s2011/ajyh/
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_mvinfo',
#        'source'  : 'http://search.vrs.sohu.com/mv_i704321.json', # http://store.tv.sohu.com/view_content/movie/5008825_704321.html
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_mvinfo',
#        'source'  : 'http://search.vrs.sohu.com/mv_i662182.json', # http://tv.sohu.com/20120517/n343417005.shtml
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_fullinfo',
#        'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=1012657', # http://tv.sohu.com/20120517/n343417005.shtml
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_fullinfo',
#        'source'  : 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=228', # http://tv.sohu.com/s2011/ajyh/
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#    },
#    {
#        'name'    : 'album_score',
#        'source'  : 'http://index.tv.sohu.com/index/switch-aid/1012657',
#        'menu'    : '电影',
#        'dest'    : PARSER_HOST,
#        'regular' : [
#            '({"index":\S+?),"asudIncomes'
#        ]
#    },
]

cmd_test1 = {
    'name'    : 'albumlist_hot',
    'source'  : 'http://so.tv.sohu.com/iapi?v=2&c=100&o=3',
    'menu'    : '电影',
    'dest'    : PARSER_HOST,
}

def test_album():
    con = Connection('localhost', 27017)
    db = con.kola
    album_table = db.album
    haha = KolaClient()
    regular = [
        'var (playlistId|pid|vid|tag|PLAYLIST_ID)\s*=\W*([\d,]+)',
        'content="text/html; charset=(\S*?)"'
    ]

    url = [
        'http://tv.sohu.com/s2011/bjdyj/',
        'http://tv.sohu.com/s2011/1663/s322643386/',
        'http://tv.sohu.com/s2012/zlyeye/',
        'http://tv.sohu.com/s2012/zlyeye/',
        'http://store.tv.sohu.com/view_content/movie/5008825_704321.html',
        'http://tv.sohu.com/20120517/n343417005.shtml',
        'http://store.tv.sohu.com/5009508/706684_1772.html',
        'http://tv.sohu.com/20110718/n313760898.shtml',
        'http://tv.sohu.com/20110328/n304983620.shtml'
    ]
    for u in  url:
        print(u)
        x = haha.RegularMatchUrl(u, regular)
        print(x)

    return

    url = album_table.find({}, fields = {'albumPageUrl': True})
    for u in  url:
        print(u['albumPageUrl'])
        x = haha.RegularMatchUrl(u['albumPageUrl'], regular)
        print(x)

    return

class test_case:
    def __init__(self):
        self.vid = ''
        self.pid = ''
        self.playlistid = ''

    def test_avs_i(self):
        url = 'http://search.vrs.sohu.com/avs_i%s_pr%s_o2_n_p1000_chltv.sohu.com.json' % (self.vid, self.pid)
        _, _, _, response = fetch(url)
        oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
        a = json.loads(oflvo)

        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_v(self):
        # url ='http://search.vrs.sohu.com/v?id=1268036&pageSize=200000&pageNum=1'
        url = 'http://search.vrs.sohu.com/v?id=1268037&pid=5497903&pageNum=1&pageSize=50&isgbk=true&var=video_similar_search_result'
        _, _, _, response = fetch(url)
        oflvo = re.search('var video_similar_search_result=(\{.*.\})', response).group(1)
        a = json.loads(oflvo)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_videopage(self):
        #url = 'http://tv.sohu.com/20130517/n376295917.shtml'
        #url = 'http://tv.sohu.com/20110222/n279464056.shtml'
    #    url = 'http://v.tv.sohu.com/20100618/n272893884.shtml'
    #    url = 'http://tv.sohu.com/20101124/n277876671.shtml'
    #    url = 'http://tv.sohu.com/s2010/72jzk/'
    #    url = 'http://tv.sohu.com/s2011/7film/'
        url = 'http://tv.sohu.com/s2011/1663/s322643386/'
        _, _, _, response = fetch(url)
        a = re.findall('var (playlistId|pid|vid|PLAYLIST_ID)\s*=\s*\W*(.+?)"*', response)
        print(a)

    def test_mvi(self):
        url = 'http://search.vrs.sohu.com/mv_i%s.json' % self.vid
        _, _, _, response = fetch(url)
        oflvo = re.search('var video_album_videos_result=(\{.*.\})', response).group(1)
        a = json.loads(oflvo)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_allvideo(self):
        url = 'http://tv.sohu.com/tvall'
        _, _, _, response = fetch(url)
        soup = bs(response)
        playlist = soup.findAll('li')
        for a in playlist:
            xx = re.findall('<a href="(\S*)"\s+target="_blank">\s*(\S*)\s*</a>', a.prettify())
            if xx:
                print(xx[0][0], xx[0][1])

    def test_videolist(self):
        url = 'http://hot.vrs.sohu.com/pl/videolist?encoding=utf-8&playlistid=%s' % self.playlistid
        _, _, _, response = fetch(url)
        a = json.loads(response)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_iapi(self):
        url = 'http://so.tv.sohu.com/iapi?v=2&c=100'
        _, _, _, response = fetch(url)
        a = json.loads(response)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_switch_aid(self):
        url = 'http://index.tv.sohu.com/index/switch-aid/' + self.playlistid
        _, _, _, response = fetch(url)
        a = json.loads(response.decode())
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_list(self):
        url = 'http://so.tv.sohu.com/list_p1101_p2_p3_p4_p5_p6_p7_p8_p9.html'
        _, _, _, response = fetch(url)
        x = re.findall('(<a class="pic" target="_blank" title=".+/></a>)', response)
        for a in x:
            print(a)
        x = re.findall('(<p class="tit tit-p">.+</a>)', response)
        for a in x:
            print(a)
        return
        x.extend(re.findall('<p class="tit tit-p">', response))
        print(str(x))

    def test_jsl(self):
        url = 'http://so.tv.sohu.com/jsl?c=100&cate=100100_100107&o=1&pageSize=1'
        _, _, _, response = fetch(url)
        a = json.loads(response)
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_playlist(self):
        url = "http://hot.vrs.sohu.com/vrs_flash.action?vid=899609"
        _, _, _, response = fetch(url)

        a = json.loads(response.decode())
        print(json.dumps(a, ensure_ascii=False, indent=4))

    def test_all(self):
        self.test_videolist()
        return

        self.test_all()
        self.test_avs_i()
        self.test_v()
        self.test_videopage()
        self.test_iapi()
        self.test_switch_aid()
        self.test_jsl()
        self.test_list()

def test_run():
    t = test_case()
#    t.test_playlist()
#    t.test_videopage()
#    return
    t.playlistid = '5770420'
    t.vid = '1181239'
    t.pid = '322963713'
    t.test_switch_aid()
    return

    t.playlistid = '1002050'
    t.vid = '460464'
    t.pid = '322963713'
    t.test_videolist()

def test():
    haha = KolaClient()
#    haha.GetRealPlayer('')
    for cmd in cmd_list:
        haha.ProcessCommand(cmd)
#    haha.ProcessCommand(cmd_test4)

if __name__ == "__main__":
#    test()
    t = '''
<a class="pic" href="http://tv.sohu.com/20130923/n387074614.shtml" target="_blank" title="http://photocdn.sohu.com/20130923/vrsb972533.jpg">
      <img height="160" src="http://photocdn.sohu.com/20130923/vrsb972533.jpeg" title="生死猜拳" width="120"/>
</a>
      '''

    x = re.findall('(vrsab_ver|vrsb)([0-9]+).(jpg|jpeg)"', t)
    print(x)
    x =  re.findall('<img.*title="(\S+)"', t)
    print(x)

    x = re.findall('(href|title)="(\S+)"', t)
    print(x)
