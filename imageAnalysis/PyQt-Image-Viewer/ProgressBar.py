# importing libraries 
from PyQt5.QtWidgets import *
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
  
class ProgressBar(QWidget): 
  
    def __init__(self, max_): 
        self.max = max_
        super().__init__() 
        self.initUI() 
  
    def initUI(self): 
  
        # creating progress bar 
        self.pbar = QProgressBar(self) 
  
        # Setting bar dimensions
        self.pbar.setGeometry(30, 40, 200, 25) 
        self.pbar.setMaximum(self.max) 
        self.pbar.setValue(0)
  
        # Setting window attributes 
        self.setGeometry(300, 300, 280, 170) 
        self.setFixedSize(240, 100)
        self.setWindowTitle("Loading Images...") 
  
        # showing all the widgets 
        self.show()

    def increment(self):
        self.pbar.setValue(self.pbar.value() + 1) 
        QApplication.processEvents() 

    def done(self):
        self.pbar.setValue(self.max)
        self.close()
