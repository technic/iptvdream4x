# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2015 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

""" Helper classes and functions for iptv streaming """

from __future__ import print_function

from Components.config import config, ConfigSelection

from ..loc import translate as _
from ..api.abstract_api import AbstractStream


class SortOrderSettings(object):
	def __init__(self):
		self.choices = {
			AbstractStream.Sort_N: ('number', _('by number')),
			AbstractStream.Sort_AZ: ('name', _('by name')),
		}
		self.c = config.plugins.IPtvDream.channel_order = ConfigSelection(self.choices.values())

	def toStr(self, value):
		return self.choices[value][0]

	def fromStr(self, s):
		return dict((v[0], k) for k, v in self.choices.items())[s]

	def getValue(self):
		return self.fromStr(self.c.value)

	def setValue(self, value):
		if isinstance(value, int):
			value = self.toStr(value)
		self.c.value = value
		self.c.save()
