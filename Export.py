from PyQt5 import QtCore, QtGui, QtWidgets
import xlsxwriter
from numpy import pi
import cv2

class ExportThread(QtCore.QThread):
    """Thread used for exporting operations. (All/Single Excel/Images)"""
    # Progress bar signals, connected to respective functions in main
    finished = QtCore.pyqtSignal()
    startPbar = QtCore.pyqtSignal(int)
    incrementPbar = QtCore.pyqtSignal()
    finishPbar = QtCore.pyqtSignal()        

    def __init__(self, bfImages, trImages, type_, path, parent=None):
        super(ExportThread, self).__init__(parent)
        self.bfImages = bfImages # Image collections
        self.trImages = trImages 
        self.type = type_ # Type of export (quantity and filetype)
        self.path = path # Selected path for export
        self.scale = 0.638 # Scale value in units of pixel/um

        self.initializeExcelFormats()

    def run(self):
        if self.type == "all-excel":
            self.exportAllExcel() 
        elif self.type == "single-excel":
            self.exportSingleExcel()
        elif self.type == "all-images":
            self.exportAllImages()
        elif self.type == "single-image":
            self.exportSingleImage()
        else:
            pass
        self.finished.emit()

    def initializeExcelFormats(self):
        """Defining formatting objects to be used with xlsxwriter for cell formatting"""
        self.h1_data = {'bold': 1,'underline': 1,'align': 'center','valign': 'vcenter','fg_color': '#FFD966'}
        self.h2_data = {'bold': 1,'underline': 1,'align': 'center','valign': 'vcenter','fg_color': '#F4B084'}
        self.h3_data = {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#C6E0B4'}
        self.id_data = {'bold': 1, 'align': 'left', 'fg_color': '#8EA9DB'}
        self.strain_data = {'align': 'right','fg_color': '#C6E0B4'}
        self.data_format_params = {'align': 'right','fg_color': '#C6E0B4'}

    def exportExcel(self, data, spheroidIds, sensorIds, dayIds):
        """
        Exports an Excel sheet for both raw data and calculated data or just raw data for single image.
        Args:
          data: Dictionary containing all shape data sorted by days and spheroid/sensor. Format given in getBaseData().
          spheroidIds: List of spheroid ids. Ex. ["1", "2", "3"]
          sensorIds: List of sensor ids. Ex. ["1a", "1b", "2a"]
          dayIds: List of day ids. Ex. ["p00", "p01", "p02"]        
        """
        # Full Excle file save path
        if self.bfImages.path:
            path = self.path + self.bfImages.path.split("/")[-2] + " - Dimensions.xlsx"
        else:
            path = self.path + "Dimensions.xlsx"

        # Create new workbook and sheet
        workbook = xlsxwriter.Workbook(path)
        rawDataSheet = workbook.add_worksheet("Raw Data")

        # Excel formats -- format object must be added to workbook object to be used when writing cells
        h1_format = workbook.add_format(self.h1_data)
        h2_format = workbook.add_format(self.h2_data)
        h3_format = workbook.add_format(self.h3_data)
        id_format = workbook.add_format(self.id_data)
        data_format = workbook.add_format(self.data_format_params)
        data_format.set_num_format('0.00')
        strain_format = workbook.add_format(self.strain_data)
        strain_format.set_num_format('0.00000000')        

        # Create map of {spheroidId:sensor count (int)} (sensors within spheroids)
        # Used for writing data to Excel with appropriate spacing
        sensorCount = {}
        for spheroidId in spheroidIds:
            sensorList = []
            for sensorId in sensorIds:
                if len(spheroidId) == 2: # If two digit spheroidId
                    if sensorId[0:2].isdigit() and int(sensorId[0:2]) == int(spheroidId): # If sensor number matches spheroid number
                        sensorList.append(sensorId)
                elif int(spheroidId) == int(sensorId[0]) and not sensorId[0:2].isdigit(): # If sensor number matches spheroid number
                    sensorList.append(sensorId)
            sensorCount[spheroidId] = sensorList      

        # Headings for a single row of data for a day --> First set of attributes is for spheroids, second is for sensors
        headerRow = ["ID#","AREA","X","Y","MAJOR","MINOR","ADJ. ANGLE","ID#","AREA","X","Y","MAJOR","MINOR","ADJ. ANGLE"]
        def writeRawDayData(startRow, startCol, dayId):
            """
            Writes the raw shape data to an Excel sheet at the given region for the given day.
            Args:
              startRow: Number of the row to start at (starting at row 0)
              startCol: Number of the column to start at (starting at col 0)
              dayId: Day ID to write the data of
            """
            rowNum, colNum = startRow, startCol
            
            # Convert spheroid and sensor data into arrays of strings for Excel write
            # If there is no row data for that shape, use row of empty strings
            spheroidRows = []
            for id_ in spheroidIds:
                rowData = data[dayId][0].get(id_,['','','','','','',''])
                spheroidRows.append([str(id_)] + rowData)
            sensorRows = []
            for id_ in sensorIds:
                rowData = data[dayId][1].get(id_,['','','','','','',''])
                sensorRows.append([str(id_)] + rowData)       
            
            # Header Rows --> merge_range used to merge cells in Excel
            rawDataSheet.merge_range(startRow, startCol, startRow, startCol + 13, "DAY{}".format(dayId.upper()), h1_format)
            rowNum = rowNum + 1
            rawDataSheet.merge_range(rowNum, startCol, rowNum, startCol + 6, "SPHEROID", h2_format)
            rawDataSheet.merge_range(rowNum, startCol + 7, rowNum, startCol + 13, "SENSOR", h2_format)
            rowNum = rowNum + 1
            for i in range(len(headerRow)):
                entry = headerRow[i]
                # ID rows have different cell formatting (blue colour)
                if i == 0 or i == 7:
                    rawDataSheet.write(rowNum, colNum, entry, id_format)
                else:
                    rawDataSheet.write(rowNum, colNum, entry, h3_format)
                colNum = colNum + 1
            rowNum = rowNum + 1
            colNum = startCol

            # Spheroid Rows
            data_start = rowNum, colNum
            # Write spheroid row data 
            for row in spheroidRows:
                for j in range(len(row)):
                    entry = row[j]
                    if j > 0:
                        # Numbers use a different function to write than an empty string, so check for empty string
                        if entry:
                            rawDataSheet.write_number(rowNum, colNum, float(entry), data_format)
                        else:
                            rawDataSheet.write(rowNum, colNum, entry, data_format)
                    else:
                        # ID requires separate data formatting
                        rawDataSheet.write_number(rowNum, colNum, float(entry), id_format)
                    colNum = colNum + 1
                currRow = rowNum

                rowNum = rowNum + 1
                colNum = startCol   

                # Skip the number of rows corresponding to the number of sensors in the spheroid
                # This allows for easier data readability in the Excel sheet
                if row == spheroidRows[-1]:
                    break
                while rowNum < currRow + len(sensorCount[row[0]]) + 1:
                    for j in range(len(row)):
                        if j > 0:
                            rawDataSheet.write(rowNum, colNum, "", data_format)
                        else:
                            rawDataSheet.write(rowNum, colNum, "", id_format)
                        colNum = colNum + 1     
                    rowNum = rowNum + 1
                    colNum = startCol

            # Sensor Rows
            rowNum, colNum = data_start
            colNum = colNum + 7
            # Write sensor row data
            for i in range(len(sensorRows)):
                row = sensorRows[i]
                for j in range(len(row)):
                    entry = row[j]
                    if j > 0:
                        if entry:
                            rawDataSheet.write_number(rowNum, colNum, float(entry), data_format)
                        else:
                            rawDataSheet.write(rowNum, colNum, entry, data_format)
                    else:
                        rawDataSheet.write(rowNum, colNum, entry, id_format)
                    colNum = colNum + 1

                # Writes a blank row with proper formatting if the sensor NUMBER changes
                if i < len(sensorRows) - 1:
                    # Gets row number, checks for single digit and double digit row numbers
                    currRowNum = row[0][0:2] if row[0][0:2].isdigit() else row[0][0]
                    nextRowNum = sensorRows[i+1][0][0:2] if sensorRows[i+1][0][0:2].isdigit() else sensorRows[i+1][0][0]
                    # Write blank row if current row number isn't equal to the next row number
                    if int(currRowNum) != int(nextRowNum):
                        rowNum = rowNum + 1  
                        colNum = startCol + 7
                        for j in range(len(row)):
                            if j > 0:
                                rawDataSheet.write(rowNum, colNum, "", data_format)
                            else:
                                rawDataSheet.write(rowNum, colNum, "", id_format)
                            colNum = colNum + 1     

                rowNum = rowNum + 1            
                colNum = startCol + 7    

        # Write to Raw Data to Excel file for each day in dictionary
        dayIds = sorted(data.keys())
        rowNum, colNum = 0, 0
        for i in range(len(dayIds)):
            id_ = dayIds[i]
            writeRawDayData(rowNum, colNum+(15*i), id_)
        # Change column widths to ensure numbers fit appropriately
        rawDataSheet.set_column(0, 15*len(dayIds), 10)
        if len(dayIds) < 2:
            # If there's only one day of data, don't try to calculate strains, just output Excel of raw data
            workbook.close()
            return

        # Worksheet used to represent calculated data from raw shape dimensions (i.e. strain data)
        calcDataSheet = workbook.add_worksheet("Calculated Data")
        headerRow = ["ID#","SPHEROID AREA STRAIN","RADIAL STRAIN","CIRCUMFERENTIAL STRAIN"]
        def writeCalcDayData(startRow, startCol, dayId):
            """
            Writes the strain data on a separate spreadsheet for the given region and day.
            Args:
              startRow: Number of the row to start at (starting at row 0)
              startCol: Number of the column to start at (starting at col 0)
              dayId: Day ID to write the data of
            """
            rowNum, colNum = startRow, startCol
            
            # Get strain data for row
            strainRows = []
            for sensorId in sensorIds:
                # Data indices: -1: Adjusted Angle, 0: Area, 3: Major, 4: Minor
                row = []
                # Number of the sensor (string), accounting for both double and single digits
                sensorNum = sensorId[0][0:2] if sensorId[0][0:2].isdigit() else sensorId[0][0]
                day0 = dayIds[0]

                # Get spheroid data
                currSpheroidData = data[dayId][0].get(sensorNum, '')
                day0SpheroidData = data[day0][0].get(sensorNum, '')

                # Empty row if either spheroid or day0 spheroid data doesn't exist
                if not currSpheroidData or not day0SpheroidData:
                    row = [sensorId, '', '', '']
                    strainRows.append(row)
                    continue

                # Calculating spheroid area strain *(currSpheroidArea - day0SpheroidArea) / day0SpheroidArea)
                areaStrain = (float(currSpheroidData[0]) - float(day0SpheroidData[0])) / float(day0SpheroidData[0]) 

                # Get sensor data
                currSensorData = data[dayId][1].get(sensorId, '')
                day0SensorData = data[day0][1].get(sensorId, '')

                # Emptry row if either sensor or day0 sensor data doesn't exist
                if not currSensorData or not day0SensorData:
                    row = [sensorId, areaStrain, '', '']
                    strainRows.append(row)
                    continue    
                # Check if difference of adjusted angles is less than 45 degrees
                if float(currSensorData[-1]) - float(currSpheroidData[-1]) < 45:
                    # (sensorMinor - day0SensorMajor) / (day0SensorMajor)
                    radialStrain = (float(currSensorData[4]) - float(day0SensorData[3])) / float(day0SensorData[3])
                    # (sensorMajor - day0SensorMinor) / (day0SensorMinor)
                    circStrain = (float(currSensorData[3]) - float(day0SensorData[4])) / float(day0SensorData[4])
                else:
                    # (sensorMajor - day0SensorMinor) / (day0SensorMinor)
                    radialStrain = (float(currSensorData[3]) - float(day0SensorData[4])) / float(day0SensorData[4])
                    # (sensorMinor - day0SensorMajor) / (day0SensorMajor)
                    circStrain = (float(currSensorData[4]) - float(day0SensorData[3])) / float(day0SensorData[3])

                row = [sensorId, areaStrain, radialStrain, circStrain] # Row to write to Excel
                strainRows.append(row)
                
            # Writing header rows
            calcDataSheet.merge_range(startRow, startCol, startRow, startCol + 3, "DAY{}".format(dayId.upper()), h1_format)
            rowNum = rowNum + 1
            for i, entry in enumerate(headerRow): 
                if i == 0:
                    calcDataSheet.write(rowNum, colNum, entry, id_format)
                else:
                    calcDataSheet.write(rowNum, colNum, entry, h3_format)
                colNum = colNum + 1
            colNum = startCol
            rowNum = rowNum + 1

            # Writing to calculated data spreadsheet
            for i, row in enumerate(strainRows):
                for j in range(len(row)):
                    entry = row[j]
                    if j > 0:
                        if entry:
                            calcDataSheet.write_number(rowNum, colNum, float(entry), strain_format)
                        else:
                            calcDataSheet.write(rowNum, colNum, entry, strain_format)
                    else:
                        calcDataSheet.write(rowNum, colNum, entry, id_format)
                    colNum = colNum + 1

                # Write blank row when going between sensors
                if i < len(strainRows) - 1:
                    currRowNum = row[0][0:2] if row[0][0:2].isdigit() else row[0][0]
                    nextRowNum = strainRows[i+1][0][0:2] if strainRows[i+1][0][0:2].isdigit() else strainRows[i+1][0][0]

                    if int(currRowNum) != int(nextRowNum):
                        rowNum = rowNum + 1  
                        colNum = startCol
                        for j in range(len(row)):
                            if j > 0:
                                calcDataSheet.write(rowNum, colNum, "", strain_format)
                            else:
                                calcDataSheet.write(rowNum, colNum, "", id_format)
                            colNum = colNum + 1     

                rowNum = rowNum + 1            
                colNum = startCol        

        # Writing calculated data to the Excel sheet
        rowNum, colNum = 0, 0
        for i, id_ in enumerate(dayIds[1:]):
            writeCalcDayData(rowNum, colNum+(5*i), id_)
        # Changing size of columns to fit numbers appropriately
        calcDataSheet.set_column(0, 5*(len(dayIds)-1), 20) 

        workbook.close() 

    def exportAllExcel(self):
        """Exports excel with shape data and strain data for all images"""
        # Redraw all images to ensure base shapes are up to date with base image
        for img in self.bfImages.list + self.trImages.list:
            img.redraw()

        data, spheroidIds, sensorIds, dayIds = self.getAllData()
        if len(data) == 0:
            return
        self.exportExcel(data, spheroidIds, sensorIds, dayIds)

    def exportSingleExcel(self):
        """Exports excel with shape data for a single image"""
        self.trImages.baseImage.redraw()
        self.bfImages.baseImage.redraw()

        data, spheroidIds, sensorIds, dayIds = self.getBaseData()
        if len(data) == 0:
            return
        self.exportExcel(data, spheroidIds, sensorIds, dayIds)

    def getShapeData(self, isEllipse, shape):
        """
        Gets a list of shape data to be written in an Excel row.

        Args:
          isEllipse: Boolean describing type of shape, Ellipse or Circle.
          shape: Shape data. (Ellipse: ((x,y),(w,h),ang,id) ; Circle: ((x, y),r,id))

        Returns:
          List of shape data to be written to Excel:
            - Major and minor of a circle are just the radius. Adjusted Angle is 0. 
            Ex. [area,x,y,major,minor,adjusted angle]
        """
        if isEllipse:
            # Get and scale data
            (x,y), (w,h), ang, _ = shape
            x, y, w, h = x/self.scale, y/self.scale, w/self.scale, h/self.scale
            # Calculate area and find the major/minor
            area = w * h * pi / 4
            major = max(w,h)
            minor = min(w,h)
            # OpenCV to ImageJ Angle Conversion
            if ang > 90:
                ang = 270 - ang
            else:
                ang = 90 - ang
            # Adjust angle from original Excel Sheet
            if ang > 90:
                ang = 180 - ang
            data = [str(area),str(x),str(y),str(major),str(minor),str(ang)]            
        else:
            (x, y), r, _ = shape
            x, y, r = x/self.scale, y/self.scale, r/self.scale
            area = pi*r**2
            data = [str(area),str(x),str(y),str(r),str(r),"0"]
        return data

    def getAllData(self):
        """ 
        Returns data of all shapes.

        Returns:
          data: Dictionary containing all shape data sorted by days and spheroid/sensor. Format given in getBaseData().
          spheroidIds: List of spheroid ids. Ex. ["1", "2", "3"]
          sensorIds: List of sensor ids. Ex. ["1a", "1b", "2a"]
          dayIds: List of day ids. Ex. ["p00", "p01", "p02"]        
        """
        data, spheroidIds, sensorIds, dayIds = self.getBaseData()
    
        for id_ in dayIds:
            bfImg = self.bfImages.map[id_]
            trImg = self.trImages.map[id_]
            if bfImg is self.bfImages.baseImage:
                continue
            spheroid_map = {}
            sensor_map = {}    

            if bfImg.base_shapes:
                # Populate spheroid map
                for shape_id, (shape, _) in bfImg.base_shapes.items():  
                    spheroid_map[shape_id] = self.getShapeData(bfImg.ellipse, shape)
            if trImg.base_shapes:
                # Populate sensor map
                for shape_id, (shape, _) in trImg.base_shapes.items():
                    sensor_map[shape_id] = self.getShapeData(trImg.ellipse, shape)
            # Add day entry corresponding to spheroid and sensor map to data dictionary
            data[id_] = (spheroid_map, sensor_map)

        return data, spheroidIds, sensorIds, dayIds

    def getBaseData(self):
        """ 
        Returns data of just the base shape.

        Returns:
          data: Dictionary containing base shape data sorted by days and spheroid/sensor. Format given below.
          spheroidIds: List of spheroid ids. Ex. ["1", "2", "3"]
          sensorIds: List of sensor ids. Ex. ["1a", "1b", "2a"]
          dayIds: List of day ids. Ex. ["p00", "p01", "p02"]
        """
        bfBaseImg = self.bfImages.baseImage
        trBaseImg = self.trImages.baseImage
        if bfBaseImg is None:
            return

        data = {} # Data formatted as dictionary. {"day_id": spheroid_map, sensor_map}
                  # Spheroid/sensor map formatted as follows: {"shape_id" : [area,x,y,major,minor,adjusted angle]}

        dayIds = sorted(self.bfImages.map.keys())

        # Get lists of Ids of base shapes
        spheroidIds = []
        sensorIds = []

        spheroid_map = {}
        sensor_map = {}                
        for shape in bfBaseImg.shapes:
            shape_id = shape[-1]
            spheroid_map[shape_id] = self.getShapeData(bfBaseImg.ellipse, shape)
            spheroidIds.append(shape_id)
        for shape in trBaseImg.shapes:
            shape_id = shape[-1]
            if not trBaseImg.isInt(shape_id):
                sensor_map[shape_id] = self.getShapeData(trBaseImg.ellipse, shape)
                sensorIds.append(shape_id)
        
        data[self.bfImages.baseId] = (spheroid_map, sensor_map)
        return data, sorted(spheroidIds), sorted(sensorIds), dayIds

    def exportAllImages(self):
        """Exports all images as PNGs"""
        allImages = self.bfImages.list + self.trImages.list 
        for img in allImages:
            img.redraw()     
        for img in allImages:
            filename = img.name.split(".")[0]
            cv2.imwrite(self.path + filename + ".png", img.imgArr)
            
    def exportSingleImage(self):
        """Exports a single pair of images as PNGs"""
        # Here self.bfImages and self.trImages are currImg and complement Image objects
        for img in (self.bfImages, self.trImages):
            filename = img.name.split(".")[0]
            cv2.imwrite(self.path + filename + ".png", img.imgArr)        