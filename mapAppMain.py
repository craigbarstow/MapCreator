from PyQt4 import QtGui
from mapCreatorUI import Ui_MapCreator
import arcpy, os, os.path, sys
from arcpy import env

class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = Ui_MapCreator()
        self.ui.setupUi(self)

        #set up global variables
        defaultFileSearchLoc = "C:\\Users"
        self.kmlInput = False
        self.templateMapLoc = ""
        self.lastTemplateDir = defaultFileSearchLoc
        self.layerLocations = {}
        self.lastLayerDir = defaultFileSearchLoc
        self.uniqueLayerLoc = ""
        self.lastUniqueLayerLoc = defaultFileSearchLoc
        self.destinationDir = ""
        self.lastDestinationDir = defaultFileSearchLoc

        """connect signals/slots"""
        self.ui.btnSetTemplateLoc.clicked.connect(self.trySetTemplateLoc)
        self.ui.btnAddLayer.clicked.connect(self.addNewLayer)
        self.ui.checkBoxLayer.clicked.connect(self.layerInputChecked)
        self.ui.checkBoxKML.clicked.connect(self.kmlInputChecked)
        self.ui.btnSetUniqueLayerLoc.clicked.connect(self.setUniqueLayerDir)
        self.ui.btnSetDestDir.clicked.connect(self.setDestDir)
        self.ui.btnCreateMaps.clicked.connect(self.makeMaps)

        """set all text fields to read only"""
        self.ui.templateLocLineEdit.setReadOnly(True)
        self.ui.uniqueLayerLineEdit.setReadOnly(True)
        self.ui.destDirLineEdit.setReadOnly(True)

        """set layer checkbox to be initially checked"""
        self.ui.checkBoxLayer.setChecked(not self.kmlInput)
        self.ui.checkBoxLayer.setEnabled(False)

    def trySetTemplateLoc(self):
        mapFile = QtGui.QFileDialog.getOpenFileName(self, "Select ArcGIS Template Map File", self.lastTemplateDir, "*.mxd")

        #set last template directory
        if len(str(mapFile)) > 0:
            self.lastTemplateDir = str(mapFile)

        #test for validity here
        self.templateMapLoc = mapFile
        self.ui.templateLocLineEdit.setText(self.templateMapLoc)

    def addNewLayer(self):
        newLayerLoc = QtGui.QFileDialog.getOpenFileName(self, "Select ArcGIS Layer File", self.lastLayerDir, "*.lyr")
        #set last layer directory variable
        layerName = str(newLayerLoc).split(r"/")[-1]

        if len(str(newLayerLoc)) > 0:
            self.lastLayerDir = str(newLayerLoc)

        #test for validity

        if len(newLayerLoc) > 0:
            self.layerLocations[layerName] = newLayerLoc
            self.ui.listLayers.insertItem(0, layerName)

    def setDestDir(self):
        destDir = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", self.lastDestinationDir))
        if len(destDir) > 0:
            self.lastDestinationDir = destDir
            self.destinationDir = destDir
            self.ui.destDirLineEdit.setText(destDir)

    def setUniqueLayerDir(self):
        uniqueDir = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", self.lastDestinationDir))
        if len(uniqueDir) > 0:
            self.lastUniqueLayerLoc = uniqueDir
            self.uniqueLayerLoc = uniqueDir
            self.ui.uniqueLayerLineEdit.setText(uniqueDir)

    def kmlInputChecked(self):
        self.kmlInput = True
        self.ui.checkBoxLayer.setChecked(False)
        self.ui.checkBoxKML.setEnabled(False)
        if not self.ui.checkBoxLayer.isEnabled():
            self.ui.checkBoxLayer.setEnabled(True)
        self.ui.uniqueLayerLabel.setText("Directory Containing KML Files")
        #self.ui.logListWidget.insertItem(0, "KML Input = " + str(self.kmlInput))

    def layerInputChecked(self):
        self.kmlInput = False
        self.ui.checkBoxKML.setChecked(False)
        self.ui.checkBoxLayer.setEnabled(False)
        if not self.ui.checkBoxKML.isEnabled():
            self.ui.checkBoxKML.setEnabled(True)
        self.ui.uniqueLayerLabel.setText("Directory Containing Layer Files")
        #self.ui.logListWidget.insertItem(0, "KML Input = " + str(self.kmlInput))

    def makeMaps(self):
        if self.kmlInput:
            print "converting kml files"

        #make maps
        """MAKE SURE .kml or .lyr LAYER FILES ARE PRESENT IN GIVEN DIR"""
        for fileName in os.listdir(self.uniqueLayerLoc):
            if fileName.endswith('.lyr'):
                origMap = arcpy.mapping.MapDocument(self.templateMapLoc)
                new_map_name = fileName.strip('.lyr') + ".mxd"
                self.ui.logListWidget.insertItem(0, "Creating map: " + str(new_map_name))
                newMapLocation = self.destinationDir + "//" + new_map_name
                #check to see if map of this name exists in the directory
                #if so delete it
                origMap.saveACopy(newMapLocation)
                del origMap

                #start work on newly created map
                newMap = arcpy.mapping.MapDocument(newMapLocation)

                #access basemap frame
                mainFrame = arcpy.mapping.ListDataFrames(newMap, "MainFrame")[0]
                layer_to_add = arcpy.mapping.Layer(self.uniqueLayerLoc+"\\" + fileName)

                """
                #Set values in table for layer
                try:
                    print self.uniqueLayerLoc+"\\" + fileName.strip(".lyr")+r".gdb\Points"
                    rows = arcpy.UpdateCursor(self.uniqueLayerLoc+"\\" + fileName.strip(".lyr")+r".gdb\Points")
                    for row in rows:
                        nameValue = row.getValue("Name")
                        #labelID has to be an int
                        row.setValue("PopupInfo", nameValue.split("|")[0][0:len(nameValue.split("|")[0])-1])
                        row.setValue("Name", nameValue.split("|")[1][1::])
                        rows.updateRow(row)
                    #delete objects to unlock them
                    del row
                    del rows
                except ValueError:
                    self.ui.logListWidget.insertItem(0, "No points found for given map.")
                """

                #add persistent layers to map
                for layerLocation in self.layerLocations.itervalues():
                    arcpy.mapping.AddLayer(mainFrame, layerLocation, "AUTO_ARRANGE")

                #add unique layer and zoom to extent of it
                arcpy.mapping.AddLayer(mainFrame, layer_to_add, "TOP")
                mainFrame.zoomToSelectedFeatures()
                #zoom out slightly, to so layer doesn't take up entire frame
                mainFrame.scale *= 1.4

                #add processing areas layer to extent indicator window
                extentFrame = arcpy.mapping.ListDataFrames(newMap, "ExtentWindow")[0]
                extentFrame.extent = mainFrame.extent
                #zoom way out to show main map extent
                extentFrame.scale = 12000000

                #start work on editing table
                #env.workspace = self.uniqueLayerLoc+"\\" + fileName.strip(".lyr")+".gdb"

                #set map title
                for element in arcpy.mapping.ListLayoutElements(newMap, "TEXT_ELEMENT"):
                    if element.name == "title":
                        element.text = fileName.strip('.lyr') + " Salmon Processing Areas & Samples"

                """
                set save privileges so that can overwrite existing files
                necessary to prevent crashes
                """
                newMap.save()

                #print map for test purposes
                arcpy.mapping.ExportToPDF(newMap, r"C:\Users\Craig\Documents\ArcGIS\AutoMaps\\"+fileName.strip(".lyr")+".pdf")
                del newMap


        self.ui.logListWidget.insertItem(0, "Map Creation Complete")
        #change to insert at end of list
        #scroll to bottom



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())



