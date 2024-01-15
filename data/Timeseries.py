""" This files contains the class definition for a timeseries.
    it also provide methods to parse input data files into timeseries objects.
    Description: A timeseries is a sequence of data points, measured typically at successive times, spaced at (often uniform) time intervals. 
"""
import pandas as pd
import os
from typing import List

class Timeseries:
    """
    Class representing a timeseries.
    """

    def __init__(self, data, sampling_rate, name):
        """
        Constructor for the Timeseries class.
        :param data: A list of data points.
        :param sampling_rate: The sampling rate of the timeseries.
        """
        self.values_data = data
        self.sampling_rate_data = sampling_rate
        self.name_data = name
    # Add more methods here as needed
    
    def get_sampling_rate(self):
        """
        Returns the sampling rate of the timeseries.
        :return: The sampling rate of the timeseries.
        """
        return self.sampling_rate
    
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
    
def parse_data_file(file_path, sampling_rate):
    """
    Parses a data file into a timeseries object.
    :param file_path: The path to the file to parse.
    :return: A timeseries object.
    """
    timeseries:List[Timeseries] = []
    file_name = os.path.basename(file_path)
    print(f"Loading data from {file_name} ...")
    try:
        df = pd.read_csv(file_path)
        time = df['TimeStamp (ms)'].values
        column_name = df.columns.values[1:]
        print(column_name)
        count = 0
        for column in column_name:
            data = df[column].values
            timeseries.append(Timeseries(data, sampling_rate, column))
            count += 1
        print(f"Loaded {count} timeseries from {file_name}.")
    except Exception as e:
        print(f"Error loading from CSV: {e}")
    return timeseries
