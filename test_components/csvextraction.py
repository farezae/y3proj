import sys
import asyncio
from bleak import BleakScanner, BleakClient
# Allow importing bleakheart from parent directory
sys.path.append('../')
from bleakheart import PolarMeasurementData 


import matplotlib.pyplot as plt 
import pandas as pd
import numpy as np
import csv

from matplotlib.animation import FuncAnimation
from matplotlib import style
from itertools import count

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

 
    ecgfieldnames = ["time", "ecg"]
    with open('02ecgdata.csv', 'w') as csv_file:
            csv_writer = csv.DictWriter(csv_file,fieldnames=ecgfieldnames)
            csv_writer.writeheader()

    rrfieldnames = ["time", "rr"]
    with open('02rrdata.csv', 'w') as csv_file:
            csv_writer = csv.DictWriter(csv_file,fieldnames=rrfieldnames)
            csv_writer.writeheader()   
           
    while True:
        ecg_frame = await ecgqueue.get()
        hr_frame = await hrqueue.get()
 
        if ecg_frame[0]=='QUIT':   # intercept exit signal
            break
            

        with open('02ecgdata.csv', 'a') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=ecgfieldnames)

            info = {
                "time": ecg_frame[1],
                "ecg": ecg_frame[2],
            }

            csv_writer.writerow(info)

        with open('02rrdata.csv', 'a') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=rrfieldnames)

            info = {
                "time": ecg_frame[1],
                "rr": ecg_frame[2][1],
            }

            csv_writer.writerow(info)

        


        
       

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

# execute the main coroutine
asyncio.run(main())


