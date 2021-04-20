class ImageCollection:
    """
    Image Collection object used to refer to a set of images.
    --> Currently just either Texas Red (sensor) images or Bright Field (spheroid) images
    """
    def __init__(self, type_, qlabel):
        self.type = type_ # Either "BF" or "TR" for those collections respectively

        self.qlabel = qlabel # Widget/window name where image is displayed
        self.path = "" # Full folder path
        self.list = [] # List of Image objects

        self.baseImage = None # Image Object that defines that each image in col. looks for to map base shapes
        self.baseId = None # ID of the base shape

        self.map = {} # Map of image IDs to Image objects

    def initMap(self):
        """Populate dictionary with images --> dict - {id : Image}"""
        for image in self.list:
            self.map[image.id] = image

    def reset(self):
        """Reset full image collection. Used when selected new set of images."""
        self.list = []
        self.map = {}
        self.baseImage = None
