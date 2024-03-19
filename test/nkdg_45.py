import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import numpy as np
import neurokit2 as nk
from scipy import signal
from scipy.signal import find_peaks

import csv
import random
import time
import os

''' saving to csv: '''
# function to write selected values from _y into the CSV file
def write_to_csv(csv_writer, values,rr,):

    info = {
        "p": values[14],
        "q": values[0],
        "r": values[3],
        "s": values[5],
        "t": values[11],
        "rr": rr,
    }
    csv_writer.writerow(info)


''' creating ECG signal: '''
plt.rcParams["figure.figsize"] = (12,4)

N = 2**10 # symbolises the number of datapoints in the simulation
heart_rate = 75
rest_period = 0.5
noise_amplitude = 0.01 

lwL = 2
lwR=1

_t = np.linspace(0,N,N) # represents time 

# create a Daubechies wavelet as the template for the heart signal
pqrst = signal.wavelets.daub(10)

# add the gap after the pqrst when the heart is resting.
samples_rest = int(rest_period * (N / len(pqrst)))
zero_array = np.zeros(samples_rest, dtype=float)
pqrst_full = np.concatenate([pqrst, zero_array])

# repeat the template to cover the entire signal
num_beats = N // len(pqrst_full) + 1
ecg_template = np.tile(pqrst_full, num_beats)[:N]

# combine all components to create ECG signal
_y =ecg_template + np.random.normal(loc=0, scale=noise_amplitude, size=N)

#find rr vals
peaks, _ = find_peaks(_y, height=0)
rr_intervals = np.diff(_t[peaks]) 
print (rr_intervals/10)

fieldnames = ["p", "q", "r", "s", "t", "rr"]

with open('data.csv', 'a', newline='') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    # Assuming _y has a length greater than or equal to 20
    for i in range(0, len(rr_intervals), 20):
        selected_values = _y[i:i+20]
        write_to_csv(csv_writer, selected_values,rr_intervals[i]/10)


dframe= np.full(N+1, fill_value=np.nan, dtype=np.cfloat) # initialise a dataframe with NaN values
t = np.tile(_t,(N,1)) # create grids for time
y=np.tile(_y,(N,1)) # create grids for signal values, 'tile' creates 2D arrays

for i in range (N):
    t[i,i+1:] = np.nan 
    y[i,i+1:] = np.nan # the upper triangular part of the arrays t and y is set to NaN.



''' plotting real-time figure: '''
# set up figure, axes
def getfigax():
    fig,(axL) = plt.subplots(ncols=1,tight_layout=True)
    axL.set(xlabel=' time ', ylabel=' ecg amplitude ')

    titL  = axL.set_title("Simulator")
    axL.grid()
    lineL,= axL.plot([],[],lw=lwL)


    return fig,axL,titL,lineL

# define update function
def update(frame,frame_times):
    frame_times[frame] = time.perf_counter()
    y2 = 1000*np.diff(frame_times)
    titL.set_text(" ECG Simulation ")

    lineL.set_data(t[frame],y[frame])


    rescale = False

    # check if data exceeds any boundaries, add a small increment to each boundary and rescale entire plot only when required
    if y[frame,frame] < axL.get_ylim()[0]:
        axL.set_ylim(y[frame,frame] - 0.1, axL.get_ylim()[1])
        rescale = True
    
    if y[frame,frame]> axL.get_ylim()[1]:
        axL.set_ylim(axL.get_ylim()[0],y[frame,frame] + 0.1 )
        rescale = True

    if t[frame,frame]>axL.get_xlim()[1]:
        axL.set_xlim(axL.get_xlim()[0], axL.get_xlim()[1] + N/5)
        rescale =True

    if rescale == len(t) - 1:
        rescale = True
    
    if rescale:
        fig.canvas.draw()

    return (lineL,titL)

fig, axL ,titL, lineL = getfigax()
fig.suptitle(" Simulator Application ")
ani = FuncAnimation(fig, update, interval=100, fargs=(dframe,),repeat=False, frames=list(range(N)), blit=True)

plt.show()



