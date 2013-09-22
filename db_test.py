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

        t = album_table.find(_filter)#.limit(10)
        for x in t:
            print(x['albumName'], x['categories'])

if __name__ == '__main__':
    a()
