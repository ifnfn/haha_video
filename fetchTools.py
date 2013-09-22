#! /usr/bin/python3
# -*- coding: utf-8 -*-

import httplib2

global headers

socket_timeout = 20

headers = {
    'User-Agent'     : 'Kolatv',
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
    conn = httplib2.Http(timeout=socket_timeout)
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



if __name__ == '__main__':
    url = 'http://store.tv.sohu.com/view_content/movie/5008825_704321.html'
    url = 'http://index.tv.sohu.com/index/switch-aid/1012657'
    url = 'http://www.kolatv.com/'
    _, _, _, response = fetch_httplib2(url)
    print(response.decode())
