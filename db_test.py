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
            if 'albumName' in x:
                print(x['albumName']),
            if 'albumPageUrl' in x:
                print(x['albumPageUrl'])

if __name__ == '__main__':
    a()
