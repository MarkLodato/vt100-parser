#!/usr/bin/python
"""
Run all of the t????-*.in tests in the current directory and compare with the
expected output.
"""

from __future__ import print_function

import sys, os
import glob
import difflib
from subprocess import Popen, PIPE

PROG = '../vt100.py'
IN_EXT = '.in'
FORMATS = ['text', 'html']

def slurp(filename):
    with open(filename, 'rb') as f:
        return f.read().decode('ascii')

def compare_output(command, out_filename):
    try:
        expected = slurp(out_filename)
    except IOError as e:
        if e.errno == 2:
            print("%s not found" % out_filename, file=sys.stderr)
            return False
        else:
            raise
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, stderr = p.communicate()
    output = output.decode('ascii')
    stderr = stderr.decode('utf-8')
    if p.returncode != 0 or stderr:
        print("program returned %d:" % p.returncode)
        print('\x1b[33m%s\x1b[m' % stderr, end='')
        return False
    elif output == expected:
        return True
    else:
        lines = difflib.unified_diff(expected.split('\n'), output.split('\n'),
                fromfile=out_filename, tofile=' '.join(command), lineterm='')
        for line in lines:
            if line[0] == '+':
                print('\x1b[32m' + line[1:] + '\x1b[0m')
            elif line[0] == '-':
                print('\x1b[31m' + line[1:] + '\x1b[0m')
            elif line[0] == '@':
                print('\x1b[36m' + line + '\x1b[0m')
            elif line[0] == ' ':
                print(line[1:])
            else:
                print(line)
        print('\n'.join(lines))
        return False

def test(test_name, fmt):
    out_filename = '%s.%s' % (test_name, fmt)
    if os.path.exists(out_filename):
        command = [sys.executable, PROG, test_name + IN_EXT, '-f', fmt]
        return compare_output(command, out_filename)

def test_all(tests):
    results = []
    for filename in tests:
        if filename.endswith(IN_EXT):
            filename = filename[:-3]
        for fmt in FORMATS:
            testname = '%s.%s' % (filename, fmt)
            r = test(filename, fmt)
            if r is None: continue
            results.append((testname, r))
            msg = ' \x1b[32mOK\x1b[0m ' if r else '\x1b[31mFAIL\x1b[0m'
            print('%-60s [%s]' % (testname, msg))

    return results

def main(patterns = None):
    if not patterns:
        tests = glob.glob('t????-*' + IN_EXT)
        tests.sort()
    else:
        tests = patterns
    r = test_all(tests)
    return int(not all(x[1] for x in r))

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(2)
