#! /usr/bin/python3
# -*- coding: utf-8 -*-

from kola import utils


def GetEPGScript(albumName):
    info = get_channel_tvmao(albumName)
    if info == None:
        info = get_channel_wasu(albumName)

    if info == None:
        info = utils.GetScript('epg', 'get_channel', [albumName])

    return info

def get_channel_wasu(albumName):
    name_key = {}
    if albumName in name_key:
        return utils.GetScript('epg', 'get_channel_wasu', [albumName, name_key[albumName]])

    return None

def get_channel_tvmao(albumName):
    name_key = {}


    if albumName in name_key:
        return utils.GetScript('epg', 'get_channel_tvmao', [albumName, name_key[albumName]])

    return None

def get_channel_qq(albumName):
    return None
