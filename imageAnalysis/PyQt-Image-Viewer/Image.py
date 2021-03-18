from PIL.ImageQt import ImageQt 
import PIL.Image
import cv2
import numpy as np
from copy import deepcopy


class Image:
    def __init__(self, id_, name, type_, path, view):
        self.id = id_
        self.name = name
        self.type = type_
        self.path = path

        self.view = view

        self.originalImg = self.preprocessImg(self.path)

        self.imgArr = self.preprocessImg(self.path)
        self.imgQt = self.convertCvImage2QtImage(self.imgArr)

        self.threshold = 120
        self.radiusRange = (40, 500) if type_ == "BF" else (10, 100)

        self.shapes = []
        self.ellipse = False # Keeps track of whether the shapes are ellipses or circles

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

    def drawCircle(self, threshold, radius_range, pBar):
        pBar.incrementPbar.emit()
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

        pBar.startPbar.emit(len(contours) + 2)
        
        # Get coordinates of circles
        circle_coords = []
        circle_num = 1
        # Circles are numbered starting from 1
        # circle_coord: (x, y), r, circ_num
        for contour in contours:
            pBar.incrementPbar.emit()

            (x, y), r = cv2.minEnclosingCircle(contour)
            if r > radius_range[1]:
                continue
            circle_coords.append([(x, y), r, str(circle_num)])
            circle_num = circle_num + 1

        # Check if spheroids have ellipses in them -- Only keep the ones that do
        circ_num = 1
        if self.type == "BF" and self.id in self.view.trImages.map:
            trImage = self.view.trImages.map[self.id]
            if len(trImage.shapes) > 0:
                temp = []
                letter_map = {0:"a",1:"b",2:"c",3:"d",4:"e"} # Letter map for ellipse naming

                for i in range(len(circle_coords)):
                    circle_coord = circle_coords[i]
                    ellipse_num = 0

                    for j in range(len(trImage.shapes)):

                        shape = trImage.shapes[j]
                        center_point = shape[0]

                        ellipseInCircle = self.isPointInsideCircle(center_point, circle_coord)
                        if ellipseInCircle and circle_coord not in temp:
                            temp.append(circle_coord)
                            # Ellipses are numbered with the corresponding cicle number + an incrementing letter
                            shape[len(shape)-1] = circle_coord[len(circle_coord)-1] + letter_map[ellipse_num]
                            ellipse_num = ellipse_num + 1
                        elif ellipseInCircle:
                            shape[len(shape)-1] = circle_coord[len(circle_coord)-1] + letter_map[ellipse_num]
                            ellipse_num = ellipse_num + 1

                circle_coords = temp

        self.shapes = deepcopy(circle_coords)
        self.ellipse = False

        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        colour = (255, 0, 0) # Red
        thickness = 3    

        # Draw circles
        for (x, y), r, circ_num in circle_coords:
            colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
            font = cv2.FONT_HERSHEY_SIMPLEX
            colour_img = cv2.putText(colour_img, circ_num, (int(x + r + 10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)
        self.setImg(colour_img)    


    def drawEllipse(self, threshold, radius_range, pBar):
        pBar.incrementPbar.emit()
        img = self.preprocessImg(self.path)

        _, thresh = cv2.threshold(img, threshold, np.max(img), cv2.THRESH_BINARY)
        raw_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        contours = []
        for contour in raw_contours:
            # Most items in raw contours are lines or small shapes
            if cv2.contourArea(contour) < (np.pi * radius_range[0] ** 2):
                continue
            contours.append(contour)

        pBar.startPbar.emit(len(contours) + 2)

        ellipse_coords = []
        ellipse_num = 1
        for contour in contours:
            pBar.incrementPbar.emit()

            (x,y),(w,h),ang = cv2.fitEllipse(contour)
            if max(w,h) > radius_range[1]:
                continue
            ellipse_coords.append([(x,y),(w,h),ang,str(ellipse_num)])  
            ellipse_num = ellipse_num + 1           

        self.shapes = deepcopy(ellipse_coords)   
        self.ellipse = True

        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        colour = (255, 0, 0) # Red
        thickness = 3

        # Draw Ellipses
        for (x,y),(w,h),ang,num in ellipse_coords:
            colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
            font = cv2.FONT_HERSHEY_SIMPLEX
            colour_img = cv2.putText(colour_img, num, (int(x+max(w,h)+10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)            
        self.setImg(colour_img)  

    def isPointInsideCircle(self, point, circle_coords):
        x, y = point
        (x_center, y_center), r, _ = circle_coords
        dist = r**2 - ((x_center-x)**2 + (y_center-y)**2);
        return dist >= 0

    def redraw(self): 
        colour = (255, 0, 0) # Red
        thickness = 3        
        font = cv2.FONT_HERSHEY_SIMPLEX

        img = self.preprocessImg(self.path)
        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        if self.ellipse:
            for (x,y),(w,h),ang,num in self.shapes:
                # If it only is an integer, it is not within a spheroid, so ignore
                if not self.isInt(num):
                    colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
                    colour_img = cv2.putText(colour_img, num, (int(x+max(w,h)+10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)             
        else:
            for (x, y), r, circ_num in self.shapes:
                # Ignore if sensor is not within a spheroid
                if self.type == "TR" and self.isInt(circ_num):
                    continue
                else:
                    colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
                    colour_img = cv2.putText(colour_img, circ_num, (int(x + r + 10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)            
        self.setImg(colour_img)  

    def isInt(self, num):
        try: 
            int(num)
            return True
        except ValueError:
            return False        