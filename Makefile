PYTHON := python2.7
ARCH := all
DESTDIR ?= build
PACKAGEDIR ?= packages
DEB ?= n
UPDATE_PO ?= n
PROVIDER ?= all

plugin_name := IPtvDream
plugin_path := /usr/lib/enigma2/python/Plugins/Extensions/$(plugin_name)
skin_path := /usr/share/enigma2/$(plugin_name)

ifeq ($(DEB),y)
pkgext := deb
else
pkgext := ipk
endif
architecture := $(ARCH)

build := $(DESTDIR)
plugindir = $(build)$(plugin_path)
skindir = $(build)$(skin_path)

all: package

pyfiles := src/__init__.py src/common.py src/dist.py src/plugin.py src/updater.py \
	src/layer.py src/loc.py src/utils.py src/manager.py src/main.py src/settings.py \
	src/standby.py src/virtualkb.py src/server.py \
	src/lib/__init__.py src/lib/epg.py \
	src/api/__init__.py src/api/abstract_api.py
datafiles := src/keymap_enigma.xml src/keymap_neutrino.xml src/IPtvDream.png

ifeq ($(PROVIDER),all)
pyfiles += src/api/api1.py src/api/teleprom.py src/api/raduga.py src/api/amigo.py src/api/emigranttv.py \
	src/api/pure.py \
	src/api/m3u.py src/api/edem_soveni.py src/api/edem_yahan.py src/api/ottclub.py src/api/shura.py \
	src/api/iptv-e2_soveni.py \
	src/api/kartina.py src/api/ktv.py \
	src/api/mywy.py src/api/naschetv.py src/api/ozo.py src/api/sovok.py src/api/baltic.py
datafiles += $(wildcard src/logo/*.png)
endif

pyext := pyo
pyinstall := $(pyfiles:src/%=$(plugindir)/%)
pycinstall := $(pyinstall:.py=.$(pyext))

$(pyinstall): $(plugindir)/%.py: src/%.py
	install -D -m644 $< $@

$(pycinstall): $(plugindir)/%.$(pyext): src/%.py
	install -d $(dir $@)
	$(PYTHON) -c 'import py_compile; py_compile.compile("$<", "$@")'


datainstall := $(patsubst src/%,$(plugindir)/%,$(datafiles))

$(datainstall): $(plugindir)/%: src/%
	install -D -m644 $< $@


skinfiles := $(shell find skin/ -name *.png) skin/iptvdream.xml
skininstall := $(patsubst skin/%,$(skindir)/%,$(skinfiles))

$(skininstall): $(skindir)/%: skin/%
	install -D -m644 $< $@

skin/iptvdream.xml: skin/skin.xml
	python skin-post.py $< $@

prepare: skin/iptvdream.xml


$(build)/etc/iptvdream/iptvdream.epgmap: src/iptvdream.epgmap
	install -D -m644 $^ $@


langs := ru en de

langs_po := $(addprefix po/,$(langs))
langs_po := $(addsuffix .po,$(langs_po))

moinstall := $(addprefix $(plugindir)/locale/,$(langs))
moinstall := $(addsuffix /LC_MESSAGES/IPtvDream.mo,$(moinstall))

$(moinstall): $(plugindir)/locale/%/LC_MESSAGES/$(plugin_name).mo: po/%.po
	install -d $(dir $@)
	msgfmt -o $@ $<

po/$(plugin_name).pot: $(pyfiles)
	xgettext -L python --from-code=UTF-8 -d $(plugin_name) -s -o $@ $^

ifeq ($(UPDATE_PO),y)

%.po: po/$(plugin_name).pot
	(! test -f $@) \
	&& msginit -l $@ -o $@ -i $< --no-translator \
	|| msgmerge --backup=none --no-location -s -N -U $@ $< \
	&& touch $@

endif

update-po:
	$(MAKE) UPDATE_PO=y $(langs_po)


#install: $(build)/etc/iptvdream/iptvdream.epgmap
install: $(pycinstall) $(datainstall) $(skininstall) $(moinstall)
	install -d $(build)/etc/iptvdream


version: src/dist.py
	mkdir -p $(dir $@)
	test  `cat $< |sed -n 's/^\s*NAME\s*=\s*"\(.*\)"$$/\1/p'` = '$(PROVIDER)'
	cat $< |sed -n 's/^\s*VERSION\s*=\s*"\(.*\)"$$/version=\1/p' > $@

include version

name := enigma2-plugin-extensions-$(shell echo $(plugin_name)-$(PROVIDER) | tr A-Z a-z)
provider := $(shell echo $(PROVIDER) |tr A-Z a-z)
pkgname := $(name)_$(version)_$(architecture)

controldir := DEBIAN

$(build)/DEBIAN/control: $(controldir)/control version
	install -d $(dir $@)
	cp $< $@
	sed -i $@ -e "s/^Package:.*/Package: $(name)/"
	sed -i $@ -e "s/^Version:.*/Version: $(version)/"
	sed -i $@ -e "s/^Architecture:.*/Architecture: $(architecture)/"

hooks := $(filter-out $(controldir)/control, $(wildcard $(controldir)/*))
hooks := $(patsubst $(controldir)/%, $(build)/DEBIAN/%, $(hooks))

$(hooks): $(build)/DEBIAN/%: $(controldir)/%
	install -m 755 $< $@


pkgdir := $(PACKAGEDIR)

$(pkgdir)/$(pkgname).$(pkgext): install $(build)/DEBIAN/control $(hooks)
	@ ! test -f "$@" || (echo "Error: package $(pkgname).$(pkgext) already exists"; false)
	mkdir -p $(pkgdir)
	dpkg-deb -b -Zgzip $(build) tmp.deb
	mv tmp.deb $@
	echo '$(version)' > $(pkgdir)/version-$(provider).txt

package: $(pkgdir)/$(pkgname).$(pkgext) info

info:
	echo '{"name": "$(name)"}' > $@.json

sshinstall: $(pkgdir)/$(pkgname).$(pkgext)
	test -n '$(HOST)'
	wput -u -nc -nv $< ftp://root@$(HOST)/tmp/$(notdir $<)
	ssh root@$(HOST) opkg install --force-reinstall /tmp/$(notdir $<)


clean:
	rm -rf build
	rm -f version

.PHONY: prepare install package info update-po clean
