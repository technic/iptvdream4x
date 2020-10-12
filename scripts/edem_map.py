#!/usr/bin/env python2

"""Extract maping from channel id to tvg-id and tvg-logo defined in m3u playlist"""

from __future__ import print_function

import re
import requests
import json


def parsePlaylist(lines):
	name = ""
	group = "Unknown"
	logo = ""
	tvg = None
	rec = False

	tvg_regexp = re.compile('#EXTINF:.*tvg-id="([^"]*)"')
	group_regexp = re.compile('#EXTINF:.*group-title="([^"]*)"')
	logo_regexp = re.compile('#EXTINF:.*tvg-logo="([^"]*)"')
	rec_regexp = re.compile('#EXTINF:.*tvg-rec="([^"]*)"')
	catchup_regexp = re.compile('#EXTINF:.*catchup-days="([^"]*)"')

	import codecs
	if lines:
		if lines[0].startswith(codecs.BOM_UTF8):
			lines[0] = lines[0][3:]

	for line in lines:
		if line.startswith("#EXTINF:"):
			name = line.strip().split(',')[1]
			m = tvg_regexp.match(line)
			if m:
				tvg = m.group(1)
			else:
				tvg = None
			m = group_regexp.match(line)
			if m:
				group = m.group(1)
			m = logo_regexp.match(line)
			if m:
				logo = m.group(1)
			else:
				logo = ""
			m = rec_regexp.match(line)
			if m:
				rec = m.group(1) == "1"
			else:
				m = catchup_regexp.match(line)
				if m:
					rec = m.group(1) != "0"
				else:
					rec = False
		elif line.startswith("#EXTGRP:"):
			group = line.strip().split(':')[1]
		elif line.startswith("#"):
			continue
		elif not line.strip():
			continue
		else:
			url = line.strip()
			assert url.find("://") > 0, "line: " + url
			yield {
				'name': name,
				'group': group,
				'url': url,
				'tvg-id': tvg,
				'tvg-logo': logo,
				'rec': rec
			}


def main(outfile):
	print("Saving playlist mapping to", outfile)
	req = requests.get('http://epg.it999.ru/edem_epg_ico.m3u8')
	lines = req.content.split('\n')

	url_regexp = re.compile(r"https?://[\w.]+/iptv/\w+/(\d+)/index.m3u8")
	result = {}
	for item in parsePlaylist(lines):
		m = url_regexp.match(item['url'])
		if not m:
			print('Bad url', item['name'])
			continue
		cid = m.group(1)
		result[cid] = {
			'tvg-id': item['tvg-id'],
			'tvg-logo': item['tvg-logo'],
		}

	with open(outfile, 'w') as f:
		json.dump(result, f)


if __name__ == "__main__":
	import sys
	main(sys.argv[1])
