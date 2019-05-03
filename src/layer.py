# -*- coding: utf-8 -*-

""" Abstraction layer for DMM and open enigma2 """

from __future__ import print_function

try:
	from enigma import eTimer as eTimerEnigma
except ImportError as ex:
	print("Assuming test environment due to exception:", ex)
	from tests.timer import eTimerTwisted as eTimerEnigma

if hasattr(eTimerEnigma, 'callback'):
	print("[IPtvDream] enigma2 SigC")
	enigma2Qt = False
	eTimer = eTimerEnigma
elif hasattr(eTimerEnigma, 'timeout'):
	print("[IPtvDream] enigma2 Qt")
	enigma2Qt = True

	class eTimer(eTimerEnigma):
		def __init__(self):
			eTimerEnigma.__init__(self)
			self.callback = []
			self.conn = self.timeout.connect(self.fire)

		def fire(self):
			for f in self.callback:
				f()

else:
	print("[IPtvDream] enigma2 Mock")
	enigma2Qt = False
	eTimer = eTimerEnigma


try:
	from enigma import BT_SCALE as SCALE
except ImportError as e:
	try:
		from enigma import SCALE_ASPECT as SCALE
	except ImportError as e:
		SCALE = 0
