# -*- coding: utf-8 -*-
#  enigma2 iptv player
#
#  Copyright (c) 2010 Alex Maystrenko <alexeytech@gmail.com>
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.

from __future__ import print_function

from .api1 import TeleportStream


# This is Raduga clone with own branding

class OTTProvider(TeleportStream):
	NAME = "PureTV"
	site = "http://core.raduga.tv/iptv/api/v1/json"
