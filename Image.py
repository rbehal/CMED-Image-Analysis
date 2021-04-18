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
        self.base_shapes = {}
        self.ellipse = False # Keeps track of whether the shapes are ellipses or circles

    def preprocessImg(self, img_path):
        image = cv2.imread(img_path, -1) # Import raw image
        # Normalize image
        min_bit = np.min(image)
        max_bit = np.max(image)
        norm_image = cv2.normalize(image, dst=None, alpha=min_bit, beta=max_bit, norm_type=cv2.NORM_MINMAX)
        image = (norm_image/16).astype('uint8')
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

        # Check if spheroids have sensors in them -- Only keep the ones that do
        if self.type == "BF" and self.id in self.view.trImages.map:
            trImage = self.view.trImages.map[self.id]
            if len(trImage.shapes) > 0:
                temp = []
                letter_map = {0:"a",1:"b",2:"c",3:"d",4:"e",5:"f",6:"g",7:"h"} # Letter map for sensor naming

                for i in range(len(circle_coords)):
                    circle_coord = circle_coords[i]
                    sensor_num = 0

                    for j in range(len(trImage.shapes)):
                        shape = trImage.shapes[j]
                        center_point = shape[0]

                        sensorInCircle = self.isPointInsideCircle(center_point, circle_coord)
                        if sensorInCircle and circle_coord not in temp:
                            temp.append(circle_coord)
                            # Sensors are numbered with the corresponding cicle number + an incrementing letter
                            shape[-1] = circle_coord[-1] + letter_map[sensor_num]
                            sensor_num = sensor_num + 1
                        elif sensorInCircle:
                            shape[-1] = circle_coord[-1] + letter_map[sensor_num]
                            sensor_num = sensor_num + 1

                circle_coords = temp

        self.base_shapes = {}
        self.shapes = deepcopy(circle_coords)
        self.ellipse = False

        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        colour = (255, 0, 0) # Red
        thickness = 3    

        # Draw circles
        for (x, y), r, circ_num in circle_coords:
            colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
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

        self.base_shapes = {}
        self.shapes = deepcopy(ellipse_coords)   
        self.ellipse = True

        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        colour = (255, 0, 0) # Red
        thickness = 3

        # Draw Ellipses
        for (x,y),(w,h),ang,num in ellipse_coords:
            colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
        self.setImg(colour_img) 

    def drawBaseShapes(self, colour_img):
        if not bool(self.base_shapes):
            return

        colour = (255, 0, 0) # Red
        thickness = 3        
        font = cv2.FONT_HERSHEY_SIMPLEX

        if self.ellipse:
            for ((x,y),(w,h),ang,num),_ in self.base_shapes.values():            
                colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
                colour_img = cv2.putText(colour_img, num, (int(x+max(w,h)+10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)            
        else:
            for ((x, y),r,circ_num),_ in self.base_shapes.values():
                colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
                colour_img = cv2.putText(colour_img, circ_num, (int(x + r + 10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)                                    

    def redraw(self): 
        colour = (255, 0, 0) # Red
        thickness = 3        
        font = cv2.FONT_HERSHEY_SIMPLEX

        img = self.preprocessImg(self.path)
        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        if self.type == "TR":
            base_img = self.view.trImages.baseImage
        else:
            base_img = self.view.bfImages.baseImage

        shapes_to_remove = []
        if self.ellipse:
            for i in range(len(self.shapes)):
                (x,y),(w,h),ang,num = self.shapes[i]
                if base_img is not None:
                    # Finding closest shapes to base image shapes and drawing them
                    self.getClosestBaseShape(i)
                # If it only is an integer, it is not within a spheroid, so ignore
                elif self.type == "TR" and not self.isPointInAnySpheroid((x,y)):
                    shapes_to_remove.append(self.shapes[i])
                else:
                    # Draw all in self.shapes if base image is None
                    colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
        else:
            for i in range(len(self.shapes)):
                (x, y), r, circ_num = self.shapes[i]              
                if base_img is not None:
                    self.getClosestBaseShape(i)
                elif self.type == "TR" and not self.isPointInAnySpheroid((x,y)): # Ignore if sensor is not within a spheroid
                    shapes_to_remove.append(self.shapes[i])
                    continue
                else:
                    colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
        if base_img is not None:
            self.drawBaseShapes(colour_img)
        map(self.shapes.remove, shapes_to_remove)
        self.setImg(colour_img) 

    ## Helper Funcitons ##
    def isPointInsideCircle(self, point, circle_coords):
        x, y = point
        (x_center, y_center), r, _ = circle_coords
        dist = r**2 - ((x_center-x)**2 + (y_center-y)**2);
        return dist >= 0

    def isPointInAnySpheroid(self, point):
        bfImage = self.view.bfImages.map[self.id]
        for shape in bfImage.shapes:
            if self.isPointInsideCircle(point, shape):
                return True
        return False

    def getClosestBaseShape(self, idx):
        if self.type == "TR":
            base_shapes = self.view.trImages.baseImage.shapes
        else:
            base_shapes = self.view.bfImages.baseImage.shapes
        
        # Finding closest base shape to the current shape
        min_dist = float('inf')
        closest_shape = None
        for shape in base_shapes:
            if self.type == "TR" and self.isInt(shape[-1]):
                continue
            dist = self.distance(self.shapes[idx][0], shape[0])
            if dist < min_dist:
                min_dist = dist
                closest_shape = shape

        # Replace in self.base_shapes if it is closer to the closest base shape
        # than any other shape in this image
        if closest_shape is None:
            return
        closest_shape_num = closest_shape[-1]
        closest_base_shape = self.base_shapes.get(closest_shape_num)
        if closest_base_shape is None or min_dist < closest_base_shape[1]:
            if min_dist > 150:
                return
            temp = deepcopy(self.shapes[idx])
            temp[-1] = closest_shape[-1]

            self.base_shapes[closest_shape_num] = temp, min_dist   
    
    def distance(self, p0, p1):
        return np.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

    def isInt(self, num):
        try: 
            int(num)
            return True
        except ValueError:
            return False        