from glob import glob
from subprocess import check_call

if __name__ == "__main__":
	for playlist in glob("*.m3u") + glob("*.m3u8"):
		check_call(["docker", "cp", playlist, "enigma2:/etc/iptvdream"])
