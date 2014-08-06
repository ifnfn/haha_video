#! /usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import redis
import memcache
import bmemcached

class CachedBase:
    def __init__(self):
        self.expireTime = 60 * 60

    def Clean(self, regular='*'):
        pass

    def Get(self, key):
        pass

    def Set(self, key, value, timeout=None):
        pass

    def GetKey(self, key):
        return key
        #key = hashlib.sha1(key.encode()).hexdigest()
        #return 'album_' + key

class RedisCached(CachedBase):
    def __init__(self):
        super().__init__()
        self.url_cachedb = redis.Redis(host='127.0.0.1', port=6379, db=1)

    def Clean(self, regular='*'):
        pipe = self.url_cachedb.pipeline()
        for key in self.url_cachedb.keys(regular):
            pipe.delete(key)
        pipe.execute()

    def Get(self, key):
        key = self.GetKey(key)
        return self.url_cachedb.get(key)

    def Set(self, key, value, timeout=None):
        key = self.GetKey(key)
        self.url_cachedb.set(key, value)
        if timeout == None:
            timeout = self.expireTime
        self.url_cachedb.expire(key, timeout)

    def Keys(self, regular):
        return self.url_cachedb.keys(regular)

class AliyunCached(CachedBase):
    def __init__(self):
        super().__init__()
        username = '927af6ee1c6411e4'
        password = hashlib.sha1(username.encode()).hexdigest()
        password = password[:10] + password[11:20].upper()
        self.url_cachedb = bmemcached.Client(('927af6ee1c6411e4.m.cnqdalicm9pub001.ocs.aliyuncs.com:11211'), username, password)

    def Clean(self, regular='*'):
        self.url_cachedb.flush_all()

    def Get(self, key):
        key = self.GetKey(key)
        print("Get:", key)
        return self.url_cachedb.get(key)

    def Set(self, key, value, timeout=None):
        key = self.GetKey(key)
        print("Set:", key)
        if timeout == None:
            timeout = self.expireTime

        self.url_cachedb.set(key, value, time=timeout)

class MemcachedCached(CachedBase):
    def __init__(self):
        super().__init__()
        self.url_cachedb = memcache.Client(['127.0.0.1:12000'],debug=0)

    def Clean(self):
        pass
    def Get(self, key):
        key = self.GetKey(key)
        return self.url_cachedb.get(key)

    def Set(self, key, value, timeout=None):
        key = self.GetKey(key)
        if timeout == None:
            timeout = self.expireTime
        self.url_cachedb.set(key, value, time=timeout)
