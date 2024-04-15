import neurokit2 as nk
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import ssl
from scipy import signal

ssl._create_default_https_context = ssl._create_unverified_context

# Simulate 30 seconds of ECG Signal (recorded at 250 samples / second)
ecg_signal = nk.ecg_simulate(duration=420, sampling_rate=50, method="ecgsyn")

print (ecg_signal)
# Automatically process the (raw) ECG signal
#signals, info = nk.ecg_process(ecg_signal, sampling_rate=250)


'''_, waves_peak = nk.ecg_delineate(ecg_signal, 
                                 rpeaks=None, 
                                 sampling_rate=1000, 
                                 method="peak", 
                                 show=True, 
                                 show_type='peaks')'''

'''ecg_signal = nk.data(dataset="ecg_1000hz")
print(ecg_signal)'''

'''_, rpeaks = nk.ecg_peaks(ecg_signal, sampling_rate=1000)
print ("rpeaks: ", rpeaks)'''

'''# Visualize
ecg50 = nk.ecg_simulate(duration=10, noise=0.01, heart_rate=50)
ecg_df = pd.DataFrame({"ECG_100": ecg50})
nk.signal_plot(ecg_df)
print (ecg_df)
plt.show()'''

'''# breaking down pqrst wavelets
pqrst = signal.wavelets.daub(10)

# Plot the Daubechies wavelet
plt.plot(pqrst, marker='o', linestyle='-', color='b')
plt.title("Daubechies Wavelet")
plt.xlabel("Coefficient Index")
plt.ylabel("Coefficient Value")
plt.grid(True)
plt.show()'''
