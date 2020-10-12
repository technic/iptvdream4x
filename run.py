"""
Python script which runs docker exec command
I use it as a launcher for PyCharm Comunity Edition
"""

from subprocess import call, check_call

if __name__ == "__main__":
    call(["docker", "exec", "enigma2", "killall", "-9", "enigma2"])
    check_call(["docker", "exec",
                "-e", "ENIGMA_DEBUG_LVL=5",
                "enigma2", "/usr/bin/enigma2"])
