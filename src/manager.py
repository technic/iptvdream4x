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

from __future__ import print_function

# system imports
from json import load as json_load
import os

# enigma2 imports
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Components.config import config, configfile, ConfigSubsection, ConfigSubDict,\
	ConfigText, ConfigYesNo, ConfigSelection
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Input import Input
from Components.Sources.List import List
from Tools.Directories import resolveFilename, SCOPE_SYSETC, SCOPE_CURRENT_PLUGIN, SCOPE_SKIN
from Tools.Import import my_import
from Tools.LoadPixmap import LoadPixmap
from enigma import getDesktop, gMainDC, eSize
from skin import loadSkin

# plugin imports
from dist import NAME, VERSION
from provision import pluginConfig
from common import ConfigNumberText
from utils import trace, APIException, APILoginFailed
from loc import translate as _
from settings import IPtvDreamConfig, IPtvDreamApiConfig
from main import IPtvDreamStreamPlayer

PLAYERS = [('1', "enigma2 ts (1)"), ('4097', "gstreamer (4097)"), ('5002', "exteplayer3 (5002)")]
KEYMAPS = [('enigma', 'enigma'), ('neutrino', 'neutrino')]
pluginConfig.keymap_type = ConfigSelection(KEYMAPS)


class SkinManager(object):
	SKIN_FILE = 'iptvdream.xml'

	def __init__(self):
		self.skins = []
		skins_dir = resolveFilename(SCOPE_SKIN, '.')
		for p in os.listdir(skins_dir):
			if os.path.isfile(os.path.join(skins_dir, p, self.SKIN_FILE)):
				self.skins.append(p)

		default = 'IPtvDream'
		assert default in self.skins
		pluginConfig.skin = ConfigSelection(self.skins, default=default)

	def load(self):
		skin = pluginConfig.skin.value
		loadSkin(os.path.join(skin, self.SKIN_FILE))

	def current(self):
		return pluginConfig.skin.value

	def setSkin(self, skin):
		pluginConfig.skin.value = skin
		pluginConfig.skin.save()


skinManager = SkinManager()
skinManager.load()


def getPlugins():
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


def loadProviders():
	if NAME == 'all':
		fname = resolveFilename(SCOPE_SYSETC, 'iptvdream.json')
		try:
			with open(fname, 'r') as f:
				to_import = json_load(f)['imports']
		except Exception as e:
			trace("[IPtvDream] config error:", e)
			to_import = []


class PluginStarter(Screen):
	def __init__(self, session, name, task=None):
		trace("Starting provider", name)

		desktop = getDesktop(0)
		self.resolution = desktop.size().width(), desktop.size().height()
		if self.resolution[0] != 1280 and not self.compatibleSkin():
			gMainDC.getInstance().setResolution(1280, 720)
			desktop.resize(eSize(1280, 720))

		Screen.__init__(self, session)
		self.cfg = manager.getConfig(name)
		self.apiClass = manager.getApi(name)
		self.task = task
		self.db = None

		try:
			self.last_service = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		except AttributeError:
			self.last_service = self.session.nav.getCurrentlyPlayingServiceReference()
		self.onClose.append(self.restoreService)
		self.session.nav.stopService()

		self.onFirstExecBegin.append(self.start)

	def start(self):
		if self.apiClass.AUTH_TYPE and self.cfg.login.value == '':
			self.login()
		else:
			self.auth()

	def auth(self):
		self.db = self.apiClass(self.cfg.login.value, self.cfg.password.value)
		try:
			self.db.start()
			if self.task == 'provider_settings':
				self.task = None
				self.openProviderSettings()
			else:
				self.run()
			return
		except APILoginFailed as e:
			cb = lambda ret: self.login()
			message = _("Authorization error") + "\n" + str(e)
		except APIException as e:
			cb = lambda ret: self.exit()
			message = _("Start of %s failed") % self.db.NAME + "\n" + str(e)
		self.session.openWithCallback(cb, MessageBox, message, MessageBox.TYPE_ERROR)

	def login(self):
		def cb(changed=False):
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
			self.session.openWithCallback(lambda ret: self.exit(), MessageBox, str(e), MessageBox.TYPE_ERROR)
		else:
			self.session.openWithCallback(self.finished, IPtvDreamStreamPlayer, self.db)

	def finished(self, ret):
		if ret == 'settings':
			self.login()
		elif ret == 'provider_settings':
			self.openProviderSettings()
		elif ret == 'clear_login':
			self.clearLogin()
			self.exit()
		else:
			self.exit()

	def openProviderSettings(self):
		if self.db:
			self.session.openWithCallback(lambda ret=None: self.start(), IPtvDreamApiConfig, self.db)

	def clearLogin(self):
		self.cfg.login.value = ''
		self.cfg.password.value = ''
		manager.saveConfig()

	def exit(self):
		self.close()

	def compatibleSkin(self):
		SUPPORTED_SKINS = ['BlueMetalFHD']
		current = config.skin.primary_skin.value
		return any(current.find(s) > -1 for s in SUPPORTED_SKINS) or skinManager.current() != 'IPtvDream'

	def restoreService(self):
		self.session.nav.playService(self.last_service)
		desktop = getDesktop(0)
		w, h = self.resolution
		trace("restore resolution", w, h)
		if w != 1280 and not self.compatibleSkin():
			gMainDC.getInstance().setResolution(w, h)
			desktop.resize(eSize(w, h))


class TokenPluginStarter(PluginStarter):
	def start(self):
		self.db = self.apiClass(self.cfg.login.value, self.cfg.password.value)
		if self.cfg.password.value == '':
			self.askToken()
		else:
			self.auth()

	def auth(self):
		try:
			self.db.start()
			if self.task == 'provider_settings':
				self.task = None
				self.openProviderSettings()
			else:
				self.run()
			return
		except APILoginFailed as e:
			cb = lambda ret: self.askToken()
			message = _("We need to authenticate your device") + "\n" + str(e)
		except APIException as e:
			cb = lambda ret: self.exit()
			message = _("Start of %s failed") % self.db.NAME + "\n" + str(e)
		self.session.openWithCallback(cb, MessageBox, message, MessageBox.TYPE_ERROR)

	def askToken(self):
		""" Ask user for pin code and obtain a token"""
		self.session.openWithCallback(
			self._codeEntered, InputBox, title=_("Please go to %s and generate pin code") % self.apiClass.token_page,
			windowTitle=_("Input pin"), type=Input.NUMBER)

	def _codeEntered(self, code):
		if code is None:
			return self.exit()
		try:
			token = self.db.getToken(code)
			self._saveToken(token)
			return self.auth()
		except APILoginFailed as e:
			cb = lambda ret: self.askToken()
			message = _("Failed to authentificate your device") + "\n" + str(e)
		except APIException as e:
			cb = lambda ret: self.exit()
			message = _("Start of %s failed") % self.db.NAME + "\n" + str(e)
		self._saveToken(None)
		self.session.openWithCallback(cb, MessageBox, message, MessageBox.TYPE_ERROR)

	def _saveToken(self, token):
		if token is None:
			token = ''
		assert isinstance(token, str)
		self.cfg.password.value = token
		self.cfg.password.save()
		manager.saveConfig()


class Manager(object):
	def __init__(self):
		self.enabled = {}
		self.apiDict = {}
		self.config = config.IPtvDream = ConfigSubDict()
		self.onConfigChanged = []
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

			try:
				trace("Loading module", f)
				module = my_import('%s.%s' % (prefix, f))
				if not hasattr(module, api_provider):
					continue
				provider = getattr(module, api_provider)
				name = provider.NAME
				self.apiDict[name] = provider
				self.config[name] = ConfigSubsection()
				self.config[name].login = ConfigNumberText()
				self.config[name].password = ConfigNumberText()
				self.config[name].parental_code = ConfigNumberText()
				self.config[name].in_menu = ConfigYesNo(default=False)
				self.config[name].playerid = ConfigSelection(PLAYERS, default='4097')
				self.config[name].last_played = ConfigText()

			except Exception:
				trace("Exception")
				import traceback
				traceback.print_exc()
				continue

		trace("Config generated for", self.config.keys())

	def getList(self):
		return sorted(
			({'name': v.NAME, 'title': v.TITLE} for v in self.apiDict.values()),
			key=lambda item: item['name'].lower())

	def getApi(self, name):
		return self.apiDict[name]

	def getConfig(self, name):
		return self.config[name]

	def saveConfig(self):
		self.config.save()
		configfile.save()
		for f in self.onConfigChanged:
			f()


manager = Manager()


class IPtvDreamManager(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("IPtvDream %s. Providers list:") % VERSION)
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Setup"))
		self["key_yellow"] = Button(_("Options"))
		self["key_blue"] = Button(_("Menu"))
		self["actions"] = ActionMap(
				["OkCancelActions", "ColorActions"], {
					"cancel": self.cancel,
					"ok": self.ok,
					"green": self.setup,
					"yellow": self.providerSetup,
					"red": self.cancel,
					"blue": self.showMenu,
				}, -1)
		self.list = self["list"] = List()
		self.onFirstExecBegin.append(self.start)

	def start(self):
		self.list.setList(map(self.makeEntry, manager.getList()))

	def makeEntry(self, entry):
		prefix = resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/IPtvDream')
		pixmap = LoadPixmap(os.path.join(prefix, 'logo/%s.png' % entry['name']))
		return entry, pixmap, entry['name']

	def getSelected(self):
		sel = self.list.getCurrent()
		if sel is not None:
			return sel[0]
		else:
			return None

	def ok(self):
		entry = self.getSelected()
		if entry is not None:
			self.startPlugin(entry['name'])

	def setup(self):
		entry = self.getSelected()
		if entry is not None:
			self.session.open(IPtvDreamConfig, manager.getApi(entry['name']))

	def providerSetup(self):
		entry = self.getSelected()
		if entry is not None:
			self.startPlugin(entry['name'], 'provider_settings')

	def startPlugin(self, name, task=None):
		if manager.getApi(name).AUTH_TYPE == 'Token':
			self.session.open(TokenPluginStarter, name, task)
		else:
			self.session.open(PluginStarter, name, task)

	def cancel(self):
		self.close()

	def showMenu(self):
		
		def cb(entry=None):
			if entry is not None:
				func = entry[1]
				func()
		
		actions = [
			(_("Choose keymap"), self.selectKeymap),
			(_("Choose skin"), self.selectSkin),
		]
		self.session.openWithCallback(cb, ChoiceBox, _("Context menu"), actions)

	def selectKeymap(self):
		def cb(selected):
			if selected is not None:
				self.applyKeymap(selected[0])
		self.session.openWithCallback(cb, ChoiceBox, title=_("Select keymap style"), list=KEYMAPS)

	def applyKeymap(self, style):
		plugin_path = resolveFilename(SCOPE_CURRENT_PLUGIN, 'Extensions/IPtvDream')
		link = os.path.join(plugin_path, 'keymap.xml')
		try:
			os.remove(link)
		except (OSError, IOError) as e:
			trace(e)
		try:
			os.symlink('keymap_%s.xml' % style, link)
		except OSError as e:
			trace(e)
			import errno
			if e.errno == errno.EPROTO:  # ignore virtual machine related error
				import shutil
				shutil.copy(os.path.join(plugin_path, 'keymap_%s.xml' % style), link)
			else:
				raise e

		pluginConfig.keymap_type.value = style
		pluginConfig.keymap_type.save()
		configfile.save()

		self.session.openWithCallback(
				self.restart, MessageBox, _("Restart enigma2 to apply keymap changes?"), MessageBox.TYPE_YESNO)

	def selectSkin(self):
		def cb(selected):
			if selected is not None:
				skinManager.setSkin(selected[0])
				self.session.openWithCallback(
					self.restart, MessageBox, _("Restart enigma2 to apply keymap changes?"), MessageBox.TYPE_YESNO)

		self.session.openWithCallback(cb, ChoiceBox, title=_("Select skin"), list=[(s, s) for s in skinManager.skins])

	def restart(self, ret):
		if ret:
			from Screens.Standby import TryQuitMainloop
			self.session.open(TryQuitMainloop, retvalue=3)


class Runner(object):
	def __init__(self):
		self._running = False

	def runPlugin(self, session, name):
		if not self._running:
			self._running = True
			session.openWithCallback(self.closed, PluginStarter, name)
		else:
			self.showWarning(session)

	def runManager(self, session):
		if not self._running:
			self._running = True
			session.openWithCallback(self.closed, IPtvDreamManager)
		else:
			self.showWarning(session)

	def closed(self, *args):
		self._running = False

	def showWarning(self, session):
		assert self._running
		session.open(MessageBox, _("IPtvDream plugin is already running!"), MessageBox.TYPE_ERROR)


runner = Runner()
