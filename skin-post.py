#!/usr/bin/python2

"""
read colors section from the skin header and replace all screens colors with explicit hex values
"""
from __future__ import print_function

import sys
from xml.etree.ElementTree import ElementTree, Element


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


if __name__ == "__main__":
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

    skin_root = Element('skin')
    for screen in root.findall('screen'):
        search(screen)
        replace_panel(screen)

    for screen in root.findall('screen'):
        if not screen.get('name') in used_panels:
            skin_root.append(screen)

    ElementTree(skin_root).write(sys.argv[2])
