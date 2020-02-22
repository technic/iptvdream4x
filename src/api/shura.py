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
import re

# plugin imports
from m3u import M3UProvider
from ..utils import Channel


class OTTProvider(M3UProvider):
	NAME = "ShuraTV"
	TVG_MAP = True

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://technic.cf/epg-soveni/"
		self.playlist = "shura_pl.m3u8"
		self.playlist_url = "http://soveni.leolitz.info/plist/shura_epg_ico.m3u8"
		self._url_regexp = re.compile(r"https?://[\w.]+/~\w+/(\d+)/hls/.*\.m3u8")

	def start(self):
		url_regexp = re.compile(r"https?://([\w.]+)/(\w+)/\d+/hls/pl.m3u8")
		self._extractKeyFromPlaylist(url_regexp)

	def makeChannel(self, num, name, url, tvg, logo, rec):
		m = self._url_regexp.match(url)
		if m:
			cid = int(m.group(1))
		else:
			cid = hash(url)
			self.trace("Failed to get cid from url", url)
		url = url.replace("localhost", self._domain).replace("00000000000000", self._key)
		return Channel(cid, name, num, rec), {'tvg': tvg, 'url': url, 'logo': logo}
