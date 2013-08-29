#!/usr/bin/python
# -*- coding: utf-8 -*-
#import tornado.httpserver
#import tornado.ioloop
#import tornado.web
#import tornado.options
import tornado.database
import time

#from tornado import gen
#from tornado import httpclient
#from tornado.options import define, options
#from tornado.escape import json_encode


class MysqlHander:  #处理数据库操作，使用tornado自带的database，当然也可以使用其他的，比如sqlalchemy

    def __init__(self):
        self.db = tornado.database.Connection("127.0.0.1", \
                  "videoSearch", "videosearch", "gr2JZjhB")

    def getword(self):
        now = time.strftime("%Y-%m-%d", time.localtime())
        titles = self.db.query("select query from DailyQueryRank where date = '%s 00:00:00'"%now)
        result = []
        for title in titles:
            result.append(title['query'])
        result = list(set(result))
        return result


if __name__ == '__main__':
    db = MysqlHander()
    title = db.getword()
    for i in title:
        print i
	
