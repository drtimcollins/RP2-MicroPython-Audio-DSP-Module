
# High speed sine wave generator class.
# Copyright (c) 2025 Tim Collins - MIT License
# See https://github.com/drtimcollins/RP2-MicroPython-Synth-Modules/blob/main/LICENSE

import uctypes
from micropython import const

# 256 samples @ 16 bits for one complete sine wave. Amplitude = 32000
with open('sineTable.dat','rb') as h:
    sineTable = h.read()

SIO_BASE = const(0xd0000000)
INTERP0_ACCUM0 = const(0x080 >> 2) # Read/write access to accumulator 0
INTERP0_ACCUM1 = const(0x084 >> 2) # Read/write access to accumulator 1
INTERP0_BASE0  = const(0x088 >> 2) # Read/write access to BASE0 register.
INTERP0_BASE1  = const(0x08c >> 2) # Read/write access to BASE1 register.
INTERP0_CTRL_LANE0 = const(0x0ac >> 2) # Control register for lane 0
INTERP0_CTRL_LANE1 = const(0x0b0 >> 2) # Control register for lane 1
INTERP0_PEEK_LANE0 = const(0x0a0 >> 2) # Read LANE0 result, without altering any internal state (PEEK).
INTERP0_PEEK_LANE1 = const(0x0a4 >> 2) # Read LANE1 result, without altering any internal state (PEEK).
INTERP0_BASE_1AND0 = const(0x0bc >> 2) # On write, the lower 16 bits go to BASE0, upper bits to BASE1 simultaneously.

class sineOsc:
    def __init__(self):
        self.phase = 0
        self.buf = []
        self.sineTableAddress = uctypes.addressof(sineTable)
    # Fills the buffer with sine wave samples.
    @micropython.viper
    def processBuffer(self):
        sio = ptr32(SIO_BASE)                 # Set up hardware interpolator
        sio[INTERP0_CTRL_LANE0] = 0x00207c00  # Set Blend bit, Mask = full width
        sio[INTERP0_CTRL_LANE1] = 0x0000fc00  # Set Signed bit, Mask = full width

        n = 0
        i = int(self.phase)
        bufP = ptr16(uctypes.addressof(self.buf))
        limit = (int(len(self.buf)) >> 1)
        sinTab = ptr16(self.sineTableAddress)
        while n < limit:
            i0 = (i >> 8) & 0x00FF	# i0 = index to sine sample (rounded down to int)
            i1 = (i0 + 1) & 0x00FF	# i1 = index to sine sample (rounded up to int)
            sio[INTERP0_BASE_1AND0] = (sinTab[i1] << 16) | sinTab[i0]
            sio[INTERP0_ACCUM1] = i # Lowest 8 bits of i used for interpolation weight
            sample = sio[INTERP0_PEEK_LANE1]	# Interpolates between sin[i0] and sin[i1]

            bufP[n] = sample
            i = i + 0x0800          # Change this for different frequencies
            n += 1
        self.phase = i
