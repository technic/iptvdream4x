#!/usr/bin/python2

"""
read colors section from the skin header and replace all screens colors with explicit hex values
"""

import sys
from xml.etree.ElementTree import ElementTree, Element

if not len(sys.argv) > 1:
    print('Specify input and output files!')
    print('usage: %s <infile> <outfile>' % sys.argv[0])
    sys.exit(1)

infile = open(sys.argv[1])
root = ElementTree()
root.parse(infile)
colors = root.find('colors')
coldict = {}

for col in colors:
    colname = col.get('name')
    colval = col.get('value')
    # print('Add color', colname, colval)
    coldict[colname] = colval


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


skin_root = Element('skin')
for screen in root.findall('screen'):
    search(screen)
    skin_root.append(screen)

ElementTree(skin_root).write(sys.argv[2])
