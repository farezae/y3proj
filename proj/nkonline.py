""" 
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Copyright (C) 2023 Fabrizio Smeraldi <fabrizio@smeraldi.net>
"""

""" ECG acquisition using an asynchronous queue - producer/consumer model """

import sys
import asyncio
import numpy as np
import pandas as pd
import neurokit2 as nk
import re

from pyo import *
from scipy.signal import find_peaks
from collections import deque
from bleak import BleakScanner, BleakClient
# Allow importing bleakheart from parent directory
sys.path.append('../')
from bleakheart import PolarMeasurementData 
from bleakheart import HeartRate

# INSTANT_RATE is unsupported when UNPACK is False
UNPACK = True
INSTANT_RATE= UNPACK and True

class EarlyReturnException(Exception):
    """Custom exception to handle early returns in sound processing."""
    pass

async def scan():
    """ Scan for a Polar device. """
    device= await BleakScanner.find_device_by_filter(
        lambda dev, adv: dev.name and "polar" in dev.name.lower())
    return device



async def run_ble_client(device, ecgqueue,hrqueue):
    """ This task connects to the BLE server (the heart rate sensor)
    identified by device, starts ECG notification and pushes the ECG 
    data to the queue. The tasks terminates when the sensor disconnects 
    or the user hits enter. """
    
    def keyboard_handler():
        """ Called by the asyncio loop when the user hits Enter """
        input() # clear input buffer
        print (f"Quitting on user command")
        quitclient.set() # causes the ble client task to exit

    
    def disconnected_callback(client):
        """ Called by BleakClient if the sensor disconnects """
        print("Sensor disconnected")
        quitclient.set() # causes the ble client task to exit


    # we use this event to signal the end of the client task
    quitclient=asyncio.Event()
    print(f"Connecting to {device}...")

    # the context manager will handle connection/disconnection for us
    async with BleakClient(device, disconnected_callback=
                           disconnected_callback) as client:
        print(f"Connected: {client.is_connected}")


        pmd=PolarMeasurementData(client, ecg_queue=ecgqueue) # create the Polar Measurement Data object; set queue for ecg data
        settings=await pmd.available_settings('ECG')  # ask about ACC settings
        print("Request for available ECG settings returned the following:")
        for k,v in settings.items():
            print(f"{k}:\t{v}")

        # Set the loop to call keyboard_handler when one line of input is
        # ready on stdin
        loop=asyncio.get_running_loop()
        loop.add_reader(sys.stdin, keyboard_handler)
        print(">>> Hit Enter to exit <<<")

        heartrate = HeartRate(client, queue=hrqueue,
                    instant_rate=INSTANT_RATE,
                    unpack=UNPACK)
        
        # start notifications for ecg; bleakheart will start pushing data to the queue we passed to PolarMeasurementData
        (err_code, err_msg, _)= await pmd.start_streaming('ECG')
        if err_code!=0:
            print(f"PMD returned an error: {err_msg}")
            sys.exit(err_code)
      
        # start notifications for hr; bleakheart will start pushing data to the queue
        await heartrate.start_notify()

        await quitclient.wait()
        if client.is_connected:
            await pmd.stop_streaming('ECG')
            await heartrate.stop_notify()
        loop.remove_reader(sys.stdin)

        # signal the consumer task to quit
        ecgqueue.put_nowait(('QUIT', None, None, None))
        hrqueue.put_nowait(('QUIT', None, None, None))



async def run_consumer_task(ecgqueue,hrqueue):
    """ This task retrieves ECG data from the queue and does 
    all the processing. You should ensure it returns control before 
    the next frame is received from the sensor. 

    In this example, we simply prints decoded ECG data as it 
    is received """
    print("After connecting, will print ECG data in the form")
    print("('ECG', tstamp, [s1,S2,...,sn])")
    print("where samples s1,...sn are in microVolt, tstamp is in ns")
    print("and it refers to the last sample sn.")

    ecg_frames_list = [] 
    hr_frames_list = []
    
    while True:
        ecg_frame = await ecgqueue.get()
        hr_frame = await hrqueue.get()
        
        
        if (ecg_frame[0]=='QUIT'):   # intercept exit signal
            break

        # continuosly append frames to individual lists 
        ecg_frames_list.append(ecg_frame)
        hr_frames_list.append(hr_frame)
        
        # once lists reach a big enough size, allow them to undergo signal processing
        if (len(ecg_frames_list) >= 10) and (len(hr_frames_list) >= 10): 
            processed_ecg_data = ecg_signalprocessing(ecg_frames_list)
            processed_rr_data = rr_signalprocessing(hr_frames_list[:5])

            melodyGeneration(processed_ecg_data,processed_rr_data)  

            # clear the lists once signal processing is complete
            ecg_frames_list.clear()
            hr_frames_list.clear()
         

        
async def main():
    print("Scanning for BLE devices")
    device=await scan()
    if device==None:
        print("Polar device not found.")
        sys.exit(-4)
    # the queue needs to be long enough to cache all the frames, since
    # PolarMeasurementData uses put_nowait
    ecgqueue=asyncio.Queue()
    hrqueue=asyncio.Queue()

    # producer task will return when the user hits enter or the
    # sensor disconnects
    producer=run_ble_client(device, ecgqueue,hrqueue)
    consumer=run_consumer_task(ecgqueue, hrqueue)


    # wait for the two tasks to exit
    await asyncio.gather(producer, consumer)
    print("Bye.")


def rr_signalprocessing(data):
    # declare empty array 'arr' to store final values 
    arr=np.array([])

    # clean, convert and standardise values
    clean_rr_data = re.sub(r'[^\d.\s]', '', str([rrdata[0] for label, timestamp, rrdata,none in data]))
    conversion = np.array([float(num) for num in clean_rr_data.split()])

    # add values to 'arr' 
    arr = np.append(arr,conversion)

    # return values as dictionary for accessibilitty 
    return {
        "RR Intervals": arr
        } 

def ecg_signalprocessing(data):
    # declare empty array 'arr' to store final values 
    arr=np.array([])

    # clean, convert and standardise values
    clean_ecg_data =  re.sub(r'[^\d.\s]', '', str([ecgdata for label, timestamp, ecgdata in data]))
    conversion = np.array([float(num) for num in clean_ecg_data.split()])

    # create numpy arrays that contain data and timestamps seperately 
    arr = np.append(arr,conversion)

    # assign value to sampling rate + process signals using neurokit package 
    samplingrate=50 
    signals, info = nk.ecg_process(arr, sampling_rate=samplingrate,method='neurokit')

    qrs_durations = []
    r_peaks = info['ECG_R_Peaks']
    q_peaks = info['ECG_Q_Peaks']
    s_peaks = info['ECG_S_Peaks']

    # qrs duration processing 
    for r in r_peaks:
        # find the nearest Q and S peaks around each R peak
        q = max([q for q in q_peaks if q < r], default=None)
        s = min([s for s in s_peaks if s > r], default=None)

        if q is not None and s is not None:
            # calculate the QRS duration in terms of samples
            qrs_duration_samples = s - q

            # convert samples to time using sampling rate formula
            qrs_duration_seconds = qrs_duration_samples / samplingrate  # sampling rate
            qrs_durations.append(qrs_duration_seconds)

    # return items as dictionary for accessibility 
    return{
        "R Peaks": r_peaks,
        "Q Peaks": q_peaks,
        "S Peaks": s_peaks,
        "QRS Durations": qrs_durations
        }


def melodyGeneration(ecgdata,rrdata):
    s = Server().boot()
    osc= Sine()
    
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
    def playQRS(ecgdata):
        melody_events = mapping(ecgdata['QRS Durations'], notes=[60,62,64,65,67,69,71,72])
        global osc
        for note in melody_events:
            freq = midiToHz(note)
            osc= Sine(freq=freq, mul=0.5)
        return osc


    ''' gong sounds '''
    def gongSounds(s,data):
        rr_intervals = data["RR Intervals"]
        print (rr_intervals)
        rr_mean = np.mean(data['RR Intervals'])
        initial = rr_intervals[0]


        # path to the gong sound file
        gong_file_path = "sounds/gong.wav"

        # metro objects + counter definition 
        gong_met_time = SigTo(float(initial), time=float(initial/10))
        gong_met = Metro(time=gong_met_time).out()

        beat_count_gong = Counter(gong_met,min=0, max=len(rr_intervals))
        gong_player = SfPlayer(gong_file_path, speed=1.5, mul=0.5, loop=False)

        # function to update Metro time
        def update_gong_met():
            idx = int(beat_count_gong.get())
            print ("updating time: ", rr_intervals[idx]/10, ",comparison: ", idx, " vs", len(rr_intervals)-1)
            if idx == (len(rr_intervals)-1):
                print ("gong data has run out!!")
                gong_player.stop()  # Stop playing once all intervals are processed
                gong_met.stop()  # Stop the metro object
                s.stop()
                raise EarlyReturnException("Early exit from gongSounds.")
            

            else:
                next_interval = float(rr_intervals[idx]/10)
                gong_met_time.setValue(next_interval)
                gong_met.setTime(next_interval)
                xfade.play()
                gong_reverb.play()
                gong_player.out()

        
        gong_reverb = Freeverb(gong_player.mix(2), size=0.9, damp=0.4, bal=0.4)
        xfade = Fader(fadein=0.5, fadeout=0.5, dur=0, mul=1) # crossfade envelope

        trig_update_gongmet = TrigFunc(gong_met, update_gong_met)
        

        return trig_update_gongmet

    ''' chime sounds '''
    def chimeSounds(data):
        print (data["R Peaks"])
        # path to the chime sound file
        chime_file_path = "sounds/tinkle.wav"

        # metro object to trigger 
        chime_met_time = SigTo(value=1.75, time=0.1)  # smooth transition for metro time changes
        chime_met = Metro(time=chime_met_time).out() 

        # counter to iterate over r_peaks
        beat_count_chime = Counter(chime_met, min=0, max=len(data['R Peaks']))
    
        # chime player
        chime_player = SfPlayer(chime_file_path, speed=0.75, loop=False, mul=0)

        # function to update amplitude based on r_peaks
        def update_chime_amplitude():
            idx = int(beat_count_chime.get())
            print ("updating amplitude: ", data['R Peaks'][idx], ",comparison: ", idx, " vs", len(data['R Peaks'])-1)
            if idx == (len(data['R Peaks'])-1):
                print ("chime data has run out!!")
                chime_met.stop()  # Stop the metro object when data runs out
                print ("chime is returning")
                return 

            else:
                amp = float(data['R Peaks'][idx])
                chime_player.setMul(amp / 100)  # update the amplitude
                chime_player.out()
        trig_update_amplitude = TrigFunc(chime_met, update_chime_amplitude)
        

        return trig_update_amplitude 

    
    def playSounds(s,ecgdata,rrdata):
        print ("reached starting point!")
        try:
            s.start()
            ''' play sounds '''
            # play binaural beat
            #binaural_leftbeat = play_leftbinaural(base_freq=40).out()
            #binaural_rightbeat = play_rightbinaural(base_freq=40, binaural_freq=8).out()

            # map QRS data to melody events + play QRS sounds 
            #QRS_sonified = playQRS(ecgdata).out()

            # play gong sounds
            gong_sounds = gongSounds(s,rrdata).out()

            # play chime sounds
            chime_sounds = chimeSounds(ecgdata).out()
            s.gui()

        except EarlyReturnException as e:
            print ("gong has returned")

    playSounds(s,ecgdata,rrdata)
    return 



# execute the main coroutine
asyncio.run(main())
