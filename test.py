#! env /usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os

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

def test():
    haha = KolaClient()
#    haha.GetRealPlayer('')
    for cmd in cmd_list:
        haha.ProcessCommand(cmd)
#    haha.ProcessCommand(cmd_test4)

if __name__ == "__main__":
    test()

