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

import time

# enigma2 imports
from Screens.MessageBox import MessageBox
from Components.Console import Console
from enigma import quitMainloop

# system imports
from twisted.web.client import getPage as _getPage, downloadPage as _downloadPage
from twisted.internet.defer import Deferred, fail

# plugin imports
from dist import NAME, VERSION
from layer import enigma2Qt

# not necessary for functioning
try:
	from loc import translate as _
except ImportError as e:
	print("[IPtvDream] loc", e)


def fatalError(err):
	"""
	Save traceback and go to bsod
	"""
	print("[IPtvDream] plugin error - exit 5")
	print(err)
	with open('/tmp/IPtvDream_crash.txt', 'w') as f:
		f.write(str(err))
	# exit code 5 = bsod
	quitMainloop(5)


def getPage(url):
	return _getPage(url, agent="IPtvDream-%s/%s" % (NAME, VERSION)).addErrback(twistedError)


def downloadPage(url, filename):
	return _downloadPage(url, filename, agent="IPtvDream-%s/%s" % (NAME, VERSION)).addErrback(twistedError)


def twistedError(err):
	raise UpdaterException(err.getErrorMessage())


class UpdaterException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)


def parseVersion(data):
	parts = data.strip().split(".")
	try:
		return tuple(map(int, parts))
	except ValueError:
		return tuple([0, 0])


class Updater(object):
	def __init__(self):
		self.url = "http://technic.cf/iptvdream4x/packages/"
		self.console = Console()
		self.prefix = "enigma2-plugin-extensions"
		self._version = None

	def checkUpdate(self):
		version = parseVersion(VERSION)
		print("[IPtvDream] Installed version:", version)

		def cb(data):
			new_version = parseVersion(data)
			self._version = new_version
			print("[IPtvDream] Available version:", new_version)
			return new_version > version

		def eb(err):
			print("[IPtvDream] Updater error:", err)
			if err.check(UpdaterException):
				return err
			else:
				fatalError(err)

		ts = int(time.time())
		return getPage(self.url + "version-%s.txt?ts=%s" % (NAME.lower(), ts)).addCallback(cb).addErrback(eb)

	def installUpdate(self):
		print("[IPtvDream] install update")
		if self._version is None:
			return fail(UpdaterException("Call checkUpdate() first"))

		version = ".".join(map(str, self._version))
		if enigma2Qt:
			ext = "deb"
		else:
			ext = "ipk"

		print("[IPtvDream] download", version, ext)
		file_name = "/tmp/IPtvDream-%s.%s" % (NAME, ext)
		name = ("IPtvDream-%s" % NAME).lower()
		url = self.url + "%s-%s_%s_all.%s" % (self.prefix, name, version, ext)

		def cb(result):
			return self._installPackage(file_name)

		def eb(err):
			print("[IPtvDream] Updater error:", err)
			if err.check(UpdaterException):
				return err
			else:
				fatalError(err)

		return downloadPage(url, file_name).addCallback(cb).addErrback(eb)

	def _installPackage(self, file_name):
		d = Deferred()

		def commandFinished(output, exitcode, extra_args=None):
			print("[IPtvDream] command returned %d output:\n%s" % (exitcode, output))
			r = (output, exitcode)
			d.callback(r)

		if enigma2Qt:
			self.console.ePopen('dpkg -i %s' % file_name, commandFinished)
		else:
			self.console.ePopen('opkg install %s' % file_name, commandFinished)
		return d


class UpdaterScreen(MessageBox):
	def __init__(self, session):
		MessageBox.__init__(self, session, _("Checking updates"), MessageBox.TYPE_INFO, enable_input=False)
		self.skinName = "MessageBox"
		self.updater = Updater()
		self.onFirstExecBegin.append(self.start)

	def start(self):
		self.updater.checkUpdate().addCallback(self.install).addErrback(self.error).addErrback(fatalError)

	def install(self, confirmed):
		if confirmed:
			self["text"].setText(_("Installing update, please wait"))
			self.updater.installUpdate().addCallback(self.finished).addErrback(self.error).addErrback(fatalError)
		else:
			self.close(False)

	def error(self, err):
		err.trap(UpdaterException)
		self.finished((err.getErrorMessage(), -1))

	def finished(self, result):
		output, exitcode = result
		if exitcode == 0:
			self.close(True)
		else:
			self.session.openWithCallback(
				lambda ret: self.close(False), MessageBox,
				_("Update failed") + ":\n %s" % output, MessageBox.TYPE_ERROR)
