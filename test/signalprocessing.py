import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from collections import deque

file_path = 'data.csv'  # Adjust the path as necessary

while True: 
    data = pd.read_csv(file_path)
    chunk_size=2

    # convert timestamps to seconds
    data['time'] = pd.to_numeric(data['time'])
    first_timestamp_ns = data['time'][0]
    data['relative_time_s'] = (data['time'] - first_timestamp_ns) / 1e9



    # placeholder queues for storing ecg characteristics
    r_peak_amplitudes = deque()
    rr_intervals_all = deque()
    s_peak_amplitudes = deque()
    q_peak_amplitudes= deque()

    # window size to look for s-peaks and q-peaks (before/after r-peaks)
    search_window = 100


    # loop through the desired ECG lists
    for index, row in data.iterrows():
        ecg_list = np.array(eval(row['ecg']))  # Convert string list to actual list
        
        ''' R-Peak Extraction '''
        # detect r_peak indexes
        r_peaks, _ = find_peaks(ecg_list, height=1500)
        # find amplitudes r_peak indexes 
        for x in r_peaks:
            r_peak_amplitudes.extend(ecg_list[r_peaks])

        
        ''' RR Interval Extraction'''
        # Calculate RR intervals
        rr_intervals = np.diff(r_peak_amplitudes)
        rr_intervals_all.extend(rr_intervals)


        ''' S-Peak Extraction '''
        for r_peak in r_peaks:
            # defining search window (immediately after r-peak to end of signal)
            start_index = r_peak + 1  
            end_index = min(r_peak + 1 + search_window, len(ecg_list))  
            
            # find index of minimum value in this window
            if start_index < len(ecg_list):  
                s_peaks,_ = find_peaks(((-ecg_list[start_index:end_index]) + start_index),height=0)
                s_peak_amplitudes.extend(ecg_list[s_peaks])


        ''' Q-Peak Extraction '''
        for r_peak in r_peaks:
            # defining search window (start of signal until r-peak)
            start_index = max(0, r_peak - search_window)  
            end_index = r_peak
            
            if end_index > 0: 
                # find index of minimum value in this window
                q_peaks,_ = find_peaks(((-ecg_list[start_index:end_index]) + start_index),height=0)
                q_peak_amplitudes.extend(ecg_list[q_peaks])



    # Example output of R-peaks and RR intervals for the first list
    print("R-peaks:", r_peak_amplitudes)
    print("RR Intervals:", rr_intervals_all)
    print ("S Peaks:" , s_peak_amplitudes)
    print ("Q Peaks:" , q_peak_amplitudes)
