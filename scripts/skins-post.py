#!/usr/bin/env python

"""
Postprocess all skins
"""

from __future__ import print_function

import os
from subprocess import check_call


if __name__ == "__main__":
	for s in ["skin", "skin-contrast", "skin-fhd", "skin-fhd-contrast"]:
		print("Processing", s)
		check_call(["python", "skin-post.py", os.path.join(s, "skin.xml"), os.path.join(s, "iptvdream.xml")])
