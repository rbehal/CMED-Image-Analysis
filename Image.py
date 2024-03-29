from PIL.ImageQt import ImageQt 
import PIL.Image
import cv2
import numpy as np
from copy import deepcopy


class Image:
    def __init__(self, id_, name, type_, path, view):
        self.id = id_ # ID of image: "p##" for day/timelapse "##" for z-stack
        self.name = name # Image name with extension
        self.type = type_ # Either "BF" or "TR" for those collections respectively
        self.path = path # Full file path to image

        self.view = view # Reference to ImageViewer

        self.originalImg = self.preprocessImg(self.path) # Raw image

        self.imgArr = self.preprocessImg(self.path) # 8-bit image represented by NumpyArray
        self.imgQt = self.convertCvImage2QtImage(self.imgArr) # QtImage object
        self.threshold = 120
        self.radiusRange = (40, 500) if type_ == "BF" else (10, 100)

        self.shapes = [] # List of fitted shape data in tuple format (format depends on if ellipses or circles)
        self.base_shapes = {} # Dictionary of {base shape id : shape data tuple} 
        self.ellipse = False # Keeps track of whether the shapes are ellipses or circles

    def preprocessImg(self, img_path):
        """
        Normalize image using minimum and maximum bit values. Necessary to display TIFF properly.
        Args:
          img_path: Raw image path. Ex. r"C:/User/Rahul/Data/image.TIFF"
        Returns:
          image: Numpy array of 8-bit image.
        """
        image = cv2.imread(img_path, -1) # Import raw image
        # Image must be normalized between min. and max. pixel values to display TIFF correctly
        min_bit = np.min(image)
        max_bit = np.max(image)
        norm_image = cv2.normalize(image, dst=None, alpha=min_bit, beta=max_bit, norm_type=cv2.NORM_MINMAX)
        image = (norm_image/16).astype('uint8')
        return image

    # Convert an opencv image to QPixmap
    def convertCvImage2QtImage(self, cv_img_arr):
        """
        Converts 8-bit image numpy array to ImageQt object.
        Args:
          cv_img_arr: Numpy array of 8-bit image.
        Returns:
          ImageQt: Qt Image object, necessary for GUI display/Piximap.
        """
        PIL_image = PIL.Image.fromarray(cv_img_arr)
        return ImageQt(PIL_image)   

    def setImg(self, imgArr):
        """
        Sets 8-bit image numpy array (imgArr) and ImageQt object (imgQt)
        Args:
          imgArr: Numpy array of 8-bit image.
        """
        self.imgArr = imgArr
        self.imgQt = self.convertCvImage2QtImage(self.imgArr)            

    def drawCircle(self, threshold, radius_range, pBar):
        """
        Detects and traces circles in the image. 
        Args:
          threshold: Integer value to run binary thresholding on. Pixel values below this will be turned black, above white.
          radius_range: (int, int) Minimum and maximum radius range to consider in pixels.
          pBar: Thread object to be used to emit progress bar signals.
        """
        pBar.incrementPbar.emit()
        img = self.preprocessImg(self.path) # Start with fresh image to fit and draw shapes to

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

            (x, y), r = cv2.minEnclosingCircle(contour) # Fits contours to a circle shape
            if r > radius_range[1]:
                continue
            circle_coords.append([(x, y), r, str(circle_num)])
            circle_num = circle_num + 1

        # Check if spheroids have sensors in them -- Only keep the ones that do
        if self.type == "BF" and self.id in self.view.trImages.map:
            trImage = self.view.trImages.map[self.id]
            if len(trImage.shapes) > 0:
                temp = []
                # Letter map for sensor naming
                # Sensors are named according to which spheroid they're in. Ex. "1a", "1b", "2a", etc.
                letter_map = {0:"a",1:"b",2:"c",3:"d",4:"e",5:"f",6:"g",7:"h"} 

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

        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB) # Convert to colour image to outline circles
        colour = (255, 0, 0) # Red
        thickness = 3    

        # Actually draw circles to array
        for (x, y), r, circ_num in circle_coords:
            colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
        self.setImg(colour_img)    


    def drawEllipse(self, threshold, radius_range, pBar):
        """
        Detects and traces ellipses in the image. 
        Args:
          threshold: Integer value to run binary thresholding on. Pixel values below this will be turned black, above white.
          radius_range: (int, int) Minimum and maximum radius range (approx. circle) to consider in pixels.
          pBar: Thread object to be used to emit progress bar signals.
        """
        pBar.incrementPbar.emit()
        img = self.preprocessImg(self.path) # Start with fresh image to fit and draw shapes to

        # Binary thresholding of image and calculation of contours
        _, thresh = cv2.threshold(img, threshold, np.max(img), cv2.THRESH_BINARY)
        raw_contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        # Filter out smaller contours and create new contour list to analyze
        contours = []
        for contour in raw_contours:
            # Most items in raw contours are lines or small shapes
            if cv2.contourArea(contour) < (np.pi * radius_range[0] ** 2):
                continue
            contours.append(contour)

        pBar.startPbar.emit(len(contours) + 2)

        ellipse_coords = []
        ellipse_num = 1
        # Loop through contours and attemp to fit ellipse objects, if they're big enough add it
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

        # Actually draw ellipses to an array
        for (x,y),(w,h),ang,num in ellipse_coords:
            colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
        self.setImg(colour_img) 

    def drawBaseShapes(self, colour_img):
        """
        Draws all the base shapes on the provided image. Base shapes are shapes of this image that correlate to the shapes of the base image.
        Args:
          colour_img: 8-bit numpy array of image to colour
        """
        if not bool(self.base_shapes):
            # If empty base_shapes dict, return
            return

        colour = (255, 0, 0) # Red
        thickness = 3        
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Draw base shapes with identifying numbering next to them 
        if self.ellipse:
            for ((x,y),(w,h),ang,num),_ in self.base_shapes.values():            
                colour_img = cv2.ellipse(colour_img, ((x,y), (w,h), ang), colour, thickness); 
                colour_img = cv2.putText(colour_img, num, (int(x+max(w,h)+10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)            
        else:
            for ((x, y),r,circ_num),_ in self.base_shapes.values():
                colour_img = cv2.circle(colour_img, (int(x),int(y)), int(r), colour, thickness) 
                colour_img = cv2.putText(colour_img, circ_num, (int(x + r + 10), int(y)), font, 2, colour, thickness, cv2.LINE_AA)                                    

    def redraw(self): 
        """Draw shapes that correlate with the closest shapes on the base image. These are the base shapes."""
        colour = (255, 0, 0) # Red
        thickness = 3        
        font = cv2.FONT_HERSHEY_SIMPLEX

        img = self.preprocessImg(self.path) # Start with raw image
        colour_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        # Define appropriate base image
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
        """
        Args:
          point: (x,y) Coordinate
          circle_coords: Circle data, coordinates will be extracted. Ex. ((x_center, y_center), r, _)

        Returns:
          True if point is inside circle, False if not
        """
        x, y = point
        (x_center, y_center), r, _ = circle_coords
        dist = r**2 - ((x_center-x)**2 + (y_center-y)**2);
        return dist >= 0

    def isPointInAnySpheroid(self, point):
        """
        Args:
          point: (x,y) Coordinate

        Returns:
            True if that point is in any of the spheroids drawn
        """
        bfImage = self.view.bfImages.map[self.id]
        for shape in bfImage.shapes:
            if self.isPointInsideCircle(point, shape):
                return True
        return False

    def getClosestBaseShape(self, idx):
        """
        Add shape to base shapes (base_shapes) with id correlating to the closest base shape.
        Args:
          idx: Index of shape to add to base shapes
        """
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
                # If closest shape is arbitrarily far away (150 pixels), ignore it 
                return
            temp = deepcopy(self.shapes[idx])
            temp[-1] = closest_shape[-1]

            self.base_shapes[closest_shape_num] = temp, min_dist   
    
    def distance(self, p0, p1):
        """
        Args:
          p0: (x1,y1) Coordinate
          p1: (x2,y2) Coordinate
        Returns:
          distance: Distance between two points
        """
        return np.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

    def isInt(self, num):
        """
        Args:
          num: String
        Returns:
          True if num is an integer string
        """
        try: 
            int(num)
            return True
        except ValueError:
            return False    

    def getSharpness(self):
        """Returns the sharpness value of the image"""
        # Compute the Laplacian of the image and then return the shar[ness]
        # measure, which is simply the variance of the Laplacian
        return cv2.Laplacian(self.imgArr, cv2.CV_64F).var()            