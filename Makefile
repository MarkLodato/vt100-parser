PYTHON = python

README.rst : vt100.py
	$(PYTHON) $^ --man > $@

test :
	cd test && $(PYTHON) ./run_all.py

.PHONY : test
