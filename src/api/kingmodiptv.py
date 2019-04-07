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
from ..utils import APIException, APILoginFailed, Channel, Group
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

	def _parsePlaylist(self, lines):
		# Copy of M3U class with some modifications
		group_names = {}
		num = 0

		name = ""
		group = "Unknown"
		archive = False
		cid = None

		import re
		tvg_regexp = re.compile('#EXTINF:.*tvg-id="([^"]*)"')
		group_regexp = re.compile('#EXTINF:.*group-title="([^"]*)"')
		archive_regexp = re.compile('#EXTINF:.*catchup-days="([^"]*)"')

		for line in lines:
			# print(line)
			if line.startswith("#EXTINF:"):
				name = line.strip().split(',')[1]
				m = tvg_regexp.match(line)
				if m:
					if self.tvg_map:
						k = unicode(m.group(1))
						try:
							cid = self.tvg_map[k]
							# print("found", cid, "for", k)
						except KeyError:
							cid = None
							self.trace("unknown tvg-id", k)
					else:
						cid = int(m.group(1))
				else:
					cid = None
				m = group_regexp.match(line)
				if m:
					group = m.group(1)
				else:
					group = "Unknown"
				m = archive_regexp.match(line)
				if m:
					archive = True
				else:
					archive = False
			elif line.startswith("#EXTGRP:"):
				group = line.strip().split(':')[1]
			elif line.startswith("#EXTM3U"):
				continue
			elif not line.strip():
				continue
			elif cid is not None:
				url = line.strip().replace("localhost", self._domain).replace("00000000000000", self._key)
				assert url.find("://") > 0, "line: " + url
				try:
					gid = group_names[group]
					g = self.groups[gid]
				except KeyError:
					gid = len(group_names)
					group_names[group] = gid
					g = self.groups[gid] = Group(gid, group.decode('utf-8').capitalize().encode('utf-8'), [])

				num += 1
				c = Channel(cid, gid, name, num, archive)
				self.channels[cid] = c
				g.channels.append(c)
				self.channels_data[cid] = {'tvg': cid, 'url': url}

		self.trace("Loaded {} channels".format(len(self.channels)))
