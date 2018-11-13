# -*- coding: utf-8 -*-
#  enigma2 iptv player
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from __future__ import print_function

from datetime import datetime
from ..utils import Channel, Group, APIWrongPin, EPG
from abstract_api import AbstractStream


class OTTProvider(AbstractStream):
	NAME = "SovokTV"
	site = "http://api.sovok.tv/v2.3/json"

	def authorize(self):
		self.trace("Authorization of username = %s" % self.username)
		params = {"login": self.username, "pass": self.password}
		reply = self.getJsonData(self.site + '/login?', params, fromauth=True)

		self.parseAccount(reply['account'])
		self.trace("Packet expire: %s" % self.packet_expire)
		self.sid = True

	def parseAccount(self, account):
		for s in account['services']:
			expire = datetime.fromtimestamp(int(s['expire']))
			if self.packet_expire is None:
				self.packet_expire = expire
			else:
				self.packet_expire = min(expire, self.packet_expire)

	def setChannelsList(self):
		data = self.getJsonData(self.site + "/channel_list?", {})
		number = 0
		for g in data['groups']:
			gid = int(g['id'])
			channels = []
			for c in g['channels']:
				cid = int(c['id'])
				number += 1
				channel = Channel(
					cid, gid, c['name'].encode('utf-8'), number,
					bool(int(c['have_archive'])), bool(int(c['protected']))
				)
				self.channels[cid] = channel
				channels.append(channel)
			self.groups[gid] = Group(gid, g['name'].encode('utf-8'), channels)

	def getStreamUrl(self, cid, pin, time=None):
		params = {"cid": cid}
		if time:
			params["gmt"] = time.strftime("%s")
		if pin:
			params["protect_code"] = pin
		data = self.getJsonData(self.site + "/get_url?", params)
		url = data['url'].encode('utf-8').split(' ')[0].replace('http/ts://', 'http://')
		if url == "protected":
			raise APIWrongPin("")
		return url

	def getChannelsEpg(self, cids):
		data = self.getJsonData(self.site + "/epg_next2?", {"cids": ",".join(map(str, cids))})
		for e in data['epg']:
			yield int(e['chid']), EPG(
				int(e['start']), int(e['end']),
				e['progname'].encode('utf-8'), e['description'].encode('utf-8'))

	def getCurrentEpg(self, cid):
		data = self.getJsonData(self.site + "/epg_next2?", {"cid": cid})
		epg = data['epg']
		for i, e in enumerate(epg[:-1]):
			yield EPG(
				int(epg[i]['ts']), int(epg[i+1]['ts']),
				e['progname'].encode('utf-8'), e['description'].encode('utf-8'))

	def getDayEpg(self, cid, date):
		data = self.getJsonData(self.site + "/epg?", {'cid': cid, 'day': date.strftime("%d%m%y")})
		for e in data['epg']:
			yield EPG(
				int(e['ut_start']), int(e['ut_end']),
				e['progname'].encode('utf-8'), e['description'].encode('utf-8'))
