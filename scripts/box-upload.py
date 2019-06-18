"""
Builds ipk package in docker and uploads it to device.
You need to specify device ip address in ./secret.json file.
"""

from subprocess import check_call
import json

if __name__ == "__main__":
	with open('secret.json') as f:
		box_ip = json.load(f)['box_ip']
	check_call(["docker", "exec", "-it", "enigma2", "./box-upload.sh", box_ip, "cbilling"])
