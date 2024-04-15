import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from collections import deque


def signalProcessingQRS(x):
    # loading
    file_path = 'data.csv'  # Adjust the path as necessary
    data = pd.read_csv(file_path)

    # convert timestamps to seconds
    data['time'] = pd.to_numeric(data['time'])
    first_timestamp_ns = data['time'][0]
    data['relative_time_s'] = (data['time'] - first_timestamp_ns) / 1e9



    # placeholder queues for storing ecg characteristics
    r_peak_amplitudes = deque()
    s_peak_amplitudes = deque()
    q_peak_amplitudes= deque()

    # Placeholder lists for storing ECG characteristics and their timestamps
    r_peak_indices = deque()
    s_peak_indices = deque()
    q_peak_indices = deque()
    qrs_durations = deque()


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

    # Example output of R-peaks and RR intervals for the first list
    print("R-peaks:", r_peak_amplitudes)
    print ("S Peaks:" , s_peak_amplitudes)
    print ("Q Peaks:" , q_peak_amplitudes)
    calculate_qrs_durations(relative_time_s, q_peak_indices, s_peak_indices)
    print("QRS Durations (s):", list(qrs_durations))