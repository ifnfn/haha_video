#! /usr/bin/python3
# -*- coding: utf-8 -*-

from pymongo import Connection

def a():
        con = Connection('localhost', 27017)
        db = con.kola
        album_table = db.album

        _filter =  {
            'categories': {'$in': ['爱情片']},
            'cid': 1}

        #t = album_table.find(_filter)#.limit(10)
        t = album_table.find()
        for x in t:
            n = 'albumName' in x and x['albumName'] or ''
            u = 'albumPageUrl' in x and x['albumPageUrl'] or ''
            i = 'playlistid' in x and x['playlistid'] or ''
            v = 'vid' in x and x['vid'] or ''
            print(n, u, i, v)

if __name__ == '__main__':
    a()
