#!/usr/bin/env python

# Requires Python 2.6

import sys, os
import re
import numpy as np


__metaclass__ = type


class Character:
    """A single character along with an associated attribute."""
    def __init__(self, char, attr = None):
        self.char = char
        self.attr = attr
    def __repr__(self):
        return str(self.char)

class InvalidParameterListError (RuntimeError):
    pass

def param_list(s, default, zero_is_default=True, min_length=1):
    """Return the list of integer parameters assuming `s` is a standard
    control sequence parameter list.  Empty elements are set to `default`."""
    def f(token):
        if not token:
            return default
        value = int(token)
        if zero_is_default and value == 0:
            return default
        return value
    if s is None:
        l = []
    else:
        try:
            l = [f(token) for token in s.split(b';')]
        except ValueError:
            raise InvalidParameterListError
    l += [default] * (min_length - len(l))
    return l


def clip(n, start, stop=None):
    """Return n clipped to range(start,stop)."""
    if stop is None:
        stop = start
        start = 0
    if n < start:
        return start
    if n >= stop:
        return stop-1
    return n


def new_sequence_decorator(dictionary):
    def decorator_generator(key):
        assert isinstance(key, bytes):
        def decorator(f, key=key):
            dictionary[key] = f.__name__
            return f
        return decorator
    return decorator_generator



class Terminal:

    # ---------- Decorators for Defining Sequences ----------

    commands = {}
    escape_sequences = {}
    control_sequences = {}

    command = new_sequence_decorator(commands)
    escape  = new_sequence_decorator(escape_sequences)
    control = new_sequence_decorator(control_sequences)

    # ---------- Constructor ----------

    def __init__(self, height=24, width=80):
        self.state = 'ground'
        self.prev_state = None
        self.next_state = None
        self.history = []
        self.width = width
        self.height = height
        self.screen = np.array([[None] * width] * height, dtype=object)
        self.pos = [0,0]
        self.tabstops = [(i%8)==0 for i in range(width)]
        self.attr = None
        self.clear()

    # ---------- Utilities ----------

    def clear(self):
        """Reset internal buffers for switching between states."""
        self.collected = bytearray()

    def output(self, c):
        """Print the character at the current position and increment the
        cursor to the next position.  If the current position is past the end
        of the line, starts a new line."""
        if self.pos[1] >= self.width:
            self.CR()
            self.LF()
        self.screen[tuple(self.pos)] = Character(c, self.attr)
        self.CUF()

    def scroll(self, n):
        """Scroll the scrolling region n lines upward (data moves up)."""
        # TODO scroll region
        if n == 0:
            return
        empty = self.width
        if n > 0:
            self.history.append( s[:n].copy() )
            if n > self.height:
                n = self.height
            s[0:-n] = s[n:]
            s[-n:] = [empty] * n
        else:
            n = -n
            if n > self.height:
                n = self.height
            s[n:] = s[0:-n]
            s[:n] = [empty] * n

    def ignore(self, c):
        """Ignore the character."""
        pass

    def collect(self, c):
        """Record the character as an intermediate."""
        self.collected.append(c)

    def clear_on_enter(self, old_state):
        """Since most enter_* functions just call self.clear(), this is a
        common function so that you can set enter_foo = clear_on_enter."""
        self.clear()

    # ---------- Parsing ----------

    def parse(self, s):
        """Parse an entire string."""
        for c in s:
            self.parse_single(c)

    def parse_single(self, c):
        """Parse a single character (integer)."""
        self.next_state = self.state
        if c < 0:
            raise ValueError('input must be non negative (got %d)' % c)
        try:
            f = getattr('parse_%s' % self.state)
        except KeyError:
            raise RuntimeError("internal error: unknown state %s" %
                    repr(self.state))
        else:
            f(c)
        self.transition()

    def transition(self):
        try:
            f = getattr('leave_%s' % self.state)
        except KeyError:
            pass
        else:
            f(self.next_state)
        self.next_state, self.state, self.prev_state = (None,
                self.next_state, self.state)
        try:
            f = getattr('enter_%s' % self.state)
        except KeyError:
            pass
        else:
            f(self.prev_state)

    def parse_ground(self, c):
        if c < 0x20:
            self.execute(c)
        else:
            self.output(c)

    # ---------- Single-character commands (C0) ----------

    def execute(self, c):
        """Execute a C0 command."""
        name = self.commands.get(bytes([c]), None)
        if name is None:
            f = self.ignore
        else:
            f = getattr(self, name, self.ignore)
        f(c)

    @command(b'\x07')       # ^G
    def BEL(self, c=None):
        """Bell"""
        pass

    @command(b'\x08')       # ^H
    def BS(self, c=None):
        """Backspace"""
        self.pos[1] -= 1
        if self.pos[1] < 0:
            self.pos[1] = 0

    @command(b'\x09')       # ^I
    def HT(self, c=None):
        """Horizontal Tab"""
        while self.pos[1] < self.width-1:
            self.pos[1] += 1
            if self.tabstops[self.pos[1]]:
                break

    @command(b'\x0a')       # ^J
    def LF(self, c=None):
        """Line Feed"""
        if self.pos[0] < self.height - 1:
            self.pos[0] += 1
        else:
            self.scroll(1)

    @command(b'\x0b')       # ^K
    def VT(self, c=None):
        """Vertical Tab"""
        self.LF(c)

    @command(b'\x0c')       # ^L
    def FF(self, c=None):
        """Form Feed"""
        self.LF(c)

    @command(b'\x0d')       # ^M
    def CR(self, c=None):
        """Carriage Return"""
        self.pos[1] = 0

    @command(b'\x18')       # ^X
    def CAN(self, c=None):
        """Cancel"""
        self.next_state = 'ground'

    @command(b'\x1a')       # ^Z
    def SUB(self, c=None):
        """Substitute"""
        self.next_state = 'ground'

    @command(b'\x1b')       # ^[
    def ESC(self, c=None):
        """Escape"""
        self.next_state = 'escape'


    # ---------- Escape Sequences ----------

    enter_escape = clear_on_enter

    def parse_escape(self, c):
        if c < 0x20:
            self.execute(c)
        elif c < 0x30:
            self.collect(c)
        elif c < 0x7f:
            self.next_state = 'ground'
            self.dispatch_escape(c)
        else:
            self.ignore(c)

    def dispatch_escape(self, c):
        command = bytes(self.collected) + bytes([c])
        name = self.escape_sequences.get(c, None)
        if name is None:
            f = self.ignore
        else:
            f = getattr(self, name, self.ignore)
        f(command)


    @escape(b'D')
    def IND(self, c=None):
        """Index"""
        self.LF()

    @escape(b'E')
    def NEL(self, c=None):
        """Next Line"""
        self.LF()
        self.CR()

    @escape(b'H')
    def HTS(self, c=None):
        """Horizontal Tab Set"""
        self.tabstops[self.pos[1]] = True

    @escape(b'M')
    def RI(self, c=None):
        """Reverse Index (reverse line feed)"""
        if self.pos[0] > 0:
            self.pos[0] -= 1
        else:
            self.scroll(-1)

    @escape(b'P')
    def DCS(self, c=None):
        """Device Control String"""
        self.next_state = 'dcs'

    @escape(b'X')
    def SOS(self, c=None):
        """Start of String"""
        self.next_state = 'sos'

    @escape(b'[')
    def CSI(self, c=None):
        """Control Sequence Introducer"""
        self.next_state = 'control_sequence'

    @escape(b'\\')
    def ST(self, c=None):
        """String Terminator"""
        pass

    @escape(b']')
    def OSC(self, c=None):
        """Operating System Command"""
        self.next_state = 'osc'

    @escape(b'^')
    def PM(self, c=None):
        """Privacy Message"""
        self.next_state = 'pm'

    @escape(b'_')
    def APC(self, c=None):
        """Application Program Command"""
        self.next_state = 'apc'


    # ---------- Control Sequences ----------

    enter_control_sequence = clear_on_enter

    def parse_control_sequence(self, c):
        if c < 0x20:
            self.execute(c)
        elif c < 0x40:
            self.collect(c)
        elif c < 0x7f:
            self.next_state = 'ground'
            self.dispatch_control_sequence(c)
        else:
            self.ignore(c)

    def dispatch_control_sequence(self, c):
        self.collected.append(c)
        m = re.match(b'^([\x30-\x39]*)([\x20-\x29]*[\x40-\x7f])$',
                     self.collected)
        if not m:
            return self.invalid_control_sequence()
        param, command = m.groups()

        name = self.control_sequences.get(command, None)
        if name is None:
            f = self.ignore_control_sequence
        else:
            f = getattr(self, name, self.ignore_control_sequence)
        try:
            f(command, param)
        except InvalidParameterListError:
            self.invalid_control_sequence()

    def invalid_control_sequence(self):
        """Called when the control sequence is invalid."""
        pass

    def ignore_control_sequence(self, command, param):
        """Called when the control sequence is ignored."""
        pass


    @control(b'@')
    def ICH(self, command=None, param=None):
        """Insert (blank) Characters"""
        # NOT IMPLEMENTED

    @control(b'A')
    def CUU(self, command=None, param=None):
        """Cursor Up"""
        n = param_list(param, 1)[0]
        self.pos[0] = clip(self.pos[0]-n, self.height)

    @control(b'B')
    def CUD(self, command=None, param=None):
        """Cursor Down"""
        n = param_list(param, 1)[0]
        self.pos[0] = clip(self.pos[0]+n, self.height)

    @control(b'C')
    def CUF(self, command=None, param=None):
        """Cursor Forward"""
        n = param_list(param, 1)[0]
        self.pos[1] = clip(self.pos[1]+n, self.width)

    @control(b'D')
    def CUB(self, command=None, param=None):
        """Cursor Backward"""
        n = param_list(param, 1)[0]
        self.pos[1] = clip(self.pos[1]-n, self.width)

    @control(b'E')
    def CNL(self, command=None, param=None):
        """Cursor Next Line"""
        self.CUD(command, param)
        slef.CR()

    @control(b'F')
    def CPL(self, command=None, param=None):
        """Cursor Previous Line"""
        self.CUU(command, param)
        slef.CR()

    @control(b'G')
    def CHA(self, command=None, param=None):
        """Character Position Absolute"""
        n = param_list(param, 1)[0]
        self.pos[1] = clip(n-1, self.width)

    @control(b'H')
    def CUP(self, command=None, param=None):
        """Cursor Position [row;column]"""
        n,m = param_list(param, 1, min_length=2)[:2]
        self.pos[0] = clip(n-1, self.height)
        self.pos[1] = clip(m-1, self.width)

    @control(b'I')
    def CHT(self, command=None, param=None):
        """Cursor Forward Tabulation"""
        n = param_list(param, 1)[0]
        for i in range(n):
            self.HT()

    @control(b'J')
    def ED(self, command=None, param=None):
        """Erase in Display

        Ps = 0  -> Erase Below (default)
        Ps = 1  -> Erase Above
        Ps = 2  -> Erase All
        Ps = 3  -> Erase Saved Lines (xterm)
        """
        # NOT IMPLEMENTED

    @control(b'K')
    def EL(self, command=None, param=None):
        """Erase in Line

        Ps = 0  -> Erase to Right (default)
        Ps = 1  -> Erase to Left
        Ps = 2  -> Erase All
        """
        # NOT IMPLEMENTED
        # Note: param might be ? for selective

    @control(b'L')
    def IL(self, command=None, param=None):
        """Insert Line(s)"""
        # NOT IMPLEMENTED

    @control(b'M')
    def DL(self, command=None, param=None):
        """Delete Line(s)"""
        # NOT IMPLEMENTED

    @control(b'P')
    def DCH(self, command=None, param=None):
        """Delete Character(s)"""
        # NOT IMPLEMENTED

    @control(b'S')
    def SU(self, command=None, param=None):
        """Scroll Up"""
        # NOT IMPLEMENTED

    @control(b'T')
    def SD(self, command=None, param=None):
        """Scroll Down / Mouse Tracking"""
        # NOT IMPLEMENTED

    @control(b'X')
    def ECH(self, command=None, param=None):
        """Erase Character"""
        # NOT IMPLEMENTED

    @control(b'Z')
    def CBT(self, command=None, param=None):
        """Cursor Backward Tabulation"""
        n = param_list(param, 1)[0]
        for i in range(n):
            while self.pos[1] > 0:
                self.pos[1] -= 1
                if self.tabstops[self.pos[1]]:
                    break

    @control(b'`')
    def HPA(self, command=None, param=None):
        """Character Position Absolute"""
        self.CHA(command, param)

    @control(b'a')
    def HPR(self, command=None, param=None):
        """Character Position Forward (Horizontal Position Right)"""
        self.CUF(command, param)

    @control(b'b')
    def REP(self, command=None, param=None):
        """Repeat"""
        # NOT IMPLEMENTED

    @control(b'd')
    def VPA(self, command=None, param=None):
        """Line Position Absolute"""
        n = param_list(param, 1)[0]
        self.pos[0] = clip(n-1, self.height)

    @control(b'e')
    def VPR(self, command=None, param=None):
        """Line Position Forward"""
        self.CUD(command, param)

    @control(b'f')
    def HVP(self, command=None, param=None):
        """Horizontal and Vertical Position"""
        self.CUP(command, param)

    @control(b'g')
    def TBC(self, command=None, param=None):
        """Tab Clear"""
        n = param_list(param, 0)[0]
        if n == 0:
            self.tabstops[self.pos[1]] = False
        elif n == 3:
            self.tabstops[:] = [False] * self.width

    @control(b'h')
    def SM(self, command=None, param=None):
        """Set Mode"""
        # NOT IMPLEMENTED

    @control(b'j')
    def HPB(self, command=None, param=None):
        """Character Position Backward"""
        self.CUB(command, param)

    @control(b'k')
    def VPB(self, command=None, param=None):
        """Line Position Backward"""
        self.CUU(command, param)

    @control(b'l')
    def RM(self, command=None, param=None):
        """Reset Mode"""
        # NOT IMPLEMENTED

    @control(b'm')
    def SGR(self, command=None, param=None):
        """Set Graphics Attributes"""
        # NOT IMPLEMENTED
        # TODO '>m' xterm

    @control(b'!p')
    def DECSTR(self, command=None, param=None):
        """Soft Terminal Reset"""
        # NOT IMPLEMENTED

    @control(b'r')
    def DECSTBM(self, command=None, param=None):
        """Set Scrolling Region"""
        # NOT IMPLEMENTED
        # Note: with param = "? Pm", restore DEC private mode values

    @control(b'$r')
    def DECCARA(self, command=None, param=None):
        """Change Attributes in Rectangular Area"""
        # NOT IMPLEMENTED

    @control(b's')
    def save_cursor(self, command=None, param=None):
        """Save cursor"""
        # NOT IMPLEMENTED
        # Note: with param = "? Pm", set DEC private mode values

    @control(b'$t')
    def DECRARA(self, command=None, param=None):
        """Reverse Attributes in Rectangular Area"""
        # NOT IMPLEMENTED

    @control(b'u')
    def restore_cursor(self, command=None, param=None):
        """Restore cursor"""
        # NOT IMPLEMENTED

    # TODO more from ctlseqs.txt



    # ---------- Control Strings ----------

    enter_osc = clear_on_enter
    enter_dsc = clear_on_enter
    enter_sos = clear_on_enter
    enter_apc = clear_on_enter
    enter_pm  = clear_on_enter

    def parse_osc(self, c): self.parse_control_string(c)
    def parse_dsc(self, c): self.parse_control_string(c)
    def parse_sos(self, c): self.parse_control_string(c)
    def parse_pm (self, c): self.parse_control_string(c)
    def parse_apc(self, c): self.parse_control_string(c)

    finish_osc = None
    finish_dsc = None
    finish_sos = None
    finish_apc = None
    finish_pm  = None

    def parse_control_string(self, c):
        # Consume the whole string and pass it to the process function.
        if c in (0x18, 0x1a):
            # CAN and SUB quit the string
            self.cancel_control_string()
            # should we self.execute(c) ?
        elif c == 0x07 and self.state == 'osc':
            # NOTE: xterm ends OSC with BEL, in addition to ESC \
            self.finish_control_string()
        elif self.collected and self.collected[-1] == 0x1b:
            # NOTE: xterm consumes the character after the ESC always, but
            # only process it if it is '\'.  Not sure about VTxxx.
            self.collected = self.collected[:-1]
            if c == 0x5c:
                self.finish_control_string()
            else:
                self.cancel_control_string()
        else:
            self.collect(c)

    def finish_control_string(self):
        name = 'finish_%s' % self.state
        f = getattr(self, name, self.ignore_control_string)
        f(self.collected)
        self.next_state = 'ground'

    def cancel_control_string(self):
        self.next_state = 'ground'

    def ignore_control_string(self):
        """Called when a control string is ignored."""
        pass




    # ================================================================
    #             Things implemented by xterm but not here.
    # ================================================================

    @command(b'\x05')       # ^E
    def ENQ(self, c=None):
        """ENQuiry"""
        # NOT IMPLEMENTED

    @command(b'\x0e')       # ^N
    def SO(self, c=None):
        """Shift Out (LS1)"""
        # NOT IMPLEMENTED

    @command(b'\x0f')       # ^O
    def SI(self, c=None):
        """Shift In (LS0)"""
        # NOT IMPLEMENTED

    # --------------------

    @escape(b'7')
    def DECSC(self, c=None):
        """Save Cursor"""
        # NOT IMPLEMENTED

    @escape(b'8')
    def DECRC(self, c=None):
        """Restore Cursor"""
        # NOT IMPLEMENTED

    @escape(b'=')
    def DECPAM(self, command=None, param=None):
        """Application Keypad"""
        # NOT IMPLEMENTED

    @escape(b'>')
    def DECPNM(self, command=None, param=None):
        """Normal Keypad"""
        # NOT IMPLEMENTED

    @escape(b'N')
    def SS2(self, c=None):
        """Single Shift 2"""
        # NOT IMPLEMENTED

    @escape(b'O')
    def SS3(self, c=None):
        """Single Shift 3"""
        # NOT IMPLEMENTED

    @escape(b' F')
    def S7C1T(self, c=None):
        """7-bit controls"""
        # NOT IMPLEMENTED

    @escape(b' G')
    def S8C1T(self, c=None):
        """8-bit controls"""
        # NOT IMPLEMENTED

    @escape(b' L')
    def set_ansi_level_1(self, c=None):
        """Set ANSI conformance level 1"""
        # NOT IMPLEMENTED

    @escape(b' M')
    def set_ansi_level_2(self, c=None):
        """Set ANSI conformance level 2"""
        # NOT IMPLEMENTED

    @escape(b' N')
    def set_ansi_level_3(self, c=None):
        """Set ANSI conformance level 3"""
        # NOT IMPLEMENTED

    # ESC # 3   DEC double-height line, top half (DECDHL)
    # ESC # 4   DEC double-height line, bottom half (DECDHL)
    # ESC # 5   DEC single-width line (DECSWL)
    # ESC # 6   DEC double-width line (DECDWL)
    # ESC # 8   DEC Screen Alignment Test (DECALN)
    # ESC % @   Select default character set, ISO 8859-1 (ISO 2022)
    # ESC % G   Select UTF-8 character set (ISO 2022)
    # ESC ( C   Designate G0 Character Set (ISO 2022)
    # ESC ) C   Designate G1 Character Set (ISO 2022)
    # ESC * C   Designate G2 Character Set (ISO 2022)
    # ESC + C   Designate G3 Character Set (ISO 2022)
    # ESC - C   Designate G1 Character Set (VT300)
    # ESC . C   Designate G2 Character Set (VT300)
    # ESC / C   Designate G3 Character Set (VT300)
    # ESC F     Cursor to lower left corner of screen (if enabled by the
    #           hpLowerleftBugCompat resource).
    # ESC l     Memory Lock (per HP terminals).  Locks memory above the cur-
    #           sor.
    # ESC m     Memory Unlock (per HP terminals)
    # ESC n     Invoke the G2 Character Set as GL (LS2).
    # ESC o     Invoke the G3 Character Set as GL (LS3).
    # ESC |     Invoke the G3 Character Set as GR (LS3R).
    # ESC }     Invoke the G2 Character Set as GR (LS2R).
    # ESC ~     Invoke the G1 Character Set as GR (LS1R).

    # --------------------

    @control(b'c')
    def DA(self, command=None, param=None):
        """Send Device Attributes"""
        # NOT IMPLEMENTED

    @control(b'i')
    def MC(self, command=None, param=None):
        """Media Copy"""
        # NOT IMPLEMENTED

    @control(b'n')
    def DSR(self, command=None, param=None):
        """Device Status Report"""
        # NOT IMPLEMENTED

    # @control(b'p') with '>': xterm pointer mode

    @control(b'"p')
    def DECSCL(self, command=None, param=None):
        """Set Conformance Level"""
        # NOT IMPLEMENTED

    @control(b'"q')
    def DECSCA(self, command=None, param=None):
        """Set Character protection Attribute"""
        # NOT IMPLEMENTED

    @control(b't')
    def window_manipulation(self, command=None, param=None):
        """Window manipulation"""
        # NOT IMPLEMENTED

    # ================================================================
    #                  Things not implemented by xterm.
    # ================================================================

    @command(b'\x00')       # ^@
    def NUL(self, c=None):
        """NULl"""
        # NOT IMPLEMENTED

    @command(b'\x01')       # ^A
    def SOH(self, c=None):
        """Start Of Heading"""
        # NOT IMPLEMENTED

    @command(b'\x02')       # ^B
    def STX(self, c=None):
        """Start of TeXt"""
        # NOT IMPLEMENTED

    @command(b'\x03')       # ^C
    def ETX(self, c=None):
        """End of TeXt"""
        # NOT IMPLEMENTED

    @command(b'\x04')       # ^D
    def EOT(self, c=None):
        """End Of Transmission"""
        # NOT IMPLEMENTED

    @command(b'\x06')       # ^F
    def ACK(self, c=None):
        """ACKnowledge"""
        # NOT IMPLEMENTED

    @command(b'\x10')       # ^P
    def DLE(self, c=None):
        """Data Link Escape"""
        # NOT IMPLEMENTED

    @command(b'\x11')       # ^Q
    def DC1(self, c=None):
        """Device Control 1"""
        # NOT IMPLEMENTED

    @command(b'\x12')       # ^R
    def DC2(self, c=None):
        """Device Control 2"""
        # NOT IMPLEMENTED

    @command(b'\x13')       # ^S
    def DC3(self, c=None):
        """Device Control 3"""
        # NOT IMPLEMENTED

    @command(b'\x14')       # ^T
    def DC4(self, c=None):
        """Device Control 4"""
        # NOT IMPLEMENTED

    @command(b'\x15')       # ^U
    def NAK(self, c=None):
        """Negative AcKnowledge"""
        # NOT IMPLEMENTED

    @command(b'\x16')       # ^V
    def SYN(self, c=None):
        """SYNchronous idle"""
        # NOT IMPLEMENTED

    @command(b'\x17')       # ^W
    def ETB(self, c=None):
        """End of Transmission Block"""
        # NOT IMPLEMENTED

    @command(b'\x19')       # ^Y
    def EM(self, c=None):
        """End of Medium"""
        # NOT IMPLEMENTED

    @command(b'\x1c')       # ^\
    def FS(self, c=None):
        """File Separator (IS4)"""
        # NOT IMPLEMENTED

    @command(b'\x1d')       # ^]
    def GS(self, c=None):
        """Group Separator (IS3)"""
        # NOT IMPLEMENTED

    @command(b'\x1e')       # ^^
    def RS(self, c=None):
        """Record Separator (IS2)"""
        # NOT IMPLEMENTED

    @command(b'\x1f')       # ^_
    def US(self, c=None):
        """Unit Separator (IS1)"""
        # NOT IMPLEMENTED

    # --------------------

    # no @escape(b'0')
    # no @escape(b'1')
    # no @escape(b'2')
    # no @escape(b'3')
    # no @escape(b'4')
    # no @escape(b'5')
    # no @escape(b'6')
    # no @escape(b'9')
    # no @escape(b':')
    # no @escape(b';')
    # no @escape(b'<')
    # no @escape(b'?')
    # no @escape(b'@')
    # no @escape(b'A')

    @escape(b'B')
    def BPH(self, command=None, param=None):
        """Break Permitted Here"""
        # NOT IMPLEMENTED

    @escape(b'C')
    def NBH(self, command=None, param=None):
        """No Break Here"""
        # NOT IMPLEMENTED

    @escape(b'F')
    def SSA(self, command=None, param=None):
        """Start of Selected Area"""
        # NOT IMPLEMENTED

    @escape(b'G')
    def ESA(self, command=None, param=None):
        """End of Selected Area"""
        # NOT IMPLEMENTED

    @escape(b'I')
    def HTJ(self, command=None, param=None):
        """Character Tabulation with Justification"""
        # NOT IMPLEMENTED

    @escape(b'J')
    def VTS(self, command=None, param=None):
        """Veritical Tab Set"""
        # NOT IMPLEMENTED

    @escape(b'K')
    def PLD(self, command=None, param=None):
        """Partial Line forward (Down)"""
        # NOT IMPLEMENTED

    @escape(b'L')
    def PLU(self, command=None, param=None):
        """Partial Line backward (Up)"""
        # NOT IMPLEMENTED

    @escape(b'Q')
    def PU1(self, command=None, param=None):
        """Private Use 1"""
        # NOT IMPLEMENTED

    @escape(b'R')
    def PU2(self, command=None, param=None):
        """Private Use 2"""
        # NOT IMPLEMENTED

    @escape(b'S')
    def STS(self, command=None, param=None):
        """Set Transmit State"""
        # NOT IMPLEMENTED

    @escape(b'T')
    def CCH(self, command=None, param=None):
        """Cancel CHaracter"""
        # NOT IMPLEMENTED

    @escape(b'U')
    def MW(self, command=None, param=None):
        """Message Waiting"""
        # NOT IMPLEMENTED

    @escape(b'V')
    def SPA(self, c=None):
        """Start of guarded (Protected) Area"""
        # NOT IMPLEMENTED

    @escape(b'W')
    def EPA(self, c=None):
        """End of guarded (Protected) Area"""
        # NOT IMPLEMENTED

    # no @escape(b'Y')

    @escape(b'Z')
    def SCI(self, c=None):
        """Single Character Introducer"""
        # NOT IMPLEMENTED

    @escape(b'a')
    def INT(self, command=None, param=None):
        """INTerrupt"""
        # NOT IMPLEMENTED

    @escape(b'b')
    def EMI(self, command=None, param=None):
        """Enable Manual Input"""
        # NOT IMPLEMENTED

    @escape(b'c')
    def RIS(self, command=None, param=None):
        """Reset to Initial State"""
        # NOT IMPLEMENTED
        # TODO

    @escape(b'd')
    def CMD(self, command=None, param=None):
        """Coding Method Delimiter"""
        # NOT IMPLEMENTED

    # --------------------

    @control(b'N')
    def EF(self, command=None, param=None):
        """Erase in Field"""
        # NOT IMPLEMENTED

    @control(b'O')
    def EA(self, command=None, param=None):
        """Erase in Area"""
        # NOT IMPLEMENTED

    @control(b'Q')
    def SSE(self, command=None, param=None):
        # NOT IMPLEMENTED
        pass

    @control(b'R')
    def CPR(self, command=None, param=None):
        """Active Position Report"""
        # NOT IMPLEMENTED

    @control(b'U')
    def NP(self, command=None, param=None):
        """Next Page"""
        # NOT IMPLEMENTED

    @control(b'V')
    def PP(self, command=None, param=None):
        """Previous Page"""
        # NOT IMPLEMENTED

    @control(b'W')
    def CTC(self, command=None, param=None):
        """Cursor Tabulation Control"""
        # NOT IMPLEMENTED

    @control(b'Y')
    def CVT(self, command=None, param=None):
        """Cursor Line Tabulation"""
        # NOT IMPLEMENTED

    @control(b'[')
    def SRS(self, command=None, param=None):
        """Start Reversed String"""
        # NOT IMPLEMENTED

    @control(b'\\')
    def PTX(self, command=None, param=None):
        """Parallel Texts"""
        # NOT IMPLEMENTED

    @control(b']')
    def SDS(self, command=None, param=None):
        """Start Directed String"""
        # NOT IMPLEMENTED

    @control(b'^')
    def SIMD(self, command=None, param=None):
        """Select Implicit Movement Direction"""
        # NOT IMPLEMENTED

    # no @control(b'_')

    @control(b'o')
    def DAQ(self, command=None, param=None):
        """Define Area Qualification"""
        # NOT IMPLEMENTED




if __name__ == "__main__":
    pass
