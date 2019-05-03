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

from twisted.trial.unittest import TestCase
from src.utils import Group, Channel, EPG
from src.api.abstract_api import AbstractStream
from typing import Type
import json
from datetime import datetime


class TestOTTProvider(TestCase):
    ProviderClass = None  # type: Type[AbstractStream]

    def setUp(self):
        import os
        with open(os.path.join(os.path.dirname(__file__), 'secret.json')) as f:
            secret = json.load(f)[self.ProviderClass.NAME]
        self._db = self.ProviderClass(secret['user'], secret['pass'])  # type: AbstractStream
        self._db.start()

    def test_setChannelsList(self):
        self._db.setChannelsList()
        for g in self._db.selectGroups():
            self.assertIsInstance(g, Group)
        for c in self._db.selectAll():
            self.assertIsInstance(c, Channel)
        print(self._db.selectAll())

    def test_getStreamUrl(self):
        self._db.setChannelsList()
        for c in self._db.selectAll():
            if not c.is_protected:
                url = self._db.getStreamUrl(c.cid, pin=None)
                self.assertIsInstance(url, str)
                break

    def test_getChannelsEpg(self):
        self._db.setChannelsList()
        for entry in self._db.getChannelsEpg(self._db.channels.keys()):
            cid, programs = entry
            self.assertIsInstance(cid, int)
            self.assertIsInstance(programs, list)
            self.assertTrue(all(isinstance(p, EPG) for p in programs))

    def test_getDayEpg(self):
        self._db.setChannelsList()
        cid = self._db.channels.keys()[0]
        programs = list(self._db.getDayEpg(cid, datetime.now()))
        for entry in programs:
            self.assertIsInstance(entry, EPG)
            self.assertLessEqual(entry.begin, entry.end)
