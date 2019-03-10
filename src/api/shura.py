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
import os

# plugin imports
from abstract_api import OfflineFavourites
from ..utils import syncTime, APIException, EPG, Channel, Group


class OTTProvider(OfflineFavourites):
	NAME = "ShuraTV"
	HAS_LOGIN = False

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://iptvdream.zapto.org/epg-soveni/"
		self.channels = {}
		self.groups = {}
		self.channels_data = {}
		self._domain = ''
		self._key = ''

	def start(self):
		try:
			from Tools.Directories import resolveFilename, SCOPE_SYSETC
			path = resolveFilename(SCOPE_SYSETC, 'iptvdream')
		except ImportError:
			path = '.'

		m3u8 = os.path.join(path, 'shura_pl.m3u8')
		if not os.path.exists(m3u8):
			raise APIException("ShuraTV playlist not found! Please copy your playlist to %s." % m3u8)

		import re
		url_regexp = re.compile("https?://([\w.]+)/(\w+)/\d+/hls/pl.m3u8")

		with open(m3u8) as f:
			for line in f:
				line = line.strip()
				m = url_regexp.match(line)
				if m:
					self._domain = m.group(1)
					self._key = m.group(2)
					self.trace("found domain and key in user playlist")
					break
		if not (self._domain and self._key):
			raise APIException("Failed to parse ShuraTV playlist located at %s." % m3u8)

		try:
			self._parsePlaylist(self.readHttp("http://soveni.leolitz.info/plist/shura_epg_ico.m3u8").split('\n'))
		except IOError as e:
			self.trace("error!", e)
			raise APIException(e)

	def _parsePlaylist(self, lines):
		group_names = {}
		num = 0

		name = ""
		group = "Unknown"
		cid = None

		import re
		tvg_regexp = re.compile('#EXTINF:.*tvg-id="([^"]*)"')
		group_regexp = re.compile('#EXTINF:.*group-title="([^"]*)"')

		for line in lines:
			# print(line)
			if line.startswith("#EXTINF:"):
				name = line.strip().split(',')[1]
				m = tvg_regexp.match(line)
				if m:
					cid = int(m.group(1))
				else:
					cid = None
				m = group_regexp.match(line)
				if m:
					group = m.group(1)
				else:
					group = "Unknown"
			elif line.startswith("#EXTGRP:"):
				group = line.strip().split(':')[1]
			elif line.startswith("#EXTM3U"):
				continue
			elif not line.strip():
				continue
			elif cid is not None:
				url = line.strip().replace("localhost", self._domain).replace("00000000000000", self._key)
				assert url.find("://") > 0, "line: " + url
				try:
					gid = group_names[group]
					g = self.groups[gid]
				except KeyError:
					gid = len(group_names)
					group_names[group] = gid
					g = self.groups[gid] = Group(gid, group.decode('utf-8').encode('utf-8'), [])

				num += 1
				c = Channel(cid, gid, name, num, name.endswith("(A)"))
				self.channels[cid] = c
				g.channels.append(c)
				self.channels_data[cid] = {'tvg': cid, 'url': url}

		# all_ch = sorted(self.channels.values(), key=lambda k: getattr(k, 'number'))
		# self.groups[-1] = Group(gid=-1, title=_("All channels"), channels=all_ch)
		# self.groups[-2] = Group(gid=-2, title=_("Favourites"), channels=[])
		# print(self.channels, self.groups)

	def getStreamUrl(self, cid, pin, t=None):
		url = self.channels_data[cid]['url']
		if t:
			url += '?utc=%s&lutc=%s' % (t.strftime('%s'), syncTime().strftime('%s'))
		return url

	def getDayEpg(self, cid, date):
		params = {"id": self.channels_data[cid]['tvg'], "day": date.strftime("%Y.%m.%d")}
		data = self.getJsonData(self.site + "/epg_day?", params)
		return map(lambda e: EPG(
				int(e['begin']), int(e['end']),
				e['title'].encode('utf-8'), e['description'].encode('utf-8')), data['data'])

	def getChannelsEpg(self, cids):
		data = self.getJsonData(self.site + "/epg_list?", {"time": syncTime().strftime("%s")})
		for c in data['data']:
			cid = c['channel_id']
			yield cid, map(lambda e: EPG(
				int(e['begin']), int(e['end']), e['title'].encode('utf-8'),
				e['description'].encode('utf-8')), c['programs'])
