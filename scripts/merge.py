from __future__ import print_function

from subprocess import check_call
import sys
import re

if __name__ == '__main__':
	provider = sys.argv[1]
	check_call(['git', 'checkout', provider])
	check_call(['git', 'merge', 'master'])
	with open('src/dist.py') as f:
		lines = f.readlines()
	ver = None
	r = re.compile(r'^\s*VERSION\s*=\s*"(.*)"$')
	for line in lines:
		m = r.match(line)
		if m:
			ver = m.group(1)
			print("Current version", list(map(int, ver.split('.'))))
	assert ver is not None, "Failed to determine version"
	check_call(['git', 'tag', '-a', '%s/v/%s' % (provider, ver), '-m', 'bump version'])
