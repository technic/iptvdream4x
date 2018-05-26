# -*- coding: utf-8 -*-
#
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2018 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.


# enigma2 imports
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigSubsection, ConfigSubDict, ConfigText, ConfigYesNo, ConfigSelection
from Components.ActionMap import ActionMap
from Components.Button import Button
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_SKIN, SCOPE_SYSETC, SCOPE_CURRENT_PLUGIN
from Tools.Import import my_import
from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT
from Components.MenuList import MenuList
from Screens.ChoiceBox import ChoiceBox
from Plugins.Plugin import PluginDescriptor
from common import ConfigNumberText
from skin import loadSkin
from enigma import gFont

# system imports
from json import load as json_load
import os

# plugin imports
from dist import NAME
from utils import trace, APIException, APILoginFailed
from loc import translate as _
from settings import IPtvDreamConfig
from main import IPtvDreamStreamPlayer

PLAYERS = [('1', "enigma2 ts (1)"), ('4097', "gstreamer (4097)"), ('5002', "exteplayer3 (5002)")]
loadSkin("IPtvDream/iptvdream.xml")


def getPlugins():
	return []
	plugins = []
	if NAME == 'all':
		f_name = resolveFilename(SCOPE_SYSETC, 'iptvdream.json')
		try:
			with open(f_name, 'r') as f:
				to_import = json_load(f)['imports']
		except Exception as e:
			trace("[IPtvDream] config error:", e)
			to_import = []
		for n in to_import:
			mod = __import__('api.%s' % n)
			getProviders = getattr(mod, 'getProviders')
	return plugins


def pluginOpen(session, name):
	trace("Open provider", name)
	session.open(PluginStarter, name)


def loadProviders():
	from json import load as json_load
	from Tools.Directories import resolveFilename, SCOPE_SYSETC

	if NAME == 'all':
		fname = resolveFilename(SCOPE_SYSETC, 'iptvdream.json')
		try:
			with open(fname, 'r') as f:
				to_import = json_load(f)['imports']
		except Exception as e:
			trace("[IPtvDream] config error:", e)
			to_import = []


class PluginStarter(Screen):
	def __init__(self, session, name):
		Screen.__init__(self, session)
		self.cfg = manager.getConfig(name)
		self.apiClass = manager.getApi(name)
		self.db = None

		try:
			self.last_service = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		except AttributeError:
			self.last_service = self.session.nav.getCurrentlyPlayingServiceReference()
		self.onClose.append(self.restoreService)
		self.session.nav.stopService()

		self.onFirstExecBegin.append(self.start)

	def start(self):
		if self.apiClass.HAS_LOGIN and self.cfg.login.value == '':
			self.login()
		else:
			self.auth()

	def auth(self):
		self.db = self.apiClass(self.cfg.login.value, self.cfg.password.value)
		try:
			self.db.start()
			return self.run()
		except APILoginFailed as e:
			cb = lambda ret: self.login()
			message = _("Authorization error") + "\n" + str(e)
		except APIException as e:
			cb = lambda ret: self.exit()
			message = _("Start of %s failed") % self.db.NAME + "\n" + str(e)
		self.session.openWithCallback(cb, MessageBox, message, MessageBox.TYPE_ERROR)

	def login(self):
		def cb(changed):
			if changed:
				self.auth()
			else:
				self.exit()
		self.session.openWithCallback(cb, IPtvDreamConfig, self.apiClass)

	def run(self):
		try:
			self.db.setChannelsList()
		except APIException as e:
			trace(e)
			return self.session.openWithCallback(lambda ret: self.exit(), MessageBox, str(e), MessageBox.TYPE_ERROR)
		self.session.openWithCallback(lambda ret: self.exit(), IPtvDreamStreamPlayer, self.db)

	def exit(self):
		self.close()

	def restoreService(self):
		self.session.nav.playService(self.last_service)


class Manager(object):
	def __init__(self):
		self.enabled = {}
		self.apiDict = {}
		self.config = config.IPtvDream = ConfigSubDict()
		self.initList()

	def initList(self):
		api_provider = 'OTTProvider'
		prefix = 'Plugins.Extensions.IPtvDream.api'
		api_path = resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/IPtvDream/api')

		self.apiDict = {}
		seen = set()

		for f in os.listdir(api_path):
			if f.endswith('.py'):
				f = f[:-3]
			elif f.endswith('.pyc') or f.endswith('.pyo'):
				f = f[:-4]
			else:
				continue
			if f in seen:
				continue
			seen.add(f)

			# FIXME: temporary hack
			# if f.find('edem') < 0:
			# 	continue

			try:
				trace("Loading module", f)
				module = my_import('%s.%s' % (prefix, f))
				print(module)
				if not hasattr(module, api_provider):
					continue
				provider = getattr(module, api_provider)
				name = provider.NAME
				self.apiDict[name] = provider
				self.config[name] = ConfigSubsection()
				self.config[name].login = ConfigNumberText()
				self.config[name].password = ConfigNumberText()
				self.config[name].in_menu = ConfigYesNo(default=False)
				self.config[name].playerid = ConfigSelection(PLAYERS, default='4097')
				self.config[name].last_played = ConfigText()

			except Exception:
				print("[IPtvDream] Exception")
				import traceback
				traceback.print_exc()
				continue

		trace("Config generated for", self.config.keys())

	def getList(self):
		return [{'name': v.NAME, 'title': v.TITLE} for v in self.apiDict.values()]

	def getApi(self, name):
		return self.apiDict[name]

	def getConfig(self, name):
		trace(id(config.IPtvDream), id(self.config), id(self.config[name]))
		return self.config[name]


manager = Manager()


class IPtvDreamManager(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Setup"))
		self["actions"] = ActionMap(
				["OkCancelActions", "ColorActions"], {
					"cancel": self.cancel,
					"ok": self.ok,
					"green": self.setup,
					"red": self.cancel,
				}, -1)
		self.listbox = self["list"] = MenuList([], content=eListboxPythonMultiContent)
		self.listbox.l.setFont(0, gFont("Regular", 22))
		self.onFirstExecBegin.append(self.start)

	def start(self):
		self.listbox.setList(map(self.makeEntry, manager.getList()))
	
	def makeEntry(self, entry):
		return [
			entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 1, 2, 585, 24,
				0, RT_HALIGN_LEFT, entry['name']),
		]

	def getSelected(self):
		sel = self.listbox.getCurrent()
		if sel is not None:
			return sel[0]
		else:
			return None

	def ok(self):
		entry = self.getSelected()
		if entry is not None:
			pluginOpen(self.session, entry['name'])

	def setup(self):
		entry = self.getSelected()
		if entry is not None:
			self.session.open(IPtvDreamConfig, manager.getApi(entry['name']))

	def cancel(self):
		self.close()
