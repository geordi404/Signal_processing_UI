import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolBar,
    QLabel,
    QLineEdit,
    QPushButton,
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
import pandas as pd
from PyQt6.QtWidgets import QFileDialog  # Import QFileDialog
import os
from PyQt6 import QtCore

from PyQt6.QtWidgets import QComboBox

from scipy.signal import butter, filtfilt

from data.Timeseries import Timeseries, parse_data_file_csv, parse_data_file_xdf
from typing import List


class MplCanvas(FigureCanvas):
    def __init__(
        self,
        width=5,
        height=4,
        dpi=100,
        Title="undefined",
        X_axis="undefined",
        Y_axis="undefined",
    ):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_xlabel(X_axis)
        self.axes.set_ylabel(Y_axis)
        self.axes.set_title(Title)
        self.fig.tight_layout()

    def update_canvas(
        self,
        X_values,
        Y_values,
        Title="undefined",
        X_axis="undefined",
        Y_axis="undefined",
    ):
        # self.axes.clear()
        self.axes.set_xlabel(X_axis)
        self.axes.set_ylabel(Y_axis)
        self.axes.set_title(Title)
        self.axes.plot(X_values, Y_values)
        # self.draw()


# this class is needed to make the navigation bar smaller
class CustomNavigationToolbar(NavigationToolbar):
    def __init__(self, canvas, parent, coordinates=True):
        super().__init__(canvas, parent, coordinates)
        self.setIconSize(QtCore.QSize(16, 16))  # Adjust the size as needed


class SignalViewer(QMainWindow):
    def __init__(self, sampling_rate):
        super().__init__()
        self.sampling_rate = sampling_rate  # Default sampling rate
        self.start_sample = 0  # Start sample for FFT
        self.end_sample = 500  # End sample for FFT
        self.signals_plotted: List[
            Timeseries
        ] = []  # Variable to store the generated signal
        self.time_stamps = None  # Variable to store the time array
        self.x_axis_in_seconds = True  # Initially, X-axis is in seconds
        self.file_name = "undefined"
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
        self.bottom_right_toolbar = CustomNavigationToolbar(
            self.bottom_right_panel, self
        )
        self.right_layout.addWidget(self.bottom_right_toolbar)
        self.right_layout.addWidget(self.bottom_right_panel)

        # FFT Control Panel
        self.fft_control_panel = QWidget()
        self.fft_control_layout = QHBoxLayout(self.fft_control_panel)
        self.start_sample_input = QLineEdit(str(self.start_sample))
        self.end_sample_input = QLineEdit(str(self.end_sample))
        self.Update_interval_view_button = QPushButton("Update")
        self.Update_interval_view_button.clicked.connect(
            lambda: self.Update_interval_view(self.file_name, "amplitude")
        )
        self.fft_control_layout.addWidget(QLabel("Start Sample:"))
        self.fft_control_layout.addWidget(self.start_sample_input)
        self.fft_control_layout.addWidget(QLabel("End Sample:"))
        self.fft_control_layout.addWidget(self.end_sample_input)
        self.fft_control_layout.addWidget(self.Update_interval_view_button)
        self.right_layout.addWidget(self.fft_control_panel)

        self.filter_control_panel = QWidget()
        self.filter_control_layout = QHBoxLayout(self.filter_control_panel)

        self.filter_type_dropdown = QComboBox()
        self.filter_type_dropdown.addItems(
            ["Lowpass", "Highpass", "Bandpass", "Bandstop"]
        )
        self.cutoff_freq_input = QLineEdit()
        self.filter_order_input = QLineEdit()

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.apply_filter)

        self.filter_control_layout.addWidget(QLabel("Filter Type:"))
        self.filter_control_layout.addWidget(self.filter_type_dropdown)
        self.filter_control_layout.addWidget(QLabel("Cutoff Frequency:"))
        self.filter_control_layout.addWidget(self.cutoff_freq_input)
        self.filter_control_layout.addWidget(QLabel("Filter Order:"))
        self.filter_control_layout.addWidget(self.filter_order_input)
        self.filter_control_layout.addWidget(self.apply_filter_button)

        self.right_layout.addWidget(self.filter_control_panel)

        # Save to Excel Button
        # self.save_excel_button = QPushButton("Save Signal to Excel")
        # self.save_excel_button.clicked.connect(self.save_to_excel)
        # self.right_layout.addWidget(self.save_excel_button)

        # Load from Excel Button
        self.load_excel_button = QPushButton("Load Signal from csv")
        self.load_excel_button.clicked.connect(self.load_from_csv)
        self.right_layout.addWidget(self.load_excel_button)

        # Toggle Button for X-axis view
        self.toggle_xaxis_button = QPushButton("Toggle X-Axis (Samples/Seconds)")
        self.toggle_xaxis_button.clicked.connect(self.toggle_xaxis)
        self.right_layout.addWidget(self.toggle_xaxis_button)

        # Signal selector dropdown selector
        self.signal_selector_layout = QHBoxLayout()
        self.signal_selector_dropdown = QComboBox()
        self.signal_selector_dropdown.addItems(["No Signal Loaded"])
        self.signal_selector_dropdown.currentIndexChanged.connect(
            self.signal_selector_index_changed
        )
        signal_selector_label = QLabel("Signal:")
        signal_selector_label.setFixedSize(50, 20)
        self.signal_selector_layout.addWidget(signal_selector_label)
        self.signal_selector_layout.addWidget(self.signal_selector_dropdown)
        # Create button to add/remove signals
        self.add_signal_button = QPushButton("Add")
        self.add_signal_button.clicked.connect(self.add_signal_to_plot)
        self.signal_selector_layout.addWidget(self.add_signal_button)
        self.remove_signal_button = QPushButton("Remove")
        self.remove_signal_button.clicked.connect(self.remove_signal_from_plot)
        self.signal_selector_layout.addWidget(self.remove_signal_button)

        # Add signal selector to right panel
        self.right_layout.addLayout(self.signal_selector_layout)

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
        b, a = butter(order, cutoff, btype=filter_type, fs=self.sampling_rate)

        # Apply the filter
        filtered_signal = filtfilt(b, a, self.signals_plotted)
        self.signals_plotted = filtered_signal
        # Update the plot
        self.plot_signals(self.file_name, "amplitude")

    def toggle_xaxis(self):
        self.x_axis_in_seconds = not self.x_axis_in_seconds
        self.plot_signals(self.file_name, "amplitude")

    def plot_signals(self, file_name, Y_axis):
        # update left_panel
        self.left_panel.axes.clear()
        print(self.signals_plotted)
        if self.signals_plotted is None or len(self.signals_plotted) == 0:
            return
        for signal in self.signals_plotted:
            print(f"Update graph with {signal.name}")
            if self.x_axis_in_seconds:
                self.left_panel.axes.plot(
                    signal.timestamps, signal.values, label=signal.name
                )
                x_label = "Time (Seconds)"
            else:
                self.left_panel.axes.plot(
                    signal.values,
                    label=signal.name,
                )
                x_label = "Sample Number"
        self.left_panel.axes.legend()
        self.left_panel.axes.set_xlabel(x_label)
        self.left_panel.axes.set_ylabel("Amplitude")
        self.left_panel.draw()

        self.Update_interval_view(file_name, Y_axis)

    def Update_interval_view(self, file_name, Y_axis):
        try:
            start = float(self.start_sample_input.text())
            end = float(self.end_sample_input.text())

            # Ensure the start and end are within the bounds of the signal
            self.start_sample = max(start, 0)
            self.end_sample = end
            print(f"start sample : {self.start_sample}")
            print(f"end sample : {self.end_sample}")
        except ValueError:
            # Handle invalid input
            print("Invalid start or end sample input.")
            return

        # Use the stored signal for analysis
        if self.signals_plotted is not None:
            # Determine the FFT window size

            N = self.end_sample - self.start_sample
            N_fft = N / 2
            if N <= 0:
                print("Invalid FFT window size.")
                return

            # Update the top right panel (Temporal View)
            self.Update_Temporal_interval_view(
                N, title=str("interval view on " + str(N) + " samples")
            )

            # Perform FFT analysis

            # self.perform_fft(N)

    def Update_Temporal_interval_view(self, N, title):
        self.top_right_panel.axes.clear()
        for signal in self.signals_plotted:
            if self.x_axis_in_seconds:
                x_label = "Time (Seconds)"
                # Get the min index of the signal to plot
                min_index = min(
                    [
                        index
                        for index, value in enumerate(signal.timestamps)
                        if self.start_sample <= value <= self.end_sample
                    ]
                )
                max_index = max(
                    [
                        index
                        for index, value in enumerate(signal.timestamps)
                        if self.start_sample <= value <= self.end_sample
                    ]
                )
                print (f"min_index : {min_index}")
                print (f"max_index : {max_index}")
                print (f"len(signal.timestamps) : {len(signal.timestamps)}")
                print (f"len(signal.values) : {len(signal.values)}")
                
                print(f"signal.timestamps[min_index:min_index] : {signal.timestamps[min_index:min_index]}")
                print(f"signal.values[min_index:max_index] : {signal.values[min_index:max_index]}")
                self.top_right_panel.axes.plot(
                    signal.timestamps[min_index:max_index],
                    signal.values[min_index:max_index],
                    label=signal.name,
                )
            else:
                self.top_right_panel.axes.plot(
                    signal.values[
                        int(self.start_sample) : int(self.end_sample)
                        if self.end_sample < len(signal.values)
                        else len(signal.values)
                    ],
                    label=signal.name,
                )
                x_label = "Sample Number"
        self.top_right_panel.axes.set_xlabel(x_label)
        self.top_right_panel.axes.set_ylabel("Amplitude")
        self.top_right_panel.axes.set_title(title)
        self.top_right_panel.axes.legend()
        self.top_right_panel.draw()

    def perform_fft(self, N):
        y_fft = (
            np.fft.fft(self.signals_plotted[self.start_sample : self.end_sample]) / N
        )

        # Frequency resolution is equal to the sampling rate divided by the number of samples
        freq_resolution = self.sampling_rate / N
        freq = np.arange(0, self.sampling_rate / 2 + freq_resolution, freq_resolution)[
            : N // 2 + 1
        ]

        # Take only the positive half of the spectrum
        y_fft_half = y_fft[: N // 2 + 1]

        self.bottom_right_panel.update_canvas(
            freq,
            np.abs(y_fft_half),
            "FFT applied on interval",
            "Frequency (Hz)",
            "amplitude",
        )

    def save_to_excel(self):
        if self.signals_plotted is not None:
            # Create a DataFrame and save to Excel
            df = pd.DataFrame(
                {"Time": self.time_stamps, "Signal": self.signals_plotted}
            )
            try:
                self.filepath = (
                    "signal_data.xlsx"  # You can modify the file path as needed
                )
                df.to_excel(self.filepath, index=False)
                print(f"Signal data saved to {self.filepath}")
            except Exception as e:
                print(f"Error saving to Excel: {e}")

    def load_from_csv(self):
        self.filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            "",
            "CSV Files (*.csv);;Text files (*.txt);; XDF Files (*.xdf)",
        )
        if self.filepath:
            if self.filepath.endswith(".xdf"):
                self.timeseries: List[Timeseries] = parse_data_file_xdf(self.filepath)
            else:
                self.timeseries: List[Timeseries] = parse_data_file_csv(
                    self.filepath, self.sampling_rate
                )
            self.update_signal_selector()

    def update_signal_selector(self):
        """
        Updates the signal selector dropdown with the timeseries loaded from the CSV file.
        """
        self.signal_selector_dropdown.clear()
        self.signal_selector_dropdown.addItems(
            [timeseries.name for timeseries in self.timeseries]
        )
        self.signal_selector_dropdown.setCurrentIndex(0)
        self.signal_selector_index_changed(0)

    #########################
    # Signal Event Handlers #
    #########################
    def signal_selector_index_changed(self, index):
        """
        signal handler for signal selector dropdown
        """
        pass
        # self.signals = self.timeseries[index].values
        # if self.timeseries[index].timestamps is not None:
        #     self.time_stamps = self.timeseries[index].timestamps
        # else:
        #     self.time_stamps = np.arange(len(self.signals)) / self.sampling_rate
        # self.file_name = self.timeseries[index].name
        # self.plot_signals(self.file_name,"amplitude")

    def add_signal_to_plot(self):
        """
        Adds a signal to the plot.
        """
        print("add signal")
        self.signals_plotted.append(
            self.timeseries[self.signal_selector_dropdown.currentIndex()]
        )
        self.plot_signals(self.file_name, "amplitude")

    def remove_signal_from_plot(self):
        """
        Removes a signal from the plot.
        """
        print("remove signal")
        for signal in self.signals_plotted:
            if (
                signal.name
                == self.timeseries[self.signal_selector_dropdown.currentIndex()].name
            ):
                self.signals_plotted.remove(signal)
        self.plot_signals(self.file_name, "amplitude")
