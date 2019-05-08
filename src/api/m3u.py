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
from time import mktime
from json import loads as json_loads

# plugin imports
from abstract_api import OfflineFavourites
from ..utils import syncTime, APIException, EPG, Channel, Group


class M3UProvider(OfflineFavourites):
	NAME = "M3U"
	HAS_LOGIN = False

	TVG_MAP = False  # True if tvg-id are non-numerical and we need to get map from server

	def __init__(self, username, password):
		super(M3UProvider, self).__init__(username, password)
		# Override site and playlist in derived class
		self.site = ""
		self.playlist = "default.m3u"
		self.playlist_url = ""
		self.channels = {}
		self.groups = {}
		# map from channel ids in playlist to epg server ids
		self.channels_data = {}
		# map from xmltv keys to epg server ids
		self.tvg_map = {}
		# map from epg server ids to channel ids
		self.tvg_ids = {}
		self._domain = ''
		self._key = ''

	def _locatePlaylist(self):
		"""Returns path to the playlist file"""
		try:
			from Tools.Directories import resolveFilename, SCOPE_SYSETC
			path = resolveFilename(SCOPE_SYSETC, 'iptvdream')
		except ImportError:
			path = '.'

		m3u8 = os.path.join(path, self.playlist)
		if not os.path.exists(m3u8):
			raise APIException("%s playlist not found! Please copy your playlist to %s." % (self.NAME, m3u8))
		return m3u8

	def start(self):
		import re
		url_regexp = re.compile(r"https?://([\w.]+)/iptv/(\w+)/\d+/index.m3u8")

		m3u8 = self._locatePlaylist()
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
			raise APIException("Failed to parse %s playlist located at %s." % (self.NAME, m3u8))

	def setChannelsList(self):
		self._downloadTvgMap()
		try:
			self._parsePlaylist(self.readHttp(self.playlist_url).split('\n'))
		except IOError as e:
			self.trace("error!", e, type(e))
			raise APIException(e)

	def _downloadTvgMap(self):
		self.tvg_map = {}
		if self.TVG_MAP:
			try:
				self.tvg_map = json_loads(self.readHttp(self.site + "/channels"))['data']
			except IOError as e:
				self.trace("error!", e)
				raise APIException(e)

	def _parsePlaylist(self, lines):
		self.tvg_ids = {}
		group_names = {}
		num = 0

		name = ""
		group = "Unknown"
		tvg = None

		import re
		tvg_regexp = re.compile('#EXTINF:.*tvg-id="([^"]*)"')
		group_regexp = re.compile('#EXTINF:.*group-title="([^"]*)"')
		url_regexp = re.compile(r"https?://[\w.]+/iptv/\w+/(\d+)/index.m3u8")

		for line in lines:
			# print(line)
			if line.startswith("#EXTINF:"):
				name = line.strip().split(',')[1]
				m = tvg_regexp.match(line)
				if m:
					if self.tvg_map:
						k = unicode(m.group(1))
						try:
							tvg = self.tvg_map[k]
						except KeyError:
							tvg = None
							self.trace("unknown tvg-id", k)
					else:
						tvg = int(m.group(1))
				else:
					tvg = None
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
			else:
				url = line.strip().replace("localhost", self._domain).replace("00000000000000", self._key)
				assert url.find("://") > 0, "line: " + url
				try:
					gid = group_names[group]
					g = self.groups[gid]
				except KeyError:
					gid = len(group_names)
					group_names[group] = gid
					g = self.groups[gid] = Group(gid, group, [])
		
				num += 1
				m = url_regexp.match(line)
				if m:
					cid = int(m.group(1))
				else:
					cid = num
				c = Channel(cid, gid, name, num, True)
				self.channels[cid] = c
				g.channels.append(c)
				self.channels_data[cid] = {'tvg': tvg, 'url': url}
				if tvg is not None:
					try:
						self.tvg_ids[tvg].append(cid)
					except KeyError:
						self.tvg_ids[tvg] = [cid]
		
		self.trace("Loaded {} channels".format(len(self.channels)))
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
		t = mktime(syncTime().timetuple())
		data = self.getJsonData(self.site + "/epg_list?", {"time": int(t)})
		for c in data['data']:
			tvg = c['channel_id']
			try:
				cids = self.tvg_ids[tvg]
			except KeyError:
				# self.trace("Unknown teleguide id", tvg)
				continue
			for cid in cids:
				yield cid, map(lambda e: EPG(
					int(e['begin']), int(e['end']), e['title'].encode('utf-8'),
					e['description'].encode('utf-8')), c['programs'])
