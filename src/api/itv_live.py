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
from json import loads as json_loads, dumps as json_dumps

# plugin imports
from abstract_api import OfflineFavourites
from ..utils import syncTime, APIException, APILoginFailed, EPG, Channel, Group


class OTTProvider(OfflineFavourites):
	NAME = "ITVLive"
	TITLE = "ITV.LIVE"
	AUTH_TYPE = "Login"

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://api.itv.live"
		self.channels_data = {}

	def start(self):
		self.channels = {}
		self.groups = {}
		self.channels_data = {}

		data = self._getJson(self.site + '/data/%s' % self.username, {})
		for number, ch in enumerate(data['channels']):
			group = ch['cat_name'].encode('utf-8')
			gid = int(ch['cat_id'])
			try:
				g = self.groups[gid]
			except KeyError:
				g = self.groups[gid] = Group(gid, group, [])

			cid = hash(ch['ch_id'])
			c = Channel(cid, ch['channel_name'].encode('utf-8'), number, bool(int(ch['rec'])), False)
			self.channels[cid] = c
			self.channels_data[cid] = {
				'url': ch['ch_url'].encode('utf-8'),
				'logo': ch['logo_url'].encode('utf-8'),
				'id': ch['ch_id_epg'],
			}
			g.channels.append(c)

	def _getJson(self, url, params):
		self.trace(url)
		try:
			reply = self.readHttp(url + urllib.urlencode(params))
		except IOError as e:
			raise APIException(e)
		try:
			json = json_loads(reply)
		except Exception as e:
			raise APIException("Failed to parse json: %s" % str(e))
		# self.trace(json)
		return json

	def getStreamUrl(self, cid, pin, time=None):
		url = self.channels_data[cid]['url']
		if time is None:
			return url
		return url.replace('video.m3u8', 'video-timeshift_abs-%s.m3u8' % time.strftime('%s'))

	def getChannelsEpg(self, cids):
		data = self._getJson(self.site + '/epg.php?', {
			'obj': json_dumps({
				'action': 'arraychepg',
				'chid': ["%d:%s" % (cid, value['id']) for cid, value in self.channels_data.items()],
			})
		})
		for e in data['res']:
			yield int(e['id']), [EPG(
				int(e['startTime']), int(e['stopTime']), e['title'].encode('utf-8'), e['desc'].encode('utf-8')
			)]

	def getDayEpg(self, cid, date):
		data = self._getJson(self.site + '/epg.php?', {
			'action': 'epg', 'chid': self.channels_data[cid]['id']
		})
		return [EPG(int(e['startTime']), int(e['stopTime']), e['title'].encode('utf-8')) for e in data['res']]

	def getPiconUrl(self, cid):
		return self.channels_data[cid]['logo']
