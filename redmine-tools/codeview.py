#!env python3
#encoding=utf8

import os
import json

import gerrit

def gerrit_main():
    username = "zhuzhg"
    host = "http://git.nationalchip.com"
    client = gerrit.Client(host)
    client.get_account('zhuzhg')


if __name__ == '__main__':
    gerrit_main()