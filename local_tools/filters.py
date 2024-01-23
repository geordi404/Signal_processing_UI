from scipy import signal
import math
import numpy as np

def butter_bandpass(lowcut, highcut, fs, order=5):
    b, a = signal.iirfilter(order, Wn=[lowcut, highcut], fs=fs, btype="bandpass", ftype="butter")
    return b, a

def butter_stoppass(lowcut, highcut, fs, order=5):
    b, a = signal.iirfilter(order, Wn=[lowcut, highcut], fs=fs, btype="bandstop", ftype="butter")
    return b, a

def butter_highpass(fcut, fs, order=5):
    b, a = signal.iirfilter(order, Wn=fcut, fs=fs, btype="high", ftype="butter")
    return b, a

def butter_lowpass(fcut, fs, order=5):
    b, a = signal.iirfilter(order, Wn=fcut, fs=fs, btype="lowpass", ftype="butter")
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y

def butter_stoppass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_stoppass(lowcut, highcut, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y

def butter_highpass_filter(data, fcut, fs, order=5):
    b, a = butter_highpass(fcut, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y

def butter_lowpass_filter(data, fcut, fs, order=5):
    b, a = butter_lowpass(fcut, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y


def normalize_range(signal):
    norm_signal = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))
    return 2 * norm_signal - 1

def apply_geordi_filtering(y, fs): 
    f60Hz = 60 # Frequency to be removed from signal (Hz)
    Q = 10  # Quality factor
    
    # Sample frequency (Hz) and cutoff frequency (Hz)
    
    fc = 2  # Cutoff frequency for the high-pass filter
    
    # Design a high-pass Butterworth filter
    order = 4  # Filter order (you can adjust this as needed)
    
    b, a = signal.iirnotch(f60Hz, Q, fs)
    Q2 = 30  # Quality factor
    b2, a2 = signal.iirnotch( f60Hz*2, Q2, fs)
    Q3 = 30  # Quality factor
    b3, a3 = signal.iirnotch( f60Hz*3, Q3, fs)
    f17Hz = 17 # Frequency to be removed from signal (Hz)
    Q3 = 30  # Quality factor
    b4, a4 = signal.iirnotch(f17Hz, Q3, fs)
    Q3 = 30  # Quality factor
    b5, a5 = signal.iirnotch(f17Hz*2, Q3, fs)
    Q3 = 30  # Quality factor
    b6, a6 = signal.iirnotch(f17Hz*3, Q3, fs)
    Q3 = 30  # Quality factor
    b7, a7 = signal.iirnotch(f17Hz*4, Q3, fs)
    Q3 = 30  # Quality factor
    b8, a8 = signal.iirnotch(f17Hz*5, Q3, fs)
    Q3 = 30  # Quality factor
    b9, a9 = signal.iirnotch(f17Hz*6, Q3, fs)
    fc = 50  # Cutoff frequency for the low-pass filter (Hz)
    low_pass_order = 4  # The order of the low-pass filter (you can adjust this)
    b_low, a_low = signal.butter(low_pass_order, fc / (fs / 2), 'low')
    
    high_pass_order = 4
    # Designing the high pass filter
    b_high, a_high = signal.butter(high_pass_order, 4 / (fs / 2), 'high')
    
    y = signal.filtfilt(b, a, y)
    y = signal.filtfilt(b2, a2, y)
    y = signal.filtfilt(b3, a3, y)
    y = signal.filtfilt(b4, a4, y)
    y = signal.filtfilt(b5, a5, y)
    y = signal.filtfilt(b6, a6, y)
    y = signal.filtfilt(b7, a7, y)
    y = signal.filtfilt(b8, a8, y)
    y = signal.filtfilt(b9, a9, y)
    y = signal.filtfilt(b_low, a_low, y)
    y = signal.filtfilt(b_high, a_high, y)
    return y