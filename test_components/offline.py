import numpy as np
import pandas as pd
import numpy as np

from pyo import *
from scipy.signal import find_peaks
from collections import deque
from appJar import gui 


file_path_qrs = 'qrsdata.csv'  # Adjust the path as necessary
qrsdata = pd.read_csv(file_path_qrs)
file_path_rr='rrdata.csv'
rrdata=pd.read_csv(file_path_rr)


app = gui("ECG Sound Synthesis", "600x400")
s = Server()
s.boot().start()


def signalProcessing(data):
    # convert timestamps to seconds
    data['time'] = pd.to_numeric(data['time'])
    first_timestamp_ns = data['time'][0]
    data['relative_time_s'] = (data['time'] - first_timestamp_ns) / 1e9

    # placeholder queues for storing ecg amplitudes
    r_peak_amplitudes = []
    s_peak_amplitudes = []
    q_peak_amplitudes= []

    # placeholder lists for storing ECG indicies
    r_peak_indices = []
    s_peak_indices = []
    q_peak_indices = []

    #placeholder queue for storing qrs durations
    qrs_durations = []


    # window size to look for s-peaks and q-peaks (before/after r-peaks)
    search_window = 50


    # loop through the desired ECG lists
    for index, row in data.iterrows():
        ecg_list = np.array(eval(row['ecg']))  # Convert string list to actual list
        relative_time_s = data['relative_time_s']

        
        ''' R-Peak Extraction '''
        # detect r_peak indexes
        r_peaks, _ = find_peaks(ecg_list, height=1500)
        # find amplitudes r_peak indexes 
        for x in r_peaks:
            r_peak_amplitudes.extend(ecg_list[r_peaks])
            r_peak_indices.extend(r_peaks)


        ''' S-Peak Extraction '''
        for r_peak in r_peaks:
            # defining search window (immediately after r-peak to end of signal)
            start_index = r_peak + 1  
            end_index = min(r_peak + 1 + search_window, len(ecg_list))  
            
            # find index of minimum value in this window
            if start_index < len(ecg_list):  
                s_peaks,_ = find_peaks(((-ecg_list[start_index:end_index]) + start_index))
                s_peak_amplitudes.extend(ecg_list[s_peaks])
                s_peak_indices.extend(s_peaks + start_index)


        ''' Q-Peak Extraction '''
        for r_peak in r_peaks:
            # defining search window (start of signal until r-peak)
            start_index = max(0, r_peak - search_window)  
            end_index = r_peak
            
            if end_index > 0: 
                # find index of minimum value in this window
                q_peaks,_ = find_peaks(((-ecg_list[start_index:end_index]) + start_index))
                q_peak_amplitudes.extend(ecg_list[q_peaks])
                q_peak_indices.extend(q_peaks + start_index)


        # Function to calculate QRS durations based on the located peaks
        def calculate_qrs_durations(relative_time_s, q_peak_indices, s_peak_indices):
            for q_idx, s_idx in zip(q_peak_indices, s_peak_indices):
                qrs_duration = relative_time_s[s_idx] - relative_time_s[q_idx]
                qrs_durations.append(abs(qrs_duration/100))

        calculate_qrs_durations(relative_time_s, q_peak_indices, s_peak_indices)

    return (q_peak_amplitudes,r_peak_amplitudes, s_peak_amplitudes, list(qrs_durations) )

    

# placeholder queues for storing ecg characteristics
q_peak_amplitudes= signalProcessing(qrsdata)[0]
r_peak_amplitudes = signalProcessing(qrsdata)[1]
s_peak_amplitudes =signalProcessing(qrsdata)[2]
qrs_durations= signalProcessing(qrsdata)[3]
rr_values=rrdata['rr_interval'].tolist()


''' binaural beat '''
# frequencies for the binaural beat
base_freq = 40  # base frequency in Hz 
binaural_freq = 8  # for anxiety/stress relief, alpha freq. lie between 8-13Hz

def play_leftbinaural(base_freq):
    left = Sine(freq=base_freq, mul=0.1).out()
    return left

def play_rightbinaural(base_freq,binaural_freq):    
    right = Sine(freq=base_freq + binaural_freq, mul=0.1).out()
    return right 


''' Q-Peak sonification // Q-Peak '''
notes = [60,62,64,65,67,69,71,72]
# function to map QRS data to a melody 
def mapping(qrs_durations, notes):
    events=[]
    for item in qrs_durations:
        item = item/1000
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

def midiToHz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)
       
def playQRS(melody_events):
    for note in melody_events:
        freq = midiToHz(note)
        osc = Sine(freq=freq, mul=1)
    return osc 


''' gong sounds // RR-intervals'''
rr_intervals = [value + 3.5 for value in rr_values]
rr_mean = np.mean(rr_values)
rr_sd = np.std(rr_values)

def gongSounds(rr_intervals,rr_mean,rr_sd):
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
        gong_player.out()

    gong_player = SfPlayer(gong_file_path, speed=1.5, mul=0.5, loop=False)
    trig_update_gongmet = TrigFunc(gong_met, update_gong_met)
    xfade = Fader(fadein=0.5, fadeout=0.5, dur=0, mul=1) # crossfade envelope
    return trig_update_gongmet 


''' chime sounds // R-peaks '''
def chimeSounds():
    # path to the chime sound file
    tinkle_file_path = "sounds/tinkle.wav"

    # metro object to trigger playbacks_tink
    chime_met_time = SigTo(value=1.75, time=0.1)  # smooth transition for metro time changes
    chime_met = Metro(time=chime_met_time ).out() 

    # counter to iterate over r_peaks
    beat_count = Counter(chime_met, min=0, max=len(r_peak_amplitudes) - 1)

    # tinkle player
    tinkle_player = SfPlayer(tinkle_file_path, speed=0.75, loop=True, mul=0)

    # function to update amplitude based on r_peaks
    def update_chime_amplitude():
        idx = int(beat_count.get())
        amp = r_peak_amplitudes[idx]
        tinkle_player.setMul(amp)  # update the amplitude
        tinkle_player.out()

    trig_update_amplitude = TrigFunc(chime_met, update_chime_amplitude)
    return trig_update_amplitude 


# play binaural beat
binaural_leftbeat = play_leftbinaural(base_freq=40).out()
binaural_rightbeat = play_rightbinaural(base_freq=40, binaural_freq=8).out()

# map QRS data to melody events + play QRS sounds 
melody_events = mapping(qrs_durations, notes)
QRS_sonified = playQRS(melody_events).out()

# play gong sounds
gong_sounds = gongSounds(rr_intervals,rr_mean,rr_sd).out()

# play chime sounds
chime_sounds = chimeSounds().out()

s.gui(locals())

    
    





