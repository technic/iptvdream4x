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

from datetime import datetime, timedelta
from twisted.trial.unittest import TestCase
from twisted.internet import task, reactor
from twisted.internet.defer import DeferredList

from src.cache import LiveEpgWorker
from ..mock_api import MockApi as OTTProvider


class TestLiveEpgWorker(TestCase):
	def setUp(self):
		# Test with iptvdream epg-server
		self.db = OTTProvider("", "")
		self.db.start()
		self.db.setChannelsList()
		self._worker = LiveEpgWorker(self.db)

	def test_update(self):
		ch_ids = self.db.channels.keys()
		assert len(ch_ids) > 10

		def check():
			t = datetime.now()
			print("Check epg at", t)
			nt = datetime.now() + timedelta(1)
			for i in ch_ids:
				program = self._worker.get(i)
				if not program:
					continue
				nt = min(nt, program.end)
				self.assertTrue(program.isAt(t), "%s -- %s" % (program.begin, program.end))
			print("OK. Next update at", nt)
			return nt
		# Check now, in 10s after first expire and one minute later
		next_time = check()
		return DeferredList([
			task.deferLater(reactor, (next_time - datetime.now() + timedelta(seconds=10)).total_seconds(), check),
			task.deferLater(reactor, (next_time - datetime.now() + timedelta(seconds=70)).total_seconds(), check),
		]).addCallback(lambda _: self._worker.stop())


if __name__ == "__main__":
	from unittest import main
	main()
