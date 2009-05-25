#!/usr/bin/python
"""
Run all of the t????-*.in tests in the current directory and compare with the
expected output.
"""

import sys, os
import glob
from subprocess import Popen, PIPE

PROG = ['../vt100.py']

def slurp(filename):
    with open(filename, 'rb') as f:
        return f.read()

def compare_output(command, out_filename):
    try:
        expected = slurp(out_filename)
    except IOError as e:
        if e.errno == 2:
            print >>sys.stderr, "%s not found" % out_filename
            return False
        else:
            raise
    output = Popen(command, stdout=PIPE).communicate()[0]
    if output == expected:
        return True
    else:
        # TODO print difference
        return False

def test(test_name):
    if test_name.endswith('.in'):
        test_name = test_name[:-3]
    command = PROG + [test_name + '.in']
    out_filename = test_name + '.text'
    return compare_output(command, out_filename)

def test_all():
    results = []
    tests = glob.glob('t????-*.in')
    tests.sort()
    for filename in tests:
        if filename.endswith('.in'):
            filename = filename[:-3]
        r = test(filename)
        results.append((filename, r))
        msg = ' \x1b[32mOK\x1b[0m ' if r else '\x1b[31mFAIL\x1b[0m'
        print '%-60s [%s]' % (filename, msg)

    return results


if __name__ == "__main__":
    r = test_all()
    if not all(x[1] for x in r):
        sys.exit(1)
