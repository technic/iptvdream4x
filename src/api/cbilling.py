# -*- coding: utf-8 -*-
#  enigma2 iptv player
#
#  Copyright (c) 2018 Alex Maystrenko <alexeytech@gmail.com>
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from __future__ import print_function

# system imports
import urllib
from json import loads as json_loads

# plugin imports
from abstract_api import OfflineFavourites
from ..utils import syncTime, APIException, APILoginFailed, EPG, Channel, Group


class OTTProvider(OfflineFavourites):
    NAME = "cbilling"
    HAS_LOGIN = False
    token_page = "https://cbilling.tv"

    def __init__(self, username, password):
        super(OTTProvider, self).__init__(username, password)
        self.site = "https://cbilling.tv/enigma"
        self.stalker_site = "http://mag.iptvx.tv/stalker_portal/server/tools"
        self._token = password
        self.web_names = {}
        self.urls = {}

    def start(self):
        self.authorize()

    def _getJson(self, url, params):
        try:
            self.trace(url)
            reply = self.readHttp(url + urllib.urlencode(params))
        except IOError as e:
            raise APIException(e)
        try:
            json = json_loads(reply)
        except Exception as e:
            raise APIException("Failed to parse json: %s" % str(e))
        # self.trace(json)
        return json

    def getToken(self, code):
        data = self._getJson(self.site + "/auth.php?", {'code': code})
        if int(data['status']) == 1:
            self._token = data['token'].encode('utf-8')
            return self._token
        else:
            self._token = None
            raise APILoginFailed(data['message'].encode('utf-8'))

    def authorize(self):
        data = self._getJson(self.site + "/update.php?", {'token': self._token})
        if int(data['status']) != 1:
            raise APILoginFailed(data['message'].encode('utf-8'))
        self.parseChannels(data['channels'])

    def parseChannels(self, channelsData):
        self.channels = {}
        self.groups = {}
        self.web_names = {}
        self.urls = {}
        group_names = {}
        for number, ch in enumerate(channelsData):
            group = ch['category'].encode('utf-8')
            try:
                gid = group_names[group]
                g = self.groups[gid]
            except KeyError:
                gid = len(group_names)
                group_names[group] = gid
                g = self.groups[gid] = Group(gid, group, [])

            cid = hash(ch['web_name'])
            c = Channel(cid, gid, ch['name'].encode('utf-8'), number, bool(ch['archive']))
            self.channels[cid] = c
            self.web_names[cid] = ch['web_name'].encode('utf-8')
            self.urls[cid] = ch['url'].encode('utf-8')
            g.channels.append(c)

    def getStreamUrl(self, cid, pin, time=None):
        if time is None:
            return self.urls[cid]
        else:
            return self.urls[cid].replace('index.m3u8', 'video-timeshift_abs-%s.m3u8' % time.strftime('%s'))

    def getDayEpg(self, cid, date):
        params = {"id": self.web_names[cid], "day": date.strftime("%Y-%m-%d")}
        data = self._getJson(self.stalker_site + "/epg_day.php?", params)
        return map(lambda e: EPG(
            int(e['begin']), int(e['end']),
            e['title'].encode('utf-8'), e['description'].encode('utf-8')), data['data'])

    def getChannelsEpg(self, cids):
        data = self._getJson(self.stalker_site + "/epg_list.php?", {"time": syncTime().strftime("%s")})
        for c in data['data']:
            yield hash(c['channel_id']), map(lambda e: EPG(
                    int(e['begin']), int(e['end']), e['title'].encode('utf-8'),
                    e['description'].encode('utf-8')
            ), c['programs'])
