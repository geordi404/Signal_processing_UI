""" This files contains the class definition for a timeseries.
    it also provide methods to parse input data files into timeseries objects.
    Description: A timeseries is a sequence of data points, measured typically at successive times, spaced at (often uniform) time intervals. 
"""
import pandas as pd
import os
from typing import List
import pyxdf
import numpy as np

from scipy.interpolate import interp1d
class Timeseries:
    """
    Class representing a timeseries.
    """

    def __init__(self, data, sampling_rate, name, timestamps=None):
        """
        Constructor for the Timeseries class.
        :param data: A list of data points.
        :param sampling_rate: The sampling rate of the timeseries.
        """
        self.values_data = data
        self.timestamps_data = timestamps
        self.sampling_rate_data = sampling_rate
        self.name_data = name

    # Add more methods here as needed

    def get_sampling_rate(self):
        """
        Returns the sampling rate of the timeseries.
        :return: The sampling rate of the timeseries.
        """
        return self.sampling_rate_data

    def set_sampling_rate(self, sampling_rate):
        """
        Sets the sampling rate of the timeseries.
        :param sampling_rate: The sampling rate of the timeseries.
        """
        self.sampling_rate_data = sampling_rate

    sampling_rate = property(get_sampling_rate, set_sampling_rate)

    def get_data(self):
        """
        Returns the data of the timeseries.
        :return: The data of the timeseries.
        """
        return self.values_data

    def set_data(self, data):
        """
        Sets the data of the timeseries.
        :param data: The data of the timeseries.
        """
        self.values_data = data

    values = property(get_data, set_data)

    def set_name(self, name):
        """
        Sets the name of the timeseries.
        :param name: The name of the timeseries.
        """
        self.name_data = name

    def get_name(self):
        """
        Returns the name of the timeseries.
        :return: The name of the timeseries.
        """
        return self.name_data

    name = property(get_name, set_name)

    def set_timestamps(self, timestamps):
        """
        Sets the timestamps of the timeseries.
        :param timestamps: The timestamps of the timeseries.
        """
        self.timestamps_data = timestamps

    def get_timestamps(self):
        """
        Returns the timestamps of the timeseries.
        :return: The timestamps of the timeseries.
        """
        return self.timestamps_data

    timestamps = property(get_timestamps, set_timestamps)


def parse_data_file_csv(file_path, target_sampling_rate, timeseries: List[Timeseries]):
    """
    Parses a data file, synchronizes start times of signals, and resamples them to a target sampling rate.
    :param file_path: Path to the CSV file.
    :param target_sampling_rate: Desired sampling rate (in Hz).
    :param timeseries: List to append the resulting Timeseries objects to.
    :return: Updated list of Timeseries objects.
    """
    file_name = os.path.basename(file_path)
    print(f"Loading data from {file_name} ...")
    try:
        df = pd.read_csv(file_path)
    
        # Determine the time column and convert it if necessary
        if df.columns[0] == 'time':
            original_time = df['time'].values  # Already in seconds
        elif df.columns[0] == 'TimeStamp (ms)':
            original_time = df['TimeStamp (ms)'].values * 0.001  # Convert from ms to seconds
        else:
            raise ValueError("Unknown time column name")
        # Find the minimum start time across signals if they are supposed to start at the same time
        # For individual signal adjustment, this part needs to be adapted
        min_start_time = np.min(original_time)
        
        # Calculate new start time based on the need to start at 0
        start_offset = min_start_time  # Assuming the earliest signal starts at 0 after adjustment
        
        # Create a new, regularly spaced time vector starting from 0
        total_duration = original_time[-1] - min_start_time
        new_time_vector = np.arange(0, total_duration, 1 / target_sampling_rate)
        
        column_names = df.columns[1:]  # Skip the first column assuming it's the time column
        print(f"Column names: {column_names}")
        count = 0
        for column in column_names:
            # Shift original time series to start at 0 and interpolate
            shifted_time = original_time - start_offset
            interpolator = interp1d(shifted_time, df[column], bounds_error=False, fill_value=0)  # Extend with zeros outside original range
            resampled_data = interpolator(new_time_vector)
            
            # Append the new, resampled timeseries to the list
            timeseries.append(Timeseries(resampled_data, target_sampling_rate, column, new_time_vector))
            count += 1
        
        print(f"Loaded and resampled {count} timeseries from {file_name}.")
    except Exception as e:
        print(f"Error loading and resampling from CSV: {e}")
    return timeseries


def parse_data_file_xdf(file_path):
    file_name = os.path.basename(file_path)
    print(f"Loading data from {file_name} ...")
    data, header = pyxdf.load_xdf(file_path)

    timeseries: List[Timeseries] = []
    count = 0
    for stream in data:
        channel_count = int(stream["info"]["channel_count"][0])
        for ch in range(channel_count):
            # Create a new timeseries object for each stream and channel
            timeseries.append(
                Timeseries(
                    stream["time_series"][:,ch],
                    stream["info"]["nominal_srate"][0],
                    f"{stream['info']['name'][0]}_{ch}",
                    stream["time_stamps"],
                )
            )
            count += 1
    print(f"Loaded {count} timeseries from {file_name}.")
    return timeseries
