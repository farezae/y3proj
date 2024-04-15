''' melody generation contains : 
    - base binaural beat
    - sonification of QRS wave
    - gong sounds mapped to RR-intervals
    - chime sounds mapped to R-peaks
'''
import pyo 
import numpy as np
from pyo import *

s = Server().boot().start()

''' data '''
# QRS avg data: between 0.005 and 0.1# QRS avg data: between 0.005 and 0.1
QRS_data = []
for i in range (0,30):
    x=random.uniform(0.005,0.1)
    QRS_data.append(x)

notes = [60,62,64,65,67,69,71,72]

rr_values = [0.9,0.8,1.2,1.1,0.9,0.7,0.5,0.8,0.7]
r_peaks = [0.5,0.4,0.6,0.8,0.5,0.3,0.2,0.6,0.7, 0.5, 0.8, 0.8, 0.7]  
s_peaks = [0.5,0.4,0.6,0.8,0.5,0.3,0.2,0.6,0.7, 0.5, 0.8, 0.8, 0.7]  


''' binaural beat '''
# frequencies for the binaural beat
base_freq = 40  # base frequency in Hz 
binaural_freq = 8  # for anxiety/stress relief, alpha freq. lie between 8-13Hz

#creating two slightly different sine waves for each ear
def play_leftbinaural(base_freq):
    left = Sine(freq=base_freq, mul=0.1).out()
    return left

def play_rightbinaural(base_freq,binaural_freq):    
    right = Sine(freq=base_freq + binaural_freq, mul=0.1).out()
    return right 



''' QRS sonification '''
notes = [60,62,64,65,67,69,71,72]

# function to map QRS data to a melody 
def mapping(qrs_data, notes):
    events=[]
    for item in qrs_data:
        # 8 notes, 0.1-0.005/8=0.011875
        if item <= 0.011875:
            events.append(notes[0])
        elif (item<=0.02375) and (item>0.011875):
            events.append(notes[1])
        elif (item<=0.035625) and (item>0.02375):
            events.append(notes[2])
        elif (item<=0.0475) and (item>0.035625):
            events.append(notes[3])
        elif (item<=0.059375) and (item>0.0475):
            events.append(notes[4])
        elif (item<=0.07125) and (item>0.059375):
            events.append(notes[5])
        elif (item<=0.083125) and (item>0.07125):
            events.append(notes[6])
        elif (item<=0.1) and (item>0.083125):
            events.append(notes[7])
        else: 
            pass
    return events

# used to convert notes to their corresponding frequency 
def midiToHz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)

# synthesises the final melody  
def playQRS(melody_events):
    for note in melody_events:
        freq = midiToHz(note)
        osc = Sine(freq=freq, mul=1)
    return osc 


''' gong sounds '''
rr_intervals = [value + 3.5 for value in rr_values]
rr_mean = np.mean(rr_values)
rr_sd = np.std(rr_values)

# path to the gong sound file
gong_file_path = "sounds/gong.wav"

# metro objects + counter definition 
gong_met_time = SigTo(rr_intervals[0], time=float(rr_mean))
gong_met = Metro(time=gong_met_time).out()
beat_count = Counter(gong_met)


# function to update Metro time
def update_gong_met():
    next_interval = rr_intervals[int(beat_count.get()) % len(rr_intervals)]
    gong_met_time.setValue(next_interval)
    gong_met.setTime(next_interval)
    xfade.play()
    #gong_player.out()

gong_player = SfPlayer(gong_file_path, speed=1.5, mul=0.5, loop=False)
trig_update_gongmet = TrigFunc(gong_met, update_gong_met)
gong_reverb = Freeverb(gong_player.mix(2), size=0.9, damp=0.4, bal=0.4).out()
xfade = Fader(fadein=0.5, fadeout=0.5, dur=0, mul=1) # crossfade envelope

''' chime sounds '''
# path to the chime sound file
chime_file_path = "sounds/tinkle.wav"

# metro object to trigger 
chime_met_time = SigTo(value=1.75, time=0.1)  # smooth transition for metro time changes
chime_met = Metro(time=chime_met_time ).out() 

# counter to iterate over r_peaks
beat_count = Counter(chime_met, min=0, max=len(r_peaks) - 1)

# chime player
chime_player = SfPlayer(chime_file_path, speed=0.75, loop=True, mul=0)

# function to update amplitude based on r_peaks
def update_chime_amplitude():
    idx = int(beat_count.get())
    amp = r_peaks[idx]
    chime_player.setMul(amp)  # update the amplitude
    #chime_player.out()

trig_update_amplitude = TrigFunc(chime_met, update_chime_amplitude)



''' play sounds '''
# play binaural beat
binaural_leftbeat = play_leftbinaural(base_freq=40).out()
binaural_rightbeat = play_rightbinaural(base_freq=40, binaural_freq=8).out()

# map QRS data to melody events + play QRS sounds 
melody_events = mapping(QRS_data, notes)
#QRS_sonified = playQRS(melody_events).out()

# play gong sounds
#gong_sounds = trig_update_gongmet.out()

# play chime sounds
#chime_sounds = trig_update_amplitude.out()
s.gui(locals())

