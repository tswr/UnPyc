.PHONY: deb deb-test tarball install remove doc tests

fast: deb reinstall

all: doc deb deb-test reinstall

deb:
	cd deb; \
	fakeroot ./mkdeb_core	

deb-test:
	cd deb; \
	lintian -i --pedantic unpyc_last.deb

install:
	sudo dpkg -i deb/unpyc_last.deb

remove:
	sudo dpkg -r unpyc

reinstall: remove install

doc:
	cd doc; \
	epydoc ../sources/UnPyc ../sources/unpyclib; \
	epydoc --check -v ../sources/UnPyc ../sources/unpyclib

tests:
	cd tests/all_opcodes; \
	perl test.pl
