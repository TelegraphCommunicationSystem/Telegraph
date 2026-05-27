from machine import Pin, I2S
import math
import _thread

# Configure I2S (ID=0) on GP13 (BCLK), GP11 (WS), GP12 (DATA)
i2s = I2S(
    0,
    sck=Pin(11), # BCLK
    ws=Pin(12), # WS
    sd=Pin(13), # DATA
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=44100,
    ibuf=40000
)

# Parameter
freq = 700
fs = 44100
samples = int(fs // freq)  # ~63 samples per cycle

# Build one sine cycle
cycle = bytearray(samples * 2)
for i in range(samples):
    val = int(0.025 * 32767 * math.sin(2 * math.pi * i / samples))
    cycle[2 * i] = val & 0xFF
    cycle[2 * i + 1] = (val >> 8) & 0xFF

# Repeat the cycle many times to form a "long" buffer
repeats = 1  # adjust to change duration
buf = bytearray()
for _ in range(repeats):
    buf.extend(cycle)

def tone_task():
    """Write continuously the audio buffer to I2S."""
    while True:
        i2s.write(buf)  # Non-blocking in MicroPython I2S

def start_generator():
    _thread.start_new_thread(tone_task, ())