#!/bin/bash
# run test script in docker
docker run -it -v `pwd`:/work technic93/e2xvfb:0.1 python update-test.py
