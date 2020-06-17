"""
Resizes widgets: size, position, fonts
"""

from __future__ import print_function

from lxml.etree import ElementTree

RATIO = 1080./720.


def fix_itemHeight(val):
	try:
		h = int(val)
		h = int(round(h * RATIO))
		return "%s" % h
	except ValueError:
		return val


def fix_size(val):
	try:
		x, y = val.split(',')
	except ValueError:
		return val
	try:
		x = int(round(int(x) * RATIO))
	except ValueError:
		pass
	try:
		y = int(round(int(y) * RATIO))
	except ValueError:
		pass
	return "%s,%s" % (x, y)


def fix_font(val):
	try:
		font, sz = val.split(';')
		sz = int(round(int(sz) * RATIO))
		return "%s;%s" % (font, sz)
	except ValueError:
		return val


def process(element):
	# print(element.items())
	for attr in element.keys():
		val = element.get(attr)
		if attr in ('position', 'size'):
			element.set(attr, fix_size(val))
		if attr.lower().endswith('font'):
			element.set(attr, fix_font(val))
	# print(element.items())


def main(input_file, output_file):
	root = ElementTree().parse(input_file)
	for screen in root.findall('screen'):
		print("====", screen.get('name'))
		process(screen)
		for widget in screen:
			process(widget)
	ElementTree(root).write(output_file)


if __name__ == "__main__":
	import sys
	if not len(sys.argv) == 3:
		print('Specify input and output files!')
		print('usage: %s <infile> <outfile>' % sys.argv[0])
		sys.exit(1)
	main(sys.argv[1], sys.argv[2])
