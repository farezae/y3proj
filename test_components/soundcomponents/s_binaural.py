# binaural beat (see ref.)

from pyo import *

s = Server().boot().start()

# frequencies for the binaural beat
base_freq = 40  # Base frequency in Hz (usually set between 200-400Hz)
binaural_freq = 8  # Frequency difference in Hz (for anxiety/stress relief, alpha freq. lie between 8-13hz)

# Create two slightly different sine waves for each ear
left_ear = Sine(freq=base_freq, mul=0.1).out(0) # Output to left ear
right_ear = Sine(freq=base_freq + binaural_freq, mul=0.1).out(1) # Output to right ear

s.gui(locals())
