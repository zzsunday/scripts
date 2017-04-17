package_name = geo-omics-scripts
version = $(strip $(shell cat VERSION))

export
.SILENT:

prefix = 
datadir = $(prefix)/share
docdir = $(datadir)/doc
bindir = $(prefix)/bin
mandir = $(datadir)/man
man1dir = $(mandir)/man1
man5dir = $(mandir)/man5
man7dir = $(mandir)/man7

EXTRA_DIST = \
	COPYRIGHT \
	docs \
	Makefile \
	modulefiles \
	README.md \
	VERSION

doc_files = COPYRIGHT README.md

dist_dir = $(package_name)-$(version)
tarball = $(dist_dir).tar.gz
html_dirs = \
		  html \
		  html/_sources \
		  html/_static \
		  html/_static/fonts \
		  html/_static/css \
		  html/_static/js \


INSTALL = /usr/bin/install
INSTALL_PROGRAM = $(INSTALL)
INSTALL_DATA = $(INSTALL) -m 644

all: sphinx-docs scripts-man

sphinx-docs:
ifeq ($(shell hostname),csheikMP)
	cd docs && $(MAKE) html man
else
	@echo "-- skipping sphinx-based documentation --"
endif

scripts-man:
	cd scripts && $(MAKE) man

# version arithmetic
major_version = $(word 1,$(subst ., ,$(version)))
minor_version = $(word 2,$(subst ., ,$(version)))
patch_version = $(word 3,$(subst ., ,$(version)))
inc_patch_version = $(shell echo $(patch_version)+1 | bc)
inc_version = $(major_version).$(minor_version).$(inc_patch_version)

distdir:
	mkdir -p -- "$(dist_dir)"
	cd lib && $(MAKE) $@
	cd scripts && $(MAKE) $@
	$(info Copying extra files ...)
	cp -a $(EXTRA_DIST) $(dist_dir)

dist: distdir
	$(info Creating $(dist_dir).tar.gz)
	tar czhf $(dist_dir).tar.gz $(dist_dir)
	$(info Cleaning up temporary dist directory ...)
	$(RM) -r -- "$(dist_dir)"
release: dist
	$(info Incrementing minor version to $(inc_version))
	$(info ${shell echo $(inc_version) > VERSION})

# install sphinx-generated docs and file in doc_files
install-docs: dest = $(DESTDIR)$(docdir)/$(package_name)
ifeq ($(shell hostname),csheikMP)
install-docs: html_dirs = $(shell cd docs/_build && find html -type d)
install-docs: html_files = $(shell cd docs/_build && find html -type f)
endif
install-docs:
	$(info Creating directories ...)
	mkdir -p -- "$(dest)"
ifeq ($(shell hostname),csheikMP)
	for i in $(html_dirs); do mkdir -p -- "$(dest)/$$i"; done
	$(info Installing html files ...)
	for i in $(html_files); do $(INSTALL_DATA) "docs/_build/$$i" $(dest)/$$(dirname $$i); done
	$(info Installing manual page ...)
	mkdir -p -- "$(DESTDIR)$(man7dir)"
	$(INSTALL_DATA) docs/_build/man/geomics.7 $(DESTDIR)$(man7dir)
endif
	$(info Installing other documentation ...)
	$(INSTALL_DATA) $(doc_files) $(dest)

install: install-docs
	cd lib && $(MAKE) install
	cd scripts && $(MAKE) install

uninstall:
	$(info Removing documentation...)
	$(RM) -r -- $(DESTDIR)/$(docdir)/$(package_name)
	$(info Removing package data...)
	$(RM) -r -- $(DESTDIR)/$(datadir)/$(package_name)
	cd scripts && $(MAKE) $@

clean:
	$(info Cleaning sphinx-generated documentation ...)
ifeq ($(shell hostname),csheikMP)
	cd docs && $(MAKE) clean
endif
	cd scripts && $(MAKE) clean

distclean: clean
	$(info Removing tarballs ...)
	$(RM) -- $(package_name)-*.tar.gz

debug:
	$(info "share: $(datadir) bin: $(bindir)")
	$(info Version: $(version))
	$(info "patch versions: $(patch_version) $(inc_patch_version)")
	$(info incremented version: $(inc_version))

.PHONY: all sphinx-docs distdir dist release scripts-man vondamm-install vondamm-clean remote-install remote-clean install-docs install clean distclean debug
