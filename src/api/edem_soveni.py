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
from ..utils import ConfSelection
from abstract_api import JsonSettings
from m3u import M3UProvider
try:
	from ..loc import translate as _
except ImportError:
	def _(text):
		return text


class OTTProvider(JsonSettings, M3UProvider):
	NAME = "EdemTV-Soveni"
	TVG_MAP = True

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://iptvdream.zapto.org/epg-soveni/"
		self.playlist = "edem_pl.m3u8"
		s = self.getSettings()
		self.playlist_url = "http://soveni.leolitz.info/plist/edem_epg_%s.m3u8" % s['playlist'].value

	def getSettings(self):
		settings = {
			'playlist': ConfSelection(_("Playlist"), 'lite', [('lite', "Lite"), ('ico', "Full")]),
		}
		return self._safeLoadSettings(settings)

	def pushSettings(self, settings):
		data = self._loadSettings()
		data.update(settings)
		self._saveSettings(data)
