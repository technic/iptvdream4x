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
from json import loads as json_loads

# plugin imports
from m3u import M3UProvider
from abstract_api import JsonSettings
from ..utils import APIException, Channel, ConfSelection, ConfString
from ..loc import translate as _


class OTTProvider(JsonSettings, M3UProvider):
	NAME = "M3U-Playlist"
	TVG_MAP = True

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		s = self.getSettings()
		self.site = s['epg_url'].value
		self.archive_tag = s['archive'].value
		self.playlist = "playlist.m3u"
		self.name_map = {}

	def start(self):
		try:
			self.name_map = json_loads(self.readHttp(self.site + "/channels_names"))['data']
		except IOError as e:
			self.trace("error!", e)
			raise APIException(e)

	def setChannelsList(self):
		self._downloadTvgMap()
		m3u = self._locatePlaylist()
		try:
			with open(m3u) as f:
				self._parsePlaylist(f.readlines())
		except IOError as e:
			self.trace("error!", e)
			raise APIException(e)

	def makeChannel(self, num, name, url, tvg, logo):
		if tvg is None:
			try:
				tvg = self.name_map[name.decode('utf-8')]
			except KeyError:
				pass
		if self.archive_tag == 'tagged':
			archive = name.endswith('(A)')
		else:
			archive = True
		return Channel(hash(url), name, num, archive), {'tvg': tvg, 'url': url, 'logo': logo}

	def getSettings(self):
		settings = {
			'archive': ConfSelection(_("Enable archive"), 'all', [
				('all', "All channels"), ('tagged', "Marked channels (A)")
			]),
			'epg_url': ConfString(_("EPG-json url"), "http://iptvdream.zapto.org/epg-soveni")
		}
		return self._safeLoadSettings(settings)
