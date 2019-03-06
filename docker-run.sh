#!/bin/bash
# run test script in docker
docker run -it -v "$(pwd)":/work -e DESTDIR=/tmp/build technic93/e2xvfb sudo -E python update-test.py
