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
from m3u import M3UProvider
from ..utils import syncTime, APIException, EPG, Channel, Group


class OTTProvider(M3UProvider):
	NAME = "ShuraTV"

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://iptvdream.zapto.org/epg-soveni/"
		self.playlist = "shura_pl.m3u8"
		self.playlist_url = "http://soveni.leolitz.info/plist/shura_epg_ico.m3u8"

	def start(self):
		import re
		url_regexp = re.compile(r"https?://([\w.]+)/(\w+)/\d+/hls/pl.m3u8")

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
				cid = num
				c = Channel(cid, gid, name, num, name.endswith("(A)"))
				self.channels[cid] = c
				g.channels.append(c)
				self.channels_data[cid] = {'tvg': tvg, 'url': url}
				if tvg is not None:
					try:
						self.tvg_ids[tvg].append(cid)
					except KeyError:
						self.tvg_ids[tvg] = [cid]
				else:
					self.trace("Failed to parse url:", line)
					continue

		self.trace("Loaded {} channels".format(len(self.channels)))
		# all_ch = sorted(self.channels.values(), key=lambda k: getattr(k, 'number'))
		# self.groups[-1] = Group(gid=-1, title=_("All channels"), channels=all_ch)
		# self.groups[-2] = Group(gid=-2, title=_("Favourites"), channels=[])
		# print(self.channels, self.groups)
