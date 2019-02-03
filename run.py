from subprocess import check_call

if __name__ == "__main__":
    # You should have Xming running on your host machine
    check_call(["docker", "exec", "-i", "-e", "DISPLAY=host.docker.internal:0.0", "enigma2_box", "enigma2"])
