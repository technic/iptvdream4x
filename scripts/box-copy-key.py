"""
Setup ssh access from virtual machine to box via key pair.
This will ask for password.
"""

from subprocess import check_call
import json

if __name__ == "__main__":
	with open('secret.json') as f:
		box_ip = json.load(f)['box_ip']
	check_call(["docker", "exec", "-it", "enigma2", "./box-copy-key.sh", box_ip])
