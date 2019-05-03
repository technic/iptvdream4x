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

from twisted.trial import unittest
from twisted.internet.defer import Deferred
from twisted.internet import task
from tests.timer import eTimerTwisted, reactor

class TestTimer(unittest.TestCase):
	def test_repeating(self):
		self.t = eTimerTwisted()
		d = Deferred()
		self.n = 0

		def cb():
			self.n += 1
			print("fired", self.n)
			if self.n >= 3:
				self.t.stop()
				d.callback(self.n)

		self.t.callback.append(cb)
		self.t.start(50)

		d.addCallback(self.assertEqual, 3)
		return d

	def test_single(self):
		self.t = eTimerTwisted()
		d = Deferred()

		def cb():
			d.callback("boom")
			self.t.stop()
		self.t.callback.append(cb)
		self.t.start(100, True)
		d.addCallback(self.assertEqual, "boom")
		return d

	def test_stopSingle(self):
		self.t = eTimerTwisted()
		self.t.start(50, True)
		def f():
			self.t.stop()
		return task.deferLater(reactor, 0.03, f)

	def test_stopRepeating(self):
		self.t = eTimerTwisted()
		self.t.start(20)
		def f():
			self.t.stop()
		return task.deferLater(reactor, 0.5, f)
