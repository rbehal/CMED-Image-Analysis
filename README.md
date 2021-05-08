# CMED Image Analysis
Image analysis program built for the Cellular Microenvironment Design Lab at McGill University. The program detects and traces circles or ellipses in a pair of images using 
user-input threshold and radius range parameters. The program was built to detect sensors in spheropids in varying colour channels of the same image. The sensors are within the 
image in the red channel, and are visible as white dots in a black background. The spheroids are represented in the bright field channel, and are visible as brownish blobs on a 
varied taupish background. The program only detects spheroids that have sensors within them, as many did not in the sample data.

# Examples

### Upon running program:

![image](https://user-images.githubusercontent.com/1645830/117553157-d9d3ab00-b01d-11eb-9be8-0327961bca6e.png)

### Detecting spheroids:

![image](https://user-images.githubusercontent.com/1645830/117553186-fcfe5a80-b01d-11eb-9140-fa7af0805cc8.png)

### Detecting sensors:

![image](https://user-images.githubusercontent.com/1645830/117553198-0be50d00-b01e-11eb-8fc9-51f5c83711ce.png)

### Export data to Excel:

![image](https://user-images.githubusercontent.com/1645830/117553211-24edbe00-b01e-11eb-8aac-ed6fa29d1e23.png)

# Original Purpose - Abstract
The development of a means to measure miniscule tissue stresses is incredibly useful for the general understanding of dynamics at play during tissue formation. 
As demonstrated in a 2019 paper, polyacrylamide microspherical stress gauges (MSGs) can be dispersed into 3D multicellular spheroid (MCS) cultures to map radial and 
circumferential stresses. The methodology for mapping these stresses included tracing out circles and ellipses on the microscopy images of the MCS and MSGs using the 
ImageJ analysis software to extract the dimensions of the fitted shapes in order eventually yield the stresses. This process of individually tracing out the shapes was 
labour intensive and inefficient.  The purpose of this research was to develop a programmatically assisted method of calculating internal stresses from microscopy images 
of MCS and MSGs. This was done by employing utilizing the OpenCV Python package to fit shapes to detected contours in binary thresholded images, provided constraint parameters 
through a GUI developed with PyQt5. This process is shown to be much faster and more efficient than manual mapping through ImageJ, with a tradeoff of perfection and error 
tracking; further work is able to be done to explore rectifications of those drawbacks.

# Other Uses
The program can easily be adapted to much more general use cases. For example, simply automatically detecting and tracing out shapes in an image and then having that data exported in the form of Excel, images, etc.
