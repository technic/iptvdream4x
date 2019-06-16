#!/bin/bash
# run test script in docker
export MSYS_NO_PATHCONV=1
docker run -v "$(pwd)":/work -e DESTDIR=/tmp/build technic93/e2xvfb sudo -E python update-test.py
