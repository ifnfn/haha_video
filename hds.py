#! /usr/bin/python3
# -*- coding: utf-8 -*-

from engine.kolaclient import GetUrl
import xml.etree.ElementTree as ET
import json
import sys, logging
import struct, time

log = logging.getLogger('svtplay_dl')

def select_quality(quality, flexibleq, streams):
    available = sorted(streams.keys(), key=int)

    try:
        optq = int(quality)
    except ValueError:
        log.error("Requested quality need to be a number")
        sys.exit(4)
    if optq:
        try:
            optf = int(flexibleq)
        except ValueError:
            log.error("Flexible-quality need to be a number")
            sys.exit(4)
        if not optf:
            wanted = [optq]
        else:
            wanted = range(optq-optf, optq+optf+1)
    else:
        wanted = [available[-1]]

    selected = None
    for q in available:
        if q in wanted:
            selected = q
            break

    if not selected:
        log.error("Can't find that quality. Try one of: %s (or try --flexible-quality)",
                  ", ".join([str(elm) for elm in available]))
        sys.exit(4)

    return streams[selected]

def readbyte(data, pos):
    return struct.unpack("B", bytes(chr(data[pos]), "ascii"))[0]

def read32(data, pos):
    end = pos + 4
    return struct.unpack(">i", data[pos:end])[0]

def read64(data, pos):
    end = pos + 8
    return struct.unpack(">Q", data[pos:end])[0]

def readboxtype(data, pos):
    boxsize = read32(data, pos)
    tpos = pos + 4
    endpos = tpos + 4
    boxtype = data[tpos:endpos]
    if boxsize > 1:
        boxsize -= 8
        pos += 8
        return pos, boxsize, boxtype

def readstring(data, pos):
    length = 0
    while bytes(chr(data[pos + length]), "ascii") != b"\x00":
        length += 1
    endpos = pos + length
    string = data[pos:endpos]
    pos += length + 1
    return pos, string

def readasrtbox(data, pos):
    #version = readbyte(data, pos)
    pos += 1
    #flags = read24(data, pos)
    pos += 3
    qualityentrycount = readbyte(data, pos)
    pos += 1
    qualitysegmentmodifers = []
    i = 0
    while i < qualityentrycount:
        temp = readstring(data, pos)
        qualitysegmentmodifers.append(temp[1])
        pos = temp[0]
        i += 1

    seqCount = read32(data, pos)
    pos += 4
    ret = {}
    i = 0

    while i < seqCount:
        firstseg = read32(data, pos)
        pos += 4
        fragPerSeg = read32(data, pos)
        pos += 4
        tmp = i + 1
        ret[tmp] = {"first": firstseg, "total": fragPerSeg}
        i += 1
    return ret

def readafrtbox(data, pos):
    #version = readbyte(data, pos)
    pos += 1
    #flags = read24(data, pos)
    pos += 3
    #timescale = read32(data, pos)
    pos += 4
    qualityentry = readbyte(data, pos)
    pos += 1
    i = 0
    while i < qualityentry:
        temp = readstring(data, pos)
        #qualitysegmulti = temp[1]
        pos = temp[0]
        i += 1
    fragrunentrycount = read32(data, pos)
    pos += 4
    i = 0
    ret = []
    while i < fragrunentrycount:
        firstfragment = read32(data, pos)
        pos += 4
        timestamp = read64(data, pos)
        pos += 8
        duration = read32(data, pos)
        pos += 4
        i += 1
        print(firstfragment, timestamp, duration)
        ret.append({'fragment' : firstfragment, 'timestamp' : timestamp, 'duration' : duration})

    return ret

def readbox(data, pos):
    #version = readbyte(data, pos)
    pos += 1
    #flags = read24(data, pos)
    pos += 3
    #bootstrapversion = read32(data, pos)
    pos += 4
    #byte = readbyte(data, pos)
    pos += 1
    #profile = (byte & 0xC0) >> 6
    #live = (byte & 0x20) >> 5
    #update = (byte & 0x10) >> 4
    #timescale = read32(data, pos)
    pos += 4
    #currentmediatime = read64(data, pos)
    pos += 8
    #smptetimecodeoffset = read64(data, pos)
    #print(currentmediatime, smptetimecodeoffset)
    pos += 8
    temp = readstring(data, pos)
    #movieidentifier = temp[1]
    pos = temp[0]
    serverentrycount = readbyte(data, pos)
    pos += 1
    serverentrytable = []
    i = 0
    while i < serverentrycount:
        temp = readstring(data, pos)
        serverentrytable.append(temp[1])
        pos = temp[0]
        i += 1
    qualityentrycount = readbyte(data, pos)
    pos += 1
    qualityentrytable = []
    i = 0
    while i < qualityentrycount:
        temp = readstring(data, pos)
        qualityentrytable.append(temp[1])
        pos = temp[0]
        i += 1

    tmp = readstring(data, pos)
    #drm = tmp[1]
    pos = tmp[0]
    tmp = readstring(data, pos)
    #metadata = tmp[1]
    pos = tmp[0]
    segmentruntable = readbyte(data, pos)
    pos += 1
    if segmentruntable > 0:
        tmp = readboxtype(data, pos)
        boxtype = tmp[2]
        boxsize = tmp[1]
        pos = tmp[0]
        if boxtype == b"asrt":
            antal = readasrtbox(data, pos)
            pos += boxsize
    fragRunTableCount = readbyte(data, pos)
    pos += 1
    i = 0
    while i < fragRunTableCount:
        tmp = readboxtype(data, pos)
        boxtype = tmp[2]
        boxsize = tmp[1]
        pos = tmp[0]
        if boxtype == b"afrt":
            antal['a' ] = readafrtbox(data, pos)
            pos += boxsize
        i += 1
    return antal


class F4mToM3u8:
    def __init__(self, url):
        url = 'http://vcbox.cntv.chinacache.net/cache/hdscctv1.f4m'
        self.url = url
        self.max_fragment = 0
        self.startUpdate = 0
        self.endUpdate = 0
        self.streams = {}
        self.m3u8String = ''
        self.baseurl  = url[0:url.rfind("/")]
        text = GetUrl('http://vcbox.cntv.chinacache.net/cache/hdscctv1.f4m')

        xml = ET.XML(text)
        mediaIter = xml.iter("{http://ns.adobe.com/f4m/1.0}media")

        for i in mediaIter:
            self.streams[int(i.attrib["bitrate"])] = {
                            "url": i.attrib["url"],
                            #"bootstrapInfoId": i.attrib["bootstrapInfoId"],
                            #"metadata": i.find("{http://ns.adobe.com/f4m/1.0}metadata").text
                        }
        print(json.dumps(self.streams, indent=4, ensure_ascii=False))
        self.localTime = 0
    def Update(self):
        #offset = time.time() - self.localTime
        #if (offset * 1000 < self.endUpdate - self.startUpdate):
        #    return self.m3u8String

        self.localTime = time.time()
        m3u8 = []

        quality = "1206"
        flexibleq = "1206"
        test = select_quality(quality, flexibleq, self.streams)

        bootstrapUrl = self.baseurl + '/' + test['url'][9:]
        bootstrap=GetUrl(bootstrapUrl + '.bootstrap')
        box = readboxtype(bootstrap, 0)

        antal = None
        if box[2] == b"abst":
            antal = readbox(bootstrap, box[0])
            print(antal)

            m  = 0
            self.startUpdate =  0
            for i in antal['a']:
                if self.startUpdate == 0:
                    self.startUpdate = i['timestamp']
                self.endUpdate = i['timestamp']

                a = round(i['duration']/1000.0, 0)
                if a > m:
                    m = a
            m3u8.append('#EXTM3U')
            m3u8.append('#EXT-X-TARGETDURATION: %d' % (m/1000))
            m3u8.append('#EXT-X-MEDIA-SEQUENCE: %d' % (self.startUpdate/10000))
            #EXT-X-MEDIA-SEQUENCE:139057731
#EXT-X-TARGETDURATION:10

            for i in antal['a']:
                fragment = i['fragment']
                if fragment > self.max_fragment:
                    m3u8.append('#EXTINF:%d,' % round(i['duration']/1000.0, 0))
                    url = "%sSeg%d-Frag%d" % (bootstrapUrl, fragment, fragment)
                    m3u8.append(url)
                    self.max_fragment = fragment

        self.m3u8String = '\n'.join(m3u8)

        return self.m3u8String

class O:
    def __init__(self):
        self.quality = "552"
        self.flexibleq =  "38878"

if __name__ == "__main__":
    options = O()
    options.quality = "552"
    options.flexibleq =  "38878"
    print(F4mToM3u8('').Update())
    #main()
