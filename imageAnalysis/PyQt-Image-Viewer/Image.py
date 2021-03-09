from PIL.ImageQt import ImageQt 
import PIL.Image
import cv2
import numpy as np


class Image:
    def __init__(self, id_, name, type_, path):
        self.id = id_
        self.name = name
        self.type = type_
        self.path = path

        self.originalImg = self.preprocessImg(self.path)

        self.imgArr = self.preprocessImg(self.path)
        self.imgQt = self.convertCvImage2QtImage(self.imgArr)

        self.threshold = 120
        self.radiusRange = (40, 500) if type_ == "BF" else (10, 100)

    def preprocessImg(self, img_path):
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        # Normalize image
        min_bit = np.min(image)
        max_bit = np.max(image)
        image = cv2.normalize(image*16, dst=None, alpha=min_bit*16, beta=max_bit*16, norm_type=cv2.NORM_MINMAX)
        return image

    # Convert an opencv image to QPixmap
    def convertCvImage2QtImage(self, cv_img_arr):
        PIL_image = PIL.Image.fromarray(cv_img_arr)
        return ImageQt(PIL_image)   

    # Given an image numpy array, update attributes appropriately
    def setImg(self, imgArr):
        self.imgArr = imgArr
        self.imgQt = self.convertCvImage2QtImage(self.imgArr)            

    def drawCircle(self, threshold, radius_range):
        img = self.preprocessImg(self.path)

        _, thresh = cv2.threshold(img, threshold, np.max(img), cv2.THRESH_BINARY)

        # Retrieval modes and contour approximation types found on OpenCV docs
        raw_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        # New contour array that only has significant contours
        contours = [] 
        for contour in raw_contours:
            # Most items in raw contours are lines or small shapes
            if cv2.contourArea(contour) < (np.pi * radius_range[0] ** 2):
                continue
            contours.append(contour)    

        circle_coords = []
        for contour in contours:
            (x, y), r = cv2.minEnclosingCircle(contour)
            if r > radius_range[1]:
                continue
            circle_coords.append((x, y, r))

        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        colour = (255, 0, 0) # Red
        thickness = 3    

        # Draw circles
        for x, y, r in circle_coords:
            colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
        self.setImg(colour_img)              

    def drawEllipse(self, threshold, radius_range):
        img = self.preprocessImg(self.path)

        _, thresh = cv2.threshold(img, threshold, np.max(img), cv2.THRESH_BINARY)
        raw_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        contours = []
        for contour in raw_contours:
            # Most items in raw contours are lines or small shapes
            if cv2.contourArea(contour) < (np.pi * radius_range[0] ** 2):
                continue
            contours.append(contour)

        ellipse_coords = []
        for contour in contours:
            (x,y),(w,h),ang = cv2.fitEllipse(contour)
            if max(w,h) > radius_range[1]:
                continue
            ellipse_coords.append(((x,y),(w,h),ang)) 

        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        colour = (255, 0, 0) # Red
        thickness = 3

        # Draw Ellipses
        for (x,y),(w,h),ang in ellipse_coords:
            colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
        self.setImg(colour_img)             

