# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2013 Alex Revetchi <revetski@gmail.com>
#  Copyright (c) 2015 Alex Maystrenko <alexeytech@gmail.com>
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from __future__ import print_function

from urllib import urlencode
from json import loads as json_loads
from datetime import datetime
from hashlib import md5
from twisted.internet.defer import maybeDeferred, succeed

from abstract_api import MODE_STREAM, MODE_VIDEOS, AbstractAPI, AbstractStream
from ..utils import tdSec, APIException, EPG, Group, Channel
try:
	from ..loc import translate as _
except ImportError:
	def _(text):
		return text


class TeleportAPI(AbstractAPI):
	PROVIDER = ""
	NUMBER_PASS = False
	site = ""

	def __init__(self, username, password):
		AbstractAPI.__init__(self, username, password)
		self.time_shift = 0
		self.time_zone = 0
		self.settings = {}
		
	def start(self):
		self.authorize()

	def authorize(self):
		self.trace("Username is", self.username)
		md5pass = md5(md5(self.username).hexdigest() + md5(self.password).hexdigest()).hexdigest()
		params = {"login": self.username, "pass": md5pass, "with_cfg": '', "with_acc": ''}
		response = self.getJsonData(self.site+"/login?", params, fromauth=True)
		
		if 'sid' in response:
			self.sid = response['sid'].encode("utf-8")
	
		if 'settings' in response:
			self.parseSettings(response['settings'])
		if 'account' in response:
			self.parseAccount(response['account'])

	def parseAccount(self, account):
		for s in account['subscriptions']:
			if 'end_date' in s:
				self.packet_expire = datetime.strptime(s['end_date'], "%Y-%m-%d")

	def parseSettings(self, data):
		from ..utils import ConfSelection, ConfInteger
		self.settings['media_server_id'] = ConfSelection(
			title=_("Media server"),
			value=str(data['media_server_id']),
			choices=[(str(s['id']), s['title'].encode('utf-8')) for s in data['media_servers']]
		)
		self.settings['time_shift'] = ConfInteger(_("Time shift"), data['time_shift'], (0, 24))


class TeleportStream(AbstractStream, TeleportAPI):
	MODE = MODE_STREAM
	HAS_PIN = True

	def __init__(self, username, password):
		super(TeleportStream, self).__init__(username, password)
		self.icons = {}
		self.icons_url = ""

	def epgEntry(self, e):
		return EPG(int(e['begin']), int(e['end']), e['title'].encode('utf-8'), e['info'].encode('utf-8'))

	def setChannelsList(self):
		params = {"with_epg": 0, "time_shift": self.time_shift}
		data = self.getJsonData(self.site+"/get_list_tv?", params)
		for g in data['groups']:
			gid = int(g['id'])
			channels = []
			for c in g['channels']:
				cid = c['id']
				channel = Channel(
						cid, c['name'].encode('utf-8'), c['number'],
						bool(c['has_archive']), bool(c['protected']))
				self.channels[cid] = channel
				channels.append(channel)
				self.icons[cid] = c['icon'].encode('utf-8')
			self.groups[gid] = Group(gid, g['user_title'].encode('utf-8'), channels)
		self.icons_url = data['icons']['default'].encode('utf-8')
		self.trace(self.groups)

	def getStreamUrl(self, cid, pin, time=None):
		params = {"cid": cid, "time_shift": self.time_shift}
		if pin:
			params["protect_code"] = pin
		if time:
			params["uts"] = time.strftime("%s")
		data = self.getJsonData(self.site+"/get_url_tv?", params, "stream url")
		return data["url"].encode("utf-8")
	
	def getChannelsEpg(self, cids):
		params = {"cid": ','.join(str(c) for c in cids), "time_shift": self.time_shift}
		data = self.getJsonData(self.site+"/get_epg_current?", params)
		for c in data['channels']:
			cid = c['id']
			programs = []
			for e in c['current'], c['next']:
				try:
					programs.append(self.epgEntry(e))
				except (KeyError, TypeError) as e:
					self.trace(e)
					continue
			yield (cid, programs)

	def getCurrentEpg(self, cid):
		return self.getChannelsEpg([cid])
	
	def getDayEpg(self, cid, date):
		params = {"cid": cid, "from_uts": datetime(date.year, date.month, date.day).strftime('%s'), "hours": 24}
		data = self.getJsonData(self.site + "/get_epg?", params)
		return map(self.epgEntry, data['channels'][0]['epg'])
	
	def getSettings(self):
		return self.settings

	def pushSettings(self, settings):
		params = {
			"var": ','.join(settings.keys()),
			"val": ','.join(map(str, settings.values()))
		}
		data = self.getJsonData(self.site + "/set?", params)
		self.parseSettings(data)

	def getFavourites(self):
		response = self.getJsonData(self.site + "/get_favorites_tv?", {})
		if response['favorites']:
			return map(int, response['favorites'].split(','))
		else:
			return []

	def uploadFavourites(self, current):
		self.getJsonData(self.site + "/set_favorites_tv?", {'val': ','.join(map(str, self.favourites))})

	def getPiconUrl(self, cid):
		return self.icons_url.replace("%ICON%", self.icons[cid])
