# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2018 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import print_function

# enigma2 imports
from Screens.Screen import Screen
from Components.config import getConfigListEntry, ConfigSearchText
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Sources.Boolean import Boolean

# plugin imports
from utils import trace
from virtualkb import VirtualKeyBoard
from common import ConfigNumberText
from loc import translate as _


class IPtvDreamConfig(ConfigListScreen, Screen):
	def __init__(self, session, apiClass):
		Screen.__init__(self, session)
		trace("Config open")
		name = apiClass.NAME

		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel
		}, -2)

		self["actions_kbd"] = ActionMap(["ColorActions"], {
			"blue": self.openKeyboard
		}, -2)

		self["actions_kbd"].setEnabled(False)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Keyboard"))
		self["Keyboard"] = Boolean(False)

		from manager import manager
		cfg = manager.getConfig(name)
		trace(id(cfg))

		cfg_list = []
		if apiClass.HAS_LOGIN:
			cfg_list = [
				getConfigListEntry(_("Login"), cfg.login),
				getConfigListEntry(_("Password"), cfg.password),
			]
		cfg_list += [
			getConfigListEntry(_("Show in main menu"), cfg.in_menu),
			getConfigListEntry(_("Player ID"), cfg.playerid)
		]
		ConfigListScreen.__init__(self, cfg_list, session)
		self.setTitle(_("Configuration of %s") % name)
		self["config"].onSelectionChanged.append(self.showHideKb)

	def remoteConfig(self):
		return

	def showHideKb(self):
		c = self["config"].getCurrent()
		# Add to support ConfigSearchText
		if c and (isinstance(c[1], ConfigSearchText) or isinstance(c[1], ConfigNumberText)):
			self["actions_kbd"].setEnabled(True)
			self["Keyboard"].boolean = True
			self["key_blue"].show()
		else:
			self["actions_kbd"].setEnabled(False)
			self["Keyboard"].boolean = False
			self["key_blue"].hide()

	def openKeyboard(self):
		c = self["config"].getCurrent()
		self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, c[0], c[1].getValue(), ['en_EN'])

	def keySave(self):
		trace("Save config")
		self.saveAll()
		from manager import manager
		manager.saveConfig()
		self.close(True)


class IPtvDreamLogin(Screen):
	# TODO
	pass
