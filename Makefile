README.rst : vt100.py
	python $^ --man > $@

test :
	cd test && ./run_all.py

.PHONY : test
