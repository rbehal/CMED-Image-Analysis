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

        self.imgArr = self.preprocessImg(self.path)
        self.imgQt = self.convertCvImage2QtImage(self.imgArr)

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
