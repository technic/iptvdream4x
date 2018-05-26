# -*- coding: utf-8 -*-
# enigma2 IPtvDream player framework
#
#  Copyright (c) 2018 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import print_function

# enigma2 imports
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Tools.BoundFunction import boundFunction

# plugin imports
from dist import NAME, TITLE
from loc import translate as _


def checkUpdate(session, callback):
	try:
		from updater import UpdaterScreen
	except ImportError as e:
		print("[IPtvDream] critical error!")
		import traceback
		traceback.print_exc()
		return session.open(MessageBox, _("IPtvDream critical error") + "\n" + str(e), MessageBox.TYPE_ERROR)

	def reboot(ret):
		session.open(TryQuitMainloop, retvalue=3)

	def run(updated):
		if updated:
			print("[IPtvDream] restart after update")
			return session.openWithCallback(
					reboot, MessageBox, _("Restarting enigma2 after IPtvDream update..."),
					MessageBox.TYPE_INFO, timeout=3)
		else:
			callback()

	session.openWithCallback(run, UpdaterScreen)


def pluginRun(name, session, **kwargs):
	def run():
		from main import pluginOpen
		pluginOpen(name, session)
	checkUpdate(session, run)


def managerRun(session, **kwargs):
	def run():
		from manager import IPtvDreamManager
		session.open(IPtvDreamManager)
	checkUpdate(session, run)


def managerMenu(menuid):
	if menuid == "mainmenu":
		return [(NAME, managerRun, "media_player", -4)]
	else:
		return []


def menuOpen(name, menuid):
	if menuid == "mainmenu":
		return [(NAME, managerRun, "media_player", -4)]
	else:
		return []


def Plugins(path, **kwargs):
	try:
		from manager import getPlugins
		plugins = getPlugins()
	except Exception as e:
		print("[IPtvDream] error loading plugins:", e)
		plugins = []

	if NAME == 'all':
		plugins += [
			PluginDescriptor(
				name="IPtvDream", description=_("list all iptv providers"),
				where=PluginDescriptor.WHERE_MENU, fnc=managerMenu, icon="IPtvDream.png"),
			PluginDescriptor(
				name="IPtvDream", description=_("list all iptv providers"),
				where=PluginDescriptor.WHERE_PLUGINMENU, fnc=managerRun, icon="IPtvDream.png")
		]
	elif not plugins:
		plugins += [
			PluginDescriptor(
				name=TITLE, description="",
				where=PluginDescriptor.WHERE_PLUGINMENU, fnc=boundFunction(pluginRun, NAME)),
			PluginDescriptor(
				name=NAME, description="",
				where=PluginDescriptor.WHERE_MENU, fnc=boundFunction(menuOpen, NAME)),
		]

	return plugins
