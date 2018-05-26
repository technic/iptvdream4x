#!/usr/bin/python2
import sys
if not len(sys.argv) > 1:
    print("Specify input file!")
    print('usage: skinfix.exe infile outfile')
    sys.exit(1)

from xml.etree.ElementTree import ElementTree, Element

infile = open(sys.argv[1])
#text = infile.read()
root = ElementTree()
root.parse(infile)
colors = root.find('colors')
coldict = {}
for col in colors:
    colname = col.get('name')
    colval = col.get('value')
    print('Add color', colname, colval)
    coldict[colname] = colval

def search(element):
    for atr in element.keys():
        if atr.lower().find('color') > -1:
            print('found color attribute', atr)
            oldcol = element.get(atr)
            if coldict.has_key(oldcol):
                element.set(atr, coldict[oldcol])
                print('replace', oldcol, 'with', coldict[oldcol])
            else:
                print('maybe good color', oldcol)
                pass
    for x in element:
        print(x)
        search(x)

skin_root = Element('skin')
for x in root.findall('screen'):
    print(x)
    search(x)
    skin_root.append(x)

if len(sys.argv) > 2:
    outfile = sys.argv[2]
else:
    outfile = 'kartina_skin.xml'
    from os.path import exists
    if exists(outfile):
        from shutil import copy
        copy(outfile, outfile+'.backup')
            

ElementTree(skin_root).write(outfile)
