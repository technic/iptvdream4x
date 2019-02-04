from subprocess import call, check_call

if __name__ == "__main__":
    call(["docker", "exec", "enigma2_box", "sudo", "killall", "enigma2"])
    check_call(["docker", "exec",
                "-e", "DISPLAY=:99",
                "-e", "ENIGMA_DEBUG_LVL=5",
                "enigma2_box", "sudo", "-E", "enigma2"])
