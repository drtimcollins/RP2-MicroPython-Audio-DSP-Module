# Sine wave generator demonstration
# Copyright (c) 2025 Tim Collins - MIT License
# See https://github.com/drtimcollins/RP2-MicroPython-Synth-Modules/blob/main/LICENSE
# Requires I2S device with:
# GP18 -> Bit Clock
# GP19 -> LR Clock
# GP20 -> Data

import time, struct, uctypes
from machine import I2S, Pin, mem32
from micropython import const
from audioDSP import DCO, DCA, AR       # Requires sineOsc.py and sineTable.dat to be in RP2 filespace

led = Pin('LED')                    # LED is used as simple indicator of processor load.

Fs = 24000                              # Sample rate = 24 kHz
BUFFER_LEN = 4000                       # Shorter buffer = less latency but higher processing overhead

sck,ws,sd = Pin(18), Pin(19), Pin(20)   # Also known as bit clock, LR clock, and data
audio_out = I2S(0, sck=sck, ws=ws, sd=sd, mode=I2S.TX,
                bits=32, format=I2S.MONO, rate=Fs, ibuf=BUFFER_LEN)

print('I2S enabled')

sineBuf = bytearray(BUFFER_LEN)
gainBuf = bytearray(BUFFER_LEN)
outBuf  = bytearray(BUFFER_LEN)
dco = DCO(sineBuf)                     # Create sine wave generator
dca = DCA(sineBuf, gainBuf, outBuf)
eg  = AR(gainBuf)

try:
    while True: 								# Infinite loop - press Ctrl-C to exit
        led.on()
        dco.process(0x0555)   			# Fills buffer with samples, 0x555 = ~500 Hz
        eg.process(eg.envPhase == 0)
        dca.process()
        I2S.shift(buf=outBuf, bits=32, shift = 12)
        led.off()
        audio_out.write(outBuf)
except (KeyboardInterrupt, Exception) as e:
    print(f"Caught exception: {type(e).__name__}")

audio_out.deinit()                      # Must deinit or pico will need resetting
print('I2S disabled')
