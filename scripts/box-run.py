from __future__ import print_function
from subprocess import check_call
import json

if __name__ == "__main__":
	with open('secret.json') as f:
		box_ip = json.load(f)['box_ip']
	print("Kill enigma2...")
	check_call(["ssh", "root@%s" % box_ip, "/sbin/init", "2"])
	print("Start enigma2...")
	check_call(["ssh", "root@%s" % box_ip, "/usr/bin/enigma2.sh"])
