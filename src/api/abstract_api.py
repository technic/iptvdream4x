# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  Copyright (c) 2013 Alex Revetchi   <alex.revetchi@gmail.com>
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from __future__ import print_function

import socket
import zlib
import cookielib
import urllib
import urllib2
from json import loads as json_loads
from os import path as os_path
try:
	from typing import Dict
except ImportError:
	pass

from xml.etree.cElementTree import fromstring
from ..utils import getHwAddr, syncTime, Group, Channel, APIException, APILoginFailed, EPG
from datetime import datetime
from urllib import urlencode
from twisted.internet.defer import Deferred, succeed
from twisted.web.client import getPage
from ..dist import VERSION

MODE_STREAM = 0
MODE_VIDEOS = 1


def renameDict(d, keys):
	for new, old in keys:
		d[new] = d.pop(old)


class AbstractAPI(object):
	MODE = MODE_STREAM
	PROVIDER = "free"
	NAME = "example"
	TITLE = None
	NEXT_API = None
	NUMBER_PASS = False
	HAS_PIN = False
	SERVICES = []
	USE_SEEK = True
	HAS_LOGIN = True

	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.sid = None
		self.packet_expire = None
		self.settings = []
	
		socket.setdefaulttimeout(10)
		self.uuid = getHwAddr('eth0')
		self.cookiejar = cookielib.CookieJar()
		self.urlopener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
		self.urlopener.addheaders = [
					('User-Agent', 'IPtvDream/%s %s' % (VERSION, self.NAME)),
					('Connection', 'Keep-Alive'),
					('Accept', 'application/json, text/javascript, */*'),
					('Accept-Encoding', 'gzip, deflate')]

	def start(self):
		"""Functions that runs on start, and needs exception handling"""
		pass

	def authorize(self):
		pass
		
	def readHttp(self, request):
		o = self.urlopener.open(request)
		enc = o.headers.get('Content-Encoding')
		if enc and 'gzip' in enc:
			reply = zlib.decompress(o.read(), 16+zlib.MAX_WBITS)
			return reply
		else:
			return o.read()

	def getData(self, url, params, name='', fromauth=None):
		reauthOnError = True
		if not self.sid and not fromauth:
			reauthOnError = False
			self.cookiejar.clear()
			self.authorize()
		elif fromauth:
			self.cookiejar.clear()
				
		try:
			request = url+urllib.urlencode(params)
			self.trace("Getting %s (%s)" % (name, request))
			reply = self.readHttp(request)
		except IOError as e:
			self.sid = None
			raise APIException(e)
		return reply

	def getJsonData(self, url, params, name='', fromauth=None):
		reauthOnError = True
		if not self.sid and not fromauth:
			reauthOnError = False
			self.cookiejar.clear()
			self.authorize()
		elif fromauth:
			self.cookiejar.clear()
		
		try:
			request = url+urllib.urlencode(params)
			self.trace("Getting %s" % name, url, request)
			reply = self.readHttp(request)
		except IOError as e:
			self.sid = None
			raise APIException(e)
		try:
			json = json_loads(reply)
		except Exception as e:
			self.sid = None
			raise APIException("Failed to parse json response: %s" % str(e))
		if 'error' in json:
			self.sid = None
			self.cookiejar.clear()
			if reauthOnError and not fromauth:
				return self.getJsonData(url, params, name)
			error = json['error']
			if str(error['code']) in ['ACC_WRONG', 'AСС_EMPTY']:
				raise APILoginFailed(str(error['code']) + ": " + error['message'].encode('utf-8'))
			else:
				raise APIException(str(error['code']) + ": " + error['message'].encode('utf-8'))
		self.trace("getJsonData ok")
		return json

	def _resolveConfigurationFile(self, file_name):
		try:
			from Tools.Directories import resolveFilename, SCOPE_SYSETC
			return resolveFilename(SCOPE_SYSETC, 'iptvdream/%s' % file_name)
		except ImportError:
			self.trace("error: cant locate configuration files")
			return "/tmp/%s" % file_name

	def trace(self, *args):
		"""Use for API debug"""
		print("[IPtvDream] %s: %s" % (self.NAME, " ".join(map(str, args))))


class AbstractStream(AbstractAPI):
	SERVICE = 1
	URL_DYNAMIC = True
	Sort_N = 0
	Sort_AZ = 1
	SORT = ('number', 'name')

	def __init__(self, username, password):
		super(AbstractStream, self).__init__(username, password)
		self.channels = {}  # type: Dict[int, Channel]
		self.groups = {}  # type: Dict[int, Group]
		self.favourites = []
		self.got_favourites = False
	
	def setChannelsList(self):
		pass

	def addFav(self, cid):
		if not self.favourites.count(cid):
			self.favourites.append(cid)
			self.uploadFavourites(self.favourites)

	def rmFav(self, cid):
		self.favourites.remove(cid)
		self.uploadFavourites(self.favourites)

	def setFavourites(self, favourites):
		self.favourites = favourites
		self.uploadFavourites(self.favourites)

	def loadChannelsEpg(self, cids):
		for cid, programs in self.getChannelsEpg(cids):
			try:
				self.channels[cid].addEpgSorted(programs)
			except KeyError:
				self.trace("unknown channel", cid)
	
	def loadCurrentEpg(self, cid):
		for e in self.getCurrentEpg(cid):
			self.channels[cid].addEpg(e)
	
	def loadDayEpg(self, cid, date):
		date = datetime(date.year, date.month, date.day)
		self.channels[cid].addEpgDay(date, list(self.getDayEpg(cid, date)))
	
	def getPiconName(self, cid):
		"""You can return reference to cid or to channel name, anything you want ;)"""
		return "%s:%s:" % (self.NAME, cid)
	
	# Return lists for GUI
	
	def selectGroups(self):
		return self.groups.values()
	
	def selectAll(self, sort_key=Sort_N):
		attr = self.SORT[sort_key]
		return sorted(self.channels.values(), key=lambda c: getattr(c, attr))
	
	def selectChannels(self, gid, sort_key=Sort_N):
		attr = self.SORT[sort_key]
		return sorted(self.groups[gid].channels, key=lambda c: getattr(c, attr))

	def selectFavourites(self):
		if not self.got_favourites:
			keys = set(self.channels.keys())
			favourites = self.getFavourites()
			self.favourites = [cid for cid in favourites if cid in keys]
			self.got_favourites = True
		return [self.channels[cid] for cid in self.favourites]
	
	def findNumber(self, number):
		for cid, ch in self.channels.iteritems():
			if ch.number == number:
				return cid
		return None
	
	def isLocked(self, cid):
		return self.channels[cid].is_protected

	# To be implemented in a derived class

	def setTimeShift(self, time_shift):
		return

	def getStreamUrl(self, cid, pin, time=None):
		"""
		:param int cid: channel id
		:param str|None pin: if channel is protected then is not None
		:param datetime|None time: If specified then get stream from archive
		:rtype: str
		"""
		return ""

	def getChannelsEpg(self, cids):
		"""
		:param list[int] cids: list of channel ids
		:rtype: list[(int, list[EPG])]
		"""
		return []

	def getCurrentEpg(self, cid):
		x = self.getDayEpg(1, datetime.now())
		print(x[0].begin)
		return []

	def getDayEpg(self, cid, date):
		"""
		:param int cid: channel id
		:param datetime date: day
		:rtype: list[EPG]
		"""
		return []

	def getFavourites(self):
		"""
		:rtype: list[int]
		"""
		return []

	def uploadFavourites(self, current):
		"""
		:param list[int] current: list of current favourites
		"""
		pass

	def getSettings(self):
		""" Return setting id to ConfEntry object dict """
		return {}

	def pushSettings(self, settings):
		"""
		Push settings to server for key to value dict
		:type settings: typing.Dict[str, str]
		"""
		pass


class OfflineFavourites(AbstractStream):
	def __init__(self, username, password):
		super(OfflineFavourites, self).__init__(username, password)
		self._favorites_file = self._resolveConfigurationFile('%s.txt' % self.NAME)

	def getFavourites(self):
		if not os_path.isfile(self._favorites_file):
			return []
		with open(self._favorites_file) as f:
			data = f.read().strip()
			fav = []
			for cid in map(int, data.split(',')):
				fav.append(cid)
			return fav

	def uploadFavourites(self, current):
		try:
			with open(self._favorites_file, 'w') as f:
				f.write(','.join(map(str, current)))
		except Exception as e:
			raise APIException(str(e))


class JsonSettings(AbstractAPI):
	def __init__(self, username, password):
		super(JsonSettings, self).__init__(username, password)
		self._settings_file = self._resolveConfigurationFile('%s.json' % self.NAME)

	def _loadSettings(self):
		from json import load as json_load
		if not os_path.isfile(self._settings_file):
			return {}
		with open(self._settings_file) as f:
			return json_load(f) or {}

	def _saveSettings(self, settings):
		from json import dump as json_dump
		try:
			with open(self._settings_file, 'w') as f:
				json_dump(settings, f)
		except Exception as e:
			raise APIException(str(e))


class CallbackCore(object):
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.sid = None
		self.requests = []
		self.authorizing = False
		self.agent = "iptvdream-plugin/%d.%d %s/%s" % (VERSION[0], VERSION[1], self.NAME, self.VERSION)
	
	# You may use this to print debug information
	def trace(self, *args):
		print("[IPtvDream] %s" % self.NAME, ' '.join(map(str, args)))
	
	# Public function to get data
	def get(self, params):
		return self._get(params, 0)
	
	# All these functions below are private.
	# You must not override or directly use them.
	def authorize(self):
		self.sid = None
		self.authorizing = True
		self.trace("Authorization of username = %s" % self.username)
		d = getPage(self.authRequest(), agent=self.agent)
		return d.addErrback(self.error).addCallback(self.retProcess).addCallback(self.authCb).addErrback(self.authErr)

	def authCb(self, json):
		self.authorizing = False
		self.trace("authCallback")
		self.sid = self.authProcess(json)
		for r in self.requests:
			r.callback(self.sid)
		self.requests = []
	
	def authErr(self, err):
		self.trace("authErrback")
		self.authorizing = False
		for r in self.requests:
			r.errback(err)
		self.requests = []
		raise err
	
	def getSid(self):
		if self.sid:
			return succeed(self.sid)
		else:
			if not self.authorizing:
				self.authorize()
			d = Deferred()
			self.requests.append(d)
			return d
	
	def _get(self, params, depth):
		return self.getSid().addCallback(self.doGet, params, depth)
	
	def doGet(self, sid, params, depth):
		self.trace("doGet")
		d = getPage(self.makeRequest(sid, params), agent=self.agent).addErrback(self.error)
		return d.addCallback(self.retProcess).addErrback(self.getErr, params, depth)

	def getErr(self, err, params, depth):
		err.trap(APIException)
		self.sid = None
		if depth < 1:
			self.trace("retry", depth + 1)
			return self._get(params, depth + 1)
		else:
			raise err
	
	def error(self, err):
		self.trace("getPage error:", err.getErrorMessage())
		raise APIException(self.NAME + "error: " + err.getErrorMessage())
