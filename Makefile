PYTHON = python

.PHONY: all
all: install test

.PHONY: install
install:
	pip install numpy
	pip install .

.PHONY: test
test:
	$(PYTHON) -m unittest discover -s tests
