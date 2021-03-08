from PyQt5 import QtCore, QtGui, QtWidgets, uic
from qrangeslider import QRangeSlider
from ProgressBar import ProgressBar

from ImageViewer import ImageViewer
import sys, os, re

gui = uic.loadUiType("main.ui")[0]     # load UI file designed in Qt Designer

class Iwindow(QtWidgets.QMainWindow, gui):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        imageLabels = (self.qlabel_img_bf, self.qlabel_img_tr)
        self.imageViewer = ImageViewer(imageLabels, self)
        self.__connectEvents()
        self.showMaximized()

    def __connectEvents(self):
        self.open_folder.clicked.connect(self.imageViewer.selectDir)
        self.next_im.clicked.connect(self.imageViewer.nextImg)
        self.prev_im.clicked.connect(self.imageViewer.prevImg)
        self.qlist_images.itemClicked.connect(self.imageViewer.item_click)
        # self.save_im.clicked.connect(self.saveImg)

        self.zoom_plus.clicked.connect(self.imageViewer.zoomPlus)
        self.zoom_minus.clicked.connect(self.imageViewer.zoomMinus)
        self.reset_zoom.clicked.connect(self.imageViewer.resetZoom)

        self.toggle_move.toggled.connect(self.imageViewer.action_move)

        self.tabWidget.currentChanged.connect(self.imageViewer.changeTab)

        self.radius_slider.startValueChanged.connect(self.minRadius_box.setValue)
        self.radius_slider.endValueChanged.connect(self.maxRadius_box.setValue)
        self.minRadius_box.valueChanged.connect(self.radius_slider.setStart)
        self.maxRadius_box.valueChanged.connect(self.radius_slider.setEnd)

    def createProgressBar(self, max_):
        self.progressBar = ProgressBar(max_)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
    app.setPalette(QtWidgets.QApplication.style().standardPalette())
    parentWindow = Iwindow(None)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()