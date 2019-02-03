from subprocess import check_call

if __name__ == "__main__":
    # You should have Xming running on your host machine
    check_call(["docker", "exec", "-i",
                "-e", "DISPLAY=:99",
                "-e", "ENIGMA_DEBUG_LVL=5",
                "enigma2_box", "sudo", "-E", "enigma2"])
