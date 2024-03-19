
from pyo import *
import numpy as np
import random

# QRS avg data: between 0.005 and 0.1
QRS_data = []
for i in range (0,30):
    x=random.uniform(0.005,0.1)
    QRS_data.append(x)

print (QRS_data)

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
    print (events)
    return events

def midiToHz(midi_note):
    return 440 * 2 ** ((midi_note - 69) / 12)
       
    
def play_melody(melody_events):    
    for note in melody_events:
        freq = note
        osc = Sine(freq=freq, mul=0.5)
    
    return osc 
    
    

s = Server().boot().start()
# map QRS data to melody events
melody_events = mapping(QRS_data, notes)
x= play_melody(melody_events).out()

s.gui(locals())



