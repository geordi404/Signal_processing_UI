import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLabel, QLineEdit, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
from PyQt6.QtWidgets import QFileDialog  # Import QFileDialog
import os
from PyQt6 import QtCore

from PyQt6.QtWidgets import QComboBox

from scipy.signal import butter, filtfilt , iirnotch

from data.Timeseries import Timeseries, parse_data_file_csv, parse_data_file_xdf
from typing import List

class MplCanvas(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100,Title="undefined",X_axis ="undefined",Y_axis="undefined"):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xlabel(X_axis)
        self.axes.set_ylabel(Y_axis)
        self.axes.set_title(Title)
        self.fig.tight_layout()  
        

    def update_canvas(self,X_values,Y_values,Title="undefined",X_axis ="undefined",Y_axis="undefined"):
        self.axes.clear()
        self.axes.set_xlabel(X_axis)
        self.axes.set_ylabel(Y_axis)
        self.axes.set_title(Title)
        self.axes.plot(X_values,Y_values)
        self.draw()
        
#this class is needed to make the navigation bar smaller
class CustomNavigationToolbar(NavigationToolbar):
    def __init__(self, canvas, parent, coordinates=True):
        super().__init__(canvas, parent, coordinates)
        self.setIconSize(QtCore.QSize(16, 16))  # Adjust the size as needed


class SignalViewer(QMainWindow):
    def __init__(self,sampling_rate):
        super().__init__()
        self.sampling_rate = sampling_rate  # Default sampling rate
        self.start_sample = 0      # Start sample for FFT
        self.end_sample = 500      # End sample for FFT
        self.signal = None         # Variable to store the generated signal

        self.signals_plotted: List[Timeseries] = []  # Variable to store the generated signal
        self.time = None           # Variable to store the time array
        self.x_axis_in_seconds = False  # Initially, X-axis is in seconds
        self.file_name= "undefined"
        # Main Widget and Layout
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.setWindowTitle("Signal Analysis Tool")
        
        # Left Panel for Whole Signal using Matplotlib
        self.left_panel = MplCanvas(width=5, height=4, dpi=100)
    
        self.left_toolbar = CustomNavigationToolbar(self.left_panel, self)
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.left_toolbar)
        self.left_layout.addWidget(self.left_panel)
        self.main_layout.addLayout(self.left_layout)

        # Right Panel for Focused Analysis
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        # Top Right Panel for Temporal View
        self.top_right_panel = MplCanvas(width=5, height=4, dpi=100)
        self.top_right_toolbar = CustomNavigationToolbar(self.top_right_panel, self)
        self.right_layout.addWidget(self.top_right_toolbar)
        self.right_layout.addWidget(self.top_right_panel)

        # Bottom Right Panel for Frequential View
        self.bottom_right_panel = MplCanvas(width=5, height=4, dpi=100)
        self.bottom_right_toolbar = CustomNavigationToolbar(self.bottom_right_panel, self)
        self.right_layout.addWidget(self.bottom_right_toolbar)
        self.right_layout.addWidget(self.bottom_right_panel)

        # FFT Control Panel
        self.fft_control_panel = QWidget()
        self.fft_control_layout = QHBoxLayout(self.fft_control_panel)
        self.start_sample_input = QLineEdit(str(self.start_sample))
        self.end_sample_input = QLineEdit(str(self.end_sample))
        self.Update_interval_view_button = QPushButton("Update")
        self.Update_interval_view_button.clicked.connect(lambda: self.Update_interval_view(self.file_name, 'amplitude'))
        self.fft_control_layout.addWidget(QLabel("Start Sample:"))
        self.fft_control_layout.addWidget(self.start_sample_input)
        self.fft_control_layout.addWidget(QLabel("End Sample:"))
        self.fft_control_layout.addWidget(self.end_sample_input)
        self.fft_control_layout.addWidget(self.Update_interval_view_button)
        self.right_layout.addWidget(self.fft_control_panel)

        self.filter_control_panel = QWidget()
        self.filter_control_layout = QHBoxLayout(self.filter_control_panel)
        
        self.filter_type_dropdown = QComboBox()
        self.filter_type_dropdown.addItems(["Lowpass", "Highpass", "Bandpass", "Bandstop","notch"])
        self.cutoff_freq_input = QLineEdit()
        self.filter_order_input = QLineEdit()

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.apply_filter)
        
        # Signal selector dropdown selector FFT
        self.signal_selector_dropdown_fft = QComboBox()
        self.signal_selector_dropdown_fft.addItems(["No Signal Loaded"])
        self.signal_selector_dropdown_fft.currentIndexChanged.connect(self.signal_selector_index_changed_fft)
        signal_selector_label_fft = QLabel("Signal: FFT")
        
        self.filter_control_layout.addWidget(signal_selector_label_fft)
        self.filter_control_layout.addWidget(self.signal_selector_dropdown_fft)
        self.filter_control_layout.addWidget(QLabel("Filter Type:"))
        self.filter_control_layout.addWidget(self.filter_type_dropdown)
        self.filter_control_layout.addWidget(QLabel("Cutoff Frequency:"))
        self.filter_control_layout.addWidget(self.cutoff_freq_input)
        self.filter_control_layout.addWidget(QLabel("Filter Order:"))
        self.filter_control_layout.addWidget(self.filter_order_input)
        self.filter_control_layout.addWidget(self.apply_filter_button)

        self.right_layout.addWidget(self.filter_control_panel)


        # Save to Excel Button
        #self.save_excel_button = QPushButton("Save Signal to Excel")
        #self.save_excel_button.clicked.connect(self.save_to_excel)
        #self.right_layout.addWidget(self.save_excel_button)

        # Load from Excel Button
        self.load_excel_button = QPushButton("Load Signal from csv")
        self.load_excel_button.clicked.connect(self.load_from_csv)
        self.right_layout.addWidget(self.load_excel_button)

        # Toggle Button for X-axis view
        self.toggle_xaxis_button = QPushButton("Toggle X-Axis (Samples/Seconds)")
        self.toggle_xaxis_button.clicked.connect(self.toggle_xaxis)
        self.right_layout.addWidget(self.toggle_xaxis_button)

        # Signal selector dropdown
        self.signal_selector_dropdown = QComboBox()
        self.signal_selector_dropdown.addItems(["No Signal Loaded"])
        self.signal_control_layout = QHBoxLayout()
        signal_selector_label = QLabel("Signal:")
        signal_selector_label.setFixedSize(50, 20)
        self.signal_control_layout.addWidget(signal_selector_label)
        self.signal_control_layout.addWidget(self.signal_selector_dropdown)
       
        self.right_layout.addLayout(self.signal_control_layout)
        self.signal_selector_dropdown.currentIndexChanged.connect(self.signal_selector_index_changed_fft)
        
        self.x_axis_in_seconds = True  # Initially, X-axis is in seconds

        # Add Right Panel to Main Layout
        self.main_layout.addWidget(self.right_panel)

        # Set Main Widget and Window Title
        self.setCentralWidget(self.main_widget)
        self.setWindowTitle("Signal Analysis Tool")












    def apply_filter(self):
        filter_type = self.filter_type_dropdown.currentText()
        cutoff = float(self.cutoff_freq_input.text())
        order = int(self.filter_order_input.text())

        # Create the filter
        if(filter_type=="notch"):
            b, a = iirnotch(cutoff, order, self.sampling_rate)
        else:
            b, a = butter(order, cutoff, btype=filter_type, fs=self.sampling_rate)
        
        # Apply the filter
        filtered_signal = filtfilt(b, a, self.signal)
        self.signal = filtered_signal
        # Update the plot
        self.plot_signals(self.file_name, "amplitude")


    def toggle_xaxis(self):
        self.x_axis_in_seconds = not self.x_axis_in_seconds
        self.plot_signals(self.file_name,"amplitude") 

    def plot_signals(self,file_name,Y_axis):
        if self.x_axis_in_seconds:
            x_axis = self.time
            x_label = "Time (Seconds)"
        else:
            x_axis = np.arange(len(self.time))
            x_label = "Sample Number"

        #update left_panel
        self.left_panel.update_canvas(x_axis,self.signal,Title=file_name,Y_axis=Y_axis,X_axis=x_label)
        self.Update_interval_view(file_name,Y_axis)
    
    def Update_interval_view(self,file_name,Y_axis):
        try:
            start = int(self.start_sample_input.text())
            end = int(self.end_sample_input.text())
 
            # Ensure the start and end are within the bounds of the signal
            self.start_sample = max(start, 0)
            self.end_sample = min(end, len(self.signal))
        except ValueError:
            # Handle invalid input
            print("Invalid start or end sample input.")
            return

        # Use the stored signal for analysis
        if self.signal is not None:
            # Determine the FFT window size
  
            N = self.end_sample - self.start_sample
            N_fft=N/2
            if N <= 0:
                print("Invalid FFT window size.")
                return

            # Update the top right panel (Temporal View)
            self.Update_Temporal_interval_view(N,title=str("interval view on "+str(N)+" samples"))

            # Perform FFT analysis

            self.perform_fft(N)

    def Update_Temporal_interval_view(self, N,title):
        if self.x_axis_in_seconds:
            x_axis = self.time[self.start_sample:self.end_sample]
            x_label = "Time (Seconds)"
        else:
            x_axis = np.arange(self.start_sample, self.end_sample)
            x_label = "Sample Number"

        self.top_right_panel.update_canvas(x_axis,self.signal[self.start_sample:self.end_sample],title)
        self.top_right_panel.axes.plot(x_axis, self.signal[self.start_sample:self.end_sample])
        self.top_right_panel.axes.set_xlabel(x_label)
        self.top_right_panel.axes.set_ylabel("Amplitude")
        self.top_right_panel.draw()

    def perform_fft(self, N):
        y_fft = np.fft.fft(self.signal[self.start_sample:self.end_sample]) / N

        # Frequency resolution is equal to the sampling rate divided by the number of samples
        freq_resolution = self.sampling_rate / N
        freq = np.arange(0, self.sampling_rate / 2 + freq_resolution, freq_resolution)[:N // 2 + 1]

        # Take only the positive half of the spectrum
        y_fft_half = y_fft[:N // 2 + 1]

        self.bottom_right_panel.update_canvas(freq,np.abs(y_fft_half),"FFT applied on interval","Frequency (Hz)","amplitude")

    def save_to_excel(self):
        if self.signal is not None:
            # Create a DataFrame and save to Excel
            df = pd.DataFrame({'Time': self.time, 'Signal': self.signal})
            try:
                self.filepath = "signal_data.xlsx"  # You can modify the file path as needed
                df.to_excel(self.filepath, index=False)
                print(f"Signal data saved to {self.filepath}")
            except Exception as e:
                print(f"Error saving to Excel: {e}")

    def load_from_csv(self):
        self.filepath, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;Text files (*.txt);; XDF Files (*.xdf)")
        if self.filepath:
            if self.filepath.endswith(".xdf"):
                self.timeseries:List[Timeseries] = parse_data_file_xdf(self.filepath)
            else:
                self.timeseries:List[Timeseries] = parse_data_file_csv(self.filepath, self.sampling_rate)
            self.update_signal_selector()
    
    def update_signal_selector(self):
        """ 
        Updates the signal selector dropdown with the timeseries loaded from the CSV file.
        """
        self.signal_selector_dropdown.clear()
        self.signal_selector_dropdown.addItems([timeseries.name for timeseries in self.timeseries])
        self.signal_selector_dropdown.setCurrentIndex(0)
        self.signal_selector_index_changed_fft(0)

    #########################
    # Signal Event Handlers #
    #########################
    def signal_selector_index_changed_fft(self, index):
        """ 
        signal handler for signal selector dropdown 
        """
        self.signal = self.timeseries[index].values
        self.time = np.arange(len(self.signal)) / self.sampling_rate
        self.file_name = self.timeseries[index].name
        self.plot_signals(self.file_name,"amplitude")
