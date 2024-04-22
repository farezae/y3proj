''' bowl sounds are mapped to s-peak amplitude values '''
''' needs fixing '''
from pyo import *
import numpy as np

# Boot the server
s = Server().boot().start()

# Sample s_peaks values for amplitude 
s_peaks = [0.5,0.4,0.6,0.8,0.5,0.3,0.2,0.6,0.7, 0.5, 0.8, 0.8, 0.7]  

# Path to the tinkle sound file
bowl_file_path = "sounds/singingbowl.wav"

# Metro object to trigger playbacks_tink
bowl_met_time = SigTo(value=1, time=0.1)  # Smooth transition for Metro time changes
bowl_met = Metro(time=bowl_met_time ).out()  # 'time=1' for a tick every second, adjust as needed

# Counter to iterate over r_peaks
beat_count = Counter(bowl_met, min=0, max=len(s_peaks) - 1)
bowl_player = SfPlayer(bowl_file_path, speed=0.75, loop=True, mul=0)

# Function to update amplitude based on r_peaks
def update_bowl_amplitude():
    idx = int(beat_count.get())
    amp = s_peaks[idx]
    bowl_player.setMul(amp)  # Update the amplitude
    bowl_player.out()

trig_update_amplitude = TrigFunc(bowl_met, update_bowl_amplitude)

# Play the tinkle sound continuously, with its amplitude modulated
bowl_sounds = trig_update_amplitude.out()

s.gui(locals())
