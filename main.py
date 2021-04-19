from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from qrangeslider import QRangeSlider

from ImageViewer import ImageViewer
import sys, os, re

gui = uic.loadUiType("main.ui")[0]     # load UI file designed in Qt Designer

class MainWindow(QtWidgets.QMainWindow, gui):
    """Main window and thread."""
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setTaskbarIcon()

        imageLabels = (self.qlabel_img_bf, self.qlabel_img_tr)
        self.imageViewer = ImageViewer(imageLabels, self)

        self.__connectEvents()
        self.initDrawDebounce()
        self.showMaximized()

    def __connectEvents(self):
        """Connects all UI objects to appropriate functions in code"""
        self.open_folder.clicked.connect(self.imageViewer.selectDir)
        self.next_im.clicked.connect(self.imageViewer.nextImg)
        self.prev_im.clicked.connect(self.imageViewer.prevImg)
        self.qlist_images.itemClicked.connect(self.imageViewer.item_click)

        self.zoom_plus.clicked.connect(self.imageViewer.zoomPlus)
        self.zoom_minus.clicked.connect(self.imageViewer.zoomMinus)
        self.reset_zoom.clicked.connect(self.imageViewer.resetZoom)
        self.toggle_move.toggled.connect(self.imageViewer.action_move)

        self.tabWidget.currentChanged.connect(self.imageViewer.changeTab)
        self.checkBox.stateChanged.connect(self.checkBoxTick)
        self.threshold_box.valueChanged.connect(self.imageViewer.changeThreshold)

        self.radius_slider.startValueChanged.connect(self.minRadius_box.setValue)
        self.radius_slider.endValueChanged.connect(self.maxRadius_box.setValue)
        self.minRadius_box.valueChanged.connect(self.radius_slider.setStart)
        self.minRadius_box.valueChanged.connect(self.imageViewer.changeRadiusRange)        
        self.maxRadius_box.valueChanged.connect(self.radius_slider.setEnd)
        self.maxRadius_box.valueChanged.connect(self.imageViewer.changeRadiusRange)

        self.calculate.clicked.connect(self.imageViewer.recalculate)
        self.draw.clicked.connect(self.imageViewer.loadImage)
        self.set_base.clicked.connect(self.imageViewer.setBaseImage)
        self.clear_base.clicked.connect(self.imageViewer.clearBaseImage)

        # Menu Bar
        self.menu_all_excel.triggered.connect(self.imageViewer.exportAllExcel)
        self.menu_single_excel.triggered.connect(self.imageViewer.exportSingleExcel)
        self.menu_all_img.triggered.connect(self.imageViewer.exportAllImages)
        self.menu_single_img.triggered.connect(self.imageViewer.exportSingleImage)

        self.menu_redraw.triggered.connect(self.imageViewer.loadImage)
        self.menu_recalculate.triggered.connect(self.imageViewer.recalculate)
        self.menu_reset_pan.triggered.connect(self.imageViewer.resetZoom)

    def startPbar(self, max_):
        """
        Resets the progress bar to 0, with a new denominator given by max_
        Args:
          max_: Integer value that represents number of steps until progress bar is complete
        """
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(max_)
        QApplication.processEvents() 

    def incrementPbar(self):
        """Increments the progress bar by 1 value"""
        self.progressBar.setValue(self.progressBar.value() + 1) 
        QApplication.processEvents() 

    def finishPbar(self):
        """Complete the progress bar and reset to zero"""
        self.progressBar.setValue(self.progressBar.maximum())
        self.progressBar.setValue(0)
        QApplication.processEvents() 

    def initDrawDebounce(self, msDelay=1000):
        """
        Initializes the draw debounce objects and attributes, i.e. the delay between changing a 
        threshold/range value and the program recalculating the image shapes.
        Args:
          msDelay: (Default value = 1000) Delay in milliseconds
        """
        self.debounce = QTimer()
        self.debounce.setInterval(msDelay)
        self.debounce.setSingleShot(True)

        self.enableDebounce()      

        self.checkBox.setCheckState(2) # Initially set to draw circles

    def disableDebounce(self):
        """Disconnects changing threshold/radius values from calculation of shapes in the image"""
        self.threshold_box.valueChanged.disconnect(self.debounce.start) 
        self.minRadius_box.valueChanged.disconnect(self.debounce.start)
        self.maxRadius_box.valueChanged.disconnect(self.debounce.start)  
    
    def enableDebounce(self):
        """Enables changing threshold/radius values calculating new shapes of image"""
        self.threshold_box.valueChanged.connect(self.debounce.start) 
        self.minRadius_box.valueChanged.connect(self.debounce.start)
        self.maxRadius_box.valueChanged.connect(self.debounce.start)          

    def checkBoxTick(self, isChecked):
        """
        Called when "Enable Circle" checkbox is ticked. Connects/disconnects appropriate debounce functions.
        Args:
          isChecked: True if "Enable Circle" checkbox is ticked --> Circles will be fit and mapped to image
        """
        try:
            if isChecked:
                # Connect draw circle
                self.debounce.timeout.connect(self.imageViewer.drawCircle)              
                self.debounce.timeout.disconnect(self.imageViewer.drawEllipse)
            else:
                # Connect draw  ellipse
                self.debounce.timeout.connect(self.imageViewer.drawEllipse)              
                self.debounce.timeout.disconnect(self.imageViewer.drawCircle)   
        except:
            pass

    def setTaskbarIcon(self):
        """Sets taskbar icon to camera"""
        if sys.platform == "win32":
            import ctypes
            appid = 'cmed Image Analysis.1.00' # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)  

    def wheelEvent(self, event):
        """Called when scrollwheel is used. Used for zooming in and out with wheel."""
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            # Dividing by 120 gets number of notches on a typical scroll wheel. See QWheelEvent documentation
            delta_notches = event.angleDelta().y() / 120
            factor = delta_notches        
            if factor > 0:
                if self.imageViewer.currImage is not None:
                    self.imageViewer.zoomPlus(True)
            elif factor < 0:
                if self.imageViewer.currImage is not None:
                    self.imageViewer.zoomMinus(True)    

    def keyPressEvent(self, event):
        """Called when any key is pressed. Used for switching between images."""
        if event.key() == Qt.Key_Left: 
            self.imageViewer.prevImg()
        elif event.key() == Qt.Key_Right:
            self.imageViewer.nextImg()

def main():
    """Main function that starts the application"""
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
    app.setPalette(QtWidgets.QApplication.style().standardPalette())
    parentWindow = MainWindow(None)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()