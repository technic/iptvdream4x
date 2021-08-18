#!/usr/bin/python2

"""
read colors section from the skin header and replace all screens colors with explicit hex values
"""
from __future__ import print_function

import os
import sys
from xml.etree.ElementTree import ElementTree, Element, parse

coldict = {}


def search(element):
	for attr in element.keys():
		if attr.lower().find('color') > -1:
			# print('found color attribute', attr)
			oldcol = element.get(attr)
			if oldcol in coldict:
				element.set(attr, coldict[oldcol])
				# print('replace', oldcol, 'with', coldict[oldcol])
			else:
				# print('maybe good color', oldcol)
				pass
	for x in element:
		search(x)


def find_panel(name):
	for s in root.findall('screen'):
		if s.get('name') == name:
			return s
	raise Exception("Panel not found: %s" % name)


used_panels = set()


def replace_panel(s):
	for i, widget in enumerate(s):
		if widget.tag != 'panel':
			continue
		s.remove(widget)
		name = widget.get('name')
		used_panels.add(name)
		for child in find_panel(name):
			s.insert(i, child)


def load_include(inc):
	tree = parse(os.path.join(os.path.dirname(input_file), inc.get('filename')))
	return tree.findall('screen')


root = Element('skin')


def main():
	for element in parse(input_file).getroot():
		if element.tag == 'include':
			for s in load_include(element):
				root.append(s)
		else:
			root.append(element)

	for col in root.find('colors'):
		colname = col.get('name')
		colval = col.get('value')
		# print('Add color', colname, colval)
		coldict[colname] = colval

	for screen in root.findall('screen'):
		search(screen)
		replace_panel(screen)

	skin_root = Element('skin')
	for screen in root.findall('screen'):
		if not screen.get('name') in used_panels:
			skin_root.append(screen)

	ElementTree(skin_root).write(output_file)


if __name__ == "__main__":
	if not len(sys.argv) > 1:
		print('Specify input and output files!')
		print('usage: %s <infile> <outfile>' % sys.argv[0])
		sys.exit(1)

	input_file = sys.argv[1]
	output_file = sys.argv[2]
	main()
