#!/usr/bin/env python

''' A basic GUi to use ImageViewer class to show its functionalities and use cases. '''

from PyQt5 import QtCore, QtGui, QtWidgets, uic

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


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
    app.setPalette(QtWidgets.QApplication.style().standardPalette())
    parentWindow = Iwindow(None)
    sys.exit(app.exec_())

if __name__ == "__main__":
    print(__doc__)
    main()