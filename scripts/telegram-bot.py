#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import re
import requests


def check_readme():
	changelog = []
	copying = False
	r = re.compile(r'^# (\d+\.\d+)\s+$')
	with open("README.md") as f:
		lines = f.readlines()
		for line in lines:
			if r.match(line):
				if copying:
					break
				copying = True
				changelog.append(line.rstrip())
			elif line.startswith('#'):
				if copying:
					break
			elif copying:
				line = line.rstrip()
				if line:
					changelog.append(line)
	if not changelog:
		raise Exception("Please provide release notes")
	return '\n'.join(changelog)


if __name__ == "__main__":
	text = check_readme()
	url = os.environ['BOT_URL']
	chat_id = os.environ['BOT_CHAT']
	r = requests.post(url, {
		"chat_id": chat_id,
		"text": text
	})
	r.raise_for_status()
	print("Message sent.")
