# -*- coding: utf-8 -*-
#  enigma2 iptv player
#
#  Copyright (c) 2020 Alex Maystrenko <alexeytech@gmail.com>
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from __future__ import print_function

# system imports
from urllib2 import HTTPError
import urllib
from json import loads as json_loads

# plugin imports
from abstract_api import JsonSettings
from m3u import M3UProvider
from ..utils import APIException, APILoginFailed
try:
	from ..loc import translate as _
except ImportError:
	def _(text):
		return text


class OTTProvider(JsonSettings, M3UProvider):
	NAME = "IpStreamOne"
	AUTH_TYPE = "Token"
	TVG_MAP = True

	token_page = "https://ipstream.one"

	def __init__(self, username, password):
		super(OTTProvider, self).__init__(username, password)
		self.site = "http://technic.cf/epg-soveni/"
		self._token = password

	def _getJson(self, url, params):
		try:
			self.trace(url)
			reply = self.readHttp(url + urllib.urlencode(params))
		except IOError as e:
			raise APIException(e)
		try:
			json = json_loads(reply)
		except Exception as e:
			raise APIException("Failed to parse json: %s" % str(e))
		return json

	def getToken(self, code):
		data = self._getJson("https://ipstream.one/api/iptvdream-apiH4s.php?", {'k': code})
		if data['status'] == '1':
			self._token = "%s-%s" % (data['user'].encode('utf-8'), data['password'].encode('utf-8'))
			return self._token
		else:
			self._token = None
			raise APILoginFailed(_("Ivalid key"))

	def start(self):
		self._downloadTvgMap()
		playlist_url = "http://www.ipstr.im/iptv/m3u_plus-%s" % self._token
		try:
			self._parsePlaylist(self.readHttp(playlist_url).split('\n'))
		except HTTPError as e:
			self.trace("HTTPError:", e, type(e), e.getcode())
			if e.code in (403, 404):
				raise APILoginFailed(e)
			else:
				raise APIException(e)
		except IOError as e:
			self.trace("IOError:", e, type(e))
			raise APIException(e)

	def setChannelsList(self):
		# Channels are downloaded during start, to allow handling login exceptions
		pass
