
# Built on Python 3.10.6 && PyQt5 5.15.9

import sys, os, platform, time
from PIL import Image
from functools import partial
import math
import json

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.uic import *

#from basicsr.utils import imwrite

from .utils import UserSettingsManager as pxlSettings
from .pxlViewportGL import ContextGL, ImageShaderGL
#from .pxlViewportGL import ContextGL, ImageShaderGL, ViewportGL


# -- -- --


# See 'TODOs.md' for current scripts states


# -- -- --

# 'os' doesn't always handle extensions or other path specific needs correctly
#   Reference delimiter where needed
delimiter = "/"
if platform.system() == 'Windows':
    delimiter = "\\"

# -- -- --




# -- -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- --

# I should probably be using QListView or QTreeView
#   But I'm incorrigible
class FolderListItem(QWidget):
    def __init__(self,parent = None):
        super(FolderListItem, self).__init__(parent)
        
        self.fullPath = ""
        self.fileName = ""
        self.folderName = ""
        self.imageCount = 0
        self.dispImagePath = ""
        
        self.infoTextBlockLayout = QVBoxLayout()
        self.infoTextBlockLayout.setContentsMargins(5,3,0,3)
        self.infoTextBlockLayout.setSpacing(5)
        self.folderNameLabel = QLabel()
        self.folderNameLabel.setObjectName("folderNameLabel")
        self.fileNameLabel = QLabel()
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.infoTextBlockLayout.addWidget(self.folderNameLabel)
        self.infoTextBlockLayout.addWidget(self.fileNameLabel)
        
        self.fileItemBlockLayout = QHBoxLayout()
        self.fileItemBlockLayout.setContentsMargins(0,0,0,10)
        self.fileItemBlockLayout.setSpacing(1)
        self.dispImageLabel = QLabel()
        self.imageCountLabel = QLabel()
        self.imageCountLabel.setObjectName("imageCountLabel")
        self.imageCountLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.imageCountLabel.setMaximumWidth(70)
        self.fileItemBlockLayout.addWidget(self.dispImageLabel, 0)
        self.fileItemBlockLayout.addLayout(self.infoTextBlockLayout, 1)
        self.fileItemBlockLayout.addWidget(self.imageCountLabel, 2)
        self.setLayout(self.fileItemBlockLayout)

    def setCurrent(self, isCurrent=False):
        currentText = "_Selected" if isCurrent else ""
        self.folderNameLabel.setObjectName("folderNameLabel"+currentText)
        self.folderNameLabel.style().unpolish(self.folderNameLabel)
        self.folderNameLabel.style().polish(self.folderNameLabel)
        self.fileNameLabel.setObjectName("fileNameLabel"+currentText)
        self.fileNameLabel.style().unpolish(self.fileNameLabel)
        self.fileNameLabel.style().polish(self.fileNameLabel)
        self.imageCountLabel.setObjectName("imageCountLabel"+currentText)
        self.imageCountLabel.style().unpolish(self.imageCountLabel)
        self.imageCountLabel.style().polish(self.imageCountLabel)

    def setFullPath(self, text):
        self.fullPath = text
        splitPath = self.fullPath.split(delimiter)
        folderText = splitPath[-1]
        self.setFolderText(folderText)
        parentFolderText = splitPath[-2] if len(splitPath)>1 else splitPath[-1]
        self.setParentFolderText(parentFolderText)
        
    def setParentFolderText(self, text):
        self.folderName = text
        self.folderNameLabel.setText(self.folderName)

    def setFolderText(self, text):
        self.fileName = text
        self.fileNameLabel.setText(self.fileName)

    def setImageCount(self, countValue):
        self.imageCount = countValue
        self.imageCountLabel.setText( str(countValue) )
        
    def setImage (self, imagePath):
        self.dispImagePath = imagePath
        self.dispImageLabel.setPixmap(QtGui.QPixmap(self.dispImagePath))


class FileListItem(QWidget):
    def __init__(self, id = None, parent = None):
        super(FileListItem, self).__init__(parent)
        
        self.id=id
        self.fullPath = ""
        self.fileName = ""
        self.folderName = ""
        self.folderPath = ""
        self.dispImagePath = ""
        self.data = {}
        
        self.infoTextBlockLayout = QVBoxLayout()
        self.infoTextBlockLayout.setContentsMargins(5,3,0,3)
        self.infoTextBlockLayout.setSpacing(5)
        self.folderNameLabel = QLabel()
        self.folderNameLabel.setObjectName("folderNameLabel")
        self.fileNameLabel = QLabel()
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.infoTextBlockLayout.addWidget(self.folderNameLabel)
        self.infoTextBlockLayout.addWidget(self.fileNameLabel)
        
        self.fileItemBlockLayout = QHBoxLayout()
        self.fileItemBlockLayout.setContentsMargins(0,0,0,10)
        self.fileItemBlockLayout.setSpacing(1)
        self.dispImageLabel = QLabel()
        self.fileItemBlockLayout.addWidget(self.dispImageLabel, 0)
        self.fileItemBlockLayout.addLayout(self.infoTextBlockLayout, 1)
        self.setLayout(self.fileItemBlockLayout)
        # setStyleSheet

    def setCurrent(self, isCurrent=False):
        currentText = "_Selected" if isCurrent else ""
        self.folderNameLabel.setObjectName("folderNameLabel"+currentText)
        self.folderNameLabel.style().unpolish(self.folderNameLabel)
        self.folderNameLabel.style().polish(self.folderNameLabel)
        self.fileNameLabel.setObjectName("fileNameLabel"+currentText)
        self.fileNameLabel.style().unpolish(self.fileNameLabel)
        self.fileNameLabel.style().polish(self.fileNameLabel)
        
    def setFullPath( self, text ):
        self.fullPath = text
        
    def setFolderPath( self, text ):
        self.folderPath = text
        
    def setFolderText( self, text ):
        self.folderName = text
        self.folderNameLabel.setText(self.folderName)

    def setImageText( self, text ):
        self.fileName = text
        self.fileNameLabel.setText(self.fileName)

    def setImage( self, imagePath ):
        self.dispImagePath = imagePath
        self.dispImageLabel.setPixmap(QtGui.QPixmap(self.dispImagePath))
        
    def setData( self, dataDict ):
        self.data = dataDict
        
class ImageDataProject(QWidget):
    def __init__( self, parent = None, settingsManager=None, dataManagmentRootPath = None, outputPath = "Default" ):
        #super(ImageLabelerWindow, self).__init__(*args)
        super(ImageDataProject, self).__init__(parent)
        
        
        self.DataManagmentRootPath = dataManagmentRootPath
        if self.DataManagmentRootPath == None :
            DataRootAbsPath = os.path.abspath(__file__)
            self.DataManagmentRootPath = os.path.dirname( DataRootAbsPath )
        
        
        self.manager = parent
        
        self.settings = settingsManager
        
        self.mouseLocked = False
        self.mousePos = None
        self.mouseDelta = QtCore.QPoint(0,0)
        
        # Self Geometry Store
        self.geometryStore = None
        # Lower Shelf Geometry Store ... Eh.... I'll fix this later
        self.lShelfGeometryStore = None
        self.ulShelfAdjustLocked = False
        
        # Minimum size of Lower Shelf
        self.minLowShelfSize = self.settings.read( 'LowShelfSize', 150 )
        
        self.confirmFileDeletion = self.settings.read( 'ConfirmDeletions', True )
        
        
        self.resizeTimer = QtCore.QTimer(self)
        self.resizeTimer.setSingleShot(True)
        
        self.folderList = None
        self.fileList = None
        self.rawImageWidget = None
        self.curFileObject = None
        self.curPromptField = None
        self.curFolderPath = None
        self.curFolderObject = None
        self.curRawPixmap = None
        
        
        
        
        self.imagePrompter = "BLIP"
        self.imagePromptFinder = None
        
        # TODO : Handle FaceFinder object load & build dynamically for faster main program init
        self.projectPath = outputPath
        self.croppedFolderName = "CroppedFaces"
        self.outputCroppedPath = os.path.join( self.projectPath, self.croppedFolderName )
        self.faceFinder = None
        
        self.classifiedName = "ClassifiedImages"
        self.outputClassifiedPath = os.path.join( self.projectPath, self.classifiedName )
        self.inputPath = "cropped_faces"
        self.outputPath = outputPath
        self.outputFolder = outputPath
        
        self.projectDataJson = ""
        self.projectSettingsJson = ""
        self.setAcceptDrops(True)
        
        self.settings.save()

    # -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # -- User Interaction Helper Functions - -- --
    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    
    def keyPressEvent(self, event):
        #print(event)
        if event.key() == QtCore.Qt.Key_Delete :
            ret = QMessageBox.question(self,'', "Remove current image from Project?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.removeDeleteImageButton_onClick()
        if event.key() in [QtCore.Qt.Key_A,QtCore.Qt.Key_Up,QtCore.Qt.Key_Left]:
            self.changeSelectedFile(-1)
            #print("Prev Key")
        elif event.key() in [QtCore.Qt.Key_D,QtCore.Qt.Key_Down,QtCore.Qt.Key_Right]:
            self.changeSelectedFile(1)
            #print("Next Key")
        elif event.key() == QtCore.Qt.Key_Q:
            print( "Killing first, then Exiting" )
            self.deleteLater()
            QApplication.quit()
        elif event.key() == QtCore.Qt.Key_Enter:
            self.proceed()
        elif event.key() == QtCore.Qt.Key_Escape:
            print( "Exiting" )
            QApplication.quit()
        event.accept()
        
    def mousePressEvent(self, e):
        self.mouseLocked = True
        #print("Mouse Press")
        # Prevent massive jump in shelf adjustments -
        self.mousePos = e.pos()
        self.mouseDelta = QtCore.QPoint(0,0)
    def mouseReleaseEvent(self, e):
        self.mouseLocked = False
        #print("Mouse Release")
        if self.ulShelfAdjustLocked:
            self.ulShelfAdjustRelease()
        
    def mouseMoveEvent(self, e):
        if self.mousePos != None and self.mouseLocked:
            self.mouseDelta = e.pos() - self.mousePos
            #print("Mouse Mouse! UL Shelf Lock - " + str(self.ulShelfAdjustLocked) +", Delta ["+str(self.mouseDelta.x())+","+str(self.mouseDelta.y())+"]" )
            #print("Mouse Mouse! UL Shelf Lock - " + str(self.ulShelfAdjustLocked) +", Delta ["+str(self.mouseDelta.x())+","+str(self.mouseDelta.y())+"]" )
            if self.ulShelfAdjustLocked:
                self.ulShelfResize()
        self.mousePos = e.pos()


    # File & Folder Drag Drop Support 
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for curFile in files:
            if os.path.isdir(curFile):
                rectFile = curFile.replace("/",delimiter).replace("\\",delimiter)
                self.manager.scanDir(rectFile)
                
                folderPath = self.manager.dirOrder[-1]
                curFileItem = FolderListItem()
                curFileItem.setFullPath(folderPath)
                if folderPath in self.manager.imageList :
                    curFileItem.setImageCount( len(self.manager.imageList[folderPath]) )
                curFolderItemWidget = QListWidgetItem(self.folderList)
                curFolderItemWidget.setSizeHint(curFileItem.sizeHint())
                self.folderList.addItem(curFolderItemWidget)
                self.folderList.setItemWidget(curFolderItemWidget, curFileItem)
            
    # -- -- -- -- -- -- 
    # -- UI Creation -- --
    # -- -- -- -- -- -- -- --
            
    def setupUI(self):
 
        #mainWidget = QWidget()
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.setSpacing(1)
        #mainWidget.setLayout(mainLayout)
        self.setLayout(mainLayout)
        #  Not needed when QWidget, uncomment for QMainWindow
        #self.setCentralWidget(mainWidget)
        
        """  ______________
            |    |         |
            |  1 |    2    |
            |    |         |
            |--------------|
            |   3  | 4 | 5 |
            |______|___|___|
        """
        
        # Set up QDockWidgets
        
        # Upper Shelf, Block 1 & 2
        self.upperShelfWidget = QWidget()
        upperShelfLayout = QHBoxLayout()
        upperShelfLayout.setAlignment(QtCore.Qt.AlignCenter)
        upperShelfLayout.setContentsMargins(0,0,0,0)
        upperShelfLayout.setSpacing(1)
        self.upperShelfWidget.setLayout(upperShelfLayout)
        self.upperShelfWidget.setMinimumWidth( 512 )
        self.upperShelfWidget.setMinimumHeight( 512 )
        self.upperShelfWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Expanding )
        mainLayout.addWidget(self.upperShelfWidget)
        
        # -- -- --
        
        # Change Upper / Lower shelf size adjuster 
        self.ulShelfSeparator = QPushButton('', self)
        self.ulShelfSeparator.setToolTip('Change Shelf Sizes')
        self.ulShelfSeparator.pressed.connect(self.ulShelfSeparator_onPressed)
        #self.ulShelfSeparator.released.connect(self.ulShelfSeparator_onReleased)
        self.ulShelfSeparator.setMaximumHeight(3)
        self.ulShelfSeparator.setStyleSheet("background-color:#555555;")
        self.ulShelfSeparator.setCursor(QtGui.QCursor(QtCore.Qt.SplitVCursor))
        self.ulShelfSeparator.setContentsMargins(0,3,0,3)
        mainLayout.addWidget(self.ulShelfSeparator)
        
        # -- -- --
        
        # Lower Shelf, Block 3 & 4
        self.lowShelfWidget = QWidget()
        self.lowShelfWidget.setFixedHeight(512)
        lowShelfLayout = QHBoxLayout()
        lowShelfLayout.setAlignment(QtCore.Qt.AlignCenter)
        lowShelfLayout.setContentsMargins(0,0,0,0)
        lowShelfLayout.setSpacing(1)
        self.lowShelfWidget.setLayout(lowShelfLayout)
        mainLayout.addWidget(self.lowShelfWidget)
        
        # -- -- --
        
        # Block 1
        fileBlock = QWidget()
        fileBlock.setMinimumWidth(400)
        fileBlock.setMaximumWidth(600)
        fileBlockLayout = QVBoxLayout()
        fileBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        fileBlockLayout.setContentsMargins(0,0,0,0)
        fileBlockLayout.setSpacing(1)
        fileBlock.setLayout(fileBlockLayout)
        upperShelfLayout.addWidget(fileBlock)
        
        # -- -- --
        line = QLabel('', self)
        line.setMaximumWidth(5)
        line.setStyleSheet("background-color:#555555;")
        line.setContentsMargins(3,0,3,0)
        upperShelfLayout.addWidget(line)
        # -- -- --

        # Block 2
        self.currentFileBlockWidget = QWidget()
        currentFileBlockLayout = QVBoxLayout()
        currentFileBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        currentFileBlockLayout.setContentsMargins(0,0,0,0)
        currentFileBlockLayout.setSpacing(1)
        self.currentFileBlockWidget.setLayout(currentFileBlockLayout)
        self.currentFileBlockWidget.setMinimumWidth( 512 )
        self.currentFileBlockWidget.setMinimumHeight( 512 )
        self.currentFileBlockWidget.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.MinimumExpanding )
        upperShelfLayout.addWidget(self.currentFileBlockWidget)

        # Block 3
        currentDataBlock = QWidget()
        currentDataBlockLayout = QHBoxLayout()
        currentDataBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        currentDataBlockLayout.setContentsMargins(0,0,0,0)
        currentDataBlockLayout.setSpacing(1)
        currentDataBlock.setLayout(currentDataBlockLayout)
        currentDataBlock.setMaximumWidth(512)
        currentDataBlock.setMinimumWidth(200)
        upperShelfLayout.addWidget(currentDataBlock)
        
        # -- -- --
        
        line = QLabel('', self)
        line.setMaximumWidth(5)
        line.setStyleSheet("background-color:#555555;")
        line.setContentsMargins(3,0,3,0)
        lowShelfLayout.addWidget(line)
        
        # -- -- --
        
        # Block 4
        self.glBlock = QWidget()
        self.glBlock.setMinimumWidth(512)
        self.glBlockLayout = QHBoxLayout()
        self.glBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.glBlockLayout.setContentsMargins(0,0,0,0)
        self.glBlockLayout.setSpacing(1)
        self.glBlock.setLayout(self.glBlockLayout)
        self.glBlock.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding )
        lowShelfLayout.addWidget(self.glBlock)
        
        # -- -- --
        line = QLabel('', self)
        line.setMaximumWidth(5)
        line.setStyleSheet("background-color:#555555;")
        line.setContentsMargins(3,0,3,0)
        lowShelfLayout.addWidget(line)
        # -- -- --
        
        # Block 5
        glSettingsBlock = QWidget()
        glSettingsBlock.setMinimumWidth(150)
        glSettingsBlock.setMaximumWidth(250)
        glSettingsBlockLayout = QVBoxLayout()
        glSettingsBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        glSettingsBlockLayout.setContentsMargins(0,0,0,0)
        glSettingsBlockLayout.setSpacing(1)
        glSettingsBlock.setLayout(glSettingsBlockLayout)
        lowShelfLayout.addWidget(glSettingsBlock)
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # File List & Options Block

        # Folder List
        self.folderList = QListWidget(self)
        self.curFolderListItem = None
        for folderPath in self.manager.dirOrder:
            # Create QCustomQWidget
            curFileItem = FolderListItem()
            curFileItem.setFullPath(folderPath)
            if folderPath in self.manager.imageList :
                curFileItem.setImageCount( len(self.manager.imageList[folderPath]) )
            curFolderItemWidget = QListWidgetItem(self.folderList)
            curFolderItemWidget.setSizeHint(curFileItem.sizeHint())
            if self.curFolderListItem == None:
                curFileItem.setCurrent(True)
                self.curFolderListItem = curFolderItemWidget

            self.folderList.addItem(curFolderItemWidget)
            self.folderList.setItemWidget(curFolderItemWidget, curFileItem)

        fileBlockLayout.addWidget(self.folderList)
        
        self.folderList.setCurrentItem( self.curFolderListItem )
        
        self.folderList.itemSelectionChanged.connect( self.folderList_onSelectionChanged )
        #self.folderList.itemDoubleClicked.connect( self.folderList_onItemDoubleClick )
        
        # -- -- --
        
        # File List
        self.fileList = QListWidget(self)

        fileBlockLayout.addWidget(self.fileList)
        
        self.fileList.itemSelectionChanged.connect( self.fileList_onSelectionChanged )
        self.fileList.itemDoubleClicked.connect( self.fileList_onItemDoubleClick )
        
        self.curFolderPath = self.folderList.itemWidget(self.curFolderListItem).fullPath
        self.rebuildFileList(self.curFolderPath)
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
        # Current File Layout Block
        
        # -- -- --
        # Prompt Bar and Buttons
        # -- -- --
        rawImagePromptBarBlock = QWidget()
        rawImagePromptBarLayout = QHBoxLayout()
        rawImagePromptBarLayout.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        rawImagePromptBarLayout.setContentsMargins(1,1,1,1)
        rawImagePromptBarLayout.setSpacing(20)
        rawImagePromptBarBlock.setLayout(rawImagePromptBarLayout)
        rawImagePromptBarBlock.setMinimumWidth( 512 )
        rawImagePromptBarBlock.setMaximumHeight( 50 )
        rawImagePromptBarBlock.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Maximum )
        currentFileBlockLayout.addWidget(rawImagePromptBarBlock)
        # -- -- --
        rawImagePromptLabelWidget = QLabel(" Image Prompt - ")
        rawImagePromptLabelWidget.setFont(QtGui.QFont("Tahoma",9,QtGui.QFont.Bold))
        #rawImagePromptLabelWidget.setMinimumWidth( 100 )
        #rawImagePromptLabelWidget.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        rawImagePromptBarLayout.addWidget(rawImagePromptLabelWidget)
        # -- -- --
        self.curPromptField = QLineEdit()
        #self.curPromptField.setText("")
        self.curPromptField.setAlignment(QtCore.Qt.AlignLeft)
        self.curPromptField.setFont(QtGui.QFont("Tahoma",12))
        self.curPromptField.setMinimumWidth( 350 )
        self.curPromptField.setMinimumHeight( 30 )
        self.curPromptField.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.Minimum )
        self.curPromptField.editingFinished.connect(self.curPromptField_editingFinished)
        rawImagePromptBarLayout.addWidget( self.curPromptField )
        # -- -- --
        line = QLabel('', self)
        line.setMaximumWidth(200)
        rawImagePromptBarLayout.addWidget(line)
        # -- -- --
        self.generateImagePromptButton = QPushButton('Generate Image Prompt', self)
        self.generateImagePromptButton.setToolTip('Create Prompt from Image, BLIP Img2Txt')
        self.generateImagePromptButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.generateImagePromptButton.setMinimumHeight(35)
        self.generateImagePromptButton.clicked.connect(self.generateImagePromptButton_onClick)
        rawImagePromptBarLayout.addWidget(self.generateImagePromptButton)
        # -- -- --
        self.findFaceButton = QPushButton('Find Faces in Photo', self)
        self.findFaceButton.setToolTip('Auto Find Faces in current image; Face Helper')
        self.findFaceButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.findFaceButton.setMinimumHeight(35)
        self.findFaceButton.clicked.connect(self.findFaceButton_onClick)
        rawImagePromptBarLayout.addWidget(self.findFaceButton)
        # -- -- --
        line = QLabel('', self)
        line.setMaximumWidth(200)
        rawImagePromptBarLayout.addWidget(line)
        # -- -- --
        
        # -- -- --
        # -- -- --
        # -- -- --
        self.rawImageBlockWidget = QWidget()
        rawImageBlockLayout = QHBoxLayout()
        rawImageBlockLayout.setContentsMargins(1,1,1,1)
        rawImageBlockLayout.setSpacing(2)
        rawImageBlockLayout.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.rawImageBlockWidget.setLayout(rawImageBlockLayout)
        self.rawImageBlockWidget.setMinimumWidth( 512 )
        self.rawImageBlockWidget.setMinimumHeight( 512 )
        self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.MinimumExpanding )
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Ignored )
        currentFileBlockLayout.addWidget(self.rawImageBlockWidget)
        #self.rawImageBlockWidget.setMinimumHeight( 512 )
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Minimum )
        
        self.rawImageWidget = QLabel(self)
        #self.rawImageWidget.setPixmap(pixmap)
        #self.rawImageWidget.resize( 512, 512 )
        self.rawImageWidget.setMinimumWidth( 10 )
        self.rawImageWidget.setMinimumHeight( 512 )
        self.rawImageWidget.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        rawImageBlockLayout.addWidget(self.rawImageWidget)
        
        
        
        # -- -- --

        self.curImageButtonBlock = QWidget()
        self.curImageButtonBlock.setFixedHeight(50)
        curImageButtonLayout = QHBoxLayout()
        curImageButtonLayout.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        curImageButtonLayout.setContentsMargins(1,1,1,1)
        curImageButtonLayout.setSpacing(5)
        self.curImageButtonBlock.setLayout(curImageButtonLayout)
        currentFileBlockLayout.addWidget(self.curImageButtonBlock)
        
        curImageButtonLayout.addStretch(1)
        
        removeImageEntryButton = QPushButton('Remove Entry From Project', self)
        removeImageEntryButton.setToolTip('Removes image from project,\n File is kept on disk.')
        removeImageEntryButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        removeImageEntryButton.setMinimumHeight(35)
        removeImageEntryButton.clicked.connect(self.removeImageEntryButton_onClick)
        curImageButtonLayout.addWidget(removeImageEntryButton)
        
        removeDeleteImageButton = QPushButton('Remove & Delete Image', self)
        removeDeleteImageButton.setToolTip('Removes image from project,\n File is deleted from disk.')
        removeDeleteImageButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        removeDeleteImageButton.setMinimumHeight(35)
        removeDeleteImageButton.clicked.connect(self.removeDeleteImageButton_onClick)
        curImageButtonLayout.addWidget(removeDeleteImageButton)
        
        curImageButtonLayout.addStretch(1)
        
        # -- -- --
        self.generateAllImagePromptButton = QPushButton('Generate ALL Image Prompts', self)
        self.generateAllImagePromptButton.setToolTip('Create Prompts from ALL Images, BLIP Img2Txt')
        self.generateAllImagePromptButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.generateAllImagePromptButton.setMinimumHeight(35)
        self.generateAllImagePromptButton.clicked.connect(self.generateAllImagePromptButton_onClick)
        curImageButtonLayout.addWidget(self.generateAllImagePromptButton)
        
        curImageButtonLayout.addStretch(1)
        
        self.findAllFacesButton = QPushButton('Find ALL Faces', self)
        self.findAllFacesButton.setToolTip('Auto Find Faces in ALL Images; Face Helper')
        self.findAllFacesButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.findAllFacesButton.setMinimumHeight(35)
        self.findAllFacesButton.clicked.connect(self.findAllFacesButton_onClick)
        curImageButtonLayout.addWidget(self.findAllFacesButton)
        
        curImageButtonLayout.addStretch(1)
        
        self.updateCropButton = QPushButton('Update GL Crop Window', self)
        self.updateCropButton.setToolTip('Load Image into GL Crop Window')
        self.updateCropButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.updateCropButton.setMinimumHeight(35)
        self.updateCropButton.clicked.connect(self.updateCropButton_onClick)
        curImageButtonLayout.addWidget(self.updateCropButton)
        
        curImageButtonLayout.addStretch(1)
        
        # -- -- --
        
        
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
        
        self.curImageCropsBlock = QWidget()
        self.curImageCropsLayout = QVBoxLayout()
        self.curImageCropsLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.curImageCropsLayout.setContentsMargins(0,0,0,0)
        self.curImageCropsLayout.setSpacing(1)
        self.curImageCropsBlock.setLayout(self.curImageCropsLayout)
        
        self.curImageCropsScrollable = QScrollArea()
        self.curImageCropsScrollable.setMaximumWidth(512)
        self.curImageCropsScrollable.setMinimumWidth(200)
        self.curImageCropsScrollable.setMinimumHeight(200)
        self.curImageCropsScrollable.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOn )
        self.curImageCropsScrollable.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
        #self.curImageCropsScrollable.verticalScrollBar().valueChanged.connect( self.scrollAreaUpdate )
        
        self.curImageCropsScrollable.setWidgetResizable(True)
        self.curImageCropsScrollable.setWidget( self.curImageCropsBlock )
        
        currentDataBlockLayout.addWidget( self.curImageCropsScrollable )
         
        
        # -- -- -- -- -- -- -- -- -- -- --
        
        # Face Finder Layouts
        #   Display current Image's found aligned & unaligned faces
        
        curImageDataBlock = QWidget()
        self.curImageDataLayout = QVBoxLayout()
        self.curImageDataLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.curImageDataLayout.setContentsMargins(1,1,1,1)
        self.curImageDataLayout.setSpacing(2)
        curImageDataBlock.setLayout(self.curImageDataLayout)
        self.curImageCropsLayout.addWidget(curImageDataBlock)

        # -- -- --
        
        cropFacesBlock = QWidget()
        self.cropFacesLayout = QVBoxLayout()
        self.cropFacesLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.cropFacesLayout.setContentsMargins(1,1,1,1)
        self.cropFacesLayout.setSpacing(2)
        cropFacesBlock.setLayout(self.cropFacesLayout)
        self.curImageDataLayout.addWidget(cropFacesBlock)
        
        # -- -- --
        
        
        # image path
        imgPath = "assets/foundFacesTemp.jpg" # os.path.join( self.DataManagmentRootPath, "assets/foundFacesTemp.jpg" )
        pixmap = QtGui.QPixmap( imgPath )
        
        
        # -- -- --
        faceImageAlignedBlock = QWidget()
        faceImageAlignedLayout = QVBoxLayout()
        faceImageAlignedLayout.setAlignment(QtCore.Qt.AlignCenter)
        faceImageAlignedLayout.setContentsMargins(1,1,1,1)
        faceImageAlignedLayout.setSpacing(2)
        faceImageAlignedBlock.setLayout(faceImageAlignedLayout)
        self.cropFacesLayout.addWidget(faceImageAlignedBlock)
        # -- -- --
        self.faceImage = QLabel(self)
        self.faceImage.setPixmap(pixmap)
        self.faceImage.resize( 512, 512 )
        faceImageAlignedLayout.addWidget(self.faceImage)
        
        # -- -- --
        
        faceImageUnalignedBlock = QWidget()
        faceImageUnalignedLayout = QVBoxLayout()
        faceImageUnalignedLayout.setAlignment(QtCore.Qt.AlignCenter)
        faceImageUnalignedLayout.setContentsMargins(1,1,1,1)
        faceImageUnalignedLayout.setSpacing(2)
        faceImageUnalignedBlock.setLayout(faceImageUnalignedLayout)
        self.cropFacesLayout.addWidget(faceImageUnalignedBlock)
        # -- -- --
        self.faceUnalignedImage = QLabel(self)
        self.faceUnalignedImage.setPixmap(pixmap)
        self.faceUnalignedImage.resize( 512, 512 )
        faceImageUnalignedLayout.addWidget(self.faceUnalignedImage)
        
        
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
        
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Current GL Loaded File Layout Block
        
        glSaveRenderPath = os.path.join( self.DataManagmentRootPath, "ViewportGLSaves" )
        
        
        self.glContext = ContextGL.ContextGLManager()
        
        #self.glSmartBlur = ImageShaderGL.ImageShaderWidget(self,0, self.glContext.format(), "smartBlur", "assets/glEdgeFinder_tmp1_alpha.png", glSaveRenderPath )
        self.glSmartBlur = ImageShaderGL.ImageShaderWidget(self,0, self.glContext.format(), "rawTexture", "assets/glEdgeFinder_tmp1_alpha.png", glSaveRenderPath )
        self.glBlockLayout.addWidget(self.glSmartBlur)
        self.glContext.contextCreated.connect( self.glSmartBlur.setSharedGlContext )
        # -- -- --
        """
        self.glEdgeFinding = ImageShaderGL.ImageShaderWidget(self,1, self.glContext.format(), "edgeDetect", "assets/glEdgeFinder_tmp2_alpha.png", glSaveRenderPath )
        self.glBlockLayout.addWidget(self.glEdgeFinding)
        self.glContext.contextCreated.connect( self.glEdgeFinding.setSharedGlContext )
        # -- -- --
        self.glSegmentation = ImageShaderGL.ImageShaderWidget(self,2, self.glContext.format(), "segment", "assets/glSegmentation_tmp1_alpha.png", glSaveRenderPath )
        self.glBlockLayout.addWidget(self.glSegmentation)
        self.glContext.contextCreated.connect( self.glSegmentation.setSharedGlContext )
        # -- -- --
        self.glTexture = ImageShaderGL.ImageShaderWidget(self,3, self.glContext.format(), "default", glSaveRenderPath )
        self.glBlockLayout.addWidget(self.glTexture)
        self.glContext.contextCreated.connect( self.glTexture.setSharedGlContext )
        """
        #self.glSegmentation.passTargetGL( self.glTexture.textureGLWidget )
        # -- -- --
        
        self.glBlockLayout.addWidget(self.glContext)
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # GL Shader Settings & Crop Classification Options
        self.outputClassifier = QListWidget()
        QListWidgetItem("Neutral", self.outputClassifier)
        glSettingsBlockLayout.addWidget(self.outputClassifier)
        
        # -- -- --
        
        cropButtonsBlock = QWidget()
        cropButtonsBlockLayout = QHBoxLayout()
        cropButtonsBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        cropButtonsBlockLayout.setContentsMargins(1,1,1,1)
        cropButtonsBlockLayout.setSpacing(2)
        cropButtonsBlock.setLayout(cropButtonsBlockLayout)
        glSettingsBlockLayout.addWidget(cropButtonsBlock)
        # -- -- --
        cropButtonsBlockLayout.addStretch(1)
        # -- -- --
        addClassifierButton = QPushButton('Add Classifier', self)
        addClassifierButton.setToolTip('Add a new Classifier option to List')
        addClassifierButton.setMinimumHeight(35)
        addClassifierButton.clicked.connect(self.addClassifierButton_onClick)
        glSettingsBlockLayout.addWidget(addClassifierButton)
        # -- -- --
        cropButtonsBlockLayout.addStretch(1)
        # -- -- --
        self.saveCropButton = QPushButton('Save Crop', self)
        self.saveCropButton.setToolTip('Save cropped image above')
        self.saveCropButton.setMinimumHeight(35)
        self.saveCropButton.clicked.connect(self.saveCropButton_onClick)
        glSettingsBlockLayout.addWidget(self.saveCropButton)
        # -- -- --
        cropButtonsBlockLayout.addStretch(1)
        
        
        # -- -- --
        
        # -- -- --
        
        
        # Trip first item's onClick
        self.fileList_onSelectionChanged()
        
        #timer = QtCore.QTimer(self)
        #timer.timeout.connect(self.glTexture.update) 
        #timer.start(1000)
        
        # Connect Resize Timer Function
        self.resizeTimer.timeout.connect(self.fitRawResizeTimeout) 
    
        self.geometryStore = self.geometry()
        #print( self.geometryStore )
    
    def resize(self):
        self.fitRawPixmapToView(True)
        if hasattr( self, 'glTexture' ) :
            self.glTexture.update()
        
        
    # -- -- -- -- -- -- -- -- -- -- -- --
    # -- UI Event Listener Functions - -- --
    # -- -- -- -- -- -- -- -- -- -- -- -- -- --
        
        
        
    @QtCore.pyqtSlot()
    def ulShelfSeparator_onPressed(self):
        self.ulShelfAdjustLocked = True
        #print("UL Shelf Adjust Pressed! UL Shelf Lock - " + str(self.ulShelfAdjustLocked) )
        # Eh, don't feel like making a custome QPushButton right now...
        self.mouseLocked = True
        # Prevent massive jump in shelf adjustments -
        #self.mousePos = e.pos()
        self.mouseDelta = QtCore.QPoint(0,0)
        self.geometryStore = self.geometry()
        self.lShelfGeometryStore = self.lowShelfWidget.geometry()
        
    @QtCore.pyqtSlot()
    def ulShelfSeparator_onReleased(self):
        if not self.mouseLocked:
            self.ulShelfAdjustRelease()
    def ulShelfResize(self):
        #print( self.mouseLocked )
        if self.mouseLocked:
            #print( "Mouse Pos - ["+ str(self.mousePos.x()) +","+str(self.mousePos.y())+"]" )
            #print( "Mouse Delta - ["+ str(self.mouseDelta.x()) +","+str(self.mouseDelta.y())+"]" )
            
            shiftHeight = 3
            #
            """
            lowShelfTop = self.lowShelfWidget.geometry().top()
            lowShelfHeight = self.lowShelfWidget.geometry().height() - shiftHeight
            # Geometry().bottom() is off by 1 pixel, documentation states
            lowShelfBottom = lowShelfTop + lowShelfHeight
            lBottomToMouse = lowShelfBottom - self.mousePos.y()
            lBottomToMouse = max( self.minLowShelfSize , lBottomToMouse )
            """
            
            # Geometry().bottom() is off by 1 pixel, documentation states
            lowShelfBottom = self.lShelfGeometryStore.bottom()
            lBottomToMouse = lowShelfBottom - self.mousePos.y()
            lBottomToMouse = max( self.minLowShelfSize , lBottomToMouse )
            
            
            #print("To Size - "+str(lBottomToMouse))
            self.lowShelfWidget.setFixedHeight( lBottomToMouse )
            
            self.upperShelfWidget.adjustSize()
            self.setGeometry( self.geometryStore )
            
    def ulShelfAdjustRelease(self):
            self.ulShelfAdjustLocked = False
            print("UL Shelf Adjust Released! UL Shelf Lock - " + str(self.ulShelfAdjustLocked) )
        
        
    @QtCore.pyqtSlot()
    def removeImageEntryButton_onClick(self):
        self.removeFileEntry(False, True, True)
        
    @QtCore.pyqtSlot()
    def removeDeleteImageButton_onClick(self):
        self.removeFileEntry(True, True, True)
        
    def loadImagePrompter(self):
        self.manager.showStatus("Loading ImageToPrompt, may take a minute", 1, False)
        from .utils import ImageToPrompt as i2p
        #self.imagePrompter = "BLIP"
        #self.imagePromptFinder = None
        modelsDir = os.path.join( self.DataManagmentRootPath, "weights" )
        self.imagePromptFinder = i2p.ImageToPrompt( modelsDir )
        self.manager.showStatus("ImageToPrompt Loaded")
        return
         
    @QtCore.pyqtSlot()
    def generateImagePromptButton_onClick(self):
        if self.imagePromptFinder == None:
            self.loadImagePrompter()
            
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        curImageFullPath = curWidget.fullPath
        
        self.manager.showStatus("ImageToPrompt : Finding Prompt in '"+curWidget.fileName+"'")
        foundPrompt = self.imagePromptFinder.interrogate( curImageFullPath )
        self.curFileObject.data['prompt'] = foundPrompt
        #print( curWidget.fileName )
        #print( self.manager.imageList[self.curFolderPath][curWidget.id] )
        self.updatePromptDisplay()
        self.manager.showStatus("ImageToPrompt : "+foundPrompt, 1)
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def generateImagePromptButton_onClick(self):
        if self.imagePromptFinder == None:
            self.loadImagePrompter()
            
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        curImageFullPath = curWidget.fullPath
        
        self.manager.showStatus("ImageToPrompt : Finding Prompt in '"+curWidget.fileName+"'")
        foundPrompt = self.imagePromptFinder.interrogate( curImageFullPath )
        self.curFileObject.data['prompt'] = foundPrompt
        #print( curWidget.fileName," -- " )
        #print("  ",foundPrompt)
        #print( curWidget.fileName )
        #print( self.manager.imageList[self.curFolderPath][curWidget.id] )
        self.updatePromptDisplay()
        self.manager.showStatus("ImageToPrompt : "+foundPrompt, 1)
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def generateAllImagePromptButton_onClick(self):
        folderCount = self.folderList.count()
        for curFolderRow in range(folderCount):
            self.folderList.setCurrentRow(curFolderRow)
            self.folderList_onSelectionChanged()
            QApplication.processEvents()
            
            curFileCount = self.fileList.count()
            for curFileRow in range(curFileCount):
                self.fileList.setCurrentRow(curFileRow)
                self.fileList_onSelectionChanged()
                
                if 'prompt' not in self.curFileObject.data:
                    QApplication.processEvents()
                    self.generateImagePromptButton_onClick()
                    QApplication.processEvents()
        
    def loadFaceFinder(self):
        if self.faceFinder == None:
            #print('Loading Face Finder')
            self.manager.showStatus("Loading FaceFinder, may take a minute", 1, False)
            from .utils import FaceFinder as ff
            self.faceFinder = ff.FaceFinder( output = self.outputCroppedPath )
            self.manager.showStatus("FaceFinder Loaded")
        #else:
        #    print('Face Finder Already Loaded')
        self.setFocus()
        
    # FaceFinder is using numpy array data
    #   Should return all found faces as arrays, shouldn't be saving faces by default
    # TODO : Saving cropped & aligned faces when finding in FaceFinder
    #          Image saving should be handled in Main
    @QtCore.pyqtSlot()
    def findFaceButton_onClick(self):
        if self.faceFinder == None:
            self.loadFaceFinder()
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        self.curFileObject = curWidget
        curImageFullPath = self.curFileObject.fullPath
        self.manager.showStatus("FaceFinder : Finding Faces in '"+curWidget.fileName+"'", 1, False)
        foundFacesDictList = self.faceFinder.input(curImageFullPath)
        self.manager.showStatus("FaceFinder : Found '"+str(len(foundFacesDictList))+"' Faces")
        if len(foundFacesDictList) > 0:
            for foundFace in foundFacesDictList:
                curAlignedFacePath = foundFace['alignedPath']
                curUnalignedFacePath = foundFace['unalignedPath']
                curDetFace = foundFace['detFace'].tolist()
                
                if not 'faces' in self.curFileObject.data:
                    self.curFileObject.data['faces'] = []
                alignedFace = { 'path':curAlignedFacePath, 'bounds':curDetFace, 'prompt':"" }
                self.curFileObject.data['faces'].append( alignedFace )
                unalignedFace = { 'path':curUnalignedFacePath, 'bounds':curDetFace, 'prompt':"" }
                self.curFileObject.data['faces'].append( unalignedFace )
                
                pixmap = QtGui.QPixmap( curAlignedFacePath )
                self.faceImage.setPixmap(pixmap)
                
                # -- -- --
                
                imagePathSplit = curImageFullPath.split(".")
                imgExt = imagePathSplit[-1]
         
                # loading image
                imgData = open(curImageFullPath, 'rb').read()
                
                pixmap = self.cropImage(
                    imgData = imgData,
                    imgType = imgExt,
                    size = 512,
                    bounds = curDetFace,
                    boundsScalar = 1.2
                )
            
                
                self.faceUnalignedImage.setPixmap(pixmap)
                pixmap.save(curUnalignedFacePath)
        self.setFocus()
            
    @QtCore.pyqtSlot()
    def findAllFacesButton_onClick(self):
        folderCount = self.folderList.count()
        for curFolderRow in range(folderCount):
            self.folderList.setCurrentRow(curFolderRow)
            self.folderList_onSelectionChanged()
            QApplication.processEvents()
            
            curFileCount = self.fileList.count()
            for curFileRow in range(curFileCount):
                self.fileList.setCurrentRow(curFileRow)
                self.fileList_onSelectionChanged()
                
                if 'faces' not in self.curFileObject.data:
                    QApplication.processEvents()
                    self.findFaceButton_onClick()
                    QApplication.processEvents()
                    
    @QtCore.pyqtSlot()
    def updateCropButton_onClick(self):
        if hasattr(self, 'glTexture') :
            curItem = self.fileList.currentItem()
            curWidget = self.fileList.itemWidget(curItem)
            curImageFullPath = curWidget.fullPath
            self.glTexture.loadImage( curImageFullPath )
            self.setFocus()
        
    @QtCore.pyqtSlot()
    def addClassifierButton_onClick(self):
        
        newClassifier, done = QInputDialog.getText(self, 'New Classifier', 'Enter your new classifier, (1-3 words) :')
        if done :
            QListWidgetItem(newClassifier, self.outputClassifier)
        self.setFocus()
            
    @QtCore.pyqtSlot()
    def saveCropButton_onClick(self):
        if hasattr(self, 'glTexture') :
            curBuffer = self.glTexture.grabFrameBuffer(withAlpha=False)
            curItem = self.outputClassifier.currentItem()
            if curItem :
                curClassFolder = curItem.text()
                curClassPath = os.path.join( self.outputClassifiedPath, curClassFolder)
                os.makedirs(curClassPath, exist_ok = True) 
                imgList=os.listdir(curClassPath)
                id = len(imgList)
                
                curClassPath = os.path.join(curClassPath, f'{curClassFolder}_{id:03d}.jpg')
                print("Saving to ",curClassPath)
                curBuffer.save(curClassPath)
            else:
                print("No Classifier Text Selected, please select a classifier before saving the crop")
        self.setFocus()
            
        
    
    @QtCore.pyqtSlot()
    def folderList_onSelectionChanged(self):
        curItem = self.folderList.currentItem()
        curWidget = self.folderList.itemWidget(curItem)
        if self.curFolderObject:
            self.curFolderObject.setCurrent(False)
        self.curFolderObject = curWidget 
        self.curFolderObject.setCurrent(True)
        if curWidget:
            self.curFolderPath = curWidget.fullPath
            self.rebuildFileList(curWidget.fullPath)
        else:
            print("Failed to find current Folter Item")
        self.setFocus()
    
        
    @QtCore.pyqtSlot()
    def folderList_onItemDoubleClick(self):
        self.folderList_onSelectionChanged()
        
    @QtCore.pyqtSlot()
    def fileList_onSelectionChanged(self):
        self.loadSelectedFile(False)
    @QtCore.pyqtSlot()
    def fileList_onItemDoubleClick(self):
        self.loadSelectedFile(True)
        
    def loadSelectedFile(self, loadToGL = False):
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        
        if self.curFileObject:
            self.curFileObject.setCurrent(False)
        self.curFileObject = curWidget 
        self.curFileObject.setCurrent(True)
        if curWidget:
            self.loadImageFile( self.curFileObject.fullPath, loadToGL )
            self.updatePromptDisplay()
        else:
            print("Failed to find current File Item")
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def curPromptField_editingFinished(self):
        self.curFileObject.data['prompt'] = self.curPromptField.text()
        self.setFocus()
    
    def updatePromptDisplay(self):
        if self.curPromptField:
            curPrompt = ""
            try:
                curPrompt = self.curFileObject.data['prompt']
            except:
                pass;
            self.curPromptField.setText(curPrompt)
    

    # -- -- -- -- -- -- -- -- -- --
    # -- Primary Functionality - -- --
    # -- -- -- -- -- -- -- -- -- -- -- --

    
    def rebuildFileList(self,folderPath=None):
        self.curFolderPath = folderPath
        if self.curFolderPath == None:
            curItem = self.folderList.currentItem()
            curWidget = self.folderList.itemWidget(curItem)
            self.curFolderPath = curWidget.fullPath
            self.curFolderObject = curWidget 
            self.curFolderObject.setCurrent(True)
        # File List
        self.fileList.clear()
        self.curFileListItem = None
        for x,folderImageData in enumerate( self.manager.imageList[self.curFolderPath] ):
            # Create QCustomQWidget
            curFileItem = FileListItem(x)
            curFileItem.setFullPath(folderImageData["filePath"])
            curFileItem.setFolderPath(folderImageData["folderPath"])
            curFileItem.setFolderText(folderImageData["folderName"])
            curFileItem.setImageText(folderImageData["fileName"])
            #curFileItem.setImage(folderImageData["dispImage"])
            curFileItem.setData(folderImageData["fileData"])
            
            
            
            curFileItemWidget = QListWidgetItem(self.fileList)
            curFileItemWidget.setSizeHint(curFileItem.sizeHint())
            if self.curFileListItem == None:
                curFileItem.setCurrent(True)
                self.curFileListItem = curFileItemWidget

            self.fileList.addItem(curFileItemWidget)
            self.fileList.setItemWidget(curFileItemWidget, curFileItem)
        
        self.fileList.setCurrentItem( self.curFileListItem )
    def changeSelectedFile(self, dir=1):
        #self.changeSelectedFile(-1)
        #self.changeSelectedFile(1)
        value = self.fileList.currentRow()
        toValue = value+dir
        if toValue<0:
            value = self.folderList.currentRow()
            toValue = value+dir
            if toValue<0:
                toValue = self.folderList.count()-1
            self.folderList.setCurrentRow(toValue)
            self.folderList_onSelectionChanged()
            self.fileList.setCurrentRow(self.fileList.count()-1)
            self.fileList_onSelectionChanged()
        elif toValue>=self.fileList.count():
            value = self.folderList.currentRow()
            toValue = value+dir
            if toValue>=self.folderList.count():
                toValue = 0
            self.folderList.setCurrentRow(toValue)
            self.folderList_onSelectionChanged()
        else:
            self.fileList.setCurrentRow( toValue )
    def writeImage(self):
        #imwrite(cropped_face, save_crop_path)
        return;
    def writeText(self, filePath, contents=""):
        with open(filePath, "w", encoding="utf8") as file:
            file.write(contents)
    
    def fitRawPixmapToView(self, resizeEvent=False):
        
        defMargin = [4,4]
        defSpacing = 4
        
        labelWidth = self.currentFileBlockWidget.width()
        labelHeight = self.currentFileBlockWidget.height()
        
        #if resizeEvent:
        #    labelWidth = int( labelWidth * .5 )
        #    labelHeight = int( labelHeight * .5 )
        #    self.resizeTimer.start(300)
        #    #return;
        
        # TODO : Set spacing and margin values in an easily accessable way
        buttonBlockHeight = self.curImageButtonBlock.height()
        
        labelWidth -= defMargin[0]
        labelHeight -= defMargin[1] + defSpacing + buttonBlockHeight
        
        
        self.rawImageWidget.setPixmap( self.curRawPixmap.scaled( labelWidth, labelHeight, QtCore.Qt.KeepAspectRatio ) )
        self.rawImageWidget.adjustSize()


        #print( self.upperShelfWidget.rect() )
        #print( self.rawImageBlockWidget.rect() )
        #print( self.currentFileBlockWidget.rect() )

        #pixRect = self.rawImageWidget.pixmap().rect()
        #print(pixRect)
        #self.rawImageWidget.setFixedWidth( pixRect.width() )
        #self.rawImageWidget.setFixedHeight( pixRect.height() )
        
    def fitRawResizeTimeout(self):
        self.fitRawPixmapToView()
        self.resizeTimer.stop()
    
    def loadImageFile(self,imageFullPath=None, updateGlTexture=False):
        if self.rawImageWidget != None:
            curImageFullPath = imageFullPath
            if curImageFullPath == None:
                curItem = self.fileList.currentItem()
                curWidget = self.fileList.itemWidget(curItem)
                curImageFullPath = curWidget.fullPath
            
            # Don't read whole image until resolution verified
            imgData = Image.open( curImageFullPath )
            imgWidth, imgHeight = imgData.size
            
            # No auto cropping of input image
            self.curRawPixmap = QtGui.QPixmap( curImageFullPath )
            
            self.fitRawPixmapToView()
            
            """
            # Auto cropping of input image to 512,512 by larges axis
            imgExt = curImageFullPath.split(".")[-1]
            # loading image
            imgData = open(curImageFullPath, 'rb').read()
            pixmap = self.cropImage(
                imgData = imgData,
                imgType = imgExt,
                size = 512
            )
            self.rawImageWidget.setPixmap(pixmap)
            """
            
            if updateGlTexture :
                self.glTexture.loadImage( curImageFullPath )
    
    # Converting image cropping to numpy, since most other modules use numpy
    #   Leaving method for now
    # TODO : Remove when numpy image array cropping is working
    def cropImage(self, imgData, imgType='png', size = 64, bounds=None, boundsScalar=1):
        # Load image
        image = QtGui.QImage.fromData(imgData, imgType)
     
        # Add Alpha, not needed yet; only needed if non alpha as well
        #image.convertToFormat(QtGui.QImage.Format_ARGB32)
     
        # Crop image to a square:
        imgsize = min(image.width(), image.height())
        rect=None
        # Not a fan of doing this, but don't feel like
        #   doing multiple checks for array() types
        if type(bounds) == type(None):
            rect = QtCore.QRect(
                int((image.width() - imgsize) / 2),
                int((image.height() - imgsize) / 2),
                imgsize,
                imgsize,
            )
        else:
            sizeXY = [ bounds[2]-bounds[0], bounds[3]-bounds[1] ]
            imgsize=max(sizeXY[0],sizeXY[1])*boundsScalar
            corner = [(bounds[0]+bounds[2])*.5 - imgsize*.5,(bounds[1]+bounds[3])*.5 - imgsize*.5]
            imgsize = int(imgsize)
            rect = QtCore.QRect(
                int(corner[0]), int(corner[1]),
                imgsize, imgsize
            )
        
        image = image.copy(rect)
     
        # Create the output image with the
        # same dimensions and an alpha channel
        # and make it completely transparent:
        out_img = QtGui.QImage(imgsize, imgsize, QtGui.QImage.Format_ARGB32)
        out_img.fill(QtCore.Qt.transparent)
     
        # Create a texture brush and paint a circle
        # with the original image onto
        # the output image:
        brush = QtGui.QBrush(image)
     
        # Paint the output image
        painter = QtGui.QPainter(out_img)
        painter.setBrush(brush)
     
        # Don't draw an outline
        painter.setPen(QtCore.Qt.NoPen)
     
        # drawing square
        painter.drawRect(0, 0, imgsize, imgsize)
     
        # closing painter event
        painter.end()
     
        # Convert the image to a pixmap and rescale it.
        pr = QtGui.QWindow().devicePixelRatio()
        pm = QtGui.QPixmap.fromImage(out_img)
        pm.setDevicePixelRatio(pr)
        size = int( size * pr )
        pm = pm.scaled(size, size, QtCore.Qt.KeepAspectRatio,
                                   QtCore.Qt.SmoothTransformation)
     
        # return back the pixmap data
        return pm

    def removeFileEntry(self, deleteFileOnDisk=False, removeEmptyFolders=True, saveProjectDataJson=False):
        # Current File
        curFileItemRow = self.fileList.currentRow()
        curFileItem = self.fileList.item( curFileItemRow )
        curFileWidget = self.fileList.itemWidget( curFileItem )
        # Having an issue getting the item widget after running .takeItem()
        curFileItem = self.fileList.takeItem(curFileItemRow)
        
        
        # Current Folder
        folderListCount = self.folderList.count()
        curFolderItemRow = self.folderList.currentRow()
        curFolderItem = self.folderList.item( curFolderItemRow )
        curFolderWidget = self.folderList.itemWidget( curFolderItem )

        updatedImageCount = curFolderWidget.imageCount
        updatedImageCount = max(0, updatedImageCount-1)
        
        
        fileName = curFileWidget.fileName
        folderName = curFileWidget.folderName
        fullPath = curFileWidget.fullPath
        folderPath = curFileWidget.folderPath
        #print( self.fileList.count()," - ", updatedImageCount )
        
        isDiskFolderEmpty = False
        
        curFolderWidget.setImageCount( self.fileList.count() )
        
        if self.fileList.count() == 0:
            curFolderItem = self.folderList.takeItem(curFolderItemRow)
            self.folderList_onSelectionChanged()
            if removeEmptyFolders :
                dirOrderIndex = self.manager.dirOrder.index(curFolderWidget.fullPath)
                if dirOrderIndex >= 0 and dirOrderIndex == curFolderItemRow:
                    self.manager.dirOrder.pop(dirOrderIndex)
                    folderFiles = os.listdir(curFolderWidget.fullPath)
                    fileIndex = folderFiles.index(fileName)
                    folderFiles.pop( fileIndex )
                    if len(folderFiles) == 0:
                        print("Folder is empty, no other files found.\n Deleting - ")
                        print(" -- ",curFolderWidget.fullPath)
                        isDiskFolderEmpty = True
                    else:
                        print("Folder is NOT empty, other files found.\n Not deleting folder - ")
                        print(" -- ",curFolderWidget.fullPath)
                else:
                    print("Dictionary order mismatch detected.\n Not deleting folder -")
                    print(" -- ",curFolderWidget.fullPath)
        else:
            toFileRow = curFileItemRow if curFileItemRow < self.fileList.count() else max(0,curFileItemRow-1)
            self.fileList.setCurrentRow(toFileRow)
            self.fileList_onSelectionChanged()
                    
            
            
        if saveProjectDataJson :
            linkedDict = self.manager.imageList[folderPath][curFileItemRow]
            isCorrectPath = fullPath == linkedDict['filePath']
            if isCorrectPath :
                print("Deleting ImageFile from Project - ")
                print(fullPath)
                del self.manager.imageList[folderPath][curFileItemRow]
                if len( self.manager.imageList[folderPath] ) == 0:
                    del self.manager.imageList[folderPath]
                    print("Deleting Folder from Project - ")
                    print(folderPath)
            else:
                print("ImageList <> DirectoryListing missmatch detected,\n Not deleting file or folder - ")
                print(folderPath)
                print(fullPath)
                deleteFileOnDisk = False
            print("SAVE DATA")
            self.manager.saveProjectData()
        
        if self.confirmFileDeletion and deleteFileOnDisk:
            ret = QMessageBox.question(self,'', "Delete current image from disk?", QMessageBox.Yes | QMessageBox.No)
            deleteFileOnDisk = ret == QMessageBox.Yes
            
        if deleteFileOnDisk :
            os.remove( fullPath )
            if isDiskFolderEmpty :
                os.rmdir( folderPath )
                
                
        curFileWidget.deleteLater()
        #curFileItem.deleteLater()
        if self.fileList.count() == 0 :
            curFolderWidget.deleteLater()
            #curFolderItem.deleteLater()
        self.setFocus()


# main function
# TODO : Implement Main
"""
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
 
    settingsManager = pxlSettings.UserSettingsManager("userSettings")
    # app created
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    screenRes = screen.size()
    userScreenRes = [ screenRes.width(), screenRes.height() ]
    
    w = ImageLabelerProjectManager( userScreenRes, settingsManager )
    w.setupUI()
    w.show()
    
    #w = ImageLabelerWindow()
    #w.setupUI()
    #w.show()
    
    # begin the app
    sys.exit(app.exec_())
"""