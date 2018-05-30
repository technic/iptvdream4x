#!/bin/bash
# run test script in docker
docker run -it -v `pwd`:/work technic93/e2xvfb sudo ./update-test.py
