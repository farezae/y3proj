''' tinkle sounds are mapped to r-peak amplitude values '''

from pyo import *
import numpy as np

# Boot the server
s = Server().boot().start()

# Sample r_peaks values for amplitude 
r_peaks = [0.5,0.4,0.6,0.8,0.5,0.3,0.2,0.6,0.7, 0.5, 0.8, 0.8, 0.7]  

# Path to the tinkle sound file
tinkle_file_path = "sounds/tinkle.wav"

# Metro object to trigger playbacks_tink
met_time = SigTo(value=1.75, time=0.1)  # Smooth transition for Metro time changes
met = Metro(time=met_time ).play()  # 'time=1' for a tick every second, adjust as needed


# Counter to iterate over r_peaks
beat_count = Counter(met, min=0, max=len(r_peaks) - 1)

# Tinkle sound player, initially silent
tinkle_player = SfPlayer(tinkle_file_path, speed=0.75, loop=True, mul=0)

# Function to update amplitude based on r_peaks
def update_amplitude():
    idx = int(beat_count.get())
    amp = r_peaks[idx]
    tinkle_player.setMul(amp)  # Update the amplitude

trig_update_amplitude = TrigFunc(met, update_amplitude)

# Play the tinkle sound continuously, with its amplitude modulated
tinkle_player.out()

s.gui(locals())
