# -*- coding: utf-8 -*-
# Enigma2 IPtvDream player framework
#
# Copyright (c) 2015 Alex Maystrenko <alexeytech@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# system imports
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web import resource, util
try:
	from twisted.web.error import ErrorPage
except ImportError:
	from twisted.web.resource import ErrorPage

# plugin imports
from .manager import manager
from .utils import trace, APIException


class ApiInstanceManager(object):
	def __init__(self):
		self.running = {}
		manager.onConfigChanged.append(self.reset)

	def reset(self):
		self.running = {}

	def getApiInstance(self, name):
		try:
			return self.running[name]
		except KeyError:
			return self.createApiInstance(name)

	def createApiInstance(self, name):
		apiClass = manager.getApi(name)
		cfg = manager.getConfig(name)
		db = apiClass(cfg.login.value, cfg.password.value)
		db.start()
		self.running[name] = db
		return db


class RedirectToStream(resource.Resource):
	isLeaf = True

	def __init__(self):
		resource.Resource.__init__(self)
		self._request = None
		self.apiInstanceManager = ApiInstanceManager()

	def _generateError(self, message):
		trace("server", message)
		return ErrorPage(404, "Error", message).render(self._request)

	def render(self, request):
		trace("server render")
		self._request = request

		req = request.path.split('/')
		if len(req) != 3:
			return self._generateError("Bad request format")
		name = req[1]
		try:
			cid = int(req[2])
		except ValueError:
			return self._generateError("Channel id must be integer")
		try:
			db = self.apiInstanceManager.getApiInstance(name)
		except KeyError:
			return self._generateError("Provider not found")
		except APIException as e:
			return self._generateError("Provider cant start (%s)" % e)
		try:
			url = db.getStreamUrl(cid, None)
			return util.redirectTo(url, request)
		except APIException as e:
			return self._generateError("getStreamUrl failed (%s)" % e)


def startApiProxy(port=9001):
	trace("Start listening on port", port)
	try:
		reactor.listenTCP(port, Site(RedirectToStream()))
	except Exception as e:
		trace("listenTCP error:", e)
