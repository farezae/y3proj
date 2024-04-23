import numpy as np
import pandas as pd
import numpy as np
import neurokit2 as nk
import re

from pyo import *
from scipy.signal import find_peaks
from collections import deque
from appJar import gui 


''' pre requisites '''
file_path_qrs = 'testdata/02ecgdata.csv'  # Adjust the path as necessary
qrsdata = pd.read_csv(file_path_qrs)
file_path_rr='testdata/02rrdata.csv'
rrdata=pd.read_csv(file_path_rr)

arr=np.array([])
offsets=[0]
times=[]


s = Server().boot().start()
osc= Sine()

''' signal processing '''
def signalProcessing(data,arr,offsets,times):
    for item in range(0,len(qrsdata)): 
        # clean, convert & standardise data so it is ready for processing
        clean = re.sub(r'[^\d.\s]', '', qrsdata.loc[item, 'ecg'])
        conversion = np.array([float(num) for num in clean.split()])

        # create numpy arrays that contain data and timestamps seperately 
        arr = np.append(arr,conversion)
        offsets.append(len(arr))
        times.append(qrsdata.loc[item, 'time'])

    # put data through processing using 'ecg_processing()' 
    signals, info = nk.ecg_process(arr, sampling_rate=50,method='neurokit')

    qrs_durations = []
    r_peaks = info['ECG_R_Peaks'] # storing r-peak results
    q_peaks = info['ECG_Q_Peaks'] # storing q-peak results
    s_peaks = info['ECG_S_Peaks'] # storing s-peak results

    # qrs duration processing 
    for r in r_peaks:
        # find the nearest Q and S peaks around each R peak
        q = max([q for q in q_peaks if q < r], default=None)
        s = min([s for s in s_peaks if s > r], default=None)

        if q is not None and s is not None:
            # calculate the QRS duration in terms of samples
            qrs_duration_samples = s - q

            # convert samples to time using sampling rate
            qrs_duration_seconds = qrs_duration_samples / 50  # Sampling rate
            qrs_durations.append(qrs_duration_seconds)

    rr_values = [0.9,0.8,1.2,1.1,0.9,0.7,0.5,0.8,0.7]

    return{
        "R Peaks": r_peaks,
        "Q Peaks": q_peaks,
        "S Peaks": s_peaks,
        "QRS Durations": qrs_durations,
        "RR Values": rr_values
        }


''' binaural beat '''
# creating two slightly different sine waves for each ear
# base frequency in Hz 
def play_leftbinaural(base_freq):
    left = Sine(freq=base_freq, mul=0.5).out()
    return left

# binaural freq. for anxiety/stress relief, alpha freq. lie between 8-13Hz
def play_rightbinaural(base_freq,binaural_freq):    
    right = Sine(freq=base_freq + binaural_freq, mul=1).out()
    return right 


''' QRS sonification '''
# function to map QRS data to a melody 
def mapping(qrs_data, notes=[60,62,64,65,67,69,71,72]):
    events=[]
    for item in qrs_data:
        # 8 notes, 0.1-0.005/8=0.011875
        if item <= 0.125:
            events.append(notes[0])
        elif 0.125 < item <= 0.25:
            events.append(notes[1])
        elif 0.25 < item <= 0.375:
            events.append(notes[2])
        elif 0.375 < item <= 0.5:
            events.append(notes[3])
        elif 0.5 < item <= 0.625:
            events.append(notes[4])
        elif 0.625 < item <= 0.75:
            events.append(notes[5])
        elif 0.75 < item <= 0.875:
            events.append(notes[6])
        elif 0.875 < item <= 1:
            events.append(notes[7])
        else: 
            events.append(notes[4]) # median duration
    return events

# used to convert notes to their corresponding frequency 
def midiToHz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)

# synthesises the final melody  
def playQRS(melody_events):
    global osc
    for note in melody_events:
        freq = midiToHz(note)
        osc= Sine(freq=freq, mul=0.5)
    return osc

''' singing bowl sounds '''
def bowlSounds(data):
    # path to the bowl sound file
    bowl_file_path = "sounds/singingbowl.wav"

    bowl_met_time = SigTo(value=1, time=3)  
    bowl_met = Metro(time=bowl_met_time).out()  


    beat_count = Counter(bowl_met, min=0, max=len(data['S Peaks']) - 1)
    bowl_player = SfPlayer(bowl_file_path, speed=1.5, loop=False, mul=0)

    # update amplitude based on s_peaks
    def update_bowl_amplitude():
        idx = int(beat_count.get())
        amp = float((data['S Peaks'])[idx])/100
        bowl_player.setMul(amp)  # update the amplitude
        bowl_player.out()

    trig_update_amplitude = TrigFunc(bowl_met, update_bowl_amplitude)
    return trig_update_amplitude


''' gong sounds '''
def gongSounds(data):
    rr_intervals = [value + 3.5 for value in data['RR Values']]
    rr_mean = np.mean(data['RR Values'])
    rr_sd = np.std(data['RR Values'])

    # path to the gong sound file
    gong_file_path = "sounds/gong.wav"

    # metro objects + counter definition 
    gong_met_time = SigTo(rr_intervals[0], time=float(rr_mean))
    gong_met = Metro(time=gong_met_time).out()
    beat_count_gong = Counter(gong_met)


    # function to update Metro time
    def update_gong_met():
        next_interval = rr_intervals[int(beat_count_gong.get()) % len(rr_intervals)]
        gong_met_time.setValue(next_interval)
        gong_met.setTime(next_interval)
        xfade.play()
        gong_player.out()

    gong_player = SfPlayer(gong_file_path, speed=1.5, mul=0.5, loop=False)
    trig_update_gongmet = TrigFunc(gong_met, update_gong_met)
    gong_reverb = Freeverb(gong_player.mix(2), size=0.9, damp=0.4, bal=0.4).out()
    xfade = Fader(fadein=0.5, fadeout=0.5, dur=0, mul=1) # crossfade envelope

    return trig_update_gongmet



''' chime sounds '''
def chimeSounds(data):
    # path to the chime sound file
    chime_file_path = "sounds/tinkle.wav"

    # metro object to trigger 
    chime_met_time = SigTo(value=1.75, time=0.1)  # smooth transition for metro time changes
    chime_met = Metro(time=chime_met_time ).out() 

    # counter to iterate over r_peaks
    beat_count_chime = Counter(chime_met, min=0, max=len(data['R Peaks']) - 1)
    # chime player
    chime_player = SfPlayer(chime_file_path, speed=0.75, loop=False, mul=0)

    # function to update amplitude based on r_peaks
    def update_chime_amplitude():
        idx = int(beat_count_chime.get())
        amp  = float((data['R Peaks'])[idx])
        chime_player.setMul(amp/100)  # update the amplitude
        chime_player.out()

    trig_update_amplitude = TrigFunc(chime_met, update_chime_amplitude)
    return trig_update_amplitude


''' process data '''
data = signalProcessing(qrsdata,arr,offsets,times)

''' play sounds '''
# play binaural beat
binaural_leftbeat = play_leftbinaural(base_freq=40).out()
binaural_rightbeat = play_rightbinaural(base_freq=40, binaural_freq=8).out()

# map QRS data to melody events + play QRS sounds 
melody_events = mapping(data['QRS Durations'], notes=[60,62,64,65,67,69,71,72])
QRS_sonified = playQRS(melody_events).out()

# play singing bowl sounds
singing_bowl_sounds = bowlSounds(data).out()
# play gong sounds
gong_sounds = gongSounds(data).out()

# play chime sounds
chime_sounds = chimeSounds(data).out()
s.gui(locals())


    







