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

from scipy.signal import find_peaks
from bleak import BleakScanner, BleakClient
# Allow importing bleakheart from parent directory
sys.path.append('../')
from bleakheart import PolarMeasurementData 
from bleakheart import HeartRate

# INSTANT_RATE is unsupported when UNPACK is False
UNPACK = True
INSTANT_RATE= UNPACK and True

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

        heartrate = HeartRate(client, hrqueue=hrqueue,
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



async def run_consumer_task(ecgqueue,hrqueue,ecg_outqueue,rr_outqueue):
    """ This task retrieves ECG data from the queue and does 
    all the processing. You should ensure it returns control before 
    the next frame is received from the sensor. 

    In this example, we simply prints decoded ECG data as it 
    is received """
    print("After connecting, will print ECG data in the form")
    print("('ECG', tstamp, [s1,S2,...,sn])")
    print("where samples s1,...sn are in microVolt, tstamp is in ns")
    print("and it refers to the last sample sn.")

    while True:
        ecg_frame = await ecgqueue.get()
        hr_frame = await hrqueue.get()
        
        if (ecg_frame[0]=='QUIT'):   # intercept exit signal
            break

        processed_ecg_data = ecg_signalprocessing(ecg_frame)
        processed_rr_data = rr_signalprocessing(hr_frame)

        print(" ecg: ", processed_ecg_data)
        print (" hr: ", processed_rr_data)



        
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

    ecg_outqueue = asyncio.Queue()
    rr_outqueue = asyncio.Queue()

    # producer task will return when the user hits enter or the
    # sensor disconnects
    producer=run_ble_client(device, ecgqueue,hrqueue)
    consumer=run_consumer_task(ecgqueue, hrqueue)


    # wait for the two tasks to exit
    await asyncio.gather(producer, consumer)
    print("Bye.")



async def push_out(ecg_outqueue,rr_outqueue): 
    while True: 
        ecg_items = await ecg_outqueue.get() 
        rr_items = await rr_outqueue.get()

        if ecg_items and rr_items > 0: 
            melodyGeneration(ecg_items, rr_items)


def melodyGeneration(ecg,rr):
    pass

def rr_signalprocessing(data):
    return (data[2][1])

def ecg_signalprocessing(data):
    arr=np.array([])
    offsets=[0]
    times=[]

    clean = re.sub(r'[^\d.\s]', '', data['ecg'])
    conversion = np.array([float(num) for num in clean.split()])

    # create numpy arrays that contain data and timestamps seperately 
    arr = np.append(arr,conversion)
    offsets.append(len(arr))
    times.append(data['time'])

    signals, info = nk.ecg_process(arr, sampling_rate=50,method='neurokit')

    qrs_durations = []
    r_peaks = info['ECG_R_Peaks']
    q_peaks = info['ECG_Q_Peaks']
    s_peaks = info['ECG_S_Peaks']

    # qrs duration processing 
    for r in r_peaks:
        # Find the nearest Q and S peaks around each R peak
        q = max([q for q in q_peaks if q < r], default=None)
        s = min([s for s in s_peaks if s > r], default=None)

        if q is not None and s is not None:
            # Calculate the QRS duration in terms of samples
            qrs_duration_samples = s - q

            # Convert samples to time using sampling rate
            qrs_duration_seconds = qrs_duration_samples / 50  # Sampling rate
            qrs_durations.append(qrs_duration_seconds)


    return{
        "R Peaks": r_peaks,
        "Q Peaks": q_peaks,
        "S Peaks": s_peaks,
        "QRS Durations": qrs_durations
        }





# execute the main coroutine
asyncio.run(main())
