import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLabel, QLineEdit, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
from PyQt6.QtWidgets import QFileDialog  # Import QFileDialog


class MplCanvas(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

class SignalViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sampling_rate = 1000  # Default sampling rate
        self.start_sample = 0      # Start sample for FFT
        self.end_sample = 500      # End sample for FFT
        self.signal = None         # Variable to store the generated signal
        self.time = None           # Variable to store the time array
        self.x_axis_in_seconds = True  # Initially, X-axis is in seconds

        # Main Widget and Layout
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)

        

        # Left Panel for Whole Signal using Matplotlib
        self.left_panel = MplCanvas(width=5, height=4, dpi=100)
    
        self.left_toolbar = NavigationToolbar(self.left_panel, self)
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.left_toolbar)
        self.left_layout.addWidget(self.left_panel)
        self.main_layout.addLayout(self.left_layout)

        # Right Panel for Focused Analysis
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        # Top Right Panel for Temporal View
        self.top_right_panel = MplCanvas(width=5, height=4, dpi=100)
        self.top_right_toolbar = NavigationToolbar(self.top_right_panel, self)
        self.right_layout.addWidget(self.top_right_toolbar)
        self.right_layout.addWidget(self.top_right_panel)

        # Bottom Right Panel for Frequential View
        self.bottom_right_panel = MplCanvas(width=5, height=4, dpi=100)
        self.bottom_right_toolbar = NavigationToolbar(self.bottom_right_panel, self)
        self.right_layout.addWidget(self.bottom_right_toolbar)
        self.right_layout.addWidget(self.bottom_right_panel)

        # FFT Control Panel
        self.fft_control_panel = QWidget()
        self.fft_control_layout = QHBoxLayout(self.fft_control_panel)
        self.start_sample_input = QLineEdit(str(self.start_sample))
        self.end_sample_input = QLineEdit(str(self.end_sample))
        self.apply_fft_button = QPushButton("Update")
        self.apply_fft_button.clicked.connect(self.apply_fft)
        self.fft_control_layout.addWidget(QLabel("Start Sample:"))
        self.fft_control_layout.addWidget(self.start_sample_input)
        self.fft_control_layout.addWidget(QLabel("End Sample:"))
        self.fft_control_layout.addWidget(self.end_sample_input)
        self.fft_control_layout.addWidget(self.apply_fft_button)
        self.right_layout.addWidget(self.fft_control_panel)


        # Save to Excel Button
        self.save_excel_button = QPushButton("Save Signal to Excel")
        self.save_excel_button.clicked.connect(self.save_to_excel)
        self.right_layout.addWidget(self.save_excel_button)

        # Load from Excel Button
        self.load_excel_button = QPushButton("Load Signal from Excel")
        self.load_excel_button.clicked.connect(self.load_from_excel)
        self.right_layout.addWidget(self.load_excel_button)

        # Toggle Button for X-axis view
        self.toggle_xaxis_button = QPushButton("Toggle X-Axis (Samples/Seconds)")
        self.toggle_xaxis_button.clicked.connect(self.toggle_xaxis)
        self.right_layout.addWidget(self.toggle_xaxis_button)

        self.x_axis_in_seconds = True  # Initially, X-axis is in seconds


        # Add Right Panel to Main Layout
        self.main_layout.addWidget(self.right_panel)

        # Set Main Widget and Window Title
        self.setCentralWidget(self.main_widget)
        self.setWindowTitle("Signal Analysis Tool")

    def plot_signal(self):
        if self.x_axis_in_seconds:
            x_axis = self.time
            x_label = "Time (Seconds)"
        else:
            x_axis = np.arange(len(self.time))
            x_label = "Sample Number"

        self.left_panel.axes.clear()
        self.left_panel.axes.plot(x_axis, self.signal)
        self.left_panel.axes.set_xlabel(x_label)
        self.left_panel.axes.set_ylabel("Amplitude")
        self.left_panel.draw()
        self.apply_fft()

    def apply_fft(self):
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
            if N <= 0:
                print("Invalid FFT window size.")
                return

            # Update the top right panel (Temporal View)
            self.update_temporal_view(N)

            # Perform FFT analysis
            self.perform_fft(N)

    def update_temporal_view(self, N):
        if self.x_axis_in_seconds:
            x_axis = self.time[self.start_sample:self.end_sample]
            x_label = "Time (Seconds)"
        else:
            x_axis = np.arange(self.start_sample, self.end_sample)
            x_label = "Sample Number"

        self.top_right_panel.axes.clear()
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

        self.bottom_right_panel.axes.clear()
        self.bottom_right_panel.axes.plot(freq, np.abs(y_fft_half))
        self.bottom_right_panel.axes.set_xlabel("Frequency (Hz)")
        self.bottom_right_panel.axes.set_ylabel("Amplitude")
        self.bottom_right_panel.draw()

    def toggle_xaxis(self):
        self.x_axis_in_seconds = not self.x_axis_in_seconds
        self.plot_signal()
        self.apply_fft()   

    def save_to_excel(self):
        if self.signal is not None:
            # Create a DataFrame and save to Excel
            df = pd.DataFrame({'Time': self.time, 'Signal': self.signal})
            try:
                filepath = "signal_data.xlsx"  # You can modify the file path as needed
                df.to_excel(filepath, index=False)
                print(f"Signal data saved to {filepath}")
            except Exception as e:
                print(f"Error saving to Excel: {e}")

    def load_from_excel(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx)")
        if filepath:
            try:
                df = pd.read_excel(filepath)
                self.time = df['Time'].values
                self.signal = df['Signal'].values
                self.plot_signal()
            except Exception as e:
                print(f"Error loading from Excel: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = SignalViewer()
    mainWin.show()
    sys.exit(app.exec())