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
from abstract_api import JsonSettings
from m3u import M3UProvider
from ..utils import ConfSelection
try:
	from ..loc import translate as _
except ImportError:
	def _(text):
		return text


class OTTProvider(M3UProvider, JsonSettings):
	NAME = "Only4TV-soveni"

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://iptvdream.zapto.org/epg-soveni"
		self.playlist = "only4tv_pl.m3u8"
		s = self.getSettings()
		self.playlist_url = "http://soveni.leolitz.info/plist/only4tv_epg_%s.m3u8" % s['playlist'].value

	def getSettings(self):
		settings = {
			'playlist': ConfSelection(_("Playlist"), 'lite', [('lite', "Lite"), ('full', "Full")]),
		}
		return self._safeLoadSettings(settings)

	def pushSettings(self, settings):
		data = self._loadSettings()
		data.update(settings)
		self._saveSettings(data)
