from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal

class SignalActionPanel(QWidget):
    normalizeButtonClicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create the first row of buttons
        row1_layout = QHBoxLayout()
        layout.addLayout(row1_layout)

        button1 = QPushButton("Normalize")
        button1.clicked.connect(lambda: self.normalizeButtonClicked.emit("Button 1 clicked"))
        row1_layout.addWidget(button1)

        # button2 = QPushButton("Button 2")
        # button2.clicked.connect(lambda: self.buttonClicked.emit("Button 2 clicked"))
        # row1_layout.addWidget(button2)

        # # Create the second row of buttons
        # row2_layout = QHBoxLayout()
        # layout.addLayout(row2_layout)

        # button3 = QPushButton("Button 3")
        # button3.clicked.connect(lambda: self.buttonClicked.emit("Button 3 clicked"))
        # row2_layout.addWidget(button3)

        # button4 = QPushButton("Button 4")
        # button4.clicked.connect(lambda: self.buttonClicked.emit("Button 4 clicked"))
        # row2_layout.addWidget(button4)

