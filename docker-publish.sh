#!/bin/bash
VERSION=0.1
docker build . -t technic93/e2xvfb:${VERSION}
docker push technic93/e2xvfb:${VERSION}
