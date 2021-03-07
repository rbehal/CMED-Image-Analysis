from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5 import QtCore, QtGui, QtWidgets

from PIL.ImageQt import ImageQt 
import PIL.Image
from Image import Image
from ImageCollection import ImageCollection
import cv2
import numpy as np
import os, re

class ImageViewer:
    ''' Basic image viewer class to show an image with zoom and pan functionaities.
        Requirement: Qt's Qlabel widget name where the image will be drawn/displayed.
    '''
    def __init__(self, imageLabels, window):
        self.bfImages = ImageCollection("BF", imageLabels[0])
        self.trImages = ImageCollection("TR", imageLabels[1])

        self.currImages = self.bfImages

        self.window = window
        self.qimage_scaled = QImage()         # Scaled image to fit to the size of currImages.qlabel
        self.qpixmap = QPixmap()              # QPixmap to fill the currImages.qlabel

        self.zoomX = 1                        # Zoom factor w.r.t size of currImages.qlabel
        self.position = [0, 0]                # Position of top left corner of currImages.qlabel w.r.t. qimage_scaled
        self.panFlag = False                  # to enable or disable pan

        self.basePath = ""
        self.currImageIdx = -1 
        self.numImages = -1
        self.items = []

        self.trImages.qlabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.bfImages.qlabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.__connectEvents()

    def __connectEvents(self):
        # Mouse events
        self.currImages.qlabel.mousePressEvent = self.mousePressAction
        self.currImages.qlabel.mouseMoveEvent = self.mouseMoveAction
        self.currImages.qlabel.mouseReleaseEvent = self.mouseReleaseAction

    def onResize(self):
        ''' Things to do when image is resized '''
        self.qpixmap = QPixmap(self.currImages.qlabel.size())
        self.qpixmap.fill(QtCore.Qt.gray)
        self.qimage_scaled = self.qimage.scaled(self.currImages.qlabel.width() * self.zoomX, self.currImages.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
        self.update()

    def getImages(self):
        ''' Get the names and paths of all the images in a directory. '''

        VALID_FORMAT = ('.BMP', '.GIF', '.JPG', '.JPEG', '.PNG', '.PBM', '.PGM', '.PPM', '.TIFF', '.TIF', '.XBM')  # Image formats supported by Qt
        id_pattern = "(p\d{1,4})" # Image id example: 'scan_Plate_R_{p03}_0_A02f00d4.TIF',

        # Populate Bright Field image list
        if os.path.isdir(self.bfImages.path):
            for file in os.listdir(self.bfImages.path):
                if file.upper().endswith(VALID_FORMAT):
                    im_path = os.path.join(self.bfImages.path, file)

                    match = re.search(id_pattern, file)
                    id_ = match.group()            
                    
                    image_obj = Image(id_, file, "BF", im_path)
                    self.bfImages.list.append(image_obj)
        
        # Populate Texas Red image list                    
        if os.path.isdir(self.trImages.path):
            for file in os.listdir(self.trImages.path):
                if file.upper().endswith(VALID_FORMAT):
                    im_path = os.path.join(self.trImages.path, file)

                    match = re.search(id_pattern, file)
                    id_ = match.group()
                    
                    image_obj = Image(id_, file, "TR", im_path)
                    self.trImages.list.append(image_obj)      
        return      

    def selectDir(self):
        ''' Select a directory, make list of images in it and display the first image in the list. '''
        # open 'select folder' dialog box
        self.basePath = str(QtWidgets.QFileDialog.getExistingDirectory(self.window, "Select Directory")) + "/"
        if not self.basePath:
            QtWidgets.QMessageBox.warning(self.window, 'No Folder Selected', 'Please select a valid Folder')
            return

        dirs = [dir_[0] for dir_ in os.walk(self.basePath)][1:]

        dir_hr = [dir_.split("/")[-1] for dir_ in dirs] # Human-readable directories
        dir_clean = list(map(str.strip, list(map(str.upper, dir_hr)))) # Stripped and trimmed dir_hr

        for i in range(len(dir_clean)):
            dir_ = dir_clean[i]
            if "BF" == dir_:
                self.bfImages.path = dirs[i]
            if "TEXAS RED" == dir_:
                self.trImages.path = dirs[i]
    
        if self.bfImages.path is None:            
            QtWidgets.QMessageBox.warning(self.window, 'Missing Folder', 'Brightfield (BF) folder cannot be found. Please select directory with BF folder.')
            return
        elif self.trImages.path is None:
            QtWidgets.QMessageBox.warning(self.window, 'Missing Folder', 'Texas Red folder cannot be found. Please select directory with Texas Red folder.')
            return

        self.getImages() # Initialize BF/TF
        self.changeImageList(self.currImages.list) # Initialize brightfield list of image names
        self.numImages = len(self.currImages.list)

        # Display first image and enable Pan 
        self.currImageIdx = 0
        self.enablePan(True)
        self.loadImage(self.currImages.list[self.currImageIdx].path)

        self.items[self.currImageIdx].setSelected(True)

        # Enable the next image button on the gui if multiple images are loaded
        if self.numImages > 1:
            self.window.next_im.setEnabled(True)

    def resizeEvent(self, evt):
        if self.currImageIdx >= 0:
            self.onResize()

    def nextImg(self):
        if self.currImageIdx < self.numImages -1:
            self.currImageIdx += 1
            self.loadImage(self.currImages.list[self.currImageIdx].path)
            self.items[self.currImageIdx].setSelected(True)
        else:
            QtWidgets.QMessageBox.warning(self.window, 'Sorry', 'No more Images!')

    def prevImg(self):
        if self.currImageIdx > 0:
            self.currImageIdx -= 1
            self.loadImage(self.currImages.list[self.currImageIdx].path)
            self.items[self.currImageIdx].setSelected(True)
        else:
            QtWidgets.QMessageBox.warning(self.window, 'Sorry', 'No previous Image!')

    def item_click(self, item):
        self.currImageIdx = self.items.index(item)
        self.loadImage(self.currImages.list[self.currImageIdx].path)

    def action_move(self):
        if self.toggle_move.isChecked():
            self.currImages.qlabel.setCursor(QtCore.Qt.OpenHandCursor)
            self.enablePan(True)        

    def loadImage(self, imagePath):
        ''' To load and display new image.'''
        self.qimage = self.convertCvImage2QtImage(self.preprocessImg(imagePath))
        self.qpixmap = QPixmap(self.currImages.qlabel.size())
        if not self.qimage.isNull():
            # reset Zoom factor and Pan position
            self.zoomX = 1
            self.position = [0, 0]
            
            self.qimage_scaled = self.qimage.scaled(self.currImages.qlabel.width(), self.currImages.qlabel.height(), QtCore.Qt.KeepAspectRatioByExpanding)
            self.update()
        else:
            self.window.statusbar.showMessage('Cannot open this image! Try another one.', 5000)

    def update(self):
        ''' This function actually draws the scaled image to currImages.qlabel.
            It will be repeatedly called when zooming or panning.
            So, I tried to include only the necessary operations required just for these tasks. 
        '''
        if not self.qimage_scaled.isNull():
            # check if position is within limits to prevent unbounded panning.
            px, py = self.position
            px = px if (px <= self.qimage_scaled.width() - self.currImages.qlabel.width()) else (self.qimage_scaled.width() - self.currImages.qlabel.width())
            py = py if (py <= self.qimage_scaled.height() - self.currImages.qlabel.height()) else (self.qimage_scaled.height() - self.currImages.qlabel.height())
            px = px if (px >= 0) else 0
            py = py if (py >= 0) else 0
            self.position = (px, py)

            if self.zoomX == 1:
                self.qpixmap.fill(QtCore.Qt.white)

            # the act of painting the qpixamp
            painter = QPainter()
            painter.begin(self.qpixmap)
            painter.drawImage(QtCore.QPoint(0, 0), self.qimage_scaled,
                    QtCore.QRect(self.position[0], self.position[1], self.currImages.qlabel.width(), self.currImages.qlabel.height()) )
            painter.end()

            self.currImages.qlabel.setPixmap(self.qpixmap)
        else:
            pass

    def mousePressAction(self, QMouseEvent):
        x, y = QMouseEvent.pos().x(), QMouseEvent.pos().y()
        if self.panFlag:
            self.pressed = QMouseEvent.pos()                            # Starting point of drag vector
            self.anchor = self.position                                 # Save the pan position when panning starts

    def mouseMoveAction(self, QMouseEvent):
        x, y = QMouseEvent.pos().x(), QMouseEvent.pos().y()
        if self.pressed:
            dx, dy = x - self.pressed.x(), y - self.pressed.y()         # Calculate the drag vector
            self.position = self.anchor[0] - dx, self.anchor[1] - dy    # Update pan position using drag vector
            self.update()                                               # Show the image with udated pan position

    def mouseReleaseAction(self, QMouseEvent):
        self.pressed = None                                             # Clear the starting point of drag vector

    def zoomPlus(self):
        self.zoomX += 1
        px, py = self.position
        px += self.currImages.qlabel.width()/2
        py += self.currImages.qlabel.height()/2
        self.position = (px, py)
        self.qimage_scaled = self.qimage.scaled(self.currImages.qlabel.width() * self.zoomX, self.currImages.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
        self.update()

    def zoomMinus(self):
        if self.zoomX > 1:
            self.zoomX -= 1
            px, py = self.position
            px -= self.currImages.qlabel.width()/2
            py -= self.currImages.qlabel.height()/2
            self.position = (px, py)
            self.qimage_scaled = self.qimage.scaled(self.currImages.qlabel.width() * self.zoomX, self.currImages.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
            self.update()

    def resetZoom(self):
        self.zoomX = 1
        self.position = [0, 0]
        self.qimage_scaled = self.qimage.scaled(self.currImages.qlabel.width() * self.zoomX, self.currImages.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
        self.update()

    def enablePan(self, value):
        self.panFlag = value

    def preprocessImg(self, img_path):
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        # Normalize image
        min_bit = np.min(image)
        max_bit = np.max(image)
        image = cv2.normalize(image*16, dst=None, alpha=min_bit*16, beta=max_bit*16, norm_type=cv2.NORM_MINMAX)
        return image

    # Convert an opencv image to QPixmapself
    def convertCvImage2QtImage(self, cv_img_arr):
        PIL_image = PIL.Image.fromarray(cv_img_arr)
        return ImageQt(PIL_image)

    def changeImageList(self, list_):
        # Make a list of qitems for the image names
        self.items = [QtWidgets.QListWidgetItem(img.name) for img in list_]
        self.window.qlist_images.clear()
        for item in self.items:
            self.window.qlist_images.addItem(item)

    def changeTab(self):
        if self.currImages.type == "BF":
            self.changeImageList(self.trImages.list)
            self.currImages = self.trImages
        else:
            self.changeImageList(self.bfImages.list)
            self.currImages = self.bfImages