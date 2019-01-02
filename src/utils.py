# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#  Copyright (c) 2013 Alex Revetchi <alex.revetchi@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import print_function

from functools import wraps
from datetime import datetime, timedelta
import time
import re
import htmlentitydefs
from os import path as os_path


def trace(*args):
	print("[IPtvDream]", " ".join(map(str, args)))


def timeit(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		t = time.time()
		result = f(*args, **kwargs)
		d = time.time() - t
		trace("timeit", f, d)
		return result
	return wrapper


def getHwAddr(ifname):
	try:
		import fcntl
		import socket
		import struct
	except ImportError:
		return '00:00:00:00:00:00'
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
	except IOError:
		return '00:00:00:00:00:00'
	return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]


global Timezone
Timezone = -time.timezone / 3600
trace("timezone is GMT", Timezone)


def tdSec(td):
	return td.days * 86400 + td.seconds


def tdmSec(td):
	# Add +1. Timer should wait for next event until event happened exactly.
	# Otherwise inaccuracy in round may lead to mistake.
	return int(tdSec(td) * 1000)+1


def secTd(sec):
	return timedelta(sec / 86400, sec % 86400)


def tupleTd(tup):
	return secTd(tup[0]*60*60 + tup[1]*60)


trace("resetting time delta !!!")
time_delta = secTd(0)


def setSyncTime(t):
	global time_delta
	time_delta = t - datetime.now()
	trace("set time delta to", tdSec(time_delta))


def syncTime():
	return datetime.now() + time_delta


def toTimestamp(t):
	return int(time.mktime(t.timetuple()))


def toDate(t):
	return t.year, t.month, t.day


class EPG(object):
	__slots__ = ('begin', 'end', 'name', 'description')

	def __init__(self, begin, end, name, description=""):
		"""
		:param int begin: Program start time in unix timestamp
		:param int end: Program end time in unix timestamp
		:param str name: Program title, single line
		:param str description: detailed description, can be multi lined
		"""
		self.begin = datetime.fromtimestamp(begin)
		self.end = datetime.fromtimestamp(end)
		self.name = name
		self.description = description

	def duration(self):
		return tdSec(self.end - self.begin)

	def timePass(self, t):
		return tdSec(t - self.begin)

	def timeLeft(self, t):
		return tdSec(self.end - t)

	def timeLeftMilliseconds(self, t):
		return tdmSec(self.end - t)

	def percent(self, t, size):
		return size * self.timePass(t) / self.duration()

	def progress(self, t):
		return float(self.timePass(t)) / float(self.duration())

	def __getitem__(self, key):
		# print("DEPRECATED")
		return self.__dict__[key]

	def __setitem__(self, key, value):
		# print("DEPRECATED")
		self.__dict__[key] = value

	def __repr__(self):
		return self.begin.strftime("%H:%M") + "-" + self.end.strftime("%H:%M") + "|" + self.name


class ConfEntry(object):
	def __init__(self, name, title):
		pass


class ConfInteger:
	def __init__(self, name, title, value, limits):
		pass


class ConfString:
	def __init__(self, name, title, value):
		pass


class ConfSelection:
	def __init__(self, name, title, value, values):
		pass


class EPGDB(object):
	def __init__(self):
		self.l = []
		self.days_start = {}
		self.last = 0

	# bisect copies from python library
	
	def bisect(self, x, lo=0, hi=None):
		if lo < 0:
			raise ValueError('lo must be non-negative')
		if hi is None:
			hi = len(self.l)
		while lo < hi:
			mid = (lo+hi)/2
			if x < self.l[mid][0]:
				hi = mid
			else:
				lo = mid+1
		return lo
	
	def bisect_left(self, x, lo=0, hi=None):
		if lo < 0:
			raise ValueError('lo must be non-negative')
		if hi is None:
			hi = len(self.l)
		while lo < hi:
			mid = (lo+hi)//2
			if self.l[mid][0] < x:
				lo = mid+1
			else:
				hi = mid
		return lo
	
	def findEpg(self, time):
		if time is None:
			time = syncTime()
			update = True
			e = self.atTime(time, self.last, update)
			if e is not None:
				return e
			e = self.atTime(time, self.last+1, update)
			if e is not None:
				return e
		else:
			update = False
		t = toTimestamp(time)
		i = self.bisect(t)
		return self.atTime(time, i, update)
	
	def atTime(self, time, i, update):
		if i == 0 or i-1 >= len(self.l):
			return None
		epg = self.l[i-1][1]
		if epg.begin <= time < epg.end:
			if update:
				self.last = i
			return i-1
		else:
			return None
	
	def checkHint(self, i, t):
		return i > 0 and (i == len(self.l) or t < self.l[i][0]) and (i == 0 or self.l[i-1] <= t)

	### Public methods
	
	def epgCurrent(self, time=None):
		i = self.findEpg(time)
		if i is not None:
			return self.l[i][1]
		else:
			return None
	
	def epgNext(self, time=None):
		i = self.findEpg(time)
		if (i is not None) and (i+1 < len(self.l)):
			epg = self.l[i][1]
			epgn = self.l[i+1][1]
			if epg.end == epgn.begin:
				return epgn
			else:
				return None
		else:
			return None
	
	def epgDay(self, date):
		# for apis that can't get correct range in getDayEpg
		try:
			t1 = self.days_start[toDate(date)]
		except KeyError:
			return []
		t2 = t1 + timedelta(1)
		i1 = self.bisect_left(toTimestamp(t1))
		i2 = self.bisect_left(toTimestamp(t2), lo=i1)
		return [x[1] for x in self.l[i1:i2]]  # FIXME: extra copy
	
	def addEpg(self, epg, hint=-1):
		t = toTimestamp(epg.begin)
		if self.checkHint(hint, t):
			i = hint
		else:
			i = self.bisect(t)
		if i > 0:
			prev = self.l[i-1][1]
			if prev.begin == epg.begin or prev.end > epg.begin:
				print("[IPtvDream] EPG conflict!")
				self.l[i-1] = (t, epg)
				return i
		self.l.insert(i, (t, epg))
		if self.last >= i:
			self.last += 1
		return i+1
	
	def addEpgSorted(self, epg_list):
		hint = 0
		for e in epg_list:
			hint = self.addEpg(e, hint)
	
	def addEpgDay(self, date, epglist):
		self.days_start[toDate(date)] = date
		self.addEpgSorted(epglist)


class Group(object):
	__slots__ = ('gid', 'title', 'channels')

	def __init__(self, gid, title, channels):
		"""
		:param int gid: group id
		:param str title: title to display
		:param list[Channel] channels: list of channels
		"""
		self.gid = gid
		self.title = title
		self.channels = channels

	def __str__(self):
		return "Group(%d: %s)" % (self.gid, self.title)

	def __repr__(self):
		return self.__str__()

	def assertTypes(self):
		assert type(self.gid) == int
		assert type(self.title) == str
		assert type(self.channels) == list
		assert all(isinstance(c, Channel) for c in self.channels)


class Channel(EPGDB):
	def __init__(self, cid, gid, name, number, has_archive=False, is_protected=False):
		"""
		:param int cid: channel id
		:param int gid: group id, that channel belongs to
		:param str name: channel title
		:param int number: channel number
		:param has_archive:
		:param is_protected:
		"""
		EPGDB.__init__(self)
		self.cid = cid
		self.gid = gid
		self.name = name
		self.number = number
		self.has_archive = has_archive
		self.is_protected = is_protected
		self.lastUpdateFailed = None

	def __str__(self):
		return "Channel(%s: %s)" % (self.cid, self.name)

	def __repr__(self):
		return self.__str__()


def unescapeEntities(text):
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					return unichr(int(text[3:-1], 16))
				else:
					return unichr(int(text[2:-1]))
			except ValueError:
				pass
		else:
			# named entity
			try:
				text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text  # leave as is
	return re.sub("&#?\w+;", fixup, text)


class APIException(Exception):
	def __init__(self, msg):
		Exception.__init__(self, msg)


class APILoginFailed(APIException):
	def __init__(self, msg):
		APIException.__init__(self, msg)


class APIWrongPin(APIException):
	def __init__(self, msg):
		APIException.__init__(self, msg)
