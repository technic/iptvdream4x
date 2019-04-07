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
from ..utils import APIException, APILoginFailed
from urllib2 import HTTPError


class OTTProvider(M3UProvider):
	NAME = "KingModIPTV"
	HAS_LOGIN = True
	TVG_MAP = True

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://iptvdream.zapto.org/epg-king/"
		self.playlist = ""
		self.playlist_url = "http://pl.kingmodiptv.top/%s/%s/tv.m3u" % (username, password)

	def setChannelsList(self):
		# Channels are downloaded during start, to allow handling login exceptions
		pass

	def start(self):
		self._downloadTvgMap()
		try:
			self._parsePlaylist(self.readHttp(self.playlist_url).split('\n'))
		except HTTPError as e:
			self.trace("HTTPError:", e, type(e), e.getcode())
			if e.code in (403, 404):
				raise APILoginFailed(e)
			else:
				raise APIException(e)
		except IOError as e:
			self.trace("IOError:", e, type(e))
			raise APIException(e)
