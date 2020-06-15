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

# system imports
from io import StringIO, BytesIO
import urllib
from json import loads as json_loads, dumps as json_dumps
from twisted.web.client import downloadPage, FileBodyProducer, readBody
from twisted.web.client import Agent
from twisted.internet import reactor
from twisted.internet.defer import Deferred

# enigma2 imports
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import getConfigListEntry, ConfigSearchText, ConfigInteger, ConfigSelection, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Sources.Boolean import Boolean

# plugin imports
from utils import trace, ConfInteger, ConfSelection, ConfString, ConfBool, APIException
from virtualkb import VirtualKeyBoard
from common import ConfigNumberText
from api.abstract_api import AbstractStream
from loc import translate as _
from updater import getPage
from common import safecb, fatalError


class SettingsRepository(object):
	def __init__(self):
		pass

	def get(self):
		raise NotImplementedError()

	def set(self, values):
		raise NotImplementedError()


class EnigmaSettingsRepository(SettingsRepository):
	def __init__(self, name):
		super(EnigmaSettingsRepository, self).__init__()

	def get(self):
		pass

	def set(self, values):
		pass


def convertEnigmaConfigEntry(title, cfg):
	if isinstance(cfg, ConfigInteger):
		return ConfInteger(title, cfg.value, cfg.limits[0])
	elif isinstance(cfg, ConfigNumberText):
		return ConfString(title, cfg.value)
	elif isinstance(cfg, ConfigSelection):
		return ConfSelection(title, cfg.value, cfg.choices.choices)
	elif isinstance(cfg, ConfigYesNo):
		return ConfBool(title, cfg.value)
	else:
		trace("Unsupported config", (title, cfg))


def getRequest(url):
	agent = Agent(reactor)
	d = agent.request(b'GET', url)
	return d.addCallback(readBody)


def postRequest(url, body):
	agent = Agent(reactor)
	d = agent.request(b'POST', url, headers=None, bodyProducer=FileBodyProducer(BytesIO(body)))
	
	def cb(response):
		trace(response)
		return readBody(response)
	return d.addCallback(cb)


class WebConfig(object):
	site = 'http://5ed6e80b94e7.ngrok.io/stb'

	def __init__(self, settings):
		self.settings = settings
		self.session = None
		self.revision = 0
		self.poll_defer = None
		self._run_defer = None

	def start(self):
		def cb(data):
			trace("recieved:", data)
			data = json_loads(data)
			self.session = data['secret']
			return data['key']

		items = []
		for k, v in self.settings.items():
			item = v.to_json()
			item['name'] = k
			items.append(item)
		print(json_dumps(items))
		return postRequest(self.site + '/new-session', json_dumps(items)).addCallback(cb)

	def _run(self):
		def eb(err):
			trace("Poll error:", err)
			self._run()

		def cb(data):
			data = json_loads(data)
			self.revision = data['revision']
			self.poll_defer.callback(data['values'])

		url = self.site + '/poll?' + urllib.urlencode({'sid': self.session, 'revision': self.revision})
		print(url)
		self._run_defer = getRequest(url)
		self._run_defer.addErrback(eb).addCallback(cb)

	def poll(self):
		assert self.poll_defer is None
		self.poll_defer = Deferred()
		self._run()
		return self.poll_defer

	def stop(self):
		d = getRequest(self.site + '/del-session?' + urllib.urlencode({'sid': self.session}))
		if self._run_defer:
			self._run_defer.cancel()
		self.session = None
		return d


class IPtvDreamWebConfig(Screen):
	def __init__(self, session, db):
		Screen.__init__(self, session)
		trace("Web config open")
		self.db = db

		self["header"] = Label(_("Connecting to server..."))
		self["image"] = Pixmap()
		self["label"] = Label()

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
			"red": self.cancel,
			"cancel": self.cancel
		}, -2)

		self.poller = WebConfig(self.db.getSettings())
		self.onFirstExecBegin.append(self.start)

	@staticmethod
	def makeQrUrl(url):
		params = urllib.urlencode({'data': url, 'size': '200x200', 'ecc': 'M'})
		return "http://api.qrserver.com/v1/create-qr-code/?" + params

	def showQrCode(self, data):
		PATH = '/tmp/qrcode.png'

		def setPixmap(ret):
			trace(ret)
			from Tools.LoadPixmap import LoadPixmap
			self["image"].instance.setPixmap(LoadPixmap(PATH))

		self["header"].setText(_("Scan QR code or visit url below"))
		self["label"].setText("Go to https://technic.cf/web\nCode: %s" % data.encode('utf-8'))
		trace(self.makeQrUrl(data))
		downloadPage(self.makeQrUrl(data), PATH).addCallback(setPixmap)

	def start(self):
		self.poller.start().addCallback(self.keyReceived).addErrback(fatalError)

	def keyReceived(self, key):
		trace("Obtained key:", key)
		self.showQrCode(key)
		self.poller.poll().addCallback(self.newSettingsReceived).addErrback(fatalError)

	def newSettingsReceived(self, settings):
		trace("Obtained settings:", settings)
		values = {s['name']: s['value'] for s in settings}
		print(values)
		self.db.pushSettings(values)
		self.poller.stop()
		self.close(True)

	def cancel(self):
		trace("Closing web Settings")
		self.poller.stop()
		self.close(False)


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
		if apiClass.AUTH_TYPE == "Login":
			cfg_list = [
				getConfigListEntry(_("Login"), cfg.login),
				getConfigListEntry(_("Password"), cfg.password),
			]
		elif apiClass.AUTH_TYPE == "Key":
			cfg_list = [
				getConfigListEntry(_("Key"), cfg.login),
			]
		cfg_list += [
			getConfigListEntry(_("Show in main menu"), cfg.in_menu),
			getConfigListEntry(_("Show in extensions list"), cfg.in_extensions),
			getConfigListEntry(_("Player ID"), cfg.playerid),
			getConfigListEntry(_("Use HLS proxy"), cfg.use_hlsgw),
		]
		ConfigListScreen.__init__(self, cfg_list, session)
		self.setTitle(_("Configuration of %s") % name)
		self["config"].onSelectionChanged.append(self.showHideKb)

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


class IPtvDreamApiConfig(ConfigListScreen, Screen):
	def __init__(self, session, db):
		Screen.__init__(self, session)
		self.skinName = "IPtvDreamConfig"
		trace("ApiConfig open")
		self.db = db  # type: AbstractStream

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

		self.settings = {}
		self.cfg_list = []
		for i, (k, v) in enumerate(self.db.getSettings().items()):
			if isinstance(v, ConfInteger):
				entry = getConfigListEntry(v.title, ConfigInteger(v.value, limits=v.limits))
			elif isinstance(v, ConfSelection):
				entry = getConfigListEntry(v.title, ConfigSelection(v.choices, default=v.value))
			elif isinstance(v, ConfString):
				entry = getConfigListEntry(v.title, ConfigSearchText(default=v.value))
			else:
				raise Exception("Unknown type in settings: " + str(type(v)))
			self.settings[i] = k
			self.cfg_list.append(entry)

		ConfigListScreen.__init__(self, self.cfg_list, session)
		self.setTitle(_("Configuration of %s") % self.db.NAME)
		self["config"].onSelectionChanged.append(self.showHideKb)

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
		update = {}
		for i, c in enumerate(self.cfg_list):
			if c[1].isChanged():
				k = self.settings[i]
				update[k] = c[1].value
		if update:
			self.pushSettings(update)
		else:
			self.close(False)

	def pushSettings(self, settings):
		try:
			self.db.pushSettings(settings)
			self.close(True)
		except APIException as ex:
			self.session.openWithCallback(
				lambda ret: self.close(False),
				MessageBox, _("Failed to send settings to server.") + "\n%s" % str(ex), MessageBox.TYPE_ERROR)
