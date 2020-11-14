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

# plugin imports
from .abstract_api import JsonSettings
from .m3u import M3UProvider
from ..utils import ConfSelection, Channel
try:
	from ..loc import translate as _
except ImportError:
	def _(text):
		return text


class OTTProvider(JsonSettings, M3UProvider):
	NAME = "Only4TV-soveni"
	TVG_MAP = True

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://technic.cf/epg-soveni"
		self.playlist = "only4tv_pl.m3u8"
		s = self.getLocalSettings()
		self.playlist_url = "http://soveni.leolitz.info/plist/only4tv_epg_%s.m3u8" % s['playlist'].value

	def getLocalSettings(self):
		settings = {
			'playlist': ConfSelection(_("Playlist"), 'lite', [('lite', "Lite"), ('full', "Full")]),
		}
		return self._safeLoadSettings(settings)

	def makeChannel(self, num, name, url, tvg, logo, rec):
		m = self._url_regexp.match(url)
		if m:
			cid = int(m.group(1))
		else:
			cid = hash(url)
			# self.trace("Failed to get cid from url", url)
		url = url.replace("localhost", self._domain).replace("00000000000000", self._key)
		return Channel(cid, name, num, True), {'tvg': tvg, 'url': url, 'logo': logo}
