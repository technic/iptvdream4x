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

from twisted.internet import task
from twisted.internet.posixbase import PosixReactorBase

def getReactor():
	# type: () -> PosixReactorBase
	"""Returns type annotated twisted reactor"""
	from twisted.internet import reactor as _reactor
	return _reactor

reactor = getReactor()


class eTimerTwisted(object):
	def __init__(self):
		self.callback = []
		self._active = False
		self._delayed = None
		self._loop = None

	def _fire(self):
		for func in self.callback:
			func()

	def start(self, ms, singleShot=False):
		"""
		:param int ms: timer duration in milliseconds
		:param bool singleShot: whether timer should be repeating
		"""
		self.stop()
		seconds = float(ms) / 1000
		if singleShot:
			self._delayed = reactor.callLater(seconds, self._fire)
			print("Timer: delayed started")
		else:
			self._loop = task.LoopingCall(self._fire)
			self._loop.start(seconds, now=False)
			print("Timer: loopping started")

	def startLongTimer(self, seconds):
		"""
		:param int seconds:
		"""
		self.start(seconds * 1000, True)

	def stop(self):
		if self._delayed:
			print("Timer: stop delayed call")
			if self._delayed.active():
				self._delayed.cancel()
			self._delayed = None
		if self._loop:
			print("Timer: stop loopping call")
			self._loop.stop()
			self._loop = None
