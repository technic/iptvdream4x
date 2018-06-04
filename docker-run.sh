#!/bin/bash
# run test script in docker
docker run -it -v `pwd`:/work -e DESTDIR=/tmp/build technic93/e2xvfb:0.1 sudo -E python update-test.py
