#!/bin/bash
export MSYS_NO_PATHCONV=1
docker run -v "$(pwd):/work" -e PYTHONPATH=/work/src e2full:latest /usr/bin/trial $@
