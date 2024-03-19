import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import numpy as np

plt.rcParams["figure.figsize"] = (12,4)

N = 2**10 # symbolises the number of datapoints in the simulation

lwL = 2
lwR=1

_t = np.linspace(0,N,N) # represents time 
_y = (1 + np.sin(5/N*2*np.pi*_t)) * (1+np.cos(2/N*2*np.pi*_t)) *\
     (0.9 * _t/N + 0.3) +\
     np.random.normal(loc=0.1,scale=0.01,size=N) # represents signal



dframe= np.full(N+1, fill_value=np.nan, dtype=np.cfloat) # initialise a dataframe with NaN values

t = np.tile(_t,(N,1)) # create grids for time
y=np.tile(_y,(N,1)) # create grids for signal values, 'tile' creates 2D arrays


for i in range (N):
    t[i,i+1:] = np.nan 
    y[i,i+1:] = np.nan # the upper triangular part of the arrays t and y is set to NaN.



# set up figure, axes
def getfigax():
    fig,(axL) = plt.subplots(ncols=1,tight_layout=True)
    axL.set(xlabel='x (L)', ylabel='y (L)')
    titL  = axL.set_title("Simulator")
    axL.grid()
    lineL,= axL.plot([],[],lw=lwL)


    return fig,axL,titL,lineL

# define update function
def update(frame,frame_times):
    frame_times[frame] = time.perf_counter()
    y2 = 1000*np.diff(frame_times)
    y2_avg = np.nanmean(y2)
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
ani = FuncAnimation(fig, update, interval=10, fargs=(dframe,),repeat=False, frames=list(range(N)), blit=True)

plt.show()