#!env python3
#encoding=utf8
#coding=utf8


import os
import sys
import traceback

import httplib2


try:
    import ConfigParser as configparser
except:
    import configparser

try:
    import urllib.request as urllib
except:
    import urllib

try:
    raw_input = raw_input
except NameError:
    raw_input = input


GerritHost = 'http://git.nationalchip.com/gerrit/a'

class Gerrit(object):
    def __init__(self, baseUrl):
        self.project = []
        self.baseUrl = baseUrl
        config = configparser.ConfigParser(allow_no_value=True)
        config_file = os.path.expanduser('~/.goxceed.conf')
        config.read(config_file)
        try:
            self.username = config.get("goxceed","username")
        except:
            self.username = raw_input('Input user name: ')

        try:
            self.password = config.get("goxceed","password")
        except:
            self.password = raw_input('Input user password: ')

        if not config.has_section('goxceed'):
            config.add_section('goxceed')
        config.set('goxceed', 'username', self.username)
        config.set('goxceed', 'password', self.password)

        with open(config_file, 'w') as fp:
                config.write(fp)

    def rawPut(self, url, text):
        if url.find('http://') < 0:
            url = self.baseUrl + url

        try:
            h = httplib2.Http(timeout=3000)
            h.add_credentials(self.username, self.password)
            headers = {'Content-Type': 'application/json;charset=UTF-8'}

            resp, content = h.request(url, 'PUT', body=text,headers=headers)

            status = resp['status']
            if status in ['201', '409', '404']:
                    return content.decode(), status;
        except:
            t, v, tb = sys.exc_info()
            print("KolaClient.GetUrl: %s %s, %s, %s" % (url, t, v, traceback.format_tb(tb)))
            return '', '408'


    def CreateBranch(self, project, src_branch, dest_branch):
        url = '/projects/%s/branches/%s' % (urllib.quote(project, ''), dest_branch)
        body = '{"revision": "%s"}' % src_branch

        #print(url, body)
        text, status = self.rawPut(url, body)
        if status == '201':
            print('"%s" Branch create %s ok.' % (project, dest_branch))
        else:
            print('"%s": %s' % (project, text[:-1]))

def main(argv):
    projects = ['application/test', 'androidtv/ios']
    if len(argv) > 2:
        src_branch = argv[1]
        dest_branch = argv[2]
    else:
        print("branch <source branch> <dest branch>")
        return

    gerrit = Gerrit(GerritHost)

    for p in projects:
        gerrit.CreateBranch(p, src_branch, dest_branch)

if __name__ == '__main__':
    main(sys.argv)
