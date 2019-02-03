# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
#  Copyright (c) 2015 Alex Maystrenko <alexeytech@gmail.com>
#  Copyright (c) 2013 Alex Revetchi <alex.revetchi@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import print_function

# enigma2 imports
from Components.Sources.Boolean import Boolean
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, configfile, ConfigText, ConfigInteger, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.Source import Source
from Components.Label import Label
from Components.Slider import Slider
from Components.Button import Button
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Input import Input
from Components.MenuList import MenuList
from Components.GUIComponent import GUIComponent
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarPlugins, InfoBarExtensions,\
	InfoBarAudioSelection, InfoBarNotifications
from Screens.Screen import Screen
from Screens.InfoBarGenerics import NumberZap as NumberZapProxy
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import PinInput, InputBox
from Tools.BoundFunction import boundFunction
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_SKIN, SCOPE_SYSETC, SCOPE_CURRENT_PLUGIN

# enigma2 core imports
from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, \
	gFont, eLabel, eSize, ePoint, iPlayableService, ePicLoad
from enigma import eServiceReference, iServiceInformation, eDVBDB
from skin import parseFont, colorNames, SkinError

# system imports
from os import path as os_path, listdir as os_listdir, mkdir as os_mkdir
from datetime import datetime, timedelta
try:
	# noinspection PyUnresolvedReferences
	from typing import Callable, Optional, List
except ImportError:
	pass

# plugin imports
from layer import eTimer
from common import StaticTextService
from utils import trace, tdSec, secTd, syncTime, APIException, APILoginFailed, APIWrongPin, EPG
from api.abstract_api import MODE_VIDEOS, MODE_STREAM, AbstractStream
from loc import translate as _
from common import parseColor
from standby import standbyNotifier
from lib.epg import EpgProgress

SKIN_PATH = resolveFilename(SCOPE_SKIN, 'IPtvDream')
ENIGMA_CONF_PATH = resolveFilename(SCOPE_SYSETC, 'enigma2')
EPGMAP_PATH = resolveFilename(SCOPE_SYSETC, 'iptvdream')

rec_png = LoadPixmap(cached=True, path=SKIN_PATH + '/rec.png')
EPG_UPDATE_INTERVAL = 60  # Seconds, in channel list.
PROGRESS_TIMER = 1000*60  # Update progress in infobar.
PROGRESS_SIZE = 500
ARCHIVE_TIME_FIX = 5  # sec. When archive paused, we could miss some video
AUTO_AUDIOSELECT = True


#  Reimplementation of InfoBarShowHide
class ShowHideScreen:
	STATE_HIDDEN = 0
	STATE_SHOWN = 1

	def __init__(self):
		# super(ShowHideScreen, self).__init__(session)
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


class IPtvDreamAudio(Screen):
	def __init__(self, session):
		super(IPtvDreamAudio, self).__init__(session)
		self.__ev_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedInfo: self.audioSelect,
				iPlayableService.evStart: self.audioClear
			})
		self.audio_selected = False

	def audioSelect(self):
		print("[IPtvDreamAudio] select")
		if self.audio_selected or not AUTO_AUDIOSELECT:
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


class NumberZap(NumberZapProxy):
	def __init__(self, session, number):
		NumberZapProxy.__init__(self, session, number)

	def keyOK(self):
		self.Timer.stop()
		self.close(int(self["number"].getText()))


class IPtvDreamStreamPlayer(
		Screen, ShowHideScreen, InfoBarBase, InfoBarMenu, InfoBarPlugins,
		InfoBarExtensions, InfoBarAudioSelection, InfoBarNotifications):

	"""
	:type channels: IPtvDreamChannels
	"""

	ALLOW_SUSPEND = True

	def __init__(self, session, db):
		Screen.__init__(self, session)
		InfoBarBase.__init__(self, steal_current_service=True)
		InfoBarMenu.__init__(self)
		InfoBarExtensions.__init__(self)
		InfoBarPlugins.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarNotifications.__init__(self)
		ShowHideScreen.__init__(self)  # Use myInfoBar because image developers modify InfoBarGenerics

		trace("start stream player")
		self.db = db
		from manager import manager
		self.cfg = manager.getConfig(self.db.NAME)
		self.cid = None

		standbyNotifier.onStandbyChanged.append(self.standbyChanged)
		self.onClose.append(lambda: standbyNotifier.onStandbyChanged.remove(self.standbyChanged))

		self.channels = self.session.instantiateDialog(IPtvDreamChannels, self.db, self)
		self.onFirstExecBegin.append(self.start)

		self.setTitle(self.db.NAME)
		self["channelName"] = Label("")
		self["channelNumber"] = Label("")
		# Epg widgets
		self["currentName"] = Label("")
		self["nextName"] = Label("")
		self["currentTime"] = Label("")
		self["nextTime"] = Label("")
		self["currentDuration"] = Label("")
		self["nextDuration"] = Label("")
		self["progressBar"] = Slider(0, PROGRESS_SIZE)

		# TODO: think more
		self["archiveDate"] = Label("")
		self["inArchive"] = Boolean(False)
		self["piconRef"] = StaticTextService()
		self["providerRef"] = StaticTextService(self.db.NAME)

		# TODO: ActionMap add help.

		self["actions"] = ActionMap(["IPtvDreamInfobarActions", "ColorActions", "OkCancelActions"], {
				"cancel": self.confirmExit,
				"closePlugin": self.exit,
				"openVideos": self.openVod,
				"green": self.openSettings,
				"openServiceList": self.showList,
				"zapUp": self.previousChannel,
				"zapDown": self.nextChannel,
				"historyNext": self.historyNext,
				"historyBack": self.historyBack,
				"showEPGList": self.showEpg,
			})

		self["live_actions"] = ActionMap(["IPtvDreamLiveActions"], {
				"zapUp": self.previousChannel,
				"zapDown": self.nextChannel,
			}, -1)

		self["archive_actions"] = ActionMap(["IPtvDreamArchiveActions"], {
				"exitArchive": self.exitArchive,
				"playpause": self.playPauseArchive,
				"play": lambda: self.playPauseArchive(True, False),
				"pause": lambda: self.playPauseArchive(False, True),
				"seekForward": self.archiveSeekFwd,
				"seekBackward": self.archiveSeekRwd,
			}, -1)

		self["NumberActions"] = NumberActionMap(["NumberActions"], {
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal,
			})

		self.currentEpg = None
		self.epgTimer = eTimer()
		self.epgProgressTimer = eTimer()
		self.epgTimer.callback.append(self.epgEvent)
		self.epgProgressTimer.callback.append(self.epgUpdateProgress)

		self.archive_pause = None
		self.shift = 0

	### Init and destroy

	def start(self):
		trace("player start")
		self.showList()

	def exit(self, ret=None):
		self.channels.saveQuery()
		self.session.deleteDialog(self.channels)
		self.close(ret)

	def confirmExit(self):
		def cb(ret):
			if ret:
				self.exit()
		self.session.openWithCallback(cb, MessageBox, _("Exit plugin?"), MessageBox.TYPE_YESNO)

	### Play

	def play(self, cid):
		trace("play cid =", cid)

		self.cid = cid
		self.session.nav.stopService()
		if cid is None:
			return

		if self.db.channels[cid].is_protected:
			trace("protected by api")
			code = self.cfg.parental_code.value
			if code:
				trace("using saved code")
				self.getUrl(code)
			else:
				self.enterPin()
		else:
			self.getUrl(None)

	def enterPin(self):
		self.session.openWithCallback(
				self.getUrl, InputBox, title=_("Enter protect password"),
				windowTitle=_("Channel Locked"), type=Input.PIN)

	def getUrl(self, pin):
		try:
			url = self.db.getStreamUrl(self.cid, pin, self.time())
		except APIWrongPin:
			self.session.openWithCallback(
					lambda ret: self.enterPin(), MessageBox, _("Wrong pin!"),
					MessageBox.TYPE_ERROR, timeout=10, enable_input=False)
			return
		except APIException as e:
			self.showError(_("Error while getting stream url:") + str(e))
			self.updateLabels()
			return

		self.playUrl(url)

	### Player

	def playUrl(self, url):
		cid = self.cid
		trace("play", url)
		ref = eServiceReference(int(self.cfg.playerid.value), 0, url)
		ref.setName(self.db.channels[cid].name)
		ref.setData(1, 1)
		self.session.nav.playService(ref)
		self.updateLabels()

	def updateLabels(self):
		cid = self.cid
		self["piconRef"].text = self.db.getPiconName(cid)
		self["channelName"].setText("%d. %s" % (self.db.channels[cid].number, self.db.channels[cid].name))
		self.epgEvent()

	def standbyChanged(self, sleep):
		if sleep:
			trace("entered standby")
			if self.shift and not self.archive_pause:
				self.playPauseArchive()
		else:
			trace("exited standby")
			if self.shift:
				self.playPauseArchive()
			else:
				self.play(self.cid)

	### Archive

	def setArchiveShift(self, time_shift):
		self.shift = time_shift
		if time_shift:
			self.archive_pause = None
			self["live_actions"].setEnabled(False)
			self["archive_actions"].setEnabled(True)
			self["inArchive"].setBoolean(True)
		else:
			self["archive_actions"].setEnabled(False)
			self["live_actions"].setEnabled(True)
			self["inArchive"].setBoolean(False)

	def time(self):
		if self.shift:
			return syncTime() + secTd(self.shift)
		else:
			return None

	def archiveSeekFwd(self):
		self.session.openWithCallback(self.fwdJumpTo, MinuteInput)

	def archiveSeekRwd(self):
		self.session.openWithCallback(self.rwdJumpTo, MinuteInput)

	def fwdJumpTo(self, minutes):
		print("[IPtvDream] fwdSeek", minutes)
		self.shift += minutes*60
		if self.shift > 0:
			self.setArchiveShift(0)
		self.play(self.cid)

	def rwdJumpTo(self, minutes):
		print("[IPtvDream] rwdSeek", minutes)
		self.shift -= minutes*60
		self.play(self.cid)

	def playPauseArchive(self, play=True, pause=True):
		if self.archive_pause and play:
			# do unPause
			self.shift -= tdSec(syncTime()-self.archive_pause)-ARCHIVE_TIME_FIX
			self.archive_pause = None
			self.play(self.cid)
			self.unlockShow()
		elif pause:
			# do pause
			self.archive_pause = syncTime()
			self.session.nav.stopService()
			self.lockShow()

	def exitArchive(self):
		self.setArchiveShift(0)
		self.play(self.cid)

	### EPG

	def epgEvent(self):
		# first stop timers
		self.epgTimer.stop()
		self.epgProgressTimer.stop()
		cid = self.cid
		time = syncTime() + secTd(self.shift)

		def setEpgCurrent():
			curr = self.db.channels[cid].epgCurrent(time)
			if not curr:
				return False

			self.currentEpg = curr
			self["currentName"].setText(curr.name)
			self["currentTime"].setText(curr.begin.strftime("%H:%M"))
			self["nextTime"].setText(curr.end.strftime("%H:%M"))
			self.epgTimer.start(curr.timeLeftMilliseconds(time) + 1000)
			self["currentDuration"].setText("+%d min" % (curr.timeLeft(time) / 60))
			self["progressBar"].setValue(curr.percent(time, PROGRESS_SIZE))
			self.epgProgressTimer.start(PROGRESS_TIMER)
			if self.shift:
				self["archiveDate"].setText(curr.begin.strftime("%d.%m"))
				self["archiveDate"].show()
			else:
				self["archiveDate"].hide()
			return True

		if not setEpgCurrent():
			try:
				self.db.loadDayEpg(cid, time)
			except APIException as e:
				print("[IPtvDream] ERROR load epg failed! cid =", cid, bool(self.shift), e)
			if not setEpgCurrent():
				self["currentName"].setText('')
				self["currentTime"].setText('')
				self["nextTime"].setText('')
				self["currentDuration"].setText('')
				self["progressBar"].setValue(0)

		def setEpgNext():
			e = self.db.channels[cid].epgNext(time)
			if not e:
				return False
			self['nextName'].setText(e.name)
			self['nextDuration'].setText("%d min" % (e.duration() / 60))
			return True

		if not setEpgNext():
			try:
				self.db.loadDayEpg(cid, time)
			except APIException:
				print("[IPtvDream] load epg next failed!")
			if not setEpgNext():
				self["nextName"].setText('')
				self["nextDuration"].setText('')

		self.serviceStarted()

	def epgUpdateProgress(self):
		time = syncTime() + secTd(self.shift)
		self["currentDuration"].setText("+%d min" % (self.currentEpg.timeLeft(time) / 60))
		self["progressBar"].setValue(self.currentEpg.percent(time, PROGRESS_SIZE))
		self.epgProgressTimer.start(PROGRESS_TIMER)

	### Dialogs

	def showEpg(self):
		self.session.openWithCallback(self.programSelected, IPtvDreamEpg, self.db, self.cid, self.shift)

	def programSelected(self, cid=None, time=None):
		if cid is not None and time is not None:
			self.setArchiveShift(tdSec(time-syncTime()))  # shift < 0
			self.play(cid)

	def showList(self):
		self.session.execDialog(self.channels)
		self.channels.callback = self.channelSelected

	def channelSelected(self, cid, time=None):
		if cid is None:
			return
		if time:
			self.programSelected(cid, time)
		elif cid != self.cid:
			self.switchChannel(cid)

	def openSettings(self):
		self.exit('settings')

	def openVod(self):
		self.exit('vod')

	### Channels

	def switchChannel(self, cid):
		# FIXME: zapping breaks archive shift
		trace("switch channel", self.cid)
		self.setArchiveShift(0)
		self.play(cid)

	def nextChannel(self):
		cid = self.channels.nextChannel()
		self.switchChannel(cid)

	def previousChannel(self):
		cid = self.channels.prevChannel()
		self.switchChannel(cid)

	def historyNext(self):
		if self.channels.historyNext():
			cid = self.channels.getCurrent()
			self.switchChannel(cid)

	def historyBack(self):
		if self.channels.historyPrev():
			cid = self.channels.getCurrent()
			self.switchChannel(cid)

	def keyNumberGlobal(self, number):
		self.session.openWithCallback(self.numberEntered, NumberZap, number)

	def numberEntered(self, num=None):
		trace("numberEntered", num)
		if num is not None and self.channels.goToNumber(num):
			cid = self.channels.getCurrent()
			self.switchChannel(cid)

	### Errors

	def showError(self, msg):
		self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR, 5)


class ChannelList(MenuList):
	def __init__(self):
		MenuList.__init__(self, [], content=eListboxPythonMultiContent, enableWrapAround=True)
		self.list = []
		self.col = {}
		self.fontCalc = []

		self.pixmapProgressBar = None
		self.pixmapArchive = None
		self.itemHeight = 28
		self.l.setFont(0, parseFont("Regular;22", ((1, 1), (1, 1))))
		self.l.setFont(1, parseFont("Regular;18", ((1, 1), (1, 1))))
		self.l.setFont(2, parseFont("Regular;20", ((1, 1), (1, 1))))
		self.showEpgProgress = config.usage.show_event_progress_in_servicelist.value
		self.num = 0
		self.highlight_cid = 0

		for x in [
				"colorEventProgressbar", "colorEventProgressbarSelected",
				"colorEventProgressbarBorder", "colorEventProgressbarBorderSelected",
				"colorServiceDescription", "colorServiceDescriptionSelected",
				"colorServicePlaying", "colorServicePlayingSelected"]:
			self.col[x] = None

	def postWidgetCreate(self, instance):
		trace("postWidgetCreate")
		MenuList.postWidgetCreate(self, instance)
		# Create eLabel instances, because we can't access eTextPara directly
		self.fontCalc = [eLabel(self.instance), eLabel(self.instance), eLabel(self.instance)]
		self.fontCalc[0].setFont(parseFont("Regular;22", ((1, 1), (1, 1))))
		self.fontCalc[1].setFont(parseFont("Regular;18", ((1, 1), (1, 1))))
		self.fontCalc[2].setFont(parseFont("Regular;20", ((1, 1), (1, 1))))

	def applySkin(self, desktop, parent):
		scale = ((1, 1), (1, 1))
		attribs = []
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "colorEventProgressbar":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorEventProgressbarSelected":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorEventProgressbarBorder":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorEventProgressbarBorderSelected":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorServiceDescription":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorServiceDescriptionSelected":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorServicePlaying":
					self.col[attrib] = parseColor(value)
				elif attrib == "colorServicePlayingSelected":
					self.col[attrib] = parseColor(value)
				elif attrib == "picServiceEventProgressbar":
					pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
					if pic:
						self.pixmapProgressBar = pic
				elif attrib == "picServiceArchive":
					pic = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, value))
					if pic:
						self.pixmapArchive = pic
				elif attrib == "serviceItemHeight":
					self.itemHeight = int(value)
				elif attrib == "serviceNameFont":
					self.l.setFont(0, parseFont(value, scale))
					self.fontCalc[0].setFont(parseFont(value, scale))
				elif attrib == "serviceInfoFont":
					self.l.setFont(1, parseFont(value, scale))
					self.fontCalc[1].setFont(parseFont(value, scale))
				elif attrib == "serviceNumberFont":
					self.l.setFont(2, parseFont(value, scale))
					self.fontCalc[2].setFont(parseFont(value, scale))
				else:
					attribs.append((attrib, value))

		self.skinAttributes = attribs
		res = GUIComponent.applySkin(self, desktop, parent)

		self.l.setItemHeight(self.itemHeight)
		self.itemWidth = self.instance.size().width()
		for x in self.fontCalc:
			# resize and move away
			x.resize(eSize(self.itemWidth, self.itemHeight))
			x.move(ePoint(int(self.instance.size().width()+10), int(self.instance.size().height()+10)))
			x.setNoWrap(1)
		return res

	def setEnumerated(self, enumerated):
		if enumerated:
			self.num = 1
		else:
			self.num = 0

	def setList(self, channels):
		self.list = channels
		print(len(channels), channels)
		self.l.setList(map(self.buildChannelEntry, channels))
		if self.num:
			self.num = 1

	def highlight(self, cid):
		self.highlight_cid = cid

	def setGroupList(self, groups):
		self.list = groups
		self.l.setList(map(self.buildGroupEntry, groups))

	def calculateWidth(self, text, font):
		self.fontCalc[font].setText(text)
		return int(round(self.fontCalc[font].calculateSize().width()*1.1))

	def buildGroupEntry(self, group):
		return [
			group,
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, self.itemWidth, self.itemHeight,
				0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, group.title)
		]

	def buildChannelEntry(self, c):
		defaultFlag = RT_HALIGN_LEFT | RT_VALIGN_CENTER
		# Filling from left to rigth

		lst = [c]
		xoffset = 1

		if self.num:
			xoffset += 55
			text = str(c.number)
			lst.append(
				(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, xoffset-5, self.itemHeight,
					2, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text))

		if self.pixmapArchive:
			width = self.pixmapArchive.size().width()
			height = self.pixmapArchive.size().height()
			if c.has_archive:
				lst.append(
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST,
						xoffset, (self.itemHeight - height) / 2, width, height, self.pixmapArchive))
			xoffset += width+5

		epg = c.epgCurrent()

		if self.showEpgProgress:
			width = 52
			height = 6
			if epg:
				percent = epg.percent(syncTime(), 100)
				lst.extend([
					(eListboxPythonMultiContent.TYPE_PROGRESS,
						xoffset+1, (self.itemHeight-height)/2, width, height,
						percent, 0, self.col['colorEventProgressbar'], self.col['colorEventProgressbarSelected']),
					(eListboxPythonMultiContent.TYPE_PROGRESS,
						xoffset, (self.itemHeight-height)/2 - 1, width+2, height+2,
						0, 1, self.col['colorEventProgressbarBorder'], self.col['colorEventProgressbarBorderSelected'])
				])
			xoffset += width+7

		text = str(c.name)
		width = self.calculateWidth(text, 0)
		if c.cid != self.highlight_cid:
			lst.append(
				(eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, width, self.itemHeight,
					0, defaultFlag, text))
		else:
			lst.append(
				(eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, width, self.itemHeight,
					0, defaultFlag, text, self.col['colorServicePlaying'], self.col['colorServicePlayingSelected']))
		xoffset += width+10

		if epg:
			text = '(%s)' % epg.name
			lst.append(
				(eListboxPythonMultiContent.TYPE_TEXT, xoffset, 0, self.itemWidth, self.itemHeight,
					1, defaultFlag, text,
					self.col['colorServiceDescription'], self.col['colorServiceDescriptionSelected']))

		return lst


class History:
	"""
	:type history: list[HistoryEntry]
	"""
	def __init__(self, size):
		self.history_size = size
		self.history = []
		self.history_idx = -1

	def isEmpty(self):
		return len(self.history) == 0

	def historyAppend(self, val):
		while len(self.history) > self.history_idx + 1:
			self.history.pop()
		self.history.append(val)
		if len(self.history) > self.history_size:
			self.history.pop(0)
		else:
			self.history_idx += 1

	def historyPrev(self):
		if self.history_idx < 1:
			return None
		else:
			self.history_idx -= 1
			return self.history[self.history_idx]

	def historyNext(self):
		if self.history_idx+1 == len(self.history):
			return None
		else:
			self.history_idx += 1
			return self.history[self.history_idx]

	def historyNow(self):
		if len(self.history):
			return self.history[self.history_idx]
		else:
			return None

	def historyPrint(self):
		print(map(str, self.history))


class HistoryEntry(object):
	def __init__(self, mode, gid, gr_idx, cid, ch_idx):
		self.mode = mode
		self.gid, self.gr_idx = gid, gr_idx
		self.cid, self.ch_idx = cid, ch_idx

	def copy(self):
		return HistoryEntry(self.mode, self.gid, self.gr_idx, self.cid, self.ch_idx)

	def fromStr(self, s):
		self.mode, self.gid, self.gr_idx, self.cid, self.ch_idx = map(int, s.split(","))

	def toStr(self):
		return ",".join(map(str, (self.mode, self.gid, self.gr_idx, self.cid, self.ch_idx)))

	def makeTuple(self):
		return self.mode, self.gid, self.gr_idx, self.cid, self.ch_idx

	def __repr__(self):
		return "HistoryEntry(%d, (%d, %d), (%d, %d))" % (self.mode, self.gid, self.gr_idx, self.cid, self.ch_idx)


class IPtvDreamChannels(Screen):
	"""
	:type db: AbstractStream
	:type saved_state: HistoryEntry
	"""

	GROUPS, ALL, GROUP, FAV = range(4)

	def __init__(self, session, db, player_ref):
		Screen.__init__(self, session)

		trace("channels init")
		self.history = History(10)
		self.db = db
		self.player_ref = player_ref
		from manager import manager
		self.cfg = manager.getConfig(self.db.NAME)

		self["key_red"] = Button(_("All"))
		self["key_green"] = Button(_("Groups"))
		self["key_yellow"] = Button(_("Add"))
		self["key_blue"] = Button(_("Favourites"))

		self.list = self["list"] = ChannelList()

		self["channelName"] = Label()
		self["epgName"] = Label()
		self["epgTime"] = Label()
		self["epgDescription"] = Label()
		self["epgProgress"] = Slider(0, 100)
		self["epgNextTime"] = Label()
		self["epgNextName"] = Label()
		self["epgNextDescription"] = Label()

		self["packetExpire"] = Label()

		self["actions"] = ActionMap(
			["OkCancelActions", "IPtvDreamChannelListActions"], {
				"cancel": self.exit,
				"ok": self.ok,
				"showAll": self.showAll,
				"showGroups": self.showGroups,
				"addFavourites": self.addRemoveFavourites,
				"showFavourites": self.showFavourites,
				"contextMenu": self.showMenu,
				"showEPGList": self.showEpgList,
				"nextBouquet": self.nextGroup,
				"prevBouquet": self.prevGroup
			}, -1)

		self.list.onSelectionChanged.append(self.selectionChanged)

		self.mode = self.GROUPS
		self.gid = None
		self.saved_state = None

		self.editMoving = False

		if self.db.packet_expire is not None:
			self["packetExpire"].setText(_("Payment expires: ") + self.db.packet_expire.strftime("%d.%m.%Y"))

		self.onLayoutFinish.append(self.initList)
		self.onShown.append(self.start)

		self.lastEpgUpdate = datetime.fromtimestamp(0)

	def initList(self):
		self.fillList()

	def start(self):
		trace("Channels list shown")
		if not self.history.isEmpty():
			self.saved_state = self.history.historyNow().copy()
		else:
			self.saved_state = None

	def saveQuery(self):
		trace("save query")
		h = self.history.historyNow()
		if h is not None:
			self.cfg.last_played.value = self.history.historyNow().toStr()
		else:
			self.cfg.last_played.value = ""
		self.cfg.last_played.save()
		configfile.save()

	def createHistoryEntry(self):
		entry = self.getSelected()
		assert entry is not None
		return HistoryEntry(self.mode, self.gid, 0, entry.cid, self.list.getSelectedIndex())

	def recoverState(self, state):
		"""
		:param HistoryEntry state:
		"""
		self.mode, self.gid = state.mode, state.gid
		if self.mode == self.GROUPS:
			self.fillGroupsList()
			self.list.moveToIndex(self.saved_state.gr_idx)
		else:
			self.fillList()
			self.list.moveToIndex(self.saved_state.ch_idx)

	def exit(self):
		if self.saved_state is not None:
			self.recoverState(self.saved_state)
		self.close(None)

	def ok(self, time=None):
		entry = self.getSelected()
		if entry is None:
			return
		if self.mode == self.GROUPS:
			self.mode = self.GROUP
			self.gid = entry.gid
			self.fillList()
			self.list.moveToIndex(0)
		else:
			idx = self.list.getSelectedIndex()
			cid = entry.cid
			self.history.historyAppend(HistoryEntry(self.mode, self.gid, 0, cid, idx))
			self.close(cid, time)

	def fetchChannelsEpg(self):
		t = syncTime()
		timeout = not self.lastEpgUpdate or ((t - self.lastEpgUpdate) > secTd(EPG_UPDATE_INTERVAL))
		if not timeout:
			return
		trace("fetchEpg", "!"*100)
		self.lastEpgUpdate = t
		to_update = [x for (x, c) in self.db.channels.items() if not c.epgNext(t)]
		if len(to_update):
			try:
				self.db.loadChannelsEpg(to_update)
			except APIException as e:
				trace("[IPtvDream] failed to get channels epg", str(e))

	def fillGroupsList(self):
		self.setTitle(" / ".join([self.db.NAME, _("Groups")]))
		groups = self.db.selectGroups()
		self.list.setGroupList(groups)
		if self.gid is not None:
			for idx, g in enumerate(groups):
				if g.gid == self.gid:
					self.list.moveToIndex(idx)
					break
			else:
				self.gid = None

	def fillList(self):
		self.fetchChannelsEpg()
		title = [self.db.NAME]
		self.list.highlight(self.player_ref.cid)

		if self.mode == self.GROUPS:
			self.fillGroupsList()
			title.append(_("Groups"))
		elif self.mode == self.GROUP:
			self.list.setList(self.db.selectChannels(self.gid))
			title.append(self.db.groups[self.gid].title)
		elif self.mode == self.ALL:
			self.list.setList(self.db.selectAll())
			title.append(_("All channels"))
		elif self.mode == self.FAV:
			self.list.setList(self.db.selectFavourites())
			title.append(_("Favourites"))

		self.setTitle(" / ".join(title))
		if self.mode == self.FAV:
			self["key_yellow"].setText(_("Remove"))
		else:
			self["key_yellow"].setText(_("Add"))

	def selectionChanged(self):
		if self.editMoving:
			return

		channel = self.getSelected()
		trace("selection =", channel)

		if self.mode == self.GROUPS or channel is None:
			self["channelName"].setText("")
			self.hideEpgLabels()
			self.hideEpgNextLabels()
		else:
			self["channelName"].setText(channel.name)
			self["channelName"].show()
			curr = channel.epgCurrent()
			if curr:
				self["epgTime"].setText("%s - %s" % (curr.begin.strftime("%H:%M"), curr.end.strftime("%H:%M")))
				self["epgName"].setText(curr.name)
				self["epgName"].show()
				self["epgTime"].show()
				self["epgProgress"].setValue(curr.percent(syncTime(), 100))
				self["epgProgress"].show()
				self["epgDescription"].setText(curr.description)
				self["epgDescription"].show()
			else:
				self.hideEpgLabels()
			curr = channel.epgNext()
			if curr:
				self["epgNextTime"].setText("%s - %s" % (curr.begin.strftime("%H:%M"), curr.end.strftime("%H:%M")))
				self["epgNextName"].setText(curr.name)
				self["epgNextDescription"].setText(curr.description)
				self["epgNextName"].show()
				self["epgNextTime"].show()
				self["epgNextDescription"].show()
			else:
				self.hideEpgNextLabels()

	def hideEpgLabels(self):
		self["epgName"].hide()
		self["epgTime"].hide()
		self["epgProgress"].hide()
		self["epgDescription"].hide()

	def hideEpgNextLabels(self):
		self["epgNextName"].hide()
		self["epgNextTime"].hide()
		self["epgNextDescription"].hide()

	def showGroups(self):
		self.mode = self.GROUPS
		self.fillList()

	def showAll(self):
		self.mode = self.ALL
		self.fillList()

	def showFavourites(self):
		self.mode = self.FAV
		self.fillList()

	def npGroup(self, diff):
		if self.mode == self.GROUP:
			groups = self.db.selectGroups()
			for idx, g in enumerate(groups):
				if g.gid == self.gid:
					self.gid = groups[(idx + diff) % len(groups)].gid
					self.fillList()
					break

	def nextGroup(self):
		self.npGroup(1)

	def prevGroup(self):
		self.npGroup(-1)

	def addRemoveFavourites(self):
		channel = self.getSelected()
		if not channel:
			return
		if self.mode == self.FAV:
			self.db.rmFav(channel.cid)
			self.showFavourites()
		elif self.mode != self.GROUPS:
			self.db.addFav(channel.cid)

	def showMenu(self):
		lst = []
		self.session.openWithCallback(self.showMenuCB, ChoiceBox, _("Context menu"), lst)

	def showMenuCB(self, entry=None):
		if entry is None:
			return
		entry = entry[1]
		trace("context cb", entry)

	def showEpgList(self):
		channel = self.getSelected()
		if channel and self.modeChannels():
			self.session.openWithCallback(self.showEpgCB, IPtvDreamEpg, self.db, channel.cid, 0)

	def showEpgCB(self, cid=None, time=None):
		trace("selected program", cid, time)
		if time is not None:
			self.ok(time)

	def getSelected(self):
		entry = self.list.getCurrent()
		trace("getSelected", entry and entry[0])
		return entry and entry[0]

	def getCurrent(self):
		return self.history.historyNow().cid

	def modeChannels(self):
		return self.mode != self.GROUPS

	def nextChannel(self):
		self.list.down()
		self.history.historyAppend(self.createHistoryEntry())
		return self.getCurrent()

	def prevChannel(self):
		self.list.up()
		self.history.historyAppend(self.createHistoryEntry())
		return self.getCurrent()

	def historyNext(self):
		h = self.history.historyNext()
		if h is not None:
			self.recoverState(h)
			return self.getCurrent()
		else:
			return None

	def historyPrev(self):
		h = self.history.historyPrev()
		if h is not None:
			self.recoverState(h)
			return self.getCurrent()
		else:
			return None

	def findChannelIndex(self, cid):
		for i, channel in enumerate(self.list.list):
			if channel.cid == cid:
				return i
		else:
			return None

	def goToNumber(self, num):
		cid = self.db.findNumber(num)
		if cid is None:
			return None
		idx = self.findChannelIndex(cid)
		if idx is None:
			self.mode, self.gid = self.ALL, None
			self.fillList()
			idx = self.findChannelIndex(cid)
		self.list.moveToIndex(idx)
		self.history.historyAppend(self.createHistoryEntry())
		return cid


class IPtvDreamEpg(Screen):
	def __init__(self, session, db, cid, shift):
		Screen.__init__(self, session)

		self["key_red"] = Button(_("Archive"))
		self["key_green"] = Button(_("Details"))
		self.list = MenuList([], content=eListboxPythonMultiContent)
		self.list.l.setFont(0, gFont("Regular", 20))
		self.list.l.setFont(1, gFont("Regular", 20))
		self.list.l.setItemHeight(28)
		self["list"] = self.list

		self["epgName"] = Label()
		self["epgDescription"] = Label()
		self["epgTime"] = Label()
		self["epgDuration"] = Label()

		self["epgProgress"] = Slider(0, 100)
		self["progress"] = self._progress = EpgProgress()
		self._progress.onChanged.append(lambda value: self["epgProgress"].setValue(int(100 * value)))

		self["sepgName"] = Label()
		self["sepgDescription"] = Label()
		self["sepgTime"] = Label()
		self["sepgDuration"] = Label()

		self["actions"] = ActionMap(
			["OkCancelActions", "IPtvDreamEpgListActions", "ColorActions"], {
				"cancel": self.exit,
				"ok": self.archive,
				"nextDay": self.nextDay,
				"prevDay": self.prevDay,
				"green": self.showSingle,
				"red": self.archive
			}, -1)

		self.db = db
		self.cid = cid
		self.shift = shift
		self.day = 0
		self.single = False
		self.list.onSelectionChanged.append(self.updateLabels)
		self.onLayoutFinish.append(self.fillList)

	def buildEpgEntry(self, entry):
		res = [
			entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 18, 2, 40, 22, 0, RT_HALIGN_LEFT, _(entry.begin.strftime('%a'))),
			(eListboxPythonMultiContent.TYPE_TEXT, 62, 2, 90, 22, 0, RT_HALIGN_LEFT, entry.begin.strftime('%H:%M')),
			(eListboxPythonMultiContent.TYPE_TEXT, 140, 2, 585, 24, 1, RT_HALIGN_LEFT, entry.name)]
		if self.db.channels[self.cid].has_archive and entry.begin < syncTime():
			res += [(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 5, 16, 16, rec_png)]
		return res

	def fillList(self):
		if self.cid is None:
			return
		self.hideLabels("s%s")
		self.list.show()

		d = syncTime()+secTd(self.shift)+timedelta(self.day)

		epg_list = self.db.channels[self.cid].epgDay(d)
		if len(epg_list) == 0:
			try:
				self.db.loadDayEpg(self.cid, d)
			except APIException as e:
				trace("getDayEpg failed cid =", self.cid, str(e))
			epg_list = self.db.channels[self.cid].epgDay(d)

		self.list.setList(map(self.buildEpgEntry, epg_list))
		self.setTitle("EPG / %s / %s %s" % (self.db.channels[self.cid].name, d.strftime("%d"), _(d.strftime("%b"))))
		self.list.moveToIndex(0)
		e = self.db.channels[self.cid].epgCurrent(d)
		if e and self.day == 0:
			try:
				self.list.moveToIndex(epg_list.index(e))
			except ValueError:
				trace("epgCurrent at other date!")

	def updateLabels(self, s="%s"):
		entry = self.list.getCurrent()
		if not entry:
			return

		entry = entry[0]
		self[s % "epgName"].setText(entry.name)
		self[s % "epgTime"].setText(entry.begin.strftime("%d.%m %H:%M"))
		self[s % "epgDescription"].setText(entry.description)
		self[s % "epgDescription"].show()
		self[s % "epgName"].show()
		self[s % "epgTime"].show()
		self[s % "epgDuration"].setText("%s min" % (entry.duration() / 60))
		self[s % "epgDuration"].show()
		self._progress.setEpg(entry)

	def hideLabels(self, s="%s"):
		trace("hide", s)
		self[s % "epgName"].hide()
		self[s % "epgTime"].hide()
		self[s % "epgDuration"].hide()
		self[s % "epgDescription"].hide()

	def showSingle(self):
		if not self.single:
			self["key_green"].setText("")
			self.single = True
			self.hideLabels()
			self.list.hide()
			self.updateLabels("s%s")

	def archive(self):
		entry = self.list.getCurrent()
		if not entry:
			return
		entry = entry[0]
		if self.db.channels[self.cid].has_archive:
			self.close(self.cid, entry.begin)

	def exit(self):
		# If single view then go to list. Else close all
		if self.single:
			self.single = False
			self["key_green"].setText(_("Details"))
			self.fillList()
			self.updateLabels()
		else:
			self.close()

	def nextDay(self):
		if self.single:
			return
		self.day += 1
		self.fillList()

	def prevDay(self):
		if self.single:
			return
		self.day -= 1
		self.fillList()


# gettext HACK:
# [_("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"), _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov") ]
