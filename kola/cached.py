#! /usr/bin/python3
# -*- coding: utf-8 -*-

import redis
import memcache
import hashlib
import bmemcached

class CachedBase:
    def __init__(self):
        self.expireTime = 60 * 60

    def Clean(self):
        pass

    def Get(self, key):
        pass

    def Set(self, key, value):
        pass

class RedisCached(CachedBase):
    def __init__(self):
        super().__init__()
        self.url_cachedb = redis.Redis(host='127.0.0.1', port=6379, db=3)

    def Clean(self):
        pipe = self.url_cachedb.pipeline()
        for key in self.url_cachedb.keys('album_*'):
            pipe.delete(key)
        pipe.execute()

    def Get(self, key):
        key = hashlib.sha1(key.encode()).hexdigest()
        return self.url_cachedb.get('album_' + key)

    def Set(self, key, value):
        key = hashlib.sha1(key.encode()).hexdigest()
        key = 'album_' + key
        self.url_cachedb.set(key, value)
        self.url_cachedb.expire(key, self.expireTime) # 一分钟过期

class BCached(CachedBase):
    def __init__(self):
        super().__init__()
        self.url_cachedb = bmemcached.Client(('927af6ee1c6411e4.m.cnqdalicm9pub001.ocs.aliyuncs.com:11211'), '927af6ee1c6411e4', '780227CNSCZDabc')

    def Clean(self):
        self.url_cachedb.flush_all()

    def Get(self, key):
        return self.url_cachedb.get(key)

    def Set(self, key, value):
        self.url_cachedb.set(key, value, time=self.expireTime)

class MemcachedCached(CachedBase):
    def __init__(self):
        super().__init__()
        self.url_cachedb = memcache.Client(['127.0.0.1:12000'],debug=0)

    def Clean(self):
        pass
    def Get(self, key):
        return self.url_cachedb.get(key)

    def Set(self, key, value):
        self.url_cachedb.set(key, value, time=self.expireTime)
