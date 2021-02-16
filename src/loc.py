# -*- coding: utf-8 -*-

"""
Localization
"""

import os
import gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


def localeInit():
	lang = language.getLanguage()[:2]  # getLanguage returns e.g. "en_US" for "language_country"
	os.environ["LANGUAGE"] = lang  # enigma2 doesn't set this (or LC_ALL, LC_MESSAGES, LANG), but gettext needs it!
	gettext.bindtextdomain("IPtvDream", resolveFilename(SCOPE_PLUGINS, "Extensions/IPtvDream/locale"))


def translate(text):
	t = gettext.dgettext("IPtvDream", text)
	if t == text:
		t = gettext.gettext(text)
	return t


localeInit()
language.addCallback(localeInit)
