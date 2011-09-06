
NAME
====

vt100.py - Parse a typescript and output text.


SYNOPSIS
========

``vt100.py [OPTIONS] [-f FORMAT] [-g WxH] (filename|-)``


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
causes the terminal to respond, or that xterm does not itself implement.


OPTIONS
=======

-h, --help                  print help message and exit
--man                       print manual page and exit
--version                   print version number and exit
-f FORMAT, --format=FORMAT  specify output format (see "Output Formats")
-g WxH, --geometry=WxH      specify console geometry (see "Configuration")
--non-script                do not ignore "Script (started|done) on" lines
--rc=FILE                   read configuration from FILE (default ~/.vt100rc)
--no-rc                     suppress reading of configuration file
-q, --quiet                 decrease debugging verbosity
-v, --verbose               increase debugging verbosity


CONFIGURATION
=============

By default, vt100.py reads ~/.vt100rc for the following 'key = value` pairs.
COLOR is any valid HTML color.  The order does not matter, except that all the
settings following ``[SECTION]`` belong to a specific section.

background = COLOR
    Default background color.

color0 = COLOR ...through... color255 = COLOR
    Color for the 8 ANSI colors (0-7), 8 bright ANSI colors (8-15), and xterm
    extended colors (16-255).

colorscheme = SECTION
    Import settings from [SECTION] before any in the current section.

format = {text, html}
    Default output format.  Default is 'text'.

foreground = COLOR
    Default foreground color.

geometry = {WxH, detect}
    Use W columns and H rows in output.  If the value 'detect' is given, the
    current terminal's geometry is detected using ``stty size``.
    Default is '80x24'.

inverse_bg = COLOR
    Background color to use for the "inverse" attribute when neither the
    character's foreground color attribute nor the ``foreground`` option is
    set.  Default is 'black'.

inverse_fg = COLOR
    Foreground color to use for the "inverse" attribute when neither the
    character's background color attribute nor the ``background`` option is
    set.  Default is 'white'.

verbosity = INT
    Act as those ``-v`` or ``-q`` was given abs(INT) times, if INT positive or
    negative, respectively.  Default is '0'.

[SECTION]
    Start a definition of a color scheme named SECTION.


REQUIREMENTS
============

* Python 2.6+ or 3.0+ (tested on 2.6, 2.7, 3.0, and 3.1)


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


SEE ALSO
========

script(1), scriptreplay(1)


AUTHOR
======

Mark Lodato <lodatom@gmail.com>


THANKS
======

Thanks to http://vt100.net for lots of helpful information, especially the
DEC-compatible parser page.

