PYTHON = python
PYTHON3 = python3
PYTHON26 = python2.6
PYTHON27 = python2.7
PYTHON31 = python3.1
PYTHON32 = python3.2

README.rst : vt100.py
	$(PYTHON) $^ --man > $@

testall : test26 test27 test31 test32

test :
	cd test && $(PYTHON) ./run_all.py

test3 :
	cd test && $(PYTHON3) ./run_all.py

test26 :
	cd test && $(PYTHON26) ./run_all.py

test27 :
	cd test && $(PYTHON27) ./run_all.py

test31 :
	cd test && $(PYTHON31) ./run_all.py

test32 :
	cd test && $(PYTHON32) ./run_all.py

.PHONY : test
