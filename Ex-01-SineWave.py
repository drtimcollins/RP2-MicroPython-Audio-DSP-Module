# Sine wave generator demonstration
# Copyright (c) 2025 Tim Collins - MIT License
# See 
# Requires I2S device with:
# GP18 -> Bit Clock
# GP19 -> LR Clock
# GP20 -> Data

import time, struct, uctypes
from machine import I2S, Pin, mem32
from micropython import const
from sineOsc import sineOsc         # Requires sineOsc.py and sineTable.dat to be in RP2 filespace

led = Pin('LED')

Fs = 24000                              # Sample rate = 24 kHz
BUFFER_LEN = 2000                       # Shorter buffer = less latency but higher processing overhead

sck,ws,sd = Pin(18), Pin(19), Pin(20)   # Also known as bit clock, LR clock, and data
audio_out = I2S(0, sck=sck, ws=ws, sd=sd, mode=I2S.TX,
                bits=16, format=I2S.MONO, rate=Fs, ibuf=BUFFER_LEN)

print('I2S enabled')

buf = bytearray(BUFFER_LEN)             # Buffer used to pass data to the I2S handler
sOsc = sineOsc()

sOsc.buf = buf

try:
    while True:                         # Infinite loop - press Ctrl-C to exit
        led.on()                        # LED used as simple indicator of processor load
        sOsc.processBuffer()
        led.off()
        audio_out.write(buf)
except (KeyboardInterrupt, Exception) as e:
    print(f"Caught exception: {type(e).__name__}")

audio_out.deinit()                      # Must deinit or pico will need resetting
print('I2S disabled')
