
NAME
====

vt100.py - Parse a typescript and output text.


SYNOPSIS
========

``vt100.py [-q|-v] [-f FORMAT] [--non-script] typescript``


DESCRIPTION
===========

This module implements a VT100-style (ANSI) terminal emulator for the purpose
of parsing the output of script(1) file and printing to a human-readable
format.  The intent is to mimic the exact output of xterm(1), as though you
cut and pasted the output from the terminal.

This program can be used to parse any file containing ANSI (ECMA-48) terminal
codes.  Usually the input is a typescript file as output from script(1), which
are usually very unreadable.  Another potential use of this program to to
parse the output of a program that produces color codes (ESC [ # m) and
produce color HTML.

Output Formats
--------------

A number of output formats are available.  Currently, that number is two.

text
    The output is a pure ASCII file with unix line endings.  All character
    attributes are ignored (even 'hidden').

html
    The output is a snippet of HTML with one ``pre`` element.  Character
    attributes, including xterm 256 colors, are supported.


Unimplemented Features
----------------------

This module is designed to mimic the output (and only output) of xterm.
Therefore, there are no plans to implement any sequence that affects input,
cause the terminal to respond, or that xterm does not itself implement.


OPTIONS
=======

-f FORMAT, --format=FORMAT  Specify output format (see "Output Formats")
--non-script                Do not ignore "Script (started|done) on" lines
-q, --quiet                 Decrease debugging verbosity.
-v, --verbose               Increase debugging verbosity.
-h, --help                  Print help message.
--man                       Print manual page.


REQUIREMENTS
============

* Python 2.6
* Numpy


TODO
====

See TODO for things that are not yet implemented.  There are many.


NOTES
=====

For testing how a terminal implements a feature, the included *rawcat* program
may be helpful.  It acts like cat(1), except that it outputs the file
literally; it does not perform LF to CRLF translation.  Alternatively, one may
replace the LF (0x0a) character with VT (0x0b) or FF (0x0c), which are treated
identically but are not subject to newline translation.

A neat feature of *rawcat* is the ``-w`` option, which causes it to pause
after each output byte so you can observe xterm draw the screen.


AUTHOR
======

Mark Lodato <lodatom@gmail.com>


THANKS
======

Thanks to http://vt100.net for lots of helpful information, especially the
DEC-compatible parser page.

