# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2015 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import print_function
from .utils import trace


class StandbyNotifier(object):
	"""
	Put your functions to onStandbyChanged
	"""
	def __init__(self):
		from Components.config import config
		config.misc.standbyCounter.addNotifier(self.enterStandby, initial_call=False)
		self.onStandbyChanged = []

	def enterStandby(self, configElement):
		trace("enter standby! have %d callbacks" % len(self.onStandbyChanged))
		for f in self.onStandbyChanged:
			f(sleep=True)
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.exitStandby)

	def exitStandby(self):
		trace("exit standby! have %d callbacks" % len(self.onStandbyChanged))
		for f in self.onStandbyChanged:
			f(sleep=False)


standbyNotifier = StandbyNotifier()
