from PyQt5 import QtCore, QtGui, QtWidgets
import xlsxwriter
from numpy import pi

class ExportThread(QtCore.QThread):
    finished = QtCore.pyqtSignal()
    startPbar = QtCore.pyqtSignal(int)
    incrementPbar = QtCore.pyqtSignal()
    finishPbar = QtCore.pyqtSignal()        

    def __init__(self, bfImages, trImages, type_, path, parent=None):
        super(ExportThread, self).__init__(parent)
        self.bfImages = bfImages
        self.trImages = trImages
        self.type = type_
        self.path = path
        self.scale = 0.638 # 0.638 pixels/um

        self.initializeExcelFormats()

    def run(self):
        if self.type == "all-excel":
            self.exportAllExcel() 
        elif self.type == "single-excel":
            self.exportSingleExcel()
        else:
            pass
        self.finished.emit()

    def initializeExcelFormats(self):
        self.h1_data = {'bold': 1,'underline': 1,'align': 'center','valign': 'vcenter','fg_color': '#FFD966'}
        self.h2_data = {'bold': 1,'underline': 1,'align': 'center','valign': 'vcenter','fg_color': '#F4B084'}
        self.h3_data = {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#C6E0B4'}
        self.id_data = {'bold': 1, 'align': 'left', 'fg_color': '#8EA9DB'}
        self.strain_data = {'align': 'right','fg_color': '#C6E0B4'}
        self.data_format_params = {'align': 'right','fg_color': '#C6E0B4'}

    def exportExcel(self, data, spheroidIds, sensorIds, dayIds):
        # Name of file
        path = self.path + self.bfImages.path.split("/")[-2] + " - Dimensions.xlsx"

        # Create new workbook and sheet
        workbook = xlsxwriter.Workbook(path)
        rawDataSheet = workbook.add_worksheet("Raw Data")

        # Excel formats
        h1_format = workbook.add_format(self.h1_data)
        h2_format = workbook.add_format(self.h2_data)
        h3_format = workbook.add_format(self.h3_data)
        id_format = workbook.add_format(self.id_data)
        data_format = workbook.add_format(self.data_format_params)
        data_format.set_num_format('0.00')
        strain_format = workbook.add_format(self.strain_data)
        strain_format.set_num_format('0.00000000')        

        # Create map of spheroids:sensor count (sensors within spheroids)
        sensorCount = {}
        for spheroidId in spheroidIds:
            sensorList = []
            for sensorId in sensorIds:
                if int(spheroidId) == int(sensorId[0]):
                    sensorList.append(sensorId)
            sensorCount[spheroidId] = sensorList      

        headerRow = ["ID#","AREA","X","Y","MAJOR","MINOR","ADJ. ANGLE","ID#","AREA","X","Y","MAJOR","MINOR","ADJ. ANGLE"]

        def writeRawDayData(startRow, startCol, dayId):
            rowNum, colNum = startRow, startCol
            
            # Convert spheroid and sensor data into arrays of strings for Excel write
            spheroidRows = []
            for id_ in spheroidIds:
                rowData = data[dayId][0].get(id_,['','','','','','',''])
                spheroidRows.append([str(id_)] + rowData)
            sensorRows = []
            for id_ in sensorIds:
                rowData = data[dayId][1].get(id_,['','','','','','',''])
                sensorRows.append([str(id_)] + rowData)       
            
            # Header Rows
            rawDataSheet.merge_range(startRow, startCol, startRow, startCol + 13, "DAY{}".format(dayId.upper()), h1_format)
            rowNum = rowNum + 1
            rawDataSheet.merge_range(rowNum, startCol, rowNum, startCol + 6, "SPHEROID", h2_format)
            rawDataSheet.merge_range(rowNum, startCol + 7, rowNum, startCol + 13, "SENSOR", h2_format)
            rowNum = rowNum + 1
            for i in range(len(headerRow)):
                entry = headerRow[i]
                if i == 0 or i == 7:
                    rawDataSheet.write(rowNum, colNum, entry, id_format)
                else:
                    rawDataSheet.write(rowNum, colNum, entry, h3_format)
                colNum = colNum + 1
            rowNum = rowNum + 1
            colNum = startCol

            # Spheroid Rows
            data_start = rowNum, colNum

            for row in spheroidRows:
                for j in range(len(row)):
                    entry = row[j]
                    if j > 0:
                        if entry:
                            rawDataSheet.write_number(rowNum, colNum, float(entry), data_format)
                        else:
                            rawDataSheet.write(rowNum, colNum, entry, data_format)
                    else:
                        rawDataSheet.write_number(rowNum, colNum, float(entry), id_format)
                    colNum = colNum + 1
                currRow = rowNum

                rowNum = rowNum + 1
                colNum = startCol   

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
                    currRowNum = row[0][0:2] if row[0][0:2].isdigit() else row[0][0]
                    nextRowNum = sensorRows[i+1][0][0:2] if sensorRows[i+1][0][0:2].isdigit() else sensorRows[i+1][0][0]

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

        # Write to Raw Data to Excel file
        dayIds = sorted(data.keys())
        rowNum, colNum = 0, 0
        for i in range(len(dayIds)):
            id_ = dayIds[i]
            writeRawDayData(rowNum, colNum+(15*i), id_)
        rawDataSheet.set_column(0, 15*len(dayIds), 10)
        if len(dayIds) < 2:
            workbook.close()
            return

        calcDataSheet = workbook.add_worksheet("Calculated Data")
        headerRow = ["ID#","SPHEROID AREA STRAIN","RADIAL STRAIN","CIRCUMFERENTIAL STRAIN"]
        def writeCalcDayData(startRow, startCol, dayId):
            rowNum, colNum = startRow, startCol
            
            # Get strain data for row
            strainRows = []
            for sensorId in sensorIds:
                # Data indices: -1: Adj. Angle, 0: Area, 3: Major, 4: Minor
                row = []

                sensorNum = sensorId[0][0:2] if sensorId[0][0:2].isdigit() else sensorId[0][0]
                day0 = dayIds[0]

                currSpheroidData = data[dayId][0].get(sensorNum, '')
                day0SpheroidData = data[day0][0].get(sensorNum, '')

                if not currSpheroidData or not day0SpheroidData:
                    row = [sensorId, '', '', '']
                    strainRows.append(row)
                    continue

                areaStrain = (float(currSpheroidData[0]) - float(day0SpheroidData[0])) / float(day0SpheroidData[0]) 

                currSensorData = data[dayId][1].get(sensorId, '')
                day0SensorData = data[day0][1].get(sensorId, '')

                if not currSensorData or not day0SensorData:
                    row = [sensorId, areaStrain, '', '']
                    strainRows.append(row)
                    continue    

                if float(currSensorData[-1]) - float(currSpheroidData[-1]) < 45:
                    radialStrain = (float(currSensorData[4]) - float(day0SensorData[3])) / float(day0SensorData[3])
                    circStrain = (float(currSensorData[3]) - float(day0SensorData[4])) / float(day0SensorData[4])
                else:
                    radialStrain = (float(currSensorData[3]) - float(day0SensorData[4])) / float(day0SensorData[4])
                    circStrain = (float(currSensorData[4]) - float(day0SensorData[3])) / float(day0SensorData[3])

                row = [sensorId, areaStrain, radialStrain, circStrain]
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

        rowNum, colNum = 0, 0
        for i, id_ in enumerate(dayIds[1:]):
            writeCalcDayData(rowNum, colNum+(5*i), id_)
        calcDataSheet.set_column(0, 5*(len(dayIds)-1), 20) 

        workbook.close() 

    def exportAllExcel(self):
        # map(lambda img: img.redraw(),self.bfImages.list + self.trImages.list)    
        for img in self.bfImages.list + self.trImages.list:
            img.redraw()

        data, spheroidIds, sensorIds, dayIds = self.getAllData()
        if len(data) == 0:
            return
        self.exportExcel(data, spheroidIds, sensorIds, dayIds)

    def exportSingleExcel(self):
        self.trImages.baseImage.redraw()
        self.bfImages.baseImage.redraw()

        data, spheroidIds, sensorIds, dayIds = self.getBaseData()
        if len(data) == 0:
            return
        self.exportExcel(data, spheroidIds, sensorIds, dayIds)

    def getShapeData(self, isEllipse, shape):
        # [area,x,y,major,minor,adjusted angle]
        if isEllipse:
            (x,y), (w,h), ang, _ = shape
            x, y, w, h = x/self.scale, y/self.scale, w/self.scale, h/self.scale
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
        data, spheroidIds, sensorIds, dayIds = self.getBaseData()
    
        for id_ in dayIds:
            bfImg = self.bfImages.map[id_]
            trImg = self.trImages.map[id_]
            if bfImg is self.bfImages.baseImage:
                continue
            spheroid_map = {}
            sensor_map = {}    

            if bfImg.base_shapes:
                for shape_id, (shape, _) in bfImg.base_shapes.items():  
                    spheroid_map[shape_id] = self.getShapeData(bfImg.ellipse, shape)
            if trImg.base_shapes:
                for shape_id, (shape, _) in trImg.base_shapes.items():
                    sensor_map[shape_id] = self.getShapeData(trImg.ellipse, shape)
            data[id_] = (spheroid_map, sensor_map)

        return data, spheroidIds, sensorIds, dayIds

    def getBaseData(self):
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