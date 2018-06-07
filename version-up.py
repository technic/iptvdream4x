#!/usr/bin/env python

""" Increase version and commit changes to git """

from __future__ import print_function

import subprocess
import re
import sys

versionFile = "src/dist.py"

if __name__ == "__main__":
	subprocess.check_call(['git', 'reset'])
	c = subprocess.call(['git', 'diff', '--exit-code', '--', versionFile])
	if c != 0:
		print("Aborted because %s has modifications!" % versionFile)
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
					ver = map(int, ver.split('.'))
					nextVer = ver
					nextVer[1] += 1
					lines[i] = 'VERSION = "%s"' % '.'.join(map(str, nextVer))
					print("Update to", lines[i])

		with open(versionFile, 'w') as f:
			f.writelines(lines)
			f.write('\n')

		assert nextVer is not None

		subprocess.check_call(['git', 'add', versionFile])
		ver = '.'.join(map(str, nextVer))
		subprocess.check_call(['git', 'commit', '-m', 'version up %s' % ver])
		subprocess.check_call(['git', 'tag', '-a', 'v/%s' % ver, '-m', 'version up %s' % ver])

	print("Done.")
