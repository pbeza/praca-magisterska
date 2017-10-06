PYTHON=python3

.PHONY: all build dist list clean

all: build

build: setup.py
	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

dist: setup.py
	$(PYTHON) setup.py sdist

list:
	dpkg -c deb_dist/*.deb

clean:
	-$(PYTHON) setup.py clean --all
	-rm -rf deb_dist dist *.egg-info *.tar.gz
