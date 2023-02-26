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

class EntryItem(QWidget):
    def __init__(self, parent = None, window = None):
        super(EntryItem, self).__init__(parent)
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
        
        self.entryHeight = 350
        self.imgMaxRes = [350,self.entryHeight]
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
        self.innerBlockLayout.addWidget(self.dispImageLabel)
        
        self.fileItemBlockLayout = QVBoxLayout()
        self.fileItemBlockLayout.setContentsMargins(0,0,0,10)
        self.fileItemBlockLayout.setSpacing(1)
        self.innerBlockLayout.addLayout(self.fileItemBlockLayout)
        
        
        self.infoTextBlockLayout = QHBoxLayout()
        self.infoTextBlockLayout.setContentsMargins(5,0,0,0)
        self.infoTextBlockLayout.setSpacing(2)
        
        self.fileNameLabel = QLabel()
        self.fileNameLabel.setFont(QtGui.QFont("Tahoma",10))
        self.fileNameLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.fileNameLabel.setStyleSheet("background-color:#150010;")
        self.fileNameLabel.setMinimumWidth( 350 )
        self.fileNameLabel.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        self.fileNameLabel.installEventFilter(self)
        self.fileNameLabel.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        # -- -- --
        self.fileNameLabel.setStyleSheet('''
            font-weight : bold;
            color : rgb(30, 75, 110);
        ''')
        # -- -- --
        self.fileNameField = QLineEdit()
        self.fileNameField.setAlignment(QtCore.Qt.AlignLeft)
        self.fileNameField.setFont(QtGui.QFont("Tahoma",10))
        self.fileNameField.setMinimumWidth( 350 )
        self.fileNameField.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        self.fileNameField.editingFinished.connect(self.fileNameField_editingFinished)
        self.fileNameField.hide()
        
        
        self.infoTextBlockLayout.addWidget(self.fileNameLabel)
        self.infoTextBlockLayout.addWidget(self.fileNameField)
        self.fileItemBlockLayout.addLayout(self.infoTextBlockLayout)
        
        
        
        # -- -- --
        
        self.buttonBlockLayout = QHBoxLayout()
        self.buttonBlockLayout.setContentsMargins(5,0,0,0)
        self.buttonBlockLayout.setSpacing(2)
        self.infoTextBlockLayout.addLayout(self.buttonBlockLayout)

        graduateNestedButton = QPushButton('Graduate Nested', self)
        graduateNestedButton.setToolTip('Move all nested data to top level')
        graduateNestedButton.setMinimumWidth( 50 )
        graduateNestedButton.setMaximumWidth( 150 )
        graduateNestedButton.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        graduateNestedButton.clicked.connect(self.graduateNestedButton_onClick)
        self.buttonBlockLayout.addWidget(graduateNestedButton)

        # -- -- --
        hSpacer = QSpacerItem(10, 1, QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.buttonBlockLayout.addItem(hSpacer)
        # -- -- --
        
        newEntryButton = QPushButton('New Data', self)
        newEntryButton.setToolTip('Add new data [key,value] to entry.')
        newEntryButton.setMinimumWidth( 50 )
        newEntryButton.setMaximumWidth( 150 )
        newEntryButton.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        newEntryButton.clicked.connect(self.newEntryButton_onClick)
        self.buttonBlockLayout.addWidget(newEntryButton)
        
        # -- -- --
        hSpacer = QSpacerItem(10, 1, QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.buttonBlockLayout.addItem(hSpacer)
        # -- -- --
        
        alphabetizeKeysButton = QPushButton('Alphabetize Data', self)
        alphabetizeKeysButton.setToolTip('Sort keys alphabetically.')
        alphabetizeKeysButton.setMinimumWidth( 50 )
        alphabetizeKeysButton.setMaximumWidth( 150 )
        alphabetizeKeysButton.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        alphabetizeKeysButton.clicked.connect(self.alphabetizeKeysButton_onClick)
        self.buttonBlockLayout.addWidget(alphabetizeKeysButton)
        
        # -- -- --
        hSpacer = QSpacerItem(10, 1, QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.buttonBlockLayout.addItem(hSpacer)
        # -- -- --
        
        self.renameFileButton = QPushButton('Rename File', self)
        self.renameFileButton.setToolTip('Rename File on Disk')
        self.renameFileButton.setMinimumWidth( 80 )
        self.renameFileButton.setMaximumWidth( 150 )
        self.renameFileButton.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        self.renameFileButton.clicked.connect(self.renameFileButton_onClick)
        self.buttonBlockLayout.addWidget(self.renameFileButton)
        # -- -- --
        hSpacer = QSpacerItem(10, 1, QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.buttonBlockLayout.addItem(hSpacer)
        # -- -- --
        self.deleteImageButton = QPushButton('Delete Image', self)
        self.deleteImageButton.setToolTip('Delete Entry and Image on Disk')
        self.deleteImageButton.setMinimumWidth( 80 )
        self.deleteImageButton.setMaximumWidth( 150 )
        self.deleteImageButton.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        self.deleteImageButton.clicked.connect(self.deleteImageButton_onClick)
        self.buttonBlockLayout.addWidget(self.deleteImageButton)
        
        # -- -- --
        hSpacer = QSpacerItem(10, 1, QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.buttonBlockLayout.addItem(hSpacer)
        # -- -- --
        
        self.infoLayout = QVBoxLayout()
        self.infoLayout.setContentsMargins(0,0,0,0)
        self.infoLayout.setSpacing(0)
        self.fileItemBlockLayout.addLayout(self.infoLayout)
        
        self.fileItemBlockLayout.addStretch(1)
        
        
        # -- -- --
        
        self.fileNameLabel.adjustSize()
        self.fileNameField.adjustSize()
        # -- -- --
        self.setLayout(self.mainBlockLayout)
        self.setMaximumHeight(350)
        self.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.MinimumExpanding )
        self.adjustSize()
        
        # -- -- --
        

        
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if obj == self.fileNameLabel:
                if obj.rect().contains(event.pos()):
                    self.toggleFileNameField()
                    return True
            if obj == self.dispImageLabel:
                if obj.rect().contains(event.pos()):
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
        if os.path.isfile(self.fullPath) :
            if loadView:
                self.window.loadImageFile( self.fullPath )
                if not self.imgLoaded:
                    scaledPixmap = self.window.curRawPixmap.scaled( self.imgMaxRes[0], self.imgMaxRes[1], QtCore.Qt.KeepAspectRatio )
                    self.dispImageLabel.setPixmap( scaledPixmap )
                    self.dispImageLabel.adjustSize()
                    self.dispImageLabel.setMinimumHeight(scaledPixmap.height())
                    self.setMinimumHeight(scaledPixmap.height())
                    self.imgLoaded = True
                self.window.curEntryId = self.id
            else:
                if not self.imgLoaded:
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
        self.fileNameLabel.setText(self.fileName)

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
            
class EntryDataKeyValue(QWidget):
    def __init__(self, parentWidget = None, dataKey = "Key", dataValue = "Defualt Value", startEditable = False, isNested=False, parent = None ):
        super(EntryDataKeyValue, self).__init__(parent)
        self.parentWidget = parentWidget
        
        self.key = dataKey
        self.value = dataValue
        
        self.isNested=isNested
        self.nestedList = []
        
        self.keyTextLabel = None
        self.valueTextLabel = None
        
        #clicked = pyqtSignal()
        
        
        # -- -- --
        # -- -- --
        # -- -- --
        
        self.mainBlockLayout = QHBoxLayout()
        self.mainBlockLayout.setContentsMargins(0,1,0,1)
        self.mainBlockLayout.setSpacing(2)
        
        
        deleteKeyValBlock = QWidget()
        deleteKeyValBlockLayout = QVBoxLayout()
        deleteKeyValBlockLayout.setContentsMargins(0,2,0,2)
        deleteKeyValBlockLayout.setSpacing(3)
        deleteKeyValBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        deleteKeyValBlock.setLayout(deleteKeyValBlockLayout)
        deleteKeyValBlock.setFixedWidth( 26 )
        deleteKeyValBlock.setStyleSheet("border-width:1px;")
        self.mainBlockLayout.addWidget(deleteKeyValBlock)
        # -- -- --
        if self.isNested:
            moveUpKeyValButton = QPushButton('^', self)
            moveUpKeyValButton.setToolTip('Move entry up a level')
            moveUpKeyValButton.setFixedWidth( 20 )
            moveUpKeyValButton.setFixedHeight( 20 )
            moveUpKeyValButton.setStyleSheet("border:1px solid #008500;background-color:#258525;color:#35ff35;font-weight:bold;")
            moveUpKeyValButton.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
            moveUpKeyValButton.setCursor(QtGui.QCursor(QtCore.Qt.UpArrowCursor))
            moveUpKeyValButton.clicked.connect(self.moveUpKeyValButton_onClick)
            deleteKeyValBlockLayout.addWidget(moveUpKeyValButton)
        # -- -- --
        deleteKeyValButton = QPushButton('×', self)
        deleteKeyValButton.setToolTip('Delete This Key:Value Entry')
        deleteKeyValButton.setFixedWidth( 20 )
        deleteKeyValButton.setFixedHeight( 20 )
        deleteKeyValButton.setStyleSheet("border:1px solid #ff0000;background-color:#550000;color:#ff3535;font-weight:bold;")
        deleteKeyValButton.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        deleteKeyValButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        deleteKeyValButton.clicked.connect(self.deleteKeyValButton_onClick)
        deleteKeyValBlockLayout.addWidget(deleteKeyValButton)
        
        keyTextBlock = QWidget()
        keyTextBlockLayout = QHBoxLayout()
        keyTextBlockLayout.setContentsMargins(0,3,0,3)
        keyTextBlockLayout.setSpacing(2)
        keyTextBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        keyTextBlock.setLayout(keyTextBlockLayout)
        keyTextBlock.setMinimumWidth( 50 )
        keyTextBlock.setMaximumWidth( 150 )
        keyTextBlock.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Expanding )
        #keyTextBlock.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        self.mainBlockLayout.addWidget(keyTextBlock)
        
        valueTextBlock = QWidget()
        self.valueTextBlockLayout = QVBoxLayout()
        self.valueTextBlockLayout.setContentsMargins(0,3,0,3)
        self.valueTextBlockLayout.setSpacing(2)
        valueTextBlock.setLayout(self.valueTextBlockLayout)
        valueTextBlock.setMinimumWidth( 100 )
        #valueTextBlock.setMaximumWidth( 150 )
        valueTextBlock.setStyleSheet("border-width:1px;")
        valueTextBlock.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        #valueTextBlock.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Minimum )
        self.mainBlockLayout.addWidget(valueTextBlock)
        
        # -- -- --
        
        self.keyTextLabel = QLabel( self.key, self )
        self.keyTextLabel.setFont(QtGui.QFont("Tahoma",9))
        self.keyTextLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.keyTextLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.keyTextLabel.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.keyTextLabel.setMinimumWidth( 100 )
        #self.keyTextLabel.setMaximumWidth( 150 )
        self.keyTextLabel.setStyleSheet("border-width:1px;font-weight:bold;")
        self.keyTextLabel.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Expanding )
        #self.keyTextLabel.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        self.keyTextLabel.installEventFilter(self)
        keyTextBlockLayout.addWidget( self.keyTextLabel )
        
        self.keyTextField = QLineEdit()
        self.keyTextField.setText( self.key )
        self.keyTextField.setAlignment(QtCore.Qt.AlignCenter)
        self.keyTextField.setFont(QtGui.QFont("Tahoma",9))
        self.keyTextField.setMinimumWidth( 100 )
        #self.keyTextField.setMaximumWidth( 150 )
        self.keyTextField.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Expanding )
        #self.keyTextField.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        self.keyTextField.editingFinished.connect(self.keyTextField_editingFinished)
        keyTextBlockLayout.addWidget( self.keyTextField )
        
        if startEditable:
            self.keyTextLabel.hide()
            self.keyTextField.show()
        else:
            self.keyTextLabel.show()
            self.keyTextField.hide()
        
        # -- -- --
        
        
        
        if type(dataValue) == dict:
            for k in dataValue:
                curKey = k
                curValue = dataValue[curKey]
                curEntryWidget = EntryDataKeyValue( self, curKey, curValue, False, True )
                self.valueTextBlockLayout.addWidget( curEntryWidget )
                self.nestedList.append(curEntryWidget)
        else:
        
            self.valueTextLabel = QLabel( self.value, self )
            self.valueTextLabel.setFont(QtGui.QFont("Tahoma",9))
            self.valueTextLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            self.valueTextLabel.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
            self.valueTextLabel.setWordWrap(True)
            self.valueTextLabel.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
            #self.valueTextLabel.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Minimum )
            self.valueTextLabel.installEventFilter(self)
            self.valueTextBlockLayout.addWidget( self.valueTextLabel )
            
            
            self.valueTextField = QLineEdit()
            self.valueTextField.setText( self.value )
            self.valueTextField.setAlignment(QtCore.Qt.AlignLeft)
            self.valueTextField.setFont(QtGui.QFont("Tahoma",9))
            self.valueTextField.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
            #self.valueTextField.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Minimum )
            self.valueTextField.editingFinished.connect(self.valueTextField_editingFinished)
            self.valueTextBlockLayout.addWidget( self.valueTextField )
            
            if startEditable:
                self.valueTextLabel.hide()
                self.valueTextField.show()
            else:
                self.valueTextLabel.show()
                self.valueTextField.hide()
            
        # -- -- --
        
        
        launchUrlBlock = QWidget()
        launchUrlBlockLayout = QVBoxLayout()
        launchUrlBlockLayout.setContentsMargins(0,2,0,2)
        launchUrlBlockLayout.setSpacing(3)
        launchUrlBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        launchUrlBlock.setLayout(launchUrlBlockLayout)
        launchUrlBlock.setMinimumWidth( 26 )
        launchUrlBlock.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        launchUrlBlock.setStyleSheet("border-width:1px;")
        self.mainBlockLayout.addWidget(launchUrlBlock)
        # -- -- --
        launchUrlButton = QPushButton('߷', self)
        launchUrlButton.setToolTip('Launch URL / File')
        launchUrlButton.setFixedWidth( 20 )
        launchUrlButton.setFixedHeight( 20 )
        launchUrlButton.setStyleSheet("border:1px solid #000085;background-color:#252585;color:#3535ff;font-weight:bold;")
        launchUrlButton.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        launchUrlButton.setCursor(QtGui.QCursor(QtCore.Qt.UpArrowCursor))
        launchUrlButton.clicked.connect(self.launchUrlButton_onClick)
        launchUrlBlockLayout.addWidget(launchUrlButton)
        
        # -- -- --
        
        keyTextBlock.adjustSize()
        #self.fileNameField.adjustSize()
        self.setLayout(self.mainBlockLayout)

        
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if obj in [self.keyTextLabel,self.valueTextLabel]:
                if obj.rect().contains(event.pos()):
                    if obj == self.keyTextLabel:
                        self.swapEditMode(self.keyTextLabel, self.keyTextField )
                    if obj == self.valueTextLabel:
                        self.swapEditMode(self.valueTextLabel, self.valueTextField )
                    #self.clicked.emit()
                    return True        
        return False
        
        
    @QtCore.pyqtSlot()
    def moveUpKeyValButton_onClick(self):
        #print( "Finished Key text editing" )
        curData = self.getData()
        self.parentWidget.parentWidget.newKeyValue( self.key, curData[self.key], editable=False)
        self.parentWidget.destroyKeyValue(self)
        self.destroy()
        
    @QtCore.pyqtSlot()
    def deleteKeyValButton_onClick(self):
        #print( "Finished Key text editing" )
        self.parentWidget.destroyKeyValue(self)
        self.destroy()
        
    @QtCore.pyqtSlot()
    def keyTextField_editingFinished(self):
        #print( "Finished Key text editing" )
        curKey = self.keyTextField.text()
        self.key = curKey
        
        self.swapEditMode( self.keyTextLabel, self.keyTextField )
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def valueTextField_editingFinished(self):
        #print( "Finished Value text editing" )
        curValue = self.valueTextField.text()
        self.value = curValue
        
        self.swapEditMode( self.valueTextLabel, self.valueTextField )
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def launchUrlButton_onClick(self):
        os.startfile( self.value )
    
    def swapEditMode(self, curLabel, curField ):
        #print("Swap values")
        if curLabel.isVisible():
            curText = curLabel.text()
            curField.setText( curText )
            curLabel.hide()
            curField.show()
            curField.setSelection( 0, len(curText) )
            curField.setFocus()
        else:
            curText = curField.text()
            curLabel.setText( curText )
            curField.hide()
            curLabel.show()
            self.setFocus()
            
    def newKeyValue(self, entryKey, entryValue, editable=False):
        curEntryWidget = EntryDataKeyValue( self, entryKey, entryValue, editable, True )
        self.valueTextBlockLayout.addWidget( curEntryWidget )
        self.nestedList.append(curEntryWidget)
        
    def getData(self):
        retData = {}
        if len(self.nestedList) > 0:
            valueGather = {}
            for x in self.nestedList:
                valueGather.update( x.getData() )
            retData = { self.key : valueGather }
        else:
            retData = { self.key : self.value }
        return retData
    def updateData( self, entryKey, entryValue ):
        #if self.hasNested:
        return { self.key : self.value }
        
    def selectKey(self):
        curText = self.keyTextField.text()
        self.keyTextField.setSelection( 0, len(curText) )
        self.keyTextField.setFocus()

    def destroyKeyValue(self, entryObject):
        try:
            nesterListItem = self.nestedList.index(entryObject)
            if nesterListItem > -1:
                self.nestedList.pop( nesterListItem )
        except Exception: pass;
        
        entryObject.setParent(None)
        entryObject.deleteLater()
        
    def destroy(self):
        for e in self.nestedList :
            e.destroy()
        self.nestedList = []
        for x in reversed(range(self.mainBlockLayout.count())): 
            curWidget = self.mainBlockLayout.itemAt(x).widget()
            if curWidget:
                curWidget.setParent(None)
        self.setParent(None)
        self.deleteLater()


class ImageViewport(QScrollArea):
    def __init__(self, window = None, parent = None ):
        super(ImageViewport, self).__init__(parent)
        self.window=window
        
    def keyPressEvent(self, event):
        self.window.keyPressEvent(event)
    def wheelEvent(self, event):
        self.window.wheelEvent(event)


class PxlBraigeIngester(QMainWindow):
    def __init__(self, settingsManager=None, *args):
        super(PxlBraigeIngester, self).__init__(*args)
        
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
        
    def setupUI(self):
        # setting up the geometry
        pad = 15
    
        geopos = [240, 180]
        geosize = [ 1340, 940 ]
    

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
        
        fileOrganizationWidget = QWidget()
        fileOrganizationLayout = QVBoxLayout()
        fileOrganizationLayout.setAlignment(QtCore.Qt.AlignCenter)
        fileOrganizationLayout.setContentsMargins(0,0,0,0)
        fileOrganizationLayout.setSpacing(1)
        fileOrganizationWidget.setLayout(fileOrganizationLayout)
        fileOrganizationWidget.setMinimumWidth( 512 )
        fileOrganizationWidget.setFixedHeight( 200 )
        fileOrganizationWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed )
        entryListSideBarLayout.addWidget(fileOrganizationWidget)
        
        # -- -- --
        
        entryOptionsShelfWidget = QWidget()
        entryOptionsShelfLayout = QVBoxLayout()
        entryOptionsShelfLayout.setAlignment(QtCore.Qt.AlignCenter)
        entryOptionsShelfLayout.setContentsMargins(0,0,0,0)
        entryOptionsShelfLayout.setSpacing(1)
        entryOptionsShelfWidget.setLayout(entryOptionsShelfLayout)
        entryOptionsShelfWidget.setMinimumWidth( 512 )
        entryOptionsShelfWidget.setFixedHeight( 30 )
        entryOptionsShelfWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Fixed )
        entryListSideBarLayout.addWidget(entryOptionsShelfWidget)
        
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

        # Block 2
        self.currentFileBlockWidget = QWidget()
        self.currentFileBlockLayout = QVBoxLayout()
        self.currentFileBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.currentFileBlockLayout.setContentsMargins(0,0,0,0)
        self.currentFileBlockLayout.setSpacing(1)
        self.currentFileBlockWidget.setLayout(self.currentFileBlockLayout)
        self.currentFileBlockWidget.setMinimumWidth( 512 )
        self.currentFileBlockWidget.setMinimumHeight( 512 )
        self.currentFileBlockWidget.setStyleSheet("background-color:#555555;")
        self.currentFileBlockWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding )
        upperShelfLayout.addWidget(self.currentFileBlockWidget)
        

        # Block 4
        self.currentDataBlock = QWidget()
        self.currentDataBlockLayout = QVBoxLayout()
        self.currentDataBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.currentDataBlockLayout.setContentsMargins(0,0,0,0)
        self.currentDataBlockLayout.setSpacing(1)
        self.currentDataBlock.setLayout(self.currentDataBlockLayout)
        
        
        self.currentDataScrollable = QScrollArea()
        #self.currentDataScrollable.setBackgroundRole( QtGui.QPalette.Dark )
        self.currentDataScrollable.setMinimumHeight(400)
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
        # Current File Layout Block
        self.rawImageBlockWidget = QWidget()
        rawImageBlockLayout = QHBoxLayout()
        rawImageBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        rawImageBlockLayout.setContentsMargins(0,0,0,0)
        rawImageBlockLayout.setSpacing(0)
        self.rawImageBlockWidget.setLayout(rawImageBlockLayout)
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
        #self.currentFileBlockLayout.addWidget(self.rawImageBlockWidget) 
        #self.rawImageBlockWidget.setMinimumHeight( 512 )
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Minimum )
        
        
        self.rawImageWidget = QLabel(self)
        #self.rawImageWidget.setPixmap(pixmap)
        #self.rawImageWidget.resize( 512, 512 )
        #self.rawImageWidget.setMinimumWidth( 10 )
        #self.rawImageWidget.setMinimumHeight( 512 )
        #self.rawImageWidget.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        rawImageBlockLayout.addWidget(self.rawImageWidget)
        #rawImageBlockLayout.addWidget(self.rawImageWidget)
        
        self.imageViewportScrollable = ImageViewport(self)
        #self.currentDataScrollable.setBackgroundRole( QtGui.QPalette.Dark )
        #self.imageViewportScrollable.setMinimumWidth(512)
        #self.imageViewportScrollable.setMinimumHeight(512)
        #self.imageViewportScrollable.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
        self.imageViewportScrollable.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
        self.imageViewportScrollable.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
        self.imageViewportScrollable.setWidgetResizable(True)
        self.imageViewportScrollable.setWidget( self.rawImageBlockWidget )
        #self.imageViewportScrollable.setWidget( self.rawImageWidget )
        self.currentFileBlockLayout.addWidget( self.imageViewportScrollable )
        
        
        # -- -- --
        """
        self.curImageButtonBlock = QWidget()
        self.curImageButtonBlock.setFixedHeight(30)
        curImageButtonLayout = QHBoxLayout()
        curImageButtonLayout.setAlignment(QtCore.Qt.AlignCenter)
        curImageButtonLayout.setContentsMargins(1,1,1,1)
        curImageButtonLayout.setSpacing(2)
        self.curImageButtonBlock.setLayout(curImageButtonLayout)
        entryOptionsShelfLayout.addWidget(self.curImageButtonBlock)
        
        curImageButtonLayout.addStretch(1)
        """
        
        # -- -- --
        # -- -- --
        # -- -- --
        
        subFolderWidget = QWidget()
        subFolderLayout = QHBoxLayout()
        subFolderLayout.setAlignment(QtCore.Qt.AlignRight)
        subFolderLayout.setContentsMargins(0,0,0,0)
        subFolderLayout.setSpacing(1)
        subFolderWidget.setLayout(subFolderLayout)
        fileOrganizationLayout.addWidget(subFolderWidget)
        # -- -- --
        self.outputJsonFile = QListWidget()
        QListWidgetItem("Root", self.outputJsonFile)
        subFolderLayout.addWidget(self.outputJsonFile)
        # -- -- --
        
        subFolderOptionsWidget = QWidget()
        subFolderOptionsLayout = QVBoxLayout()
        subFolderOptionsLayout.setAlignment(QtCore.Qt.AlignRight)
        subFolderOptionsLayout.setContentsMargins(0,0,0,0)
        subFolderOptionsLayout.setSpacing(1)
        subFolderOptionsWidget.setLayout(subFolderOptionsLayout)
        subFolderLayout.addWidget(subFolderOptionsWidget)
        
        subFolderOptionsLayout.addStretch(1)
        
        newFolderButton = QPushButton('New Sub Folder', self)
        newFolderButton.setToolTip('Add new folder for file organization')
        newFolderButton.clicked.connect(self.newFolderButton_onClick)
        subFolderOptionsLayout.addWidget(newFolderButton)
        
        subFolderOptionsLayout.addStretch(1)
        
        setToFolderButton = QPushButton('Set To Folder', self)
        setToFolderButton.setToolTip('Set current image to Folder')
        setToFolderButton.clicked.connect(self.setToFolderButton_onClick)
        subFolderOptionsLayout.addWidget(setToFolderButton)
        
        subFolderOptionsLayout.addStretch(1)
        
        deleteFolderButton = QPushButton('Delete Folder', self)
        deleteFolderButton.setToolTip('Delete folder, move all entries to another')
        deleteFolderButton.clicked.connect(self.deleteFolderButton_onClick)
        subFolderOptionsLayout.addWidget(deleteFolderButton)
        
        subFolderOptionsLayout.addStretch(1)
        
        
        # -- -- --
        # -- -- --
        # -- -- --

        self.curImageButtonBlock = QWidget()
        self.curImageButtonBlock.setFixedHeight(30)
        curImageButtonLayout = QHBoxLayout()
        curImageButtonLayout.setAlignment(QtCore.Qt.AlignCenter)
        curImageButtonLayout.setContentsMargins(1,1,1,1)
        curImageButtonLayout.setSpacing(2)
        self.curImageButtonBlock.setLayout(curImageButtonLayout)
        entryOptionsShelfLayout.addWidget(self.curImageButtonBlock)
        
        curImageButtonLayout.addStretch(1)
        
        addKeyValueWidget = QWidget()
        addKeyValueLayout = QHBoxLayout()
        addKeyValueLayout.setAlignment(QtCore.Qt.AlignRight)
        addKeyValueLayout.setContentsMargins(0,0,0,0)
        addKeyValueLayout.setSpacing(1)
        addKeyValueWidget.setLayout(addKeyValueLayout)
        curImageButtonLayout.addWidget(addKeyValueWidget)
        # -- -- --
        presetNewDataText = QLabel('Preset New Data -', self)
        presetNewDataText.setFont(QtGui.QFont("Tahoma",9))
        addKeyValueLayout.addWidget(presetNewDataText)
        # -- -- --
        self.addKeyFieldWidget = QLineEdit("Key")
        self.addKeyFieldWidget.setAlignment(QtCore.Qt.AlignLeft)
        self.addKeyFieldWidget.setFont(QtGui.QFont("Tahoma",9))
        self.addKeyFieldWidget.setFixedWidth(100)
        self.addKeyFieldWidget.setFixedHeight(30)
        addKeyValueLayout.addWidget( self.addKeyFieldWidget )
        # -- -- --
        self.addValueFieldWidget = QLineEdit("Default Value")
        self.addValueFieldWidget.setAlignment(QtCore.Qt.AlignLeft)
        self.addValueFieldWidget.setFont(QtGui.QFont("Tahoma",9))
        self.addValueFieldWidget.setFixedWidth(350)
        self.addValueFieldWidget.setFixedHeight(30)
        addKeyValueLayout.addWidget( self.addValueFieldWidget )
        # -- -- --
        #addKeyValToAllButton = QPushButton('JSON Folder', self)
        #addKeyValToAllButton.setToolTip('Locate Folder to Scan for JSONs & Images')
        #addKeyValToAllButton.clicked.connect(self.loadScanDirButton_onClick)
        #entryOptionsShelfLayout.addWidget(loadScanDirButton)
        # -- -- --
        
        
        curImageButtonLayout.addStretch(1)
        
        
        graduateNestedButton = QPushButton('Graduate Nested Data', self)
        graduateNestedButton.setToolTip('Move all nested data to top level.')
        graduateNestedButton.clicked.connect(self.graduateNestedButton_onClick)
        curImageButtonLayout.addWidget(graduateNestedButton)
        
        curImageButtonLayout.addStretch(1)
        
        alphabetizeEntriesButton = QPushButton('Alphabetize Entries', self)
        alphabetizeEntriesButton.setToolTip('Sort all entries by file name.')
        alphabetizeEntriesButton.clicked.connect(self.alphabetizeEntriesButton_onClick)
        curImageButtonLayout.addWidget(alphabetizeEntriesButton)
        
        curImageButtonLayout.addStretch(1)
        
        alphabetizeKeysButton = QPushButton('Alphabetize All Data', self)
        alphabetizeKeysButton.setToolTip('Sort all entries keys alphabetically.')
        alphabetizeKeysButton.clicked.connect(self.alphabetizeKeysButton_onClick)
        curImageButtonLayout.addWidget(alphabetizeKeysButton)
        
        curImageButtonLayout.addStretch(1)
        
        saveChangesButton = QPushButton('Save', self)
        saveChangesButton.setToolTip('Save to one JSON file')
        saveChangesButton.clicked.connect(self.saveChangesButton_onClick)
        curImageButtonLayout.addWidget(saveChangesButton)
        
        curImageButtonLayout.addStretch(1)
        
        # -- -- --
        
        
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
        self.resizeTimer.timeout.connect(self.fitRawResizeTimeout)
        
    
    def resizeEvent(self,event):
        self.findViewportRect()
        
        self.fitRawPixmapToView()
        self.scrollAreaUpdate()
    def findViewportRect(self):
        upperShelfRect = self.upperShelfWidget.frameGeometry()
        imgViewportRect = self.currentFileBlockWidget.frameGeometry()
        self.imgViewerRect = QtCore.QRect( imgViewportRect.x(), upperShelfRect.y(), imgViewportRect.width(), imgViewportRect.height() )
        
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
        
        if sourceImgPath and os.path.isdir(sourceImgPath):
            self.sourceFolderPath = self.settings.set( "sourceFolderPath", sourceImgPath )
            self.scanDir( self.sourceFolderPath )
            self.gatherAndFixJsonData( sourceImgPath )
            
            self.entryItems = []
            self.entryDataToBuild = []
            self.curEntryId = 0 
            
            jdataLength = len(self.jsonDict)
            print("Found ",jdataLength," entries.")
            
            rImageCount = len(self.rogueImages)
            if rImageCount > 0:
                print("Rogue images found - ", len(self.rogueImages) )
                #for r in self.rogueImages:
                #    print(" - ",r)
                #print("-- -- -- --")
                ret = QMessageBox.question(self,'Found Extra Files', f'Add {rImageCount} extra as empty entries?', QMessageBox.Yes | QMessageBox.No)
                if ret == QMessageBox.Yes:
                    for r in self.rogueImages:
                        self.jsonDict[r] = {}
                    self.rogueImages = []
                    jdataLength = len(self.jsonDict)
                    print("New entry count - ",jdataLength)
            
            if len(self.rogueEntries) > 0:
                print("Rogue entries left - ")
                print(self.rogueEntries)
                print("-- -- -- --")
            if jdataLength > 0:
                self.addJsonDataToWindow()
        self.setFocus()
    
    def scanDir(self, imagePath=""):
        return;
        if imagePath != "":
            activeList=[]
            if os.path.isdir(imagePath):
                # If User wants to store ALL sub-folders,
                #   Even empty or folder only contents
                #
                #    self.dirOrder.append(imagePath)
                #    self.imageList[imagePath]=[]
                defaultImageDict = {
                    "fileName":"",
                    "filePath":"",
                    "folderName":"",
                    "folderPath":"",
                    "dispImage":"",
                    "fileData":[]
                }
                
                parentFolder = imagePath.split("/")[-1].split("\\")[-1]
                imgList=os.listdir(imagePath)
                for x in imgList:
                    curFullPath = os.path.join(imagePath,x)
                    if os.path.isdir(curFullPath):
                        self.scanDir( curFullPath )
                    else:
                        curExt=x.split(".")[-1]
                        if curExt.lower() in self.extList:
                            self.foundFileCount+=1
                            curImageDict = defaultImageDict.copy()
                            curImageDict["fileName"]=x
                            curImageDict["filePath"]=curFullPath
                            curImageDict["folderName"]=parentFolder
                            curImageDict["folderPath"]=imagePath
                            
                            # If User doesn't want to store ALL sub-folders
                            if imagePath not in self.dirOrder:
                                self.dirOrder.append(imagePath)
                            if imagePath not in self.imageList:
                                self.imageList[imagePath]=[]
                            
                            self.imageList[imagePath].append(curImageDict)

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
    def scrollAreaUpdate_allPrior(self,event=None):
        if self.isUpdatingEntries :
            return;
        #if len(self.entryDataToBuild) > 0:
        if self.autoLoadThumbnails and len(self.entryDataToBuild) > 0:
            self.isUpdatingEntries = True
            #self.update()
            QApplication.processEvents()
            QApplication.processEvents() # Needed; To catch secondary updates
            
            scrollVal = self.currentDataScrollable.verticalScrollBar().value()
            #preScrollMax = self.currentDataScrollable.verticalScrollBar().maximum()
            
            #scrollOffset = self.currentDataBlock.geometry().y()
            scrollHeight = self.currentDataScrollable.geometry().height()
            #objOffset = scrollOffset# - scrollHeight
            curEntryCount = len( self.entryDataToBuild )
            #print( scrollVal, scrollOffset, scrollHeight,  objOffset)
            #print( " -- -- " )
            #print( scrollOffset, scrollHeight )
            #print( " -- " )
            
            # Ehhh, I'll figure out maintaining position later
            
            refObjPos = None
            refObjOffset = 0
            for e in range(curEntryCount):
                curEntry = self.entryDataToBuild[e]
                curEntryTop = curEntry.geometry().y() - scrollVal
                if curEntryTop >= 0 :
                    refObjPos = curEntry
                    refObjOffset = curEntryTop
                    break;
            if not refObjPos:
                refObjPos = self.entryDataToBuild[0]
            
            
            for e in range(curEntryCount):
                if len(self.entryDataToBuild) == 0:
                    break;
                curEntry = self.entryDataToBuild[0]
                curEntryGeo = curEntry.geometry()
                curEntryTop = curEntryGeo.y() - scrollVal
                curEntryPreHeight = curEntryGeo.height()
                #print(curEntryTop, scrollHeight, curEntryPreHeight)
                #print(scrollHeight)
                if curEntryTop < scrollHeight :
                    curEntry = self.entryDataToBuild.pop(0)
                    #curEntry.buildDataObjects()
                    #if self.autoLoadThumbnails:
                    #    curEntry.viewImageButton_onClick( False )
                    curEntry.viewImageButton_onClick( False )
                    #self.update()
                    QApplication.processEvents()
                    QApplication.processEvents()
                    if curEntryTop < 0:
                        scrollVal = refObjPos.geometry().y() + refObjOffset
                        self.currentDataScrollable.verticalScrollBar().setValue( scrollVal )
                        #self.update()
                        QApplication.processEvents()
                        QApplication.processEvents()
                    """if curEntryTop < 0:
                        heightDelt = curEntry.geometry().height()# - curEntryPreHeight
                        #objOffset -= heightDelt
                        scrollVal += heightDelt
                        self.currentDataScrollable.verticalScrollBar().setValue( scrollVal )
                        self.update()
                        QApplication.processEvents()
                    """
                else:
                    break;
                #if curGeo.top()
                #    self.entryDataToBuild.append( curEntryItem )
            
            
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
        if self.rawImageWidget != None:
            curImageFullPath = imageFullPath
            
            # Don't read whole image until resolution verified
            #imgData = Image.open( curImageFullPath )
            #imgWidth, imgHeight = imgData.size
            
            # No auto cropping of input image
            self.curRawPixmap = QtGui.QPixmap( curImageFullPath )
            self.rawImageSize = self.curRawPixmap.size()
            
            self.resetImageViewer()
            self.fitRawPixmapToView()
            

    def gatherAndFixJsonData(self, path):
        if os.path.exists(path):
            #print("exists")
            iData = {}
            iFileDataKeys = []
            iFileData = {}
            
            dirFileList = os.listdir(path)
            jsonFileList = list(filter( lambda x: ".json" in x, dirFileList ))
            refFileList = list(filter( lambda x: ".json" not in x, dirFileList ))
            
            for x,jname in enumerate( jsonFileList ):
                #print(x)
                #if jname != "pxlBraige_jdata_test.json":
                #if jname != "tester.json":
                #    continue;
                curJsonPath = os.path.join( path, jname )
                if os.path.exists( curJsonPath ):
                    #print(curJsonPath)
                    tojname = jname.replace(".","_").replace(" ","_").replace("(","").replace(")","")
                    difEncoding = False
                    with open( curJsonPath, "r", encoding="utf-8" ) as curJson:
                        jsonText = curJson.read()
                        if ord(jsonText[0]) < 400:
                            data = json.loads(jsonText)
                            iFileData[tojname]=data
                        else:
                            difEncoding=True
                    if difEncoding :
                        with open( curJsonPath, "r", encoding="utf-8-sig" ) as curJson:
                            data = json.load(curJson)
                            iFileData[tojname]=data
            iFileDataKeys = list(iFileData.keys())
            #print( iFileDataKeys )
            
            hashKeyFixList={}
            hashKeyFixImageList=[]
            addedKeyCheck=[]
            for x,dictKey in enumerate( iFileDataKeys ):
                curFileDict = iFileData[ dictKey ]
                for d in curFileDict:
                    if d not in addedKeyCheck:
                        if len(d) == 10 and "pxlBraige_" not in d :
                            refFileCheck = list(filter( lambda c: d in c, refFileList ))
                            hashKeyFixList[d] = refFileCheck
                            hashKeyFixImageList += refFileCheck
                        iData[d] = curFileDict[d]
                        addedKeyCheck.append(d)
            iDataKeys = list(iData.keys())
            hashLeftOvers = []
            #print( iDataKeys )
            for hKey in hashKeyFixList:
                hFixList = hashKeyFixList[hKey]
                if len(hFixList) == 0:
                    print(" - Missing image for Hash '",hKey,"'")
                    print(iData[hKey])
                    if 'url' in iData[hKey]:
                        iurl = iData[hKey]['url']
                        iurl = iurl.split("/").pop()
                        print(" - Checking existing image from 'url' - ",iurl)
                        iUrlCheck = list(filter( lambda x: iurl in x, refFileList ))
                        for v in iUrlCheck:
                            print( "Found - ", v )
                            #print( v in iDataKeys )
                            if v in iDataKeys :
                                print("Found existing entry; ",v)
                                del iData[hKey]
                            else:
                                print("No existing entry; Adding - ",v)
                                iData[v] = iData[hKey].copy()
                                iData[v]['hash'] = hKey
                                del iData[hKey]
                    else:
                        hashLeftOvers.append( hKey )
                    print(" -- -- -- ")
                    continue;
                elif len(hFixList) > 1:
                    print("!! WARNING !! - Multiple images with same hash detected")
                    print( hFixList )
                    print(" -- -- -- ")
                hFixed = False
                for toImg in hFixList:
                    if toImg in iDataKeys:
                        print(" Hash & Image entries exist -- ")
                        print(" - Hash ", hKey,"; Image ", toImg)
                        print(" -- -- -- ")
                        hFixed = True
                    else:
                        print(" Fixing entry - ",toImg)
                        iData[toImg] = iData[hKey].copy()
                        iData[toImg]['hash'] = hKey
                        print(" -- -- -- ")
                        hFixed = True
                if hFixed :
                    del iData[hKey]
                else:
                    hashLeftOvers.append( hKey )
            
            #print( list(iData.keys()) )
            rImages = []
            for r in refFileList:
                if r not in iData:
                    rImages.append(r)
            self.jsonDict = iData
            self.rogueImages = rImages
            self.rogueEntries = hashLeftOvers
        else:
            print("Path - '",path,"' doesn't exist.")
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
            curEntryItem = EntryItem(window=self)
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
    import UserSettingsManager as pxlSettings
 
    settingsManager = pxlSettings.UserSettingsManager("userSettings")
    
    app = QApplication(sys.argv)
    w = PxlBraigeIngester(settingsManager)
    w.setupUI()
    w.show()
    
    sys.exit(app.exec_())