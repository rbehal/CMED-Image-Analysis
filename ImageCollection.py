class ImageCollection:
    """
    Image Collection object used to refer to a set of images.
    --> Currently just either Texas Red (sensor) images or Bright Field (spheroid) images
    """
    def __init__(self, type_, qlabel):
        self.type = type_

        self.qlabel = qlabel # Widget/window name where image is displayed
        self.path = "" # Full folder path
        self.list = [] # List of Image objects

        self.baseImage = None
        self.baseId = None

        self.map = {}

    def initMap(self):
        """Populate dictionary with images --> dict - {id : Image}"""
        for image in self.list:
            self.map[image.id] = image

    def reset(self):
        """Reset full image collection. Used when selected new set of images."""
        self.list = []
        self.map = {}
        self.baseImage = None
