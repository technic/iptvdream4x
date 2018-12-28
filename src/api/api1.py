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

from twisted.internet.defer import maybeDeferred, succeed
from abstract_api import MODE_STREAM, MODE_VIDEOS, AbstractAPI, AbstractStream, CallbackCore
from datetime import datetime
from hashlib import md5
from ..utils import tdSec, APIException, EPG, Group, Channel
from urllib import urlencode
from json import loads as json_loads


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

	def authorize(self, params=None):
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

	def parseSettings(self, settings):
		pass


class TeleportStream(AbstractStream, TeleportAPI):
	MODE = MODE_STREAM
	HAS_PIN = True
	
	def __init__(self, username, password):
		super(TeleportStream, self).__init__(username, password)

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
						cid, gid, c['name'].encode('utf-8'), c['number'],
						bool(c['has_archive']), bool(c['protected']))
				self.channels[cid] = channel
				channels.append(channel)
			self.groups[gid] = Group(gid, g['user_title'].encode('utf-8'), channels)
		print(self.groups)

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
			for e in c['current'], c['next']:
				try:
					yield cid, self.epgEntry(e)
				except (KeyError, TypeError) as e:
					self.trace(e)
					continue

	def getCurrentEpg(self, cid):
		return self.getChannelsEpg([cid])
	
	def getDayEpg(self, cid, date):
		params = {"cid": cid, "from_uts": datetime(date.year, date.month, date.day).strftime('%s'), "hours": 24}
		data = self.getJsonData(self.site + "/get_epg?", params)
		return map(self.epgEntry, data['channels'][0]['epg'])
	
	def getSettings(self):
		return self.settings

	def pushSettings(self, sett):
		for s in sett:
			params = {'var': s[0]['id'], 'val': s[1]}
			response = self.getJsonData(self.site+"/set?", params, "Push setting [%s] new value." % s[0]['id'])
			s[0]['value'] = s[1]
	
	def getFavourites(self):
		response = self.getJsonData(self.site + "/get_favorites_tv?", {})
		if response['favorites']:
			return map(int, response['favorites'].split(','))
		else:
			return []
	
	def uploadFavourites(self, current, cid, added):
		self.getJsonData(self.site + "/set_favorites_tv?", {'val': ','.join(map(str, self.favourites))})


### TODO:

NUMS_ON_PAGE = 18


class OzoVideos(CallbackCore):
	MODE = MODE_VIDEOS
	iTitle = None
	NUMBER_PASS = False
	HAS_PIN = True
	SERVICES = []
	USE_SEEK = True
	languages = ["ru_RU", "en_EN"]
	
	def __init__(self, username, password):
		self.NAME = self.iName
		self.VERSION = VERSION
		CallbackCore.__init__(self, username, password)
	
	### Interface for CallbackCore
	
	def makeRequest(self, sid, params):
		params['sid'] = sid
		cmd = params['cmd']
		return "%s/%s?%s" % (self.site, cmd, urlencode(params))
	
	def retProcess(self, reply):
		try:
			data = json_loads(reply)
		except Exception as e:
			raise APIException("json error: " + str(e))
		if 'error' in data:
			raise APIException(data['error']['message'].encode('utf-8'))
		else:
			return data
	
	def authRequest(self):
		md5pass = md5(md5(self.username).hexdigest() + md5(self.password).hexdigest()).hexdigest()
		return "%s/login?%s" % (self.site, urlencode({"login": self.username, "pass": md5pass}))
	
	def authProcess(self, data):
		return data['sid']
	
	### Private functions
	
	def fixMovie(self, entry):
		rename = [
			("name", "title"), ("desc", "description"), ("actors", "acters"),
			("poster", "pic"), ("genres", "genre")
		]
		for new, old in rename:
			entry[new] = entry[old]
			del entry[old]
		entry['rating'] = ""
		entry['added'] = ""
		return entry
	
	### IPtvDream API
	
	def loadvideos(self, genres, searchstr, sortkey, page):
		params = {'cmd': "get_list_movie", 'limit': NUMS_ON_PAGE, 'extended': 1, 'page': page + 1}
		if searchstr:
			params['word'] = searchstr
		if genres:
			params['genre'] = ",".join(genres)
		if sortkey != "id":
			params['sort'] = sortkey
			params['order'] = 1  # ascent
		
		def f(data):
			c = int(data['options']['count'])
			c = c / NUMS_ON_PAGE + (c % NUMS_ON_PAGE > 0)
			return (map(self.fixMovie, data['groups']), c)
		return self.get(params).addCallback(f)
	
	def loadvid(self, vid):
		def f(data):
			try:
				return (self.fixMovie(data['groups'][0]), [])
			except IndexError:
				raise APIException("video not found")
		d = self.get({'cmd': "get_list_movie", 'limit': NUMS_ON_PAGE, 'extended': 1, 'idlist': vid})
		return d.addCallback(f)
	
	def isseries(self, entry):
		return False
	
	def loadseries(self, entry):
		return succeed([])
	
	def videourl(self, entry, code=None):
		def f(data):
			return data['url'].encode('utf-8')
		params = {'cmd': "get_url_movie", 'cid': entry['id']}
		if code is not None:
			params['protect_code'] = code
		return self.get(params).addCallback(f)
	
	def loadgenres(self):
		def f(data):
			return [(g['id'], g['title']) for g in data['groups']]
		return self.get({'cmd': "get_genre_movie"}).addCallback(f)
	
	def sortkeys(self):
		return [("id", "Последние"), ("name", "По названию")]
