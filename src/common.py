# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from Components.config import ConfigText
from Components.Sources.StaticText import StaticText
from skin import colorNames, SkinError

from functools import wraps

# provide it from common file
from updater import fatalError


def safecb(callback):
	@wraps(callback)
	def wrapper(obj, data):
		try:
			obj._wantCallbacks
		except AttributeError:
			print("IGNORE late callback")
			return None
		return callback(obj, data)
	return wrapper


class ConfigNumberText(ConfigText):
	def __init__(self, default=''):
		ConfigText.__init__(self, default, fixed_size=False)
		self.setUseableChars('0123456789')

	# override, do not show input dialog
	def onSelect(self, session):
		self.allmarked = (self.value != "")


def parseColor(s):  # FIXME: copy-paste form skin source
	if s[0] != '#':
		try:
			return colorNames[s]
		except:
			raise SkinError("color '%s' must be #aarrggbb or valid named color" % (s))
	return int(s[1:], 0x10)


class StaticTextService(StaticText):
	service = property(StaticText.getText, StaticText.setText)
