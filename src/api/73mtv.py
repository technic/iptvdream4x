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
from ..utils import APILoginFailed, ConfSelection
try:
	from ..loc import translate as _
except ImportError:
	def _(text):
		return text


class OTTProvider(JsonSettings, M3UProvider):
	NAME = "73mtv"
	AUTH_TYPE = "Login"

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://technic.cf/epg-1ott/"

	def start(self):
		data = self.getJsonData("http://pl.73mtv.net/PinApi/%s/%s" % (self.username, self.password), {})
		token = data['token']
		if not token:
			raise APILoginFailed(_("Wrong number or pin"))
		s = self.getLocalSettings()
		self.playlist_url = 'http://pl.73mtv.net/api/%s/high/ottnav.%s' % (token, s['format'].value)

	def getStreamUrl(self, cid, pin, time=None):
		url = self.channels_data[cid]['url']
		if time:
			url += '?archive=%s' % time.strftime('%s')
		return url

	def getLocalSettings(self):
		settings = {
			'format': ConfSelection(_("Streaming format"), 'm3u', [('m3u', "TS"), ('m3u8', "HLS")])
		}
		return self._safeLoadSettings(settings)
