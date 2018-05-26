# -*- coding: utf-8 -*-

"""
Localization
"""

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import gettext


def localeInit():
	lang = language.getLanguage()[:2]  # getLanguage returns e.g. "en_US" for "language_country"
	os.environ["LANGUAGE"] = lang  # enigma2 doesn't set this (or LC_ALL, LC_MESSAGES, LANG), but gettext needs it!
	gettext.bindtextdomain("IPtvDream", resolveFilename(SCOPE_PLUGINS, "Extensions/IPtvDream/locale"))


def translate(txt):
	t = gettext.dgettext("IPtvDream", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)
