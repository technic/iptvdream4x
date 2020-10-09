"""
Builds ipk package in docker and uploads it to device.
You need to specify device ip address in ./secret.json file.
"""

from subprocess import check_call
import os
import json

if __name__ == "__main__":

	provider = "all"
	build_dir = "/tmp/iptvdream-build"

	check_call(["docker", "exec", "-it", "enigma2", "rm", "-rf", build_dir])

	make = [
		"docker", "exec", "-it",
		"-e", "PROVIDER=%s" % provider,
		"-e", "DESTDIR=%s" % build_dir,
		"enigma2", "make"
	]

	check_call(make + ["info"])

	with open('info.json') as f:
		data = json.load(f)
		ipk = "packages/%s_%s_all.ipk" % (data['name'], data['version'])

	os.remove(ipk)
	check_call(make + [ipk])
	assert os.path.isfile(ipk)

	with open('secret.json') as f:
		box_ip = json.load(f)['box_ip']

	# On windows I have scp and ssh as bat symlinks, they require shell=True
	check_call(["scp", ipk, "root@%s:/tmp/test.ipk" % box_ip], shell=True)
	check_call(["ssh", "root@%s" % box_ip, "opkg install --force-reinstall /tmp/test.ipk"], shell=True)
