import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLabel, QLineEdit, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
from PyQt6.QtWidgets import QFileDialog  # Import QFileDialog
import MainWindow


import sys
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel

class SamplingRateDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Sampling Rate")
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Sampling Rate:")
        self.layout.addWidget(self.label)

        self.lineEdit = QLineEdit(self)
        self.layout.addWidget(self.lineEdit)

        self.button = QPushButton("Confirm", self)
        self.button.clicked.connect(self.on_confirm)
        self.layout.addWidget(self.button)

        self.sampling_rate = None

    def on_confirm(self):
        try:
            self.sampling_rate = float(self.lineEdit.text())
            self.accept()
        except ValueError:
            self.label.setText("Please enter a valid number!")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = SamplingRateDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:  # Use QDialog.DialogCode.Accepted
        sampling_rate = dialog.sampling_rate
        mainWin = MainWindow.SignalViewer(sampling_rate)  # Assuming your main window can accept sampling rate

        mainWin.setCentralWidget(mainWin.main_widget)
        mainWin.showMaximized()
        sys.exit(app.exec())