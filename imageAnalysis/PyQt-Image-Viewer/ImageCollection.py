class ImageCollection:
    def __init__(self, type_, qlabel):
        self.type = type_

        self.qlabel = qlabel # Widget/window name where image is displayed
        self.path = "" # Full folder path
        self.list = [] # List of Image objects

        self.map = {}

    def initMap(self):
        for image in self.list:
            self.map[image.id] = image

    def reset(self):
        self.list = []
        self.map = {}
