#! /usr/bin/python3
# -*- coding: utf-8 -*-

import base64
import hashlib
import os
import sys
import traceback
import zlib

import httplib2


global headers

MAX_TRY = 3
socket_timeout = 30

headers = {
    'User-Agent'     : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36',
    'Accept'         : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Keep-Alive'     : '115',
    'Connection'     : 'keep-alive',
    'Cache-Control'  : 'max-age=0'
}

def fetch_httplib2(url, method='GET', data=None, header=headers, cookies=None, referer=None, acceptencoding=None):
    if cookies and cookies != 'none':
        header['Cookie'] = cookies
    if referer:
        header['referer'] = referer
    if acceptencoding == None or acceptencoding == 'default':
        header['Accept-Encoding'] = 'gzip, deflate'
    else:
        header['Accept-Encoding'] = acceptencoding

    if method == 'POST':
        header['Content-Type'] = 'application/x-www-form-urlencoded'
    conn = httplib2.Http('.cache', timeout=socket_timeout)
    conn.follow_redirects = True
    response, responses = conn.request(uri=url, method=str(method).upper(), body=data,  headers=header)
    try:
        content_type = response['content-type']
    except:
        content_type = ''
    try:
        location = response['location']
    except:
        location = ''

    if 'referer' in headers:
        headers.pop('referer')
    if 'Cookie' in headers:
        headers.pop('Cookie')

    return response['status'], content_type, location, responses

def GetUrl(url, times = 0):
    key = hashlib.md5(url.encode('utf8')).hexdigest().upper()
    filename = './cache/' + key
    if times > MAX_TRY:
        return '', '', False
    try:
        status, _, _, response = fetch_httplib2(url)
        if status != '200' and status != '304':
            print('status %s, try %d ...' % (status, times + 1))
            return GetUrl(url, times + 1)
        return response, filename, False
    except:
        t, v, tb = sys.exc_info()
        print("KolaClient.GetUrl: %s %s, %s, %s" % (url, t, v, traceback.format_tb(tb)))
        return GetUrl(url, times + 1)

def GetCacheUrl(url):
    response = ''

    key = hashlib.md5(url.encode('utf8')).hexdigest().upper()
    filename = './cache/' + key
    exists = os.path.exists(filename)
    if exists:
        f = open(filename, 'rb')
        response = f.read()
        f.close()
    else:
        response,_,_ = GetUrl(url)
        if response:
            try:
                f = open(filename, 'wb')
                f.write(response)
                f.close()
            except:
                pass

    return response, filename, exists

def PostUrl(url, body, key=""):
    try:
        compress = zlib.compressobj(9,
                                    zlib.DEFLATED,
                                    - zlib.MAX_WBITS,
                                    zlib.DEF_MEM_LEVEL,
                                    0)
        body = b"\x5A\xA5" + compress.compress(body.encode())
        body += compress.flush()
        body = base64.encodebytes(body).decode()

        ret, _, _, response = fetch_httplib2(url, 'POST', body, cookies = "key=" + key)
        if ret != "200":
            print(response)
            return None
        return response
    except:
        t, v, tb = sys.exc_info()
        print("PostUrl: %s, %s, %s" % (t, v, traceback.format_tb(tb)))
        return None

if __name__ == '__main__':
    url = 'http://store.tv.sohu.com/view_content/movie/5008825_704321.html'
    url = 'http://index.tv.sohu.com/index/switch-aid/1012657'
    url = 'http://www.kolatv.com/'
    _, _, _, response = fetch_httplib2(url)
    print(response.decode())
