PYTHON = python
PYTHON3 = python3

README.rst : vt100.py
	$(PYTHON) $^ --man > $@

test :
	cd test && $(PYTHON) ./run_all.py

test3 :
	cd test && $(PYTHON3) ./run_all.py

.PHONY : test
