# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Common utils for enigma2 plugin, not directly related to iptv logic"""

from __future__ import print_function

from functools import wraps

from Components.config import ConfigText
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.Screen import Screen
from enigma import iPlayableService
from skin import colorNames, SkinError

from layer import eTimer
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


# Reimplementation of InfoBarShowHide
class ShowHideScreen(Screen):
	STATE_HIDDEN = 0
	STATE_SHOWN = 1

	def __init__(self, session):
		super(ShowHideScreen, self).__init__(session)
		self.__state = self.STATE_SHOWN

		self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {
				"toggleShow": self.toggleShow,
				"hide": self.hide,
			}, 1)  # lower prio to make it possible to override ok and cancel..

		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.doTimerHide)
		self.hideTimer.start(5000, True)

		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)
		self.__locked = 0

	def serviceStarted(self):
		if self.execing:
			if config.usage.show_infobar_on_zap.value:
				self.doShow()

	def __onShow(self):
		self.__state = self.STATE_SHOWN
		self.startHideTimer()

	def startHideTimer(self):
		if self.__state == self.STATE_SHOWN:
			idx = config.usage.infobar_timeout.index
			if idx:
				self.hideTimer.start(idx*1000, True)

	def __onHide(self):
		self.__state = self.STATE_HIDDEN

	def doShow(self):
		self.show()
		self.startHideTimer()

	def doTimerHide(self):
		self.hideTimer.stop()
		if self.__state == self.STATE_SHOWN:
			self.hide()

	def toggleShow(self):
		if self.__state == self.STATE_SHOWN:
			self.hide()
			self.hideTimer.stop()
		elif self.__state == self.STATE_HIDDEN:
			self.show()

	def lockShow(self):
		self.__locked = self.__locked + 1
		if self.execing:
			self.show()
			self.hideTimer.stop()

	def unlockShow(self):
		self.__locked = self.__locked - 1
		if self.execing:
			self.startHideTimer()


class AutoAudioSelection(Screen):
	def __init__(self, session):
		super(AutoAudioSelection, self).__init__(session)
		self.__ev_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedInfo: self.audioSelect,
				iPlayableService.evStart: self.audioClear
			})
		self.audio_selected = False

	def audioSelect(self):
		print("[IPtvDreamAudio] select")
		if self.audio_selected:
			return
		self.audio_selected = True
		service = self.session.nav.getCurrentService()
		audio = service and service.audioTracks()
		n = audio and audio.getNumberOfTracks() or 0
		if n > 0:
			selected_audio = audio.getCurrentTrack()
			for x in range(n):
				language = audio.getTrackInfo(x).getLanguage()
				print("[IPtvDreamAudio] scan langstr:", x, language)
				if language.find('rus') > -1 and x != selected_audio:
					audio.selectTrack(x)
					break

	def audioClear(self):
		print("[IPtvDreamAudio] clear")
		self.audio_selected = False
