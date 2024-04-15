''' gong sounds are mapped to rr intervals + 3.5
    avg breath 1.5-2sec + 1.5-2sec exhale inhale, '''

from pyo import *
import numpy as np

# Boot the server
s = Server().boot().start()

# extracted values
rr_values = [0.9,0.8,1.2,1.1,0.9,0.7,0.5,0.8,0.7]
rr_intervals = [value + 3.5 for value in rr_values]
    
rr_mean = np.mean(rr_values)
rr_sd = np.std(rr_values)

# Path to the gong sound file
gong_file_path = "sounds/gong.wav"

# Metro object with RR intervals
met = Metro(time=rr_intervals[0]).play()
met_time = SigTo(rr_intervals[0], time=float(rr_mean))

# Counter for beats
beat_count = Counter(met)

# Function to update Metro time
def update_met():
    next_interval = rr_intervals[int(beat_count.get()) % len(rr_intervals)]
    met_time.setValue(next_interval)
    met.setTime(next_interval)

# Trigger function for updating Metro
trig_update_met = TrigFunc(met, update_met)

gong_player = SfPlayer(gong_file_path, speed=0.75, mul=0.05, loop=False)

# Reverb with longer tail
gong_reverb = Freeverb(gong_player.mix(2), size=0.9, damp=0.4, bal=0.4).out()

# Crossfade envelope
xfade = Fader(fadein=0.5, fadeout=0.5, dur=0, mul=1)
gong_with_reverb = xfade.mix(2) * gong_reverb

# Function to play gong sound
def play_gong():
    xfade.play()  # Start crossfade envelope
    gong_player.play()

# Trigger function for playing gong sound
trig_play_gong = TrigFunc(met, play_gong).out()


s.gui(locals())