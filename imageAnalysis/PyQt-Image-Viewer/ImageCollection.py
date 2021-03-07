class ImageCollection:
    def __init__(self, type_, qlabel):
        self.type = type_

        self.qlabel = qlabel # Widget/window name where image is displayed
        self.path = "" # Full folder path
        self.list = [] # List of image names