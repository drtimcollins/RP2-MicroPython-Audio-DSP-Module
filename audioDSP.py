# Real-time audio synthesis classes
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

#######################################################################
# DCO - Digitally Controlled Oscillator. Real-time sine wave generator.
#######################################################################
class DCO:
    def __init__(self, outputBuffer):   # 32-bit outputBuffer
        self.phase = 0
        self.outBufferAddress = uctypes.addressof(outputBuffer)
        self.sineTableAddress = uctypes.addressof(sineTable)
        self.numSamples = len(outputBuffer) >> 2

    # Fills the buffer with sine wave samples.
    @micropython.viper
    def process(self, deltaPhase : int):
        sio = ptr32(SIO_BASE)                 # Set up hardware interpolator
        sio[INTERP0_CTRL_LANE0] = 0x00207c00  # Set Blend bit, Mask = full width
        sio[INTERP0_CTRL_LANE1] = 0x0000fc00  # Set Signed bit, Mask = full width

        n = 0
        i = int(self.phase)
        pOutBuffer = ptr32(self.outBufferAddress)        
        pSineTable = ptr16(self.sineTableAddress)
        while n < int(self.numSamples):
            i0 = (i >> 8) & 0x00FF	# i0 = index to sine sample (rounded down to int)
            i1 = (i0 + 1) & 0x00FF	# i1 = index to sine sample (rounded up to int)
            sio[INTERP0_BASE_1AND0] = (pSineTable[i1] << 16) | pSineTable[i0]
            sio[INTERP0_ACCUM1] = i # Lowest 8 bits of i used for interpolation weight
            sample = sio[INTERP0_PEEK_LANE1]	# Interpolates between sin[i0] and sin[i1]

            pOutBuffer[n] = sample
            
            i = i + deltaPhase                  # deltaPhase = (frequency * 65536) / Fs
            n += 1
        self.phase = i

#######################################################################
# DCA - Digitally Controlled Amplifier.
#######################################################################
class DCA:
    def __init__(self, inputBuffer, gainBuffer, outputBuffer):
        self.outBufferAddress  = uctypes.addressof(outputBuffer)	# Store memory addresses of in and out buffers
        self.inBufferAddress   = uctypes.addressof(inputBuffer)
        self.gainBufferAddress = uctypes.addressof(gainBuffer)
        self.numSamples = len(outputBuffer) >> 2

    @micropython.viper
    def process(self):
        n = 0
        pOutBuffer  = ptr32(self.outBufferAddress)					# Treat buffers as arrays of 32-bit words
        pInBuffer   = ptr32(self.inBufferAddress)        
        pGainBuffer = ptr32(self.gainBufferAddress)        
        while n < int(self.numSamples):
            pOutBuffer[n] = (pInBuffer[n] * pGainBuffer[n]) >> 16	# Fixed point multiplication
            n += 1

#######################################################################
# AR - Attack-Release envelope generator
#######################################################################
class AR:
    def __init__(self, outputBuffer):
        self.outBufferAddress  = uctypes.addressof(outputBuffer)	# Store memory addresses of out buffer
        self.numSamples = len(outputBuffer) >> 2
        self.envPhase = 0		# 0 = off, 1 = Attacking, 2 = Releasing
        self.envValue = 0
        self.setParameters(20, 10000)
    
    def setParameters(self, attackTime, releaseTime):				# Times are measured in samples
        self.attDelta = 0xFFFF // attackTime
        self.relDelta = 0xFFFF // releaseTime
        
    @micropython.viper
    def process(self, trigger: bool):
        n = 0
        pOutBuffer  = ptr32(self.outBufferAddress)					# Treat buffers as arrays of 32-bit words
        if trigger:
            p = 1
        else:
            p = int(self.envPhase)
        x = int(self.envValue)        
        ad = int(self.attDelta)
        rd = int(self.relDelta)
        while n < int(self.numSamples):
            if p == 1:
                x += ad
                if x > 0xFFFF:
                    x = 0xFFFF
                    p = 2
            elif p == 2:
                x -= rd
                if x < 0:
                    x = 0
                    p = 0
            else:
                x = 0
            pOutBuffer[n] = x
            n += 1
        self.envValue = x
        self.envPhase = p
        
                    
                
        