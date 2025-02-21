# RP2 MicroPython Audio DSP Module

Module for real-time, MicroPython audio synthesis using RP2 microcontrollers.

### audioDSP.py
This module contains the real-time audio processing classes:

- DCO - A sine wave Digitally Controlled Oscillator
- DCA - A Digitally Controlled Amplifier

All processing is done using the MicroPython Viper emitter. The DCO uses a sinewave lookup table, sineTable.dat; both audioDSP.py and sineTable.dat must be uploaded into the RP2 filespace to function. The DCO class uses the RP2 hardware interpolator for sine wave generation and will need modifying if used on other processors.

### Examples

1. **Ex-01-SineWave.py**: Simple test example. Plays a continuous sine wave tone of approximately 500Hz to an I2S output.
2. **Ex-02-OscPlusAmp.py**: Like example 1 but adds a DCA into the audio signal chain. 

