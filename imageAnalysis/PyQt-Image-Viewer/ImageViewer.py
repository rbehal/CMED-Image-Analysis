from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore, QtGui, QtWidgets

from Image import Image
from ImageCollection import ImageCollection
from math import factorial
import os, re

class ImageViewer:
    ''' Basic image viewer class to show an image with zoom and pan functionaities.
        Requirement: Qt's Qlabel widget name where the image will be drawn/displayed.
    '''
    def __init__(self, imageLabels, window):
        self.bfImages = ImageCollection("BF", imageLabels[0])
        self.trImages = ImageCollection("TR", imageLabels[1])

        self.currImageCol = self.trImages    # Current image collection

        self.window = window
        self.qimage_scaled = QImage()         # Scaled image to fit to the size of currImageCol.qlabel
        self.qpixmap = QPixmap()              # QPixmap to fill the currImageCol.qlabel

        self.zoomX = 1                        # Zoom factor w.r.t size of currImageCol.qlabel
        self.position = [0, 0]                # Position of top left corner of currImageCol.qlabel w.r.t. qimage_scaled
        self.mousex, self.mousey = 0, 0
        self.panFlag = False                  # To enable or disable pan
        self.pressed = False                  # Mouse pressed

        self.basePath = ""
        self.dayFolders = [] 

        self.currImage = None
        self.currImageIdx = -1 
        self.numImages = -1
        self.qImageNameItems = []

        self.initializeQLabels()

    def initializeQLabels(self):
        # Mouse events
        self.trImages.qlabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.trImages.qlabel.setCursor(QtCore.Qt.OpenHandCursor)
        self.bfImages.qlabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.bfImages.qlabel.setCursor(QtCore.Qt.OpenHandCursor) 

        self.trImages.qlabel.mousePressEvent = self.mousePressAction
        self.trImages.qlabel.mouseMoveEvent = self.mouseMoveAction
        self.trImages.qlabel.mouseReleaseEvent = self.mouseReleaseAction       
        self.trImages.qlabel.setMouseTracking(True)
        self.bfImages.qlabel.mousePressEvent = self.mousePressAction
        self.bfImages.qlabel.mouseMoveEvent = self.mouseMoveAction
        self.bfImages.qlabel.mouseReleaseEvent = self.mouseReleaseAction         
        self.bfImages.qlabel.setMouseTracking(True)

    def onResize(self):
        ''' Things to do when image is resized '''
        self.qpixmap = QPixmap(self.currImageCol.qlabel.size())
        self.qpixmap.fill(QtCore.Qt.gray)
        self.qimage_scaled = self.qimage.scaled(self.currImageCol.qlabel.width() * self.zoomX, self.currImageCol.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
        self.scaleUpdate()

    def getImages(self):
        ''' Get the names and paths of all the images in a directory. '''

        VALID_FORMAT = ('.BMP', '.GIF', '.JPG', '.JPEG', '.PNG', '.PBM', '.PGM', '.PPM', '.TIFF', '.TIF', '.XBM')  # Image formats supported by Qt
        id_pattern = "(p\d{1,4})" # Image id example: 'scan_Plate_R_{p03}_0_A02f00d4.TIF',
        
        self.bfImages.reset()
        self.trImages.reset()

        # If data is timelapse divided into BF and Texas Red Folders
        if len(self.dayFolders) == 0:
            # Initializing progress bar
            totalNumFiles = len(os.listdir(self.bfImages.path)) + len(os.listdir(self.trImages.path))
            self.window.startPbar(totalNumFiles)

            # Populate Bright Field image list
            for file in os.listdir(self.bfImages.path):
                self.window.incrementPbar()
                if file.upper().endswith(VALID_FORMAT):
                    im_path = os.path.join(self.bfImages.path, file)

                    match = re.search(id_pattern, file)
                    if match:
                        id_ = match.group()
                    else:
                        continue     
                    
                    image_obj = Image(id_, file, "BF", im_path, self)
                    self.bfImages.list.append(image_obj)
            
            # Populate Texas Red image list                    
            for file in os.listdir(self.trImages.path):
                self.window.incrementPbar()
                if file.upper().endswith(VALID_FORMAT):
                    im_path = os.path.join(self.trImages.path, file)

                    match = re.search(id_pattern, file)
                    id_ = match.group()
                    
                    image_obj = Image(id_, file, "TR", im_path, self)
                    self.trImages.list.append(image_obj)
        else: # Or else it must be daily folders  
            # Initializing progress bar
            totalNumFiles = len(self.dayFolders*3) # 3 files in every day folder
            self.window.startPbar(totalNumFiles)

            day_file_pattern = "_.{6}d(\d)"

            for day_num, day_path in self.dayFolders:
                for file in os.listdir(day_path):
                    self.window.incrementPbar()

                    im_path = os.path.join(day_path, file)
                    # All files with day structure have p00, so in id and name it's replaced with p[day_num]                    
                    id_ = "p{0:0=2d}".format(int(day_num)) 
                    name = file.replace("p00",id_)
                    
                    match = re.search(day_file_pattern, file)
                    if match:
                        groups = match.groups()[0]
                        if groups == "4":
                            image_obj = Image(id_, name, "BF", im_path, self)
                            self.bfImages.list.append(image_obj)                            
                        elif groups == "3":
                            image_obj = Image(id_, name, "TR", im_path, self)
                            self.trImages.list.append(image_obj)  
                        else:
                            continue

        self.bfImages.initMap()
        self.trImages.initMap()   
        self.window.finishPbar()
        return      

    def selectDir(self):
        ''' Select a directory, make list of images in it and display the first image in the list. '''
        # open 'select folder' dialog box
        self.basePath = str(QtWidgets.QFileDialog.getExistingDirectory(self.window, "Select Directory")) + "/"
        if not self.basePath:
            QtWidgets.QMessageBox.warning(self.window, 'No Folder Selected', 'Please select a valid Folder')
            return

        subdirs = next(os.walk(self.basePath))[1]
        dirs = [os.path.join(self.basePath, dir_) for dir_ in subdirs]            
        dir_clean = list(map(str.strip, list(map(str.upper, subdirs))))

        day_pattern = "DAY(\d{1,2})" # Regex for finding day folders
        for i in range(len(dir_clean)):
            dir_ = dir_clean[i]
            if "BF" == dir_:
                self.bfImages.path = dirs[i]
            if "TEXAS RED" == dir_:
                self.trImages.path = dirs[i]

            match = re.search(day_pattern, dir_)
            if match:
                day_num = match.groups()[0]
                self.dayFolders.append((day_num, dirs[i]))
            else:
                continue

        if len(self.dayFolders) + len(self.trImages.path + self.bfImages.path) == 0:
            QtWidgets.QMessageBox.warning(self.window, 'Improper Folder Structure', 'Folder structure selected is not supported. Please refer to available documentation.')
            return
        elif self.bfImages.path == "" and len(self.dayFolders) == 0:            
            QtWidgets.QMessageBox.warning(self.window, 'Missing Folder', 'Brightfield (BF) folder cannot be found. Please select directory with BF folder.')
            return
        elif self.trImages.path == "" and len(self.dayFolders) == 0:
            QtWidgets.QMessageBox.warning(self.window, 'Missing Folder', 'Texas Red folder cannot be found. Please select directory with Texas Red folder.')
            return

        self.window.tabWidget.setCurrentIndex(1)
        self.getImages() # Initialize BF/TF

        # Display first image of TR and enable Pan 
        self.currImageIdx = 0
        self.currImage = self.currImageCol.list[self.currImageIdx]
        self.numImages = len(self.currImageCol.list)

        self.changeImageList(self.currImageCol.list) # Initializelist of image names
        self.enablePan(True)

        # Enable the next image button on the gui if multiple images are loaded
        if self.numImages > 1:
            self.window.next_im.setEnabled(True)

    def resizeEvent(self, evt):
        if self.currImageIdx >= 0:
            self.onResize()

    def nextImg(self):
        if self.currImage is not None:
            if self.currImageIdx < self.numImages -1:
                self.currImageIdx += 1
                self.changeImage()
                self.qImageNameItems[self.currImageIdx].setSelected(True)
            else:
                QtWidgets.QMessageBox.warning(self.window, 'Sorry', 'No more Images!')

    def prevImg(self):
        if self.currImage is not None:
            if self.currImageIdx > 0:
                self.currImageIdx -= 1
                self.changeImage()
                self.qImageNameItems[self.currImageIdx].setSelected(True)
            else:
                QtWidgets.QMessageBox.warning(self.window, 'Sorry', 'No previous Image!')

    def item_click(self, item):
        if self.currImageCol is not None:
            self.currImageIdx = self.qImageNameItems.index(item)
            self.changeImage()

    def action_move(self):
        if self.toggle_move.isChecked():
            self.enablePan(True)        

    def loadImage(self):
        ''' To load and display new image.'''
        self.qimage = self.currImage.imgQt
        self.qpixmap = QPixmap(self.currImageCol.qlabel.size())
        if not self.qimage.isNull():
            # reset Zoom factor and Pan position
            self.zoomX = 1
            self.position = [0, 0]
            
            self.qimage_scaled = self.qimage.scaled(self.currImageCol.qlabel.width(), self.currImageCol.qlabel.height(), QtCore.Qt.KeepAspectRatioByExpanding)
            self.scaleUpdate()
        else:
            self.window.statusbar.showMessage('Cannot open this image! Try another one.', 5000)

    def scaleUpdate(self):
        ''' This function actually draws the scaled image to currImageCol.qlabel.
            It will be repeatedly called when zooming or panning.
            So, I tried to include only the necessary operations required just for these tasks. 
        '''
        if not self.qimage_scaled.isNull():
            # check if position is within limits to prevent unbounded panning.
            px, py = self.position
            px = px if (px <= self.qimage_scaled.width() - self.currImageCol.qlabel.width()) else (self.qimage_scaled.width() - self.currImageCol.qlabel.width())
            py = py if (py <= self.qimage_scaled.height() - self.currImageCol.qlabel.height()) else (self.qimage_scaled.height() - self.currImageCol.qlabel.height())
            px = px if (px >= 0) else 0
            py = py if (py >= 0) else 0
            self.position = (px, py)

            if self.zoomX == 1:
                self.qpixmap.fill(QtCore.Qt.white)
            # the act of painting the qpixamp
            painter = QPainter()
            painter.begin(self.qpixmap)
            painter.drawImage(QtCore.QPoint(0, 0), self.qimage_scaled,
                    QtCore.QRect(self.position[0], self.position[1], self.currImageCol.qlabel.width(), self.currImageCol.qlabel.height()) )
            painter.end()

            self.currImageCol.qlabel.setPixmap(self.qpixmap)
        else:
            pass

    def mousePressAction(self, QMouseEvent):
        if self.panFlag:
            self.pressed = QMouseEvent.pos()                            # Starting point of drag vector
            self.anchor = self.position                                 # Save the pan position when panning starts

    def mouseMoveAction(self, QMouseEvent):
        self.mousex, self.mousey = QMouseEvent.pos().x(), QMouseEvent.pos().y()
        if self.pressed:
            dx, dy = self.mousex - self.pressed.x(), self.mousey - self.pressed.y()         # Calculate the drag vector
            self.position = self.anchor[0] - dx, self.anchor[1] - dy    # Update pan position using drag vector
            self.scaleUpdate()                                               # Show the image with udated pan position

    def mouseReleaseAction(self, QMouseEvent):
        self.pressed = None                                             # Clear the starting point of drag vector        

    def zoomPlus(self, scroll=False):
        px, py = self.position

        if scroll:
            # These calculations come from calculating where the mousex is relative to the original image
            # then multipying that by the new zoom, (zoomX + 1) --> ((self.mousex+px)/self.zoomX)*(self.zoomX+1)
            img_x =  (self.mousex+px) + (self.mousex+px)/self.zoomX
            img_y = (self.mousey+py) + (self.mousey+py)/self.zoomX
            # Subtract mousex and mousey to get the new top left corner for scaleUpdate
            px, py = img_x - self.mousex, img_y - self.mousey
        else:
            px += self.currImageCol.qlabel.width()/2
            py += self.currImageCol.qlabel.height()/2
        
        self.zoomX += 1
        self.position = (px, py)
        self.qimage_scaled = self.qimage.scaled(self.currImageCol.qlabel.width() * self.zoomX, self.currImageCol.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
        self.scaleUpdate()

    def zoomMinus(self, scroll=False):
        if self.zoomX > 1:
            px, py = self.position

            if scroll: 
                # Same as zoomPlus but reverse 
                img_x = (self.mousex+px) - (self.mousex+px)/self.zoomX
                img_y = (self.mousey+py) - (self.mousey+py)/self.zoomX
                px, py = img_x - self.mousex, img_y - self.mousey
            else:
                px -= self.currImageCol.qlabel.width()/2
                py -= self.currImageCol.qlabel.height()/2                

            self.zoomX -= 1
            self.position = (px, py)
            self.qimage_scaled = self.qimage.scaled(self.currImageCol.qlabel.width() * self.zoomX, self.currImageCol.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
            self.scaleUpdate()

    def resetZoom(self):
        self.zoomX = 1
        self.position = [0, 0]
        self.qimage_scaled = self.qimage.scaled(self.currImageCol.qlabel.width() * self.zoomX, self.currImageCol.qlabel.height() * self.zoomX, QtCore.Qt.KeepAspectRatioByExpanding)
        self.scaleUpdate()

    def enablePan(self, value):
        self.panFlag = value

    def changeImageList(self, list_):
        self.changeImage()
        # Make a list of qitems for the image names
        self.qImageNameItems = [QtWidgets.QListWidgetItem(img.name) for img in list_]
        self.window.qlist_images.clear()
        for item in self.qImageNameItems:
            self.window.qlist_images.addItem(item)
        self.qImageNameItems[self.currImageIdx].setSelected(True)            

    def changeTab(self, idx):
        if self.numImages > 0:
            if idx == 1:
                self.window.checkBox.setCheckState(0) # Draw Ellipses for red channel
                self.currImageCol = self.trImages 
                self.changeImageList(self.trImages.list)
            else:
                self.window.checkBox.setCheckState(2) # Circles for Bright Field
                self.currImageCol = self.bfImages 
                self.changeImageList(self.bfImages.list)

    def changeThreshold(self):
        if self.currImage is not None:
            self.currImage.threshold = self.window.threshold_slider.value()

    def changeRadiusRange(self):
        if self.currImage is not None:
            self.currImage.radiusRange = self.window.radius_slider.getRange()

    def changeImage(self):
        self.currImage = self.currImageCol.list[self.currImageIdx]
        self.loadImage()

        self.window.disableDebounce()
        self.window.threshold_box.setValue(self.currImage.threshold)
        self.window.radius_slider.setRange(self.currImage.radiusRange[0], self.currImage.radiusRange[1])
        self.window.enableDebounce()

        if len(self.currImage.shapes) == 0:
            self.window.debounce.start()

    def drawCircle(self):
        if self.currImage is not None:
            thresh = self.window.threshold_slider.value()
            rng = self.window.radius_slider.getRange()
            window = self.window
            
            self.thread = DrawCircleThread(self.currImage, thresh, rng, window)

            self.thread.finished.connect(self.loadImage)   
            self.thread.startPbar.connect(self.window.startPbar)   
            self.thread.incrementPbar.connect(self.window.incrementPbar)    
            self.thread.finishPbar.connect(self.window.finishPbar)    

            self.thread.start()

    def drawEllipse(self):
        if self.currImage is not None:
            thresh = self.window.threshold_slider.value()
            rng = self.window.radius_slider.getRange()
            window = self.window
            
            self.thread = DrawEllipseThread(self.currImage, thresh, rng, window)

            self.thread.finished.connect(self.loadImage)  
            self.thread.startPbar.connect(self.window.startPbar)   
            self.thread.incrementPbar.connect(self.window.incrementPbar)    
            self.thread.finishPbar.connect(self.window.finishPbar)    

            self.thread.start()            

    def redraw(self):
        if self.currImage is not None:
            self.currImage.redraw()
            self.loadImage()

class DrawCircleThread(QtCore.QThread):
    finished = QtCore.pyqtSignal()
    startPbar = QtCore.pyqtSignal(int)
    incrementPbar = QtCore.pyqtSignal()
    finishPbar = QtCore.pyqtSignal()

    def __init__(self, img, thresh, rng, window, parent=None):
        super(DrawCircleThread, self).__init__(parent)
        self.img = img
        self.thresh = thresh
        self.range = rng

    def run(self):
        self.img.drawCircle(self.thresh, self.range, self)
        self.finishPbar.emit()
        self.finished.emit()

class DrawEllipseThread(QtCore.QThread):
    finished = QtCore.pyqtSignal()
    startPbar = QtCore.pyqtSignal(int)
    incrementPbar = QtCore.pyqtSignal()
    finishPbar = QtCore.pyqtSignal()    

    def __init__(self, img, thresh, rng, window, parent=None):
        super(DrawEllipseThread, self).__init__(parent)
        self.img = img
        self.thresh = thresh
        self.range = rng

    def run(self):
        self.img.drawEllipse(self.thresh, self.range, self)
        self.finishPbar.emit()
        self.finished.emit()