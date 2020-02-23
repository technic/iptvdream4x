# -*- coding: utf-8 -*-
#  enigma2 iptv player
#
#  Copyright (c) 2019 Alex Maystrenko <alexeytech@gmail.com>
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from __future__ import print_function

# plugin imports
from abstract_api import JsonSettings
from m3u import M3UProvider
from ..utils import APILoginFailed
try:
	from ..loc import translate as _
except ImportError:
	def _(text):
		return text


class OTTProvider(JsonSettings, M3UProvider):
	NAME = "1ott"
	AUTH_TYPE = "Login"

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://technic.cf/epg-1ott/"

	def start(self):
		data = self.getJsonData("http://list.1ott.net/PinApi/%s/%s" % (self.username, self.password), {})
		token = data['token']
		if not token:
			raise APILoginFailed(_("Wrong number or pin"))
		self.playlist_url = 'http://list.1ott.net/api/%s/high/ottplay.m3u' % token

	def getStreamUrl(self, cid, pin, time=None):
		url = self.channels_data[cid]['url']
		if time:
			url += '?archive=%s' % time.strftime('%s')
		return url
