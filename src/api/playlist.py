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
from m3u import M3UProvider
from ..utils import APIException, Channel


class OTTProvider(M3UProvider):
	NAME = "M3U-Playlist"

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://iptvdream.zapto.org/epg-soveni"
		self.playlist = "playlist.m3u"

	def start(self):
		pass

	def setChannelsList(self):
		self._downloadTvgMap()
		m3u = self._locatePlaylist()
		try:
			with open(m3u) as f:
				self._parsePlaylist(f.readlines())
		except IOError as e:
			self.trace("error!", e)
			raise APIException(e)

	def makeChannel(self, url, gid, name, num):
		return Channel(hash(url), gid, name, num, name.endswith('(A)'))
