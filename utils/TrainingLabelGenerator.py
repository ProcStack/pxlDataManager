# Built on Python 3.10.6 && PyQt5 5.15.9

import sys, os, shutil, platform, time
from PIL import Image
import json

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtOpenGL
from PyQt5.QtWidgets import *
from PyQt5.uic import *


# 'os' doesn't always handle extentions or other path specific needs correctly
#   Reference delimiter where needed
delimiter = "/"
if platform.system() == 'Windows':
    delimiter = "\\"

# -- -- --

scriptAbsDir = os.path.abspath(__file__)
scriptDir = os.path.dirname(scriptAbsDir)







# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --


# Yar, QSettings exists in PyQt5, but ::shrugs::
class UserSettingsManager():
    def __init__(self, name="userSettings"):
        self.name = name
        self.file = name + ".json"
        self.fileFullPath = os.path.abspath( self.file )
        self.fileRoot = os.path.dirname( self.fileFullPath )
        
        self.hasChanges = False
        self._values = {}
        
        self._subscribers = []
        
        self.load()
        
    def load(self):
        if os.path.isfile( self.fileFullPath ):
            with open( self.fileFullPath, "r", encoding="utf-8" ) as curJson:
                data = json.load(curJson)
                self._values = data
    def save(self):
        if self.hasChanges:
            f = open( self.fileFullPath, "w")
            f.write(json.dumps(self._values, indent = 2))
            f.close()
            self.newChanges(False)
        return True
    # I keep typing '.read()' ...
    def read(self, settingName, default=None ):
        return self.value( settingName, default )
    def value(self, settingName, default=None ):
        if settingName in self._values:
            return self._values[ settingName ]
        else:
            self.set( settingName, default )
        return default
    def set(self, settingName, settingValue ):
        if settingName in self._values and self._values[settingName] == settingValue:
            return settingValue
        self._values[ settingName ] = settingValue
        self.newChanges(True)
        return settingValue
    def newChanges(self, newHasChanges=False ):
        self.hasChanges = newHasChanges
        self.emitChangesValue( self.hasChanges )
        
    # Has Changes Event Listeners
    def subscribe(self, func):
        self._subscribers.append( func )
    def emitChangesValue(self, emitState ):
        for func in self._subscribers:
            func( emitState )
        
        

# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --

class CropAndLabelItem(QWidget):
    def __init__(self, parent = None, window = None):
        super(CropAndLabelItem, self).__init__(parent)
        self.window = window
        
        self.id = 0
        self.markedDeleted = False
        self.fullPath = ""
        self.fileName = ""
        self.folderName = ""
        self.folderPath = ""
        self.dispImagePath = ""
        self.data = {}
        self.dataObjects = []
        
        self.entryHeight = 512
        self.imgMaxRes = [512,self.entryHeight]
        self.imgLoaded = False
        # -- -- --
        # -- -- --
        # -- -- --
        
        self.mainBlockLayout = QHBoxLayout()
        self.mainBlockLayout.setContentsMargins(0,0,0,0)
        self.mainBlockLayout.setSpacing(0)
        
        # -- -- --
        
        self.innerBlockLayout = QHBoxLayout()
        self.innerBlockLayout.setContentsMargins(5,0,0,0)
        self.innerBlockLayout.setSpacing(2)
        self.mainBlockLayout.addLayout(self.innerBlockLayout)
        
        self.dispImageLabel = QLabel("View Image")
        self.dispImageLabel.setAlignment(QtCore.Qt.AlignBottom)
        self.dispImageLabel.setStyleSheet("background-color:#cccccc;")
        self.dispImageLabel.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.dispImageLabel.installEventFilter(self)
        self.dispImageLabel.setFixedWidth( 512 )
        self.dispImageLabel.setFixedHeight( 512 )
        self.innerBlockLayout.addWidget(self.dispImageLabel)
        
        self.fileItemBlockLayout = QVBoxLayout()
        self.fileItemBlockLayout.setContentsMargins(0,0,0,10)
        self.fileItemBlockLayout.setSpacing(1)
        self.innerBlockLayout.addLayout(self.fileItemBlockLayout)
        
        
        self.infoTextBlockLayout = QHBoxLayout()
        self.infoTextBlockLayout.setContentsMargins(5,0,0,0)
        self.infoTextBlockLayout.setSpacing(2)
        
        # -- -- --
        self.promptText = QLineEdit()
        self.promptText.setAlignment(QtCore.Qt.AlignLeft)
        self.promptText.setFont(QtGui.QFont("Tahoma",12))
        self.promptText.setMinimumWidth( 450 )
        self.promptText.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        self.promptText.editingFinished.connect(self.promptText_editingFinished)
        
        
        self.infoTextBlockLayout.addWidget(self.promptText)
        self.fileItemBlockLayout.addLayout(self.infoTextBlockLayout)
        
        
        self.infoLayout = QVBoxLayout()
        self.infoLayout.setContentsMargins(0,0,0,0)
        self.infoLayout.setSpacing(0)
        self.fileItemBlockLayout.addLayout(self.infoLayout)
        
        self.fileItemBlockLayout.addStretch(1)
        
        
        # -- -- --
        
        self.optionsBlockLayout = QHBoxLayout()
        self.optionsBlockLayout.setContentsMargins(5,0,0,0)
        self.optionsBlockLayout.setSpacing(2)
        self.fileItemBlockLayout.addWidget(self.optionsBlockLayout)
        
        self.optionsBlockLayout.addStretch(1)
        # -- -- --
        moveToSelectedOutputButton = QPushButton('Set To Selected Output', self)
        moveToSelectedOutputButton.setToolTip('Move this entry to the current selected output sub-folder')
        moveToSelectedOutputButton.clicked.connect(self.moveToSelectedOutputButton_onClick)
        self.optionsBlockLayout.addWidget(moveToSelectedOutputButton)
        # -- -- --
        self.optionsBlockLayout.addStretch(1)
        # -- -- --
        removeDeleteImageButton = QPushButton('Delete Entry and Prompt File', self)
        removeDeleteImageButton.setToolTip('Delete item from disk, removing prompt text file as well.')
        removeDeleteImageButton.clicked.connect(self.removeDeleteImageButton_onClick)
        self.optionsBlockLayout.addWidget(removeDeleteImageButton)
        # -- -- --
        self.optionsBlockLayout.addStretch(1)
        # -- -- --
        
        # -- -- --
        
        self.promptText.adjustSize()
        # -- -- --
        self.setLayout(self.mainBlockLayout)
        self.setMaximumHeight(512)
        self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.MinimumExpanding )
        self.adjustSize()
        
        # -- -- --
        

        
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if obj == self.dispImageLabel:
                if obj.rect().contains(event.pos()):
                    print("Image Clicked")
                    self.viewImageButton_onClick(True)
                    return True 
        return False
        
    @QtCore.pyqtSlot()
    def fileNameField_editingFinished(self):
        #self.fileNameLabel()
        #self.fileNameField.setMinimumWidth( self.fileNameLabel.width()+10 )
        self.toggleFileNameField()
        self.renameFileButton_onClick()
        
    @QtCore.pyqtSlot()
    def viewImageButton_onClick(self, loadView=True):
        #print(os.path.isfile(self.fullPath))
        if os.path.isfile(self.fullPath) and not self.imgLoaded:
            scaledPixmap = QtGui.QPixmap( self.fullPath ).scaled( self.imgMaxRes[0], self.imgMaxRes[1], QtCore.Qt.KeepAspectRatio )
            self.dispImageLabel.setPixmap( scaledPixmap )
            self.dispImageLabel.adjustSize()
            self.dispImageLabel.setMinimumHeight(scaledPixmap.height())
            self.setMinimumHeight(scaledPixmap.height())
            self.imgLoaded = True
                
        #else:
        #    #print("File doesn't exist; ",self.fullPath)
        self.window.setFocus()
        
    @QtCore.pyqtSlot()
    def newEntryButton_onClick(self):
        #print(os.path.isfile(self.fullPath))
        # text = self.tableWidget.currentIndex().data()
        
        newKey = self.window.addKeyFieldWidget.text()
        newValue = self.window.addValueFieldWidget.text()
        
        self.newKeyValue(newKey,newValue,True)
        #self.window.setFocus()
        
    @QtCore.pyqtSlot()
    def graduateNestedButton_onClick(self):
        #self.removeFileEntry(True, True, True)
        for e in self.dataObjects:
            if len(e.nestedList) > 0:
                for n in e.nestedList:
                    n.moveUpKeyValButton_onClick()
                e.deleteKeyValButton_onClick()
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def alphabetizeKeysButton_onClick(self):
        #self.removeFileEntry(True, True, True)
        dataKeys = []
        dataObjs = []
        for e in self.dataObjects:
            dataKeys.append(e.key)
            dataObjs.append(e)
            e.setParent(None)
        self.dataObjects=[]
        dataKeys, dataObjs = zip(*sorted(zip(dataKeys, dataObjs)))
        for d in dataObjs:
            self.dataObjects.append(d)
            self.infoLayout.addWidget(d)
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def renameFileButton_onClick(self):
        #print(os.path.isfile(self.fullPath))
        # text = self.tableWidget.currentIndex().data()

        #print( self.fullPath  )
        #print( self.fileName  )
        #print( self.folderPath  )
        if self.window.autoRenameFiles :
            fromPath = self.fullPath
            toPath = self.folderPath+delimiter+self.fileName
            if os.path.isfile( toPath ):
                runner = 0
                isValid = True
                altFileName = self.fileName
                altToPath = toPath
                splitFileName = self.fileName.split(".")
                ext = splitFileName.pop()
                fileNameBase = ".".join( splitFileName )
                while os.path.isfile( altToPath ):
                    runner+=1
                    if runner>100:
                        isValid=False
                        print("Runaway file renaming condition")
                        break;
                    altFileName = fileNameBase+"_"+str(runner).zfill(2)+"."+ext
                    altToPath = self.folderPath+delimiter+altFileName
                if not isValid:
                    return
                toPath = altToPath
                self.fileName = altFileName
                self.fileNameLabel.setText( altFileName )
            self.fullPath = toPath
            os.rename( fromPath, toPath )  
        
    @QtCore.pyqtSlot()
    def deleteImageButton_onClick(self):
        if self.window.markForDeleteOnly:
            self.markedDeleted = not self.markedDeleted
            newText = "Keep Image" if self.markedDeleted else "Delete Image"
            self.deleteImageButton.setText( newText )
            
            newStyle = "background-color:rgba(200,150,150,.5);" if self.markedDeleted else ""
            self.setStyleSheet( newStyle )
        else:
            print("Deleting - ",self.fullPath)
            os.remove( self.fullPath )
            self.destroy()
        
    def setId( self, idVal ):
        self.id = idVal
        
    def setFullPath( self, text ):
        self.fullPath = text
        
    def setFolderPath( self, text ):
        self.folderPath = text
        
    def setImageText( self, text ):
        self.fileName = text
        #self.fileNameLabel.setText(self.fileName)

    def setImage( self, imagePath ):
        self.dispImagePath = imagePath
        self.dispImageLabel.setPixmap(QtGui.QPixmap(self.dispImagePath))
        
    def toggleFileNameField( self ):
        if self.fileNameLabel.isVisible():
            curText = self.fileName
            self.fileNameField.setText( curText )
            self.fileNameLabel.hide()
            self.fileNameField.show()
            selectionLength = len(curText)
            if "pxlBraige_" in curText :
                textSplitter = curText.split("_")
                if len(textSplitter)>1:
                    selectionLength = len(textSplitter[0])+len(textSplitter[1])+2
            self.fileNameField.setSelection( 0, selectionLength )
            self.fileNameField.setFocus()
        else:
            curText = self.fileNameField.text()
            self.fileName = curText
            self.fileNameLabel.setText( curText )
            self.fileNameField.hide()
            self.fileNameLabel.show()
            self.setFocus()
    
    def newKeyValue( self, keyName, valueData, editable=False):
        curEntryWidget = EntryDataKeyValue( self, keyName, valueData, editable )
        self.infoLayout.addWidget(curEntryWidget)
        self.dataObjects.append( curEntryWidget )
        if editable :
            curEntryWidget.selectKey()
        
    def setData( self, entryKey, dataDict ):
        #print( entryKey )
        self.fileName = entryKey
        self.fullPath = self.window.sourceFolderPath+delimiter+entryKey
        self.folderPath = self.window.sourceFolderPath
        self.setImageText( entryKey )
        self.data = dataDict
        
        if 'promptFile' in self.data:
            #self.data['promptFile']
            with open(self.data['promptFile']) as promptFile:
                self.data['prompt'] = promptFile.readline()
                self.promptText.setText( self.data['prompt'] )
        
    def getData(self):
        valueGather = {}
        if len(self.dataObjects) > 0:
            for x in self.dataObjects:
                valueGather.update( x.getData() )
        else:
            valueGather = self.data
        
        retData = { self.fileName : valueGather }
        return retData
    
    def buildDataObjects(self):
        for x in reversed(range(self.infoLayout.count())): 
            self.infoLayout.itemAt(x).widget().setParent(None)
    
        for entry in self.data:
            val = self.data[entry]
            
            #if type(val) in [str,int,float]:
            curEntryWidget = EntryDataKeyValue( self, entry, val, False )
            self.infoLayout.addWidget(curEntryWidget)
            self.dataObjects.append( curEntryWidget )
            #elif type(val) == dict:
            #    for val in self.data[entry]:
            #        subEntry = val
            #        subVal = self.data[entry][val]
            #        curEntryWidget = QWidget()
            #        self.infoLayout.addWidget(curEntryWidget)
            
    @QtCore.pyqtSlot()
    def promptText_editingFinished(self):
        toPrompt = self.promptText.text()
        self.setPrompt( toPrompt, False )
    def setPrompt(self, toPrompt, setField=True):
        if setField:
            self.promptText.setText( toPrompt )
        self.data['prompt'] = toPrompt
        self.writePrompt()
    def writePrompt(self):
        if "promptFile" in self.data:
            with open(self.data['promptFile'], "w", encoding="utf8") as file:
                file.write( self.data['prompt'] )
    def destroyKeyValue(self, entryObject):
        try:
            keyValListItem = self.dataObjects.index(entryObject)
            if keyValListItem > -1:
                self.dataObjects.pop( keyValListItem )
        except Exception: pass;
        
        entryObject.setParent(None)
        entryObject.deleteLater()
        
    def destroy(self):
        for e in self.dataObjects :
            e.destroy()
        self.dataObjects = []
        for x in reversed(range(self.mainBlockLayout.count())): 
            curWidget = self.mainBlockLayout.itemAt(x).widget()
            if curWidget:
                curWidget.setParent(None)
        self.window.destroyEntry( self, self.fileName, self.id )
            

class LabelOutputManager(QMainWindow):
    def __init__(self, settingsManager=None, *args):
        super(LabelOutputManager, self).__init__(*args)
        
        self.resizeTimer = QtCore.QTimer(self)
        self.resizeTimer.setSingleShot(True)
        self.exiting=False
        
        self.settings = settingsManager
        
        self.jsonDict = {}
        self.jsonFiles = {}
        self.rogueEntries = []
        self.entryItems = []
        self.entryDataToBuild = []
        self.curEntryId = 0 
        
        self.sourceFolderPath = self.settings.read( "sourceFolderPath", "" )
        self.outputFolderPath = self.settings.read( "outputFolderPath", "" )
        
        self.autoScanFolder = self.settings.read( "autoScanFolder", True )
        self.verifyScanFolder = self.settings.read( "verifyScanFolder", True )
        self.autoLoadThumbnails = self.settings.read( "autoLoadThumbnails", True )
        self.markForDeleteOnly = self.settings.read( "markForDeleteOnly", False )
        self.autoRenameFiles = self.settings.read( "autoRenameFiles", True )
        
        self.isUpdatingEntries = False
        
        self.statusTimer = None
        self.statusTimeout = 4000
        
        self.imagePrompter = "BLIP"
        self.imagePromptFinder = None
        
        self.fileListWidget = None
        self.curRawPixmap = None
        self.currentDataBlockLayout = None
        
        self.rawImageSize = None
        self.rawScaledImageSize = None
        
        self.imgViewerRect = QtCore.QRect(0,0,0,0)
        self.curMouseScroll=0
        self.curImageZoomRate = .1;
        self.curImageZoom=1
        self.curImageOrigPos=[0,0]
        self.curImageOffset=[0,0]
        
        
        self.mouseLocked = False
        self.mouseMoved = False
        self.mouseOrigPos = None
        self.mouseLockedPos = None
        self.mouseDelta = None
        self.mouseOffsetFitted = None
        self.mouseScaleFitted = None
        self.mouseButton = 0
        
        self.settings.save()
 
    def keyPressEvent(self, event):
        #print(event)
        """
        if event.key() == QtCore.Qt.Key_Delete :
            ret = QMessageBox.question(self,'', "Delete current image from disk?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.removeDeleteImageButton_onClick()
        """
        if event.key() in [QtCore.Qt.Key_A,QtCore.Qt.Key_Up,QtCore.Qt.Key_Left]:
            self.changeSelectedFile(-1)
            #print("Prev Key")
        elif event.key() in [QtCore.Qt.Key_D,QtCore.Qt.Key_Down,QtCore.Qt.Key_Right]:
            self.changeSelectedFile(1)
            #print("Next Key")
        elif event.key() == QtCore.Qt.Key_Q:
            print( "Killing first, then Exiting" )
            self.exiting = True
            self.settings.save()
            self.deleteLater()
            QApplication.quit()
        elif event.key() == QtCore.Qt.Key_Enter:
            self.proceed()
        elif event.key() == QtCore.Qt.Key_Escape:
            print( "Exiting" )
            self.exiting = True
            self.settings.save()
            QApplication.quit()
        event.accept()
        
    def closeEvent(self, event=None):
        self.exiting = True
        self.settings.save()
        try:
            event.accept()
        except:
            pass;
        return super().closeEvent(event)
        
    def mouseMoveEvent(self, e):
        if self.mouseLocked :
            self.mouseLockedPos = e.pos()
            self.mouseDelta = self.mouseLockedPos - self.mouseOrigPos
            if self.mouseButton == 1:
                dX = self.mouseDelta.x()
                dY = self.mouseDelta.y()
                self.curImageOffset=[dX,dY]
            elif self.mouseButton == 3:
                dX = self.mouseDelta.x()
                dY = self.mouseDelta.y()
                self.curImageOffset=[dX,dY]
            
            
            self.updateImageViewerOffset()
            self.mouseMoved = True
            self.update()

    def mousePressEvent(self, e):
        if self.curRawPixmap and self.rawImageWidget:
            self.mouseLocked = True
            self.mouseOrigPos = e.pos()
            self.curImageOrigPos = [self.rawImageWidget.geometry().x(),self.rawImageWidget.geometry().y()]
            
            if e.button() == QtCore.Qt.LeftButton:
                self.mouseButton = 1
            elif e.button() == QtCore.Qt.RightButton:
                self.mouseButton = 3

    def mouseReleaseEvent(self, e):
        self.mouseLocked = False
        if self.mouseMoved :
            self.updateImageViewerOffset()
        self.mouseMoved = False
        
    def wheelEvent(self,event):
        if self.curRawPixmap and self.rawImageWidget:
            if self.imgViewerRect.contains(event.pos()):
                delta = event.angleDelta().y()
                self.curMouseScroll = float(delta and delta // abs(delta))
                
                self.curImageZoom = max(.01, min(5.0, self.curImageZoom + self.curMouseScroll * self.curImageZoomRate) )
                #print(self.curImageZoom,"% [",event.x(),",",event.y(),"]")
                #print(event.source())
                #print(self.imgViewerRect)
                
                self.updateImageViewerScale()
                self.setFocus()
        
    def resetImageViewer(self):
        self.curImageZoom=1
        self.curImageOffset=[0,0]
        self.curImageOrigPos = [self.rawImageWidget.geometry().x(),self.rawImageWidget.geometry().y()]
        #self.updateImageViewerScale()
        #self.updateImageViewerOffset()
        
    def findImageViewerZoom(self):
        if self.rawImageSize and self.rawScaledImageSize:
            self.curImageZoom = float( self.rawScaledImageSize.width() / self.rawImageSize.width() )
        else:
            self.curImageZoom=1.0
        #self.curImageOffset=[0,0]
        #self.updateImageViewer()
        
    def updateImageViewerScale(self):
        imgWidth = int(self.rawImageSize.width() * self.curImageZoom)
        imgHeight = int(self.rawImageSize.height() * self.curImageZoom)
        
        scaledPixMap = self.curRawPixmap.scaled( imgWidth, imgHeight, QtCore.Qt.KeepAspectRatio )
        self.rawScaledImageSize = scaledPixMap.size()
        self.rawImageWidget.setPixmap( scaledPixMap )
        self.rawImageWidget.adjustSize()
        #self.rawImageWidget.resize( self.rawScaledImageSize )
        #print(" Setting viewport scale - [",imgWidth,",",imgHeight,"]")
        #self.rawImageWidget.update()
        self.rawImageWidget.adjustSize()
        #self.rawImageBlockWidget.update()
        QApplication.processEvents()
        self.updateImageViewerOffset()
    def updateImageViewerOffset(self):
        ix = int( self.curImageOrigPos[0] + self.curImageOffset[0] )
        iy = int( self.curImageOrigPos[1] + self.curImageOffset[1] )
        #self.rawImageWidget.move(ix, iy)
        self.rawImageWidget.move(ix, iy)
        #print(self.curImageOffset)
        #print(" Setting viewport offset [",ix,",",iy,"]")
        
        
    def createStatusBar(self, message=None):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.setStatusStyle(0)
        
        #if self.statusTimer == None:
        #    self.statusTimer = QtCore.QTimer(self)
        #    self.statusTimer.setSingleShot(True)
        #    self.statusTimer.timeout.connect(self.timeoutStatus)
    def setStatusStyle(self, importance=0):
        if self.statusBar:
            colorList = ["#353535", "#355555", "#553535"]
            self.statusBar.setStyleSheet(f"""
                border-width: 1px 0px 0px 0px;
                border-style: solid none none none;
                border-color: #555555;
                background-color:#cccccc;
                color:{colorList[importance]};
                font-weight:bold;
            """)
    def timeoutStatus(self):
        self.clearStatus()
        self.statusTimer.stop()
    def clearStatus(self):
        self.showStatus()
    def showStatus(self, message=None, importance=0, setTimeout=True):
        if self.statusBar == None:
            self.createStatusBar()
        if message == None:
            self.statusBar.clearMessage()
        else:
            self.setStatusStyle(importance)
            if setTimeout:
                self.statusBar.showMessage(" -- "+message+" -- ", self.statusTimeout)
            else:
                self.statusBar.showMessage(" -- "+message+" -- ")
            #if messageTimeout:
            #    self.statusTimer.start( self.statusTimeout )
        QApplication.processEvents()
        
    def setupUI(self):
        # setting up the geometry
        pad = 15
    
        geopos = [240, 180]
        geosize = [ 1340, 940 ]
    
        self.createStatusBar()

        mainWidget = QWidget()
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.setSpacing(1)
        mainWidget.setLayout(mainLayout)
        #self.setLayout(mainLayout)
        #  Not needed when QWidget, uncomment for QMainWindow
        self.setCentralWidget(mainWidget)
        
        """  ______________
            |    |         |
            |  1 |    2    |
            |    |         |
            |--------------|
            |   3  | 4 | 5 |
            |______|___|___|
        """
        
        
        
        
        scanDirBlockWidget = QWidget()
        scanDirBlockLayout = QHBoxLayout()
        scanDirBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        scanDirBlockLayout.setContentsMargins(0,0,0,0)
        scanDirBlockLayout.setSpacing(1)
        scanDirBlockWidget.setLayout(scanDirBlockLayout)
        mainLayout.addWidget(scanDirBlockWidget)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        scanDirBlockLayout.addItem(hSpacer)
        # -- -- --
        loadScanDirButton = QPushButton('JSON Folder', self)
        loadScanDirButton.setToolTip('Locate Folder to Scan for JSONs & Images')
        loadScanDirButton.clicked.connect(self.loadScanDirButton_onClick)
        scanDirBlockLayout.addWidget(loadScanDirButton)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        scanDirBlockLayout.addItem(hSpacer)
        # -- -- --
        self.scanDirWidget = QLineEdit( self.sourceFolderPath )
        self.scanDirWidget.setAlignment(QtCore.Qt.AlignLeft)
        self.scanDirWidget.setFont(QtGui.QFont("Tahoma",10))
        scanDirBlockLayout.addWidget( self.scanDirWidget )
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        scanDirBlockLayout.addItem(hSpacer)
        # -- -- --
        scanDirButton = QPushButton('Read JSON Files', self)
        scanDirButton.setToolTip('Read all JSON files')
        scanDirButton.clicked.connect(self.scanDirButton_onClick)
        scanDirBlockLayout.addWidget(scanDirButton)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        scanDirBlockLayout.addItem(hSpacer)
        
        
        # -- -- --
        # -- -- --
        # -- -- --
        
        outputDirBlockWidget = QWidget()
        outputDirBlockLayout = QHBoxLayout()
        outputDirBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        outputDirBlockLayout.setContentsMargins(0,0,0,0)
        outputDirBlockLayout.setSpacing(1)
        outputDirBlockWidget.setLayout(outputDirBlockLayout)
        mainLayout.addWidget(outputDirBlockWidget)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        outputDirBlockLayout.addItem(hSpacer)
        # -- -- --
        outputScanDirButton = QPushButton('Output Folder', self)
        outputScanDirButton.setToolTip('Locate Folder to Save JSONs & Images')
        outputScanDirButton.clicked.connect(self.outputScanDirButton_onClick)
        outputDirBlockLayout.addWidget(outputScanDirButton)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        outputDirBlockLayout.addItem(hSpacer)
        # -- -- --
        self.outputDirWidget = QLineEdit( self.outputFolderPath )
        self.outputDirWidget.setAlignment(QtCore.Qt.AlignLeft)
        self.outputDirWidget.setFont(QtGui.QFont("Tahoma",10))
        outputDirBlockLayout.addWidget( self.outputDirWidget )
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        outputDirBlockLayout.addItem(hSpacer)
        # -- -- --
        scanDirButton = QPushButton('Save', self)
        scanDirButton.setToolTip('Save, Copy, & Delete Files. If Same Dir, Original JSON deleted')
        scanDirButton.clicked.connect(self.saveChangesButton_onClick)
        outputDirBlockLayout.addWidget(scanDirButton)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        outputDirBlockLayout.addItem(hSpacer)
        
        
        # -- -- --
        # -- -- --
        # -- -- --
        
        optionsBlockWidget = QWidget()
        optionsBlockLayout = QHBoxLayout()
        optionsBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        optionsBlockLayout.setContentsMargins(0,0,0,0)
        optionsBlockLayout.setSpacing(1)
        optionsBlockWidget.setLayout(optionsBlockLayout)
        mainLayout.addWidget(optionsBlockWidget)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        optionsBlockLayout.addItem(hSpacer)
        # -- -- --
        self.optionAutoLoadThumbs = QCheckBox("Auto Load Thumbnails")
        self.optionAutoLoadThumbs.setChecked( self.autoLoadThumbnails )
        self.optionAutoLoadThumbs.stateChanged.connect(lambda:self.optionStateChange(self.optionAutoLoadThumbs,1))
        optionsBlockLayout.addWidget(self.optionAutoLoadThumbs)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        optionsBlockLayout.addItem(hSpacer)
        # -- -- --
        self.optionAutoRenameFiles = QCheckBox("Auto Rename Files On Disk")
        self.optionAutoRenameFiles.setChecked( self.autoRenameFiles )
        self.optionAutoRenameFiles.stateChanged.connect(lambda:self.optionStateChange(self.optionAutoRenameFiles,3))
        optionsBlockLayout.addWidget(self.optionAutoRenameFiles)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        optionsBlockLayout.addItem(hSpacer)
        # -- -- --
        findPromptsButton = QPushButton('Generate Prompts', self)
        findPromptsButton.setToolTip('Generate prompts and all files')
        findPromptsButton.clicked.connect(self.findPromptsButton_onClick)
        optionsBlockLayout.addWidget(findPromptsButton)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        optionsBlockLayout.addItem(hSpacer)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        optionsBlockLayout.addItem(hSpacer)
        # -- -- --
        
        self.findToReplaceText = QLineEdit()
        self.findToReplaceText.setAlignment(QtCore.Qt.AlignLeft)
        self.findToReplaceText.setFont(QtGui.QFont("Tahoma",10))
        optionsBlockLayout.addWidget(self.findToReplaceText)
        # -- -- --
        self.replaceToText = QLineEdit()
        self.replaceToText.setAlignment(QtCore.Qt.AlignLeft)
        self.replaceToText.setFont(QtGui.QFont("Tahoma",10))
        optionsBlockLayout.addWidget(self.replaceToText)
        # -- -- --
        findReplacePromptsButton = QPushButton('Find Replace', self)
        findReplacePromptsButton.setToolTip('Find replace in all prompts')
        findReplacePromptsButton.clicked.connect(self.findReplacePromptsButton_onClick)
        optionsBlockLayout.addWidget(findReplacePromptsButton)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        optionsBlockLayout.addItem(hSpacer)
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        optionsBlockLayout.addItem(hSpacer)
        
        
        
		
        # -- -- --
        # -- -- --
        # -- -- --
        
        # Upper Shelf, Block 1 & 2
        self.upperShelfWidget = QWidget()
        upperShelfLayout = QHBoxLayout()
        upperShelfLayout.setAlignment(QtCore.Qt.AlignCenter)
        upperShelfLayout.setContentsMargins(0,0,0,0)
        upperShelfLayout.setSpacing(1)
        self.upperShelfWidget.setLayout(upperShelfLayout)
        self.upperShelfWidget.setMinimumWidth( 512 )
        self.upperShelfWidget.setMinimumHeight( 512 )
        self.upperShelfWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding )
        mainLayout.addWidget(self.upperShelfWidget)
        # -- -- --
        self.entryListSideBarWidget = QWidget()
        entryListSideBarLayout = QVBoxLayout()
        entryListSideBarLayout.setAlignment(QtCore.Qt.AlignCenter)
        entryListSideBarLayout.setContentsMargins(0,0,0,0)
        entryListSideBarLayout.setSpacing(1)
        self.entryListSideBarWidget.setLayout(entryListSideBarLayout)
        #self.entryListSideBarWidget.setMinimumWidth( 512 )
        #self.entryListSideBarWidget.setFixedHeight( 30 )
        #self.entryListSideBarWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed )
        upperShelfLayout.addWidget(self.entryListSideBarWidget)
        
        
        # -- -- --
        """
        # Lower Shelf, Block 3 & 4
        lowShelfWidget = QWidget()
        lowShelfWidget.setMinimumHeight(512)
        lowShelfWidget.setMaximumHeight(700)
        lowShelfLayout = QVBoxLayout()
        lowShelfLayout.setAlignment(QtCore.Qt.AlignCenter)
        lowShelfLayout.setContentsMargins(0,0,0,0)
        lowShelfLayout.setSpacing(1)
        lowShelfWidget.setLayout(lowShelfLayout)
        mainLayout.addWidget(lowShelfWidget)
        """
        # -- -- --
        

        # Block 4
        self.currentDataBlock = QWidget()
        self.currentDataBlockLayout = QVBoxLayout()
        self.currentDataBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.currentDataBlockLayout.setContentsMargins(0,0,0,0)
        self.currentDataBlockLayout.setSpacing(1)
        self.currentDataBlock.setLayout(self.currentDataBlockLayout)
        
        
        self.currentDataScrollable = QScrollArea()
        #self.currentDataScrollable.setBackgroundRole( QtGui.QPalette.Dark )
        #self.currentDataScrollable.setMinimumHeight(400)
        self.currentDataScrollable.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOn )
        self.currentDataScrollable.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
        #self.currentDataScrollable.viewportEvent.connect( self.scrollAreaUpdate )
        self.currentDataScrollable.verticalScrollBar().valueChanged.connect( self.scrollAreaUpdate )
        
        
        self.currentDataScrollable.setWidgetResizable(True)
        self.currentDataScrollable.setWidget( self.currentDataBlock )
        
            
        entryListSideBarLayout.addWidget( self.currentDataScrollable )
        
        curProjectHeaderText = QLabel('-- Load a Folder with JSON Files --', self)
        curProjectHeaderText.setFont(QtGui.QFont("Tahoma",9))
        self.currentDataBlockLayout.addWidget(curProjectHeaderText) 
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Set Final Self.Geometry Settings
        self.setGeometry( geopos[0], geopos[1], geosize[0], geosize[1] )
        #self.manager.setProjectViewGeometry( geopos[0], geopos[1], geosize[0], geosize[1] )
        
        # Trip first item's onClick
        #self.fileListWidget_onSelectionChanged()
        
        #timer = QtCore.QTimer(self)
        #timer.timeout.connect(self.glTexture.update) 
        #timer.start(1000)
        
        # Connect Resize Timer Function
        #self.resizeTimer.timeout.connect(self.fitRawResizeTimeout)
        
    
    def resizeEvent(self,event):
        self.findViewportRect()
        
        self.fitRawPixmapToView()
        self.scrollAreaUpdate()
    def findViewportRect(self):
        return;
        #upperShelfRect = self.upperShelfWidget.frameGeometry()
        #imgViewportRect = self.currentFileBlockWidget.frameGeometry()
        #self.imgViewerRect = QtCore.QRect( imgViewportRect.x(), upperShelfRect.y(), imgViewportRect.width(), imgViewportRect.height() )
        
    @QtCore.pyqtSlot()
    def loadScanDirButton_onClick(self):
        print( "Load Project" )
        selectedFolder = self.openFolderDialog( "Select Folder With Images & JSON Files" )
        if selectedFolder :
            self.scanDirWidget.setText(selectedFolder) 
            
            curOutputText = self.outputDirWidget.text()
            if len(curOutputText) == 0:
                self.setOutputPath( selectedFolder )
            
            if self.autoScanFolder:
                self.scanDirButton_onClick()
        self.setFocus()

    def outputScanDirButton_onClick(self):
        print( "Output Project" )
        selectedFolder = self.openFolderDialog( "Select Output Folder For Saving Images & JSON Files" )
        if selectedFolder :
            self.setOutputPath( selectedFolder )
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def scanDirButton_onClick(self):
        print( "Scan Dir... " )
        sourceImgPath = self.scanDirWidget.text()
        self.findViewportRect()
        
        loadImageCount = -1
        if sourceImgPath and os.path.isdir(sourceImgPath):
            self.isUpdatingEntries = True
            self.currentDataScrollable.verticalScrollBar().setValue( 0 )
            
            for x in reversed(range(self.currentDataBlockLayout.count())): 
                self.currentDataBlockLayout.itemAt(x).widget().setParent(None)
            
            self.sourceFolderPath = self.settings.set( "sourceFolderPath", sourceImgPath )
            
            activeList=[]
            id=0
            ext=".png"
            txtExt=".txt"
            if os.path.isdir(sourceImgPath):
                parentFolder = sourceImgPath.split("/")[-1].split("\\")[-1]
                imgList=os.listdir(sourceImgPath)
                
                imgList = list( filter(lambda x: ext in x or txtExt in x, imgList) )
                promptList = list( filter(lambda x: txtExt in x, imgList) )
                imgList = list( filter(lambda x: ext in x, imgList) )
                
                suffix="_croppedFaceA.png"
                suffixPrompt="_croppedFaceA.txt"
                sufTest = list( filter(lambda x: suffix in x, imgList) )
                if len(sufTest)>0 and len(sufTest) != len(imgList):
                    suffix="_croppedFaceB.png"
                    suffixPrompt="_croppedFaceB.txt"
                    sufTest = list( filter(lambda x: suffix in x, imgList) )
                runRename = len(sufTest) != len(imgList)
                
                #print(runRename,len(sufTest), len(imgList))
                #return
                    
                loadImageCount = len(imgList)
                for x,curFileName in enumerate(imgList):
                    if self.exiting:
                        break;
                    if ext not in curFileName:
                        continue;
                    curFullPath = os.path.join(sourceImgPath,curFileName)
                    curTextFullPath = os.path.join(sourceImgPath,promptList[x])
                    if os.path.isfile(curFullPath):
                        
                        self.showStatus("Loading "+str(x)+"/"+str(loadImageCount)+" Images",1,False)
                        toFileName = curFileName
                        toFullPath = curFullPath
                        
                        toTextName = promptList[x]
                        toFullTextPath = os.path.join(sourceImgPath,toTextName)
                        
                        if runRename:
                            toFileName = str(x).zfill(5)+suffix
                            toFullPath = os.path.join(sourceImgPath,toFileName)
                            #print(curFullPath, toFullPath)
                            os.rename(curFullPath, toFullPath)
                            
                            toTextName = str(x).zfill(5)+suffixPrompt
                            toFullTextPath = os.path.join(sourceImgPath,toTextName)
                            #print(curTextFullPath, toFullTextPath)
                            os.rename(curTextFullPath, toFullTextPath)
                        
                        #print(" -- -- ")
                        #continue
                        curData = {}
                        curData['imageFile']=toFullPath
                        curData['promptFile']=toFullTextPath
                        
                        curEntryItem = CropAndLabelItem(window=self)
                        curEntryItem.setId( id )
                        curEntryItem.setData( toFileName, curData )
                        curEntryItem.setImage( toFullPath )
                        id+=1
                        
                        #curEntryItem.buildDataObjects()
                        #self.update()
                        QApplication.processEvents()
                        
                        self.currentDataBlockLayout.addWidget( curEntryItem )
                        self.entryItems.append( curEntryItem )
                        
                        scrollHeight = self.currentDataScrollable.geometry().height()
            
        self.currentDataBlock.adjustSize()
        self.isUpdatingEntries = False
        
        self.showStatus("Loaded "+str(loadImageCount)+" Images")
            
        self.setFocus()
    
    @QtCore.pyqtSlot()
    def saveChangesButton_onClick(self):
        print( "Saving JSON... " )
        if self.outputFolderPath and os.path.isdir(self.outputFolderPath):
            #print(self.sourceFolderPath, self.outputFolderPath)
            self.jsonDict = {}
            markedDeleted = []
            for e in self.entryItems:
                if e.markedDeleted:
                    markedDeleted.append( e )
                else:
                    curData = e.getData()
                    #print(curData)
                    self.jsonDict.update( curData )
                    
                    fromPath = e.fullPath
                    toPath = self.outputFolderPath+delimiter+e.fileName
                    if fromPath == toPath:
                        #print( os.rename( fromPath, toPath ) )
                        #print( toPath )
                        pass;
                    else:
                        shutil.copy( fromPath, toPath )
                #print( curData )
            for e in markedDeleted:
                #if self.sourceFolderPath == self.outputFolderPath:
                #    print("Deleting - ",e.fullPath)
                #    os.remove( e.fullPath )
                e.destroy()
            self.saveProjectData( self.outputFolderPath )
            
            self.scanDirWidget.setText( self.outputFolderPath )
            #self.scanDirButton_onClick()
        self.setFocus()
        
    def optionStateChange(self, optionBox, optionEnum ):
        if optionEnum == 1:
            #print( "Setting 'Auto Load Thumbnails' - ",optionBox.isChecked())
            self.autoLoadThumbnails = self.settings.set( "autoLoadThumbnails", optionBox.isChecked() )
            if self.autoLoadThumbnails:
                self.scrollAreaUpdate()
        elif optionEnum == 3:
            #print( "Setting 'Auto Rename Files' - ",optionBox.isChecked())
            self.autoRenameFiles = self.settings.set( "autoRenameFiles", optionBox.isChecked() )
        
        
    @QtCore.pyqtSlot()
    def newFolderButton_onClick(self):
        #self.removeFileEntry(True, True, True)
        for e in self.entryItems:
            for d in e.dataObjects:
                if len(d.nestedList) > 0:
                    for n in d.nestedList:
                        n.moveUpKeyValButton_onClick()
                    d.deleteKeyValButton_onClick()
        self.setFocus()
    @QtCore.pyqtSlot()
    def setToFolderButton_onClick(self):
        #self.removeFileEntry(True, True, True)
        for e in self.entryItems:
            for d in e.dataObjects:
                if len(d.nestedList) > 0:
                    for n in d.nestedList:
                        n.moveUpKeyValButton_onClick()
                    d.deleteKeyValButton_onClick()
        self.setFocus()
    @QtCore.pyqtSlot()
    def deleteFolderButton_onClick(self):
        #self.removeFileEntry(True, True, True)
        for e in self.entryItems:
            for d in e.dataObjects:
                if len(d.nestedList) > 0:
                    for n in d.nestedList:
                        n.moveUpKeyValButton_onClick()
                    d.deleteKeyValButton_onClick()
        self.setFocus()
        
        
        
    @QtCore.pyqtSlot()
    def graduateNestedButton_onClick(self):
        #self.removeFileEntry(True, True, True)
        for e in self.entryItems:
            for d in e.dataObjects:
                if len(d.nestedList) > 0:
                    for n in d.nestedList:
                        n.moveUpKeyValButton_onClick()
                    d.deleteKeyValButton_onClick()
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def alphabetizeEntriesButton_onClick(self):
        entryNames = []
        entryObjs = []
        for e in self.entryItems:
            entryNames.append(e.fileName)
            entryObjs.append(e)
            e.setParent(None)
        self.entryItems=[]
        entryNames, entryObjs = zip(*sorted(zip(entryNames, entryObjs)))
        self.entryDataToBuild=[]
        for d in entryObjs:
            self.entryItems.append(d)
            self.currentDataBlockLayout.addWidget(d)
            if not d.imgLoaded:
                self.entryDataToBuild.append(d)
        self.scrollAreaUpdate()
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def alphabetizeKeysButton_onClick(self):
        for e in self.entryItems:
            for d in e.dataObjects:
                d.alphabetizeKeysButton_onClick()
        self.setFocus()
        
            
    @QtCore.pyqtSlot()
    def addClassifierButton_onClick(self):
        self.setFocus()
            
    @QtCore.pyqtSlot()
    def saveButton_onClick(self):
        self.setFocus()
            
        
    
    @QtCore.pyqtSlot()
    def folderList_onSelectionChanged(self):
        self.setFocus()
    
        
    @QtCore.pyqtSlot()
    def folderList_onItemDoubleClick(self):
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def fileListWidget_onSelectionChanged(self):
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def fileListWidget_onItemDoubleClick(self):
        self.setFocus()
        
    def loadImagePrompter(self):
        self.showStatus("Loading ImageToPrompt, may take a minute", 1, False)
        import utils.ImageToPrompt as i2p
        #self.imagePrompter = "BLIP"
        #self.imagePromptFinder = None
        modelsDir = os.path.join( scriptDir, "weights" )
        self.imagePromptFinder = i2p.ImageToPrompt( modelsDir )
        self.showStatus("ImageToPrompt Loaded")
        return
        
    @QtCore.pyqtSlot()
    def findPromptsButton_onClick(self):
        if self.imagePromptFinder == None:
            self.loadImagePrompter()
        curPromptSearch = 0
        foundPromptCount = 0
        for curEntry in self.entryItems:
            QApplication.processEvents()
            
            if 'prompt' not in curEntry.data:
                foundPromptCount+=1
                self.showStatus("Finding Empty Prompt "+str(foundPromptCount),1,False)
                curEntryImage = curEntry.data['imageFile']
                
                self.currentDataScrollable.verticalScrollBar().setValue( curEntry.geometry().y() )
                
                QApplication.processEvents()
                foundPrompt = self.imagePromptFinder.interrogate( curEntryImage )
                curEntry.setPrompt( foundPrompt )
                print( curEntryImage," -- " )
                print("  ",foundPrompt)
        self.showStatus("Checked "+str(len(self.entryItems))+" Images; Found "+str(foundPromptCount)+" Prompts")
        self.setFocus()
        
        
        
    @QtCore.pyqtSlot()
    def findReplacePromptsButton_onClick(self):
        
        findText = self.findToReplaceText.text()
        replaceToText = self.replaceToText.text()
        foundPromptCount=0
        for curEntry in self.entryItems:
            QApplication.processEvents()
            
            if 'prompt' in curEntry.data:
                foundPromptCount+=1
                self.showStatus("Find Replacing; Checking "+str(foundPromptCount),1,False)
                if findText in curEntry.data['prompt']:
                    toPrompt = curEntry.data['prompt']
                    #print(toPrompt)
                    toPrompt = toPrompt.replace( findText, replaceToText )
                    #print(toPrompt)
                    #print("-- -- --")
                    self.currentDataScrollable.verticalScrollBar().setValue( curEntry.geometry().y() )
                    curEntry.setPrompt( toPrompt )
                #print( curEntryImage," -- " )
                #print("  ",foundPrompt)
        self.showStatus("Checked "+str(len(self.entryItems))+" Images; Found "+str(foundPromptCount)+" Prompts")
        self.setFocus()
        
        
        
    def openFolderDialog(self, dialogText = "Select A Folder "):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialogFolder = QFileDialog.getExistingDirectory(self, dialogText, options=options)
        
        dialogFolder = dialogFolder.replace("/", delimiter)
        
        return dialogFolder
    
    def scrollAreaUpdate(self,event=None):
        if self.isUpdatingEntries :
            return;
        #if len(self.entryDataToBuild) > 0:
        if self.autoLoadThumbnails and len(self.entryDataToBuild) > 0:
        #if len(self.entryDataToBuild) > 0:
            self.isUpdatingEntries = True
            #self.update()
            QApplication.processEvents()
            QApplication.processEvents() # Needed; To catch secondary updates
            
            scrollVal = self.currentDataScrollable.verticalScrollBar().value()
            scrollHeight = self.currentDataScrollable.geometry().height()
            
            #print(scrollVal, scrollHeight)
            
            # Ehhh, I'll figure out maintaining position later
            
            refObjPos = None
            refObjOffset = 0
            markedToPop=[]
            for x,curEntry in enumerate(self.entryDataToBuild):
                curEntryTop = curEntry.geometry().y() - scrollVal
                if curEntryTop >= 0 and  curEntryTop <= scrollHeight :
                
                    #curEntry.buildDataObjects()
                    #self.update()
                    #QApplication.processEvents()
                    #if self.autoLoadThumbnails:
                    #    curEntry.viewImageButton_onClick( False )
                    curEntry.viewImageButton_onClick( False )
                    markedToPop.append( x )
                    QApplication.processEvents()
                    QApplication.processEvents()
                if self.exiting:
                    break;
                if curEntryTop > scrollHeight:
                    break;
            if len(markedToPop)>0:
                #print(" To pop from update list -")
                #print(markedToPop)
                markedToPop.reverse()
                for p in markedToPop:
                    self.entryDataToBuild.pop(p)
            
            self.currentDataBlock.adjustSize()
            self.isUpdatingEntries = False
            
        else:
            try:
                self.currentDataScrollable.verticalScrollBar().valueChanged.disconnect( self.scrollAreaUpdate )
            except Exception:
                pass;
    def changeSelectedFile(self, dir=1):
        toValue = self.curEntryId+dir
        toValue = min( len(self.entryItems)-1, max(0, toValue) )
        self.entryItems[toValue].viewImageButton_onClick()
        #self.currentDataScrollable.verticalScrollBar().setSliderPosition( self.entryItems[toValue].geometry().top() ) 
        self.currentDataScrollable.ensureWidgetVisible( self.entryItems[toValue], 0, 2 ) 
        self.setFocus()
        
    
    def fitRawPixmapToView(self):
        if self.curRawPixmap and self.rawImageWidget:
            defMargin = [4,4]
            defSpacing = 4
            
            labelWidth = self.currentFileBlockWidget.width()
            labelHeight = self.currentFileBlockWidget.height()
            
            #buttonBlockHeight = self.curImageButtonBlock.height()
            
            #labelWidth -= defMargin[0]
            #labelHeight -= defMargin[1] + defSpacing# + buttonBlockHeight
            
            scaledPixMap = self.curRawPixmap.scaled( labelWidth, labelHeight, QtCore.Qt.KeepAspectRatio )
            self.rawScaledImageSize = scaledPixMap.size()
            self.rawImageWidget.setPixmap( scaledPixMap )
            self.rawImageWidget.adjustSize()
            self.findImageViewerZoom()

        
    def fitRawResizeTimeout(self):
        self.fitRawPixmapToView()
        self.resizeTimer.stop()
        return False
    
    def loadImageFile(self,imageFullPath=None, updateGlTexture=False):
        return;
            
    def addJsonDataToWindow(self):
        print("Creating Entries")
        
        self.entryItems = []
        self.entryDataToBuild = []
        self.curEntryId = 0
        self.isUpdatingEntries = True
        self.currentDataScrollable.verticalScrollBar().setValue( 0 )
        
        for x in reversed(range(self.currentDataBlockLayout.count())): 
            self.currentDataBlockLayout.itemAt(x).widget().setParent(None)
            
        for x,e in enumerate(self.jsonDict):
            if self.exiting:
                break;
            curEntryItem = CropAndLabelItem(window=self)
            curEntryItem.setId( x )
            curEntryItem.setData( e, self.jsonDict[e] )
            
            curEntryItem.buildDataObjects()
            #self.update()
            QApplication.processEvents()
            
            self.currentDataBlockLayout.addWidget( curEntryItem )
            self.entryItems.append( curEntryItem )
            
            scrollHeight = self.currentDataScrollable.geometry().height()
            if x*350 <= scrollHeight:
                #if curEntryTop <= scrollHeight :
                curEntryItem.viewImageButton_onClick( x == 0 )
                #curEntryItem.buildDataObjects()
                #self.update()
                #QApplication.processEvents()
            else:
                self.entryDataToBuild.append( curEntryItem )
        
        self.currentDataBlock.adjustSize()
        self.isUpdatingEntries = False
        if len(self.entryDataToBuild) > 0:
            self.currentDataScrollable.verticalScrollBar().valueChanged.connect( self.scrollAreaUpdate )
            self.scrollAreaUpdate()
            
    def destroyEntry( self, entryObject, entryName, entryId ):
        #print( entryName, entryId )
        try:
            entryObjListItem = self.entryItems.index(entryObject)
            if entryObjListItem > -1:
                self.entryItems.pop( entryObjListItem )
        except Exception: pass;
        try:
            entryBuildListItem = self.entryDataToBuild.index(entryObject)
            if entryBuildListItem > -1:
                self.entryDataToBuild.pop( entryBuildListItem )
        except Exception: pass;
        
        if entryName in self.jsonDict:
            #print( "Found in main dict" )
            del self.jsonDict[entryName]
        entryObject.setParent(None)
        entryObject.deleteLater()
        if len(self.entryDataToBuild) > 0:
            try:
                self.currentDataScrollable.verticalScrollBar().valueChanged.connect( self.scrollAreaUpdate )
            except Exception: pass;
            self.scrollAreaUpdate()
        self.currentDataBlock.adjustSize()
        
    def setOutputPath( self, outputFolder ):
        self.outputFolderPath = self.settings.set( "outputFolderPath", outputFolder )
        self.outputDirWidget.setText(outputFolder)
        
    def saveProjectData(self, outPath):
            
        #if not os.path.isdir( outPath ) :
        #    os.mkdir( outPath )
            
        jsonOut = self.jsonDict
        
        
        outFilePath = outPath+delimiter+"pxlBraige_ingested.json"

        f = open( outFilePath, "w")
        f.write(json.dumps(jsonOut, indent = 2))
        f.close()
        
        print("Json Exported -")
        print(outFilePath)
            

# main function
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
 
    settingsManager = UserSettingsManager("userSettings")
    
    app = QApplication(sys.argv)
    w = LabelOutputManager(settingsManager)
    w.setupUI()
    w.show()
    
    sys.exit(app.exec_())