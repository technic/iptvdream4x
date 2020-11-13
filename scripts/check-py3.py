from __future__ import print_function

import sys
import py_compile
import glob


def check(f):
	print('check', f)
	py_compile.compile(f)


def main():
	print("Python", sys.version)
	files = glob.glob("src/*.py") + glob.glob("src/**/*.py")
	for f in files:
		check(f)


if __name__ == "__main__":
	main()
