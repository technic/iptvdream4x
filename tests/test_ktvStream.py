from __future__ import print_function
from unittest import TestCase
from src.api.kartina import OTTProvider
from src.utils import Group, Channel, EPG
import json
from datetime import datetime


class TestKtvStream(TestCase):
    def setUp(self):
        import os
        print('DIR', os.getcwd())
        with open('../secret.json') as f:
            secret = json.load(f)['kartina']
        self._db = OTTProvider(secret['user'], secret['pass'])

    def test_setChannelsList(self):
        self._db.setChannelsList()
        for g in self._db.selectGroups():
            self.assertIsInstance(g, Group)
        for c in self._db.selectAll():
            self.assertIsInstance(c, Channel)

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
            cid, program = entry
            self.assertIsInstance(cid, int)
            self.assertIsInstance(program, EPG)

    def test_getDayEpg(self):
        self._db.setChannelsList()
        cid = self._db.channels.keys()[0]
        programs = list(self._db.getDayEpg(cid, datetime.now()))
        for entry in programs:
            self.assertIsInstance(entry, EPG)
            self.assertLessEqual(entry.begin, entry.end)
