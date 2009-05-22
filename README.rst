
NAME
====

vt100.py - A virtual terminal emulator.


SYNOPSIS
========

vt100.py [-q|-v] [--non-script] typescript


DESCRIPTION
===========

This module implements a VT100-style (ANSI) terminal emulator.  The intent is
to parse the output of script(1) and display it in a human-readable form.  The
output will eventually include ASCII, VT100, and HTML.  Currently, only ASCII
(no color) is supported.


REQUIREMENTS
============

* Python 2.6
* Numpy


AUTHOR
======

Mark Lodato <lodatom@gmail.com>


THANKS
======

Thanks go to http://vt100.net for lots of helpful information, especially the
DEC-compatible parser page.

