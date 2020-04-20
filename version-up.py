#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Increase version and commit changes to git """

from __future__ import print_function

import subprocess
import re
import sys

versionFile = "src/dist.py"
readmeFile = "README.md"


def check_readme(version):
	version = '.'.join(map(str, version))
	changelog = []
	copying = False
	r = re.compile(r'^## %s\s+$' % version)
	with open(readmeFile) as f:
		lines = f.readlines()
		for line in lines:
			if r.match(line):
				copying = True
			elif line.startswith('#'):
				copying = False
			elif copying:
				line = line.rstrip()
				if line:
					changelog.append(line)
	if not changelog:
		raise Exception("Please provide release notes for version %s" % version)

	changelog = "\n".join(["[size=18pt]Версия %s[/size]" % version] + changelog)
	print("\nChangelog bb:")
	print(changelog)
	return changelog


def clip(s):
	subprocess.Popen(['clip'], stdin=subprocess.PIPE).communicate(s)
	print("Copied to clipboard")


if __name__ == "__main__":
	subprocess.check_call(['git', 'reset'])
	c = subprocess.call(['git', 'diff', '--exit-code', '--', versionFile, readmeFile])
	if c != 0:
		print("Aborted because %s or %s has modifications!" % (versionFile, readmeFile))
		sys.exit(1)
	else:
		nextVer = None
		with open(versionFile, 'r') as f:
			lines = f.readlines()
			r = re.compile(r'^\s*VERSION\s*=\s*"(.*)"$')
			for i, line in enumerate(lines):
				m = r.match(line)
				if m:
					ver = m.group(1)
					print("Current version", ver)
					ver = list(map(int, ver.split('.')))
					nextVer = ver
					nextVer[1] += 1
					lines[i] = 'VERSION = "%s"' % '.'.join(map(str, nextVer))
					print("Update to", lines[i])

		log = check_readme(nextVer)

		with open(versionFile, 'w') as f:
			f.writelines(lines)
			f.write('\n')

		assert nextVer is not None

		subprocess.check_call(['git', 'add', versionFile])
		ver = '.'.join(map(str, nextVer))
		subprocess.check_call(['git', 'commit', '-m', 'version up %s' % ver])
		subprocess.check_call(['git', 'tag', '-a', 'v/%s' % ver, '-m', 'version up %s' % ver])
		subprocess.check_call(['git', 'push'])

	print("Done.\n")

	if sys.platform == 'win32':
		clip(log)
		import json
		with open('secret.json') as f:
			url = json.load(f)['forum']
		subprocess.call(["C:/Program Files/Mozilla Firefox/firefox.exe", url])
