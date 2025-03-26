PYTHON = python

TESTS = tests/test_api.py tests/test_rtrace.py tests/test_bsdf.py tests/test_rcontrib.py

.PHONY: all
all: build

.PHONY: build
build:
	pip install .

.PHONY: test
test:
	$(PYTHON) -m unittest -v $(TESTS)
