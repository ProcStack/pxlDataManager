
# Built on Python 3.10.6 && PyQt5 5.15.9

import sys, os, platform, time
from PIL import Image
from functools import partial
import math
import json

import ctypes
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtOpenGL
from PyQt5.QtWidgets import *
from PyQt5.uic import *

#from basicsr.utils import imwrite

import utils.UserSettingsManager as pxlSettings
import utils.ViewportGL as ViewerGL
import utils.ViewportBufferGL as ViewerBufferGL

# -- -- --

# Current known issues -
# _Resizing Lower Shelf is janky as all the funking trumpet players...
# _ViewportGL's seem to be sharing uniform values, bleh...
#
# TODOs -
# _Implement the Settings Manager, easy, but needs to be done
# _Auto Load Crops isn't implemented
# _Get ViewportGL loading with more options and sliders and better Fragment Shader
# _Make AI's Async; FaceFinder & ImageToPrompt
# _Implement OpenPose finder for ControlNet prep



# -- -- --

# 'os' doesn't always handle extentions or other path specific needs correctly
#   Reference delimiter where needed
delimiter = "/"
if platform.system() == 'Windows':
    delimiter = "\\"

# -- -- --

# Orig name (for code clean up) - scriptAbsDir
ImageLabelerAbsPath = os.path.abspath(__file__)
# Orig name (for code clean up) - scriptDir
ImageLabelerScriptDir = os.path.dirname(ImageLabelerAbsPath)

ImageLabelerActiveProject = "No Project Loaded"
ImageLabelerProjectData = {}


# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --

# Folders expected to be in root of script
# TODO : Allow for input output folder paths
class ImageLabelerProjectManager(QMainWindow):
    def __init__(self, screenRes=[600,450], settingsManager=None, *args):
        super(ImageLabelerProjectManager, self).__init__(*args)
        
        self.settings = settingsManager
        
        self.menuBar = None
        self.mouseLocked = False
        self.mouseMoved = False

        self.screenRes = screenRes
        self.screenCenter = [int(screenRes[0]*.5), int(screenRes[1]*.5)]
        
        self.managerInitSize = [ 600, 450 ]
        
        self.managerInitPos = [ 200, 200 ]
        self.managerInitPos[0] = int( self.screenCenter[0] - self.managerInitSize[0]*.5 )
        self.managerInitPos[1] = int( self.screenCenter[1] - self.managerInitSize[1]*.5 )
        
        self.projectLoadMinSize = [ int(self.screenRes[0]*.75), int(self.screenRes[1]*.75) ]

        #self.projectLoadMinWidth = [min( screenRes[0], 1000 ),min( screenRes[1], 700 )]
        
        
        self.sourceDir = ""
        self.outputDir = ""
        
        self.projectRootDirName = "Projects"
        self.projectName = "Default"
        self.curSelectedProjectText = None
        
        self.existingProjects = {}
        self.projectNameWidget = None
        self.projectPath = None
        self.projectWidget = None
        
        self.loadProjectBlockWidget = None
        # Images found in Source folder hierarchy
        self.imageList={}
        # Ordered Director List
        self.dirOrder=[]
        
        self.hasUnsavedData = False
        
        # Should found folders be Empty
        #   Or only have folders in them
        #     Dont list these directories in Project's Folder List
        self.bypassEmptyAndFoldersOnly = True
        
        self.curProjectData = {
            'name':"",
            'dataJson':"",
            'settingsJson':""
        }

        self.extList=["jpg","jpeg","gif","png", "bmp"]#, "svg"] # Check SVG, since it likes vector postions
        self.fileDataJsonName = "ProjectData.json"
        self.fileDataJsonPath = None # os.path.join(outputDir, self.fileDataJsonName)
        self.settingsJsonName = "ProjectSettings.json"
        self.settingsJsonPath = None # = os.path.join(outputDir, "Classifiers.json")

        #self.sourceAbsDir = os.path.join(ImageLabelerScriptDir, self.sourceDir)


        # Images by Folder Path
        self.imageList={}
        # Ordered Director List
        self.dirOrder=[]
        self.foundFileCount=0
        
        # -- -- --
        # -- -- --
        
        self.statusTimer = None
        self.statusTimeout = 4000
        
        self.menuBar = None
        self.statusBar = None
 
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            print("Project Manager; Enter Key")
            self.proceed()
        elif event.key() == QtCore.Qt.Key_Escape:
            print( "Exiting" )
            QApplication.quit()
        event.accept()
        
        
        
    def createMenuBar(self):
        self.menuBar = QMenuBar(self)
        
        # == == ==
        # == == ==
        # == == ==
        
        fileMenu = QMenu("&File", self)
        self.menuBar.addMenu(fileMenu)
        # -- -- --
        self.newProjectAction = QAction("New Project", self)
        fileMenu.addAction( self.newProjectAction )
        #self.newProjectAction.triggered.connect( self.menu_file_newProject )
        # -- -- --
        self.openProjectAction = QAction("Open Project", self)
        fileMenu.addAction(self.openProjectAction)
        #self.openProjectAction.triggered.connect( self.menu_file_newProject )
        # -- -- --
        self.openProjectFolderAction = QAction("Open Project Folder in Explorer", self)
        fileMenu.addAction(self.openProjectFolderAction)
        self.openProjectFolderAction.triggered.connect( self.menu_file_openFolderInExplorer )
        # -- -- --
        # -- -- --
        self.saveProjectFolderAction = QAction("Save Project", self)
        fileMenu.addAction(self.saveProjectFolderAction)
        self.saveProjectFolderAction.triggered.connect( self.menu_file_saveProject )
        # -- -- --
        self.exitAction = QAction("Exit", self)
        fileMenu.addAction(self.exitAction)
        self.exitAction.triggered.connect( QApplication.quit )
        
        # == == ==
        # == == ==
        # == == ==
        
        editMenu = QMenu("&Edit", self)
        self.menuBar.addMenu(editMenu)
        # -- -- --
        self.undoDeleteAction = QAction("Undo File Delete", self)
        editMenu.addAction( self.undoDeleteAction )
        self.undoDeleteAction.setShortcut( QtGui.QKeySequence.Undo )
        #self.undoDeleteAction.triggered.connect( self.menu_edit_undoDelete )
        # -- -- --
        self.redoDeleteAction = QAction("Redo File Delete", self)
        editMenu.addAction( self.redoDeleteAction )
        self.redoDeleteAction.setShortcut( QtGui.QKeySequence.Redo )
        #self.redoDeleteAction.triggered.connect( self.menu_edit_redoDelete )
        
        # == == ==
        # == == ==
        # == == ==
        
        browseToMenu = QMenu("&Browse to ...", self)
        self.menuBar.addMenu(browseToMenu)
        # -- -- --
        self.browseProjectFolderAction = QAction("Project Folder", self)
        browseToMenu.addAction( self.browseProjectFolderAction )
        self.browseProjectFolderAction.triggered.connect( self.menu_browse_projectFolder )
        # -- -- --
        self.browseSelectedFolderAction = QAction("Selected Image Folder", self)
        browseToMenu.addAction( self.browseSelectedFolderAction )
        self.browseSelectedFolderAction.triggered.connect( self.menu_browse_selectedFolder )
        # -- -- --
        self.browseCropFolderAction = QAction("Cropped Faces Folder", self)
        browseToMenu.addAction( self.browseCropFolderAction )
        self.browseCropFolderAction.triggered.connect( self.menu_browse_cropFolder )
        # -- -- --
        self.browseClassFolderAction = QAction("Classified Crops Folder", self)
        browseToMenu.addAction( self.browseClassFolderAction )
        self.browseClassFolderAction.triggered.connect( self.menu_browse_classFolder )
        # -- -- --
        
        # == == ==
        # == == ==
        # == == ==
        
        optionsMenu = QMenu("&Options", self)
        self.menuBar.addMenu(optionsMenu)
        # -- -- --
        self.infoAction = QAction("Confirm File/Folder Delete From Disk", self)
        optionsMenu.addAction( self.infoAction )
        #self.infoAction.triggered.connect( self.menu_options_confirmDelete )
        # -- -- --
        
        
        # == == ==
        # == == ==
        # == == ==
        
        helpMenu = QMenu("&Help", self)
        self.menuBar.addMenu(helpMenu)
        # -- -- --
        self.infoAction = QAction("Info", self)
        helpMenu.addAction( self.infoAction )
        #self.infoAction.triggered.connect( self.menu_help_info )
        # -- -- --
        
        
        #self.saveAction.setShortcut( "Ctrl+S" )
        #self.copyAction.setShortcut( QtGui.QKeySequence.Copy )
        
        
        
        self.setMenuBar(self.menuBar)
        
    def menu_file_openFolderInExplorer(self):
        self.browseToPath(self.projectPath)
    def menu_file_saveProject(self):
        self.saveProjectData()
        """
        self.projectName = curProjectName
        self.projectPath = self.existingProjects[curProjectName]['ProjectPath']
        self.fileDataJsonPath = self.existingProjects[curProjectName]['ProjectDataJsonPath']
        self.settingsJsonPath = self.existingProjects[curProjectName]['SettingsJsonPath']
        
        self.fileDataJsonPath = os.path.join(self.projectPath, self.fileDataJsonName)self.existingProjects[x]['ProjectDataJsonPath'] = pdJsonPath
                    
        self.fileDataJsonName = "ProjectData.json"
        self.imageList={}
        """
    def menu_browse_projectFolder(self):
        self.browseToPath(self.projectPath)
    def menu_browse_selectedFolder(self):
        self.browseToPath(self.projectWidget.curFolderPath)
    def menu_browse_cropFolder(self):
        self.browseToPath(self.projectWidget.outputCroppedPath)
    def menu_browse_classFolder(self):
        self.browseToPath(self.projectWidget.outputClassifiedPath)
        
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
 
        self.setWindowTitle("Image & AI Labeling Tools")
        
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setSpacing(1)
        self.mainLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        # -- -- --
        
        # Spash screen for loading or making a new Project
        self.loadProjectBlockWidget = QWidget()
        self.loadProjectBlockWidget.setMaximumWidth(700)
        self.loadProjectBlockWidget.setMaximumHeight(1000)
        # -- -- --
        loadProjectBlockLayout = QVBoxLayout()
        loadProjectBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        loadProjectBlockLayout.setContentsMargins(0,0,0,0)
        loadProjectBlockLayout.setSpacing(1)
        self.loadProjectBlockWidget.setLayout(loadProjectBlockLayout)
        self.mainLayout.addWidget(self.loadProjectBlockWidget)

        
        # -- -- --
        
        # Loaded Project Display
        self.curProjectBlockWidget = QWidget()
        #self.curProjectBlockWidget.setStyleSheet("border: 1px solid black;")
        # -- -- --
        self.curProjectBlockLayout = QVBoxLayout()
        self.curProjectBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.curProjectBlockLayout.setContentsMargins(3,3,3,3)
        self.curProjectBlockWidget.setLayout( self.curProjectBlockLayout )
        self.mainLayout.addWidget(self.curProjectBlockWidget)
        
        
        # -- -- --
        # -- -- --
        # -- -- --
        
        tlabel = QLabel('Load Project - ', self)
        tlabel.setAlignment(QtCore.Qt.AlignLeft)
        loadProjectBlockLayout.addWidget(tlabel)
        
        # -- -- --
        
        
        # Found Projects List
        
        tlabel = QLabel('-- Found Project List --', self)
        tlabel.setAlignment(QtCore.Qt.AlignCenter)
        loadProjectBlockLayout.addWidget(tlabel)
        # -- -- --
        self.foundProjectsList = QListWidget()
        self.foundProjectsList.itemSelectionChanged.connect( self.foundProjectsList_onSelectionChanged )
        self.foundProjectsList.itemDoubleClicked.connect( self.foundProjectsList_onItemDoubleClick )
        
        loadProjectBlockLayout.addWidget(self.foundProjectsList)
        # -- -- --
        
        itemKeys = []
        projectsRootDir = os.path.join(ImageLabelerScriptDir, self.projectRootDirName)
        print(projectsRootDir)
        if not os.path.isdir( projectsRootDir ) :
            print(" No '",self.projectRootDirName,"' folder found, making -\n  ",projectsRootDir)
            os.mkdir( projectsRootDir )
        projectsRootDirList=os.listdir(projectsRootDir)
        for x in projectsRootDirList:
            curFullPath = os.path.join(projectsRootDir,x)
            if os.path.isdir(curFullPath):
                projectDirFileList=os.listdir(curFullPath)
                if self.fileDataJsonName in projectDirFileList:
                    itemKeys.append(x)
                    self.existingProjects[x]={}
                    # -- -- --
                    self.existingProjects[x]['ProjectPath'] = curFullPath
                    # -- -- --
                    pdJsonPath = os.path.join(curFullPath,self.fileDataJsonName)
                    self.existingProjects[x]['ProjectDataJsonPath'] = pdJsonPath
                    # -- -- --
                    settingsJsonPath = os.path.join(curFullPath,self.settingsJsonName)
                    settingsJsonPath = settingsJsonPath if os.path.isfile(settingsJsonPath) else None
                    self.existingProjects[x]['SettingsJsonPath'] = settingsJsonPath
        # -- -- --
        if len(itemKeys) > 0:
            for project in itemKeys:
                QListWidgetItem(project, self.foundProjectsList)
            self.foundProjectsList.setCurrentRow(0)
            self.foundProjectsList_onSelectionChanged()
        # -- -- --
        
        
        # Load Project Options
        
        vSpacer = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
        loadProjectBlockLayout.addItem(vSpacer)
        # -- -- --
        curSelectedProjectWidget = QWidget()
        curSelectedProjectLayout = QHBoxLayout()
        curSelectedProjectLayout.setAlignment(QtCore.Qt.AlignCenter)
        curSelectedProjectLayout.setContentsMargins(0,0,0,0)
        curSelectedProjectLayout.setSpacing(1)
        curSelectedProjectWidget.setLayout(curSelectedProjectLayout)
        loadProjectBlockLayout.addWidget(curSelectedProjectWidget)
        # -- -- --
        curProjectHeaderText = QLabel('Current Selected Project --', self)
        curProjectHeaderText.setFont(QtGui.QFont("Tahoma",9))
        loadProjectBlockLayout.addWidget(curProjectHeaderText)
        # -- -- --
        self.curSelectedProjectText = QLabel('', self)
        self.curSelectedProjectText.setText( self.projectName )
        self.curSelectedProjectText.setFont(QtGui.QFont("Tahoma",14))
        self.curSelectedProjectText.setContentsMargins(20,0,0,0)
        loadProjectBlockLayout.addWidget(self.curSelectedProjectText)
        # -- -- --
        scanDirBlockWidget = QWidget()
        self.scanDirBlockLayout = QHBoxLayout()
        self.scanDirBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.scanDirBlockLayout.setContentsMargins(0,3,0,3)
        self.scanDirBlockLayout.setSpacing(1)
        scanDirBlockWidget.setLayout(self.scanDirBlockLayout)
        
        loadProjectBlockLayout.addWidget(scanDirBlockWidget)
        # -- -- --
        self.scanDirBlockLayout.addStretch(1)
        # -- -- --
        self.verifyImagesButton = QPushButton('Verify Images', self)
        self.verifyImagesButton.setToolTip('Verify images stored in the project still exist')
        self.verifyImagesButton.clicked.connect(self.verifyImagesButton_onClick)
        self.scanDirBlockLayout.addWidget(self.verifyImagesButton)
        # -- -- --
        self.scanDirBlockLayout.addStretch(1)
        # -- -- --
        """
        self.cullEmptyFoldersButton = QPushButton('Rebuild Source Folder Scan', self)
        self.cullEmptyFoldersButton.setToolTip(' - Rebuild Image & Folder scan')
        self.cullEmptyFoldersButton.clicked.connect(self.cullEmptyFoldersButton_onClick)
        self.scanDirBlockLayout.addWidget(self.cullEmptyFoldersButton)
        # -- -- --
        self.scanDirBlockLayout.addStretch(1)
        """
        # -- -- --
        self.cullEmptyFoldersButton = QPushButton('Cull Empty Folders', self)
        self.cullEmptyFoldersButton.setToolTip(' - Remove empty project known image folders\n - Remove folders only containing folders,\n    No empty folder listings in Project View')
        self.cullEmptyFoldersButton.clicked.connect(self.cullEmptyFoldersButton_onClick)
        self.scanDirBlockLayout.addWidget(self.cullEmptyFoldersButton)
        # -- -- --
        self.scanDirBlockLayout.addStretch(1)
        # -- -- --
        self.loadButton = QPushButton('Load Selected Project', self)
        self.loadButton.setToolTip('Load selected project')
        self.loadButton.clicked.connect(self.loadButton_onClick)
        self.scanDirBlockLayout.addWidget(self.loadButton)
        # -- -- --
        self.scanDirBlockLayout.addStretch(1)
        # -- -- --
        
        
        # -- -- --
        
        
        vSpacer = QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        loadProjectBlockLayout.addItem(vSpacer)
        
        line = QLabel('', self)
        line.setFont(QtGui.QFont("Tahoma",1))
        line.resize( 300, 1 )
        #line.setStyleSheet("border: 1px solid black;")
        line.setStyleSheet("background-color:#808080;")
        loadProjectBlockLayout.addWidget(line)
        
        vSpacer = QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Minimum)
        loadProjectBlockLayout.addItem(vSpacer)
        
        
        # -- -- --
        
        tlabel = QLabel('New Project - ', self)
        tlabel.setAlignment(QtCore.Qt.AlignLeft)
        loadProjectBlockLayout.addWidget(tlabel)
        
        # -- -- --
        
        self.projectNameWidget = QLineEdit()
        self.projectNameWidget.setText("NewProjectName")
        self.projectNameWidget.setAlignment(QtCore.Qt.AlignCenter)
        self.projectNameWidget.setFont(QtGui.QFont("Tahoma",14))
        self.projectNameWidget.editingFinished.connect(self.projectName_editingFinished)
        loadProjectBlockLayout.addWidget( self.projectNameWidget )
        
        # -- -- --
        
        vLineSpacer = QSpacerItem(10, 15, QSizePolicy.Minimum, QSizePolicy.Maximum)
        loadProjectBlockLayout.addItem(vLineSpacer)
        
        
        # -- -- --
        
        
        scanDirBlockWidget = QWidget()
        self.scanDirBlockLayout = QHBoxLayout()
        self.scanDirBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        self.scanDirBlockLayout.setContentsMargins(0,0,0,0)
        self.scanDirBlockLayout.setSpacing(1)
        scanDirBlockWidget.setLayout(self.scanDirBlockLayout)
        loadProjectBlockLayout.addWidget(scanDirBlockWidget)
        # -- -- --
        self.loadScanDirButton = QPushButton('Sources Folder', self)
        self.loadScanDirButton.setToolTip('Locate Folder to Scan for Images')
        self.loadScanDirButton.clicked.connect(self.loadScanDirButton_onClick)
        self.scanDirBlockLayout.addWidget(self.loadScanDirButton)
        # -- -- --
        self.scanDirWidget = QLineEdit()
        self.scanDirWidget.setAlignment(QtCore.Qt.AlignLeft)
        self.scanDirWidget.setFont(QtGui.QFont("Tahoma",10))
        self.scanDirBlockLayout.addWidget( self.scanDirWidget )
        # -- -- --
        hSpacer = QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.scanDirBlockLayout.addItem(hSpacer)
        # -- -- --
        self.scanDirButton = QPushButton('Scan', self)
        self.scanDirButton.setToolTip('Regressively search through folder for Images')
        self.scanDirButton.clicked.connect(self.scanDirButton_onClick)
        self.scanDirBlockLayout.addWidget(self.scanDirButton)
        
        # -- -- --
        
        scanDirResultsWidget = QWidget()
        scanDirResultsLayout = QHBoxLayout()
        scanDirResultsLayout.setAlignment(QtCore.Qt.AlignCenter)
        scanDirResultsLayout.setContentsMargins(0,0,0,0)
        scanDirResultsLayout.setSpacing(1)
        scanDirResultsWidget.setLayout(scanDirResultsLayout)
        loadProjectBlockLayout.addWidget(scanDirBlockWidget)
        # -- -- --
        filabel = QLabel('Found Images - ', self)
        #filabel.setAlignment(QtCore.Qt.AlignCenter)
        #filabel.setStyleSheet("border: 1px solid black;")
        scanDirResultsLayout.addWidget(filabel)
        # -- -- --
        self.scanFoundImages = QLabel(' -- ', self)
        #self.scanFoundDirs.setAlignment(QtCore.Qt.AlignCenter)
        #self.scanFoundDirs.setStyleSheet("border: 1px solid black;")
        scanDirResultsLayout.addWidget(self.scanFoundImages)
        # -- -- --
        filabel = QLabel('Found Directories - ', self)
        #filabel.setAlignment(QtCore.Qt.AlignCenter)
        #filabel.setStyleSheet("border: 1px solid black;")
        scanDirResultsLayout.addWidget(filabel)
        # -- -- --
        self.scanFoundDirs = QLabel(' -- ', self)
        #self.scanFoundDirs.setAlignment(QtCore.Qt.AlignCenter)
        #self.scanFoundDirs.setStyleSheet("border: 1px solid black;")
        scanDirResultsLayout.addWidget(self.scanFoundDirs)
        # -- -- --
                
                
                
        vSpacer = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Maximum)
        loadProjectBlockLayout.addItem(vSpacer)
        
                
        # -- -- --
        
        
        self.newProjectButton = QPushButton('Save & Open New Project', self)
        self.newProjectButton.setToolTip('Save scanned directory images as new project')
        self.newProjectButton.clicked.connect(self.newProjectButton_onClick)
        loadProjectBlockLayout.addWidget(self.newProjectButton)
        
        # -- -- --
        # -- -- --
        # -- -- --
                
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Set Final Self.Geometry Settings
        
        self.setGeometry( self.managerInitPos[0], self.managerInitPos[1], self.managerInitSize[0], self.managerInitSize[1] )
        
    
    @QtCore.pyqtSlot()
    def projectName_editingFinished(self):
        
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def loadScanDirButton_onClick(self):
        print( "Load Project" )
        selectedFolder = self.openFolderDialog()
        if selectedFolder :
            self.scanDirWidget.setText(selectedFolder)
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def scanDirButton_onClick(self):
        print( "Scan Dir... " )
        sourceImgPath = self.scanDirWidget.text()
        if sourceImgPath and os.path.isdir(sourceImgPath):
            self.dirOrder = []
            self.imageList = {}
            self.foundFileCount=0
            self.scanDir(sourceImgPath)
            print("Found ",self.foundFileCount," images.")
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def loadButton_onClick(self):
        self.loadProject()
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def newProjectButton_onClick(self):
        print( "New Project" )
        
        self.projectName = self.projectNameWidget.text()
        print( "Making the project '",self.projectName,"'" )
        
        self.projectPath = os.path.join(ImageLabelerScriptDir, self.projectRootDirName, self.projectName)
        self.projectPath = self.projectPath.replace("/", delimiter)
        
        self.fileDataJsonPath = os.path.join(self.projectPath, self.fileDataJsonName)
        self.settingsJsonPath = os.path.join(self.projectPath, self.settingsJsonName)
        
        self.saveProjectData()
        #self.projectNameWidget
        self.loadProject()#self.curProjectData)
        self.setFocus()
    
    @QtCore.pyqtSlot()
    def projectList_onItemDoubleClick(self):
        curItem = self.foundProjectsList.currentItem()
        curProjectName = curItem.text()
        print( curProjectName )
        #curItem = self.foundProjectsList.currentItem()
        #self.rebuildFileList(curWidget.fullPath)
        self.setFocus()
        
        
    @QtCore.pyqtSlot()
    def foundProjectsList_onSelectionChanged(self):
        curItem = self.foundProjectsList.currentItem()
        curProjectName = curItem.text()

        
        self.projectName = curProjectName
        self.projectPath = self.existingProjects[curProjectName]['ProjectPath']
        self.fileDataJsonPath = self.existingProjects[curProjectName]['ProjectDataJsonPath']
        self.settingsJsonPath = self.existingProjects[curProjectName]['SettingsJsonPath']
        
        
        if self.curSelectedProjectText:
            self.curSelectedProjectText.setText( self.projectName )
        #curItem = self.fileList.currentItem()
        #curWidget = self.fileList.itemWidget(curItem)
        #self.loadImageFile( curWidget.fullPath, False )
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def foundProjectsList_onItemDoubleClick(self):
        self.loadProject()
        """
        # Verify if no item selected, dunno how this would trigger without it already being selected
        #   But maybe a case, dunno
        curItem = self.foundProjectsList.currentItem()
        curProjectName = curItem.text()

        self.curSelectedProjectText.setText( curProjectName )
        
        self.projectName = curProjectName
        self.projectPath = self.existingProjects[curProjectName]['ProjectPath']
        self.fileDataJsonPath = self.existingProjects[curProjectName]['ProjectDataJsonPath']
        self.settingsJsonPath = self.existingProjects[curProjectName]['SettingsJsonPath']
        """
                    
        #curItem = self.fileList.currentItem()
        #curWidget = self.fileList.itemWidget(curItem)
        #self.loadImageFile( curWidget.fullPath, False )
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def verifyImagesButton_onClick(self):
        print(" Verify Images Exist ")
        #curItem = self.foundProjectsList.currentItem()
        #self.rebuildFileList(curWidget.fullPath)
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def cullEmptyFoldersButton_onClick(self):
        print(" Cull Empty Folders ")
        self.loadProjectData()
        
        #self.imageList=data['imageList']
        # Ordered Director List
        #=data['dirOrder']
        
        dirCount = 0
        dirRemovedCount = 0
        newDirOrder = []
        for x,curFolder in enumerate( self.dirOrder ):
            if curFolder not in self.imageList or len(self.imageList[curFolder])==0 :
                dirRemovedCount += 1
                #print( x,"; Caught Empty Folder - ",curFolder )
                #print( os.listdir( curFolder ) )
                if curFolder in self.imageList :
                    del self.imageList[curFolder]
            else:
                newDirOrder.append( curFolder )
        
        print( "Removed ",dirRemovedCount," folders.")
        print( "Total new folder count - ", len(curFolder) )
        
        self.dirOrder = newDirOrder
        
        self.saveProjectData()
        
        self.setFocus()
        
    # -- -- --
    
    def browseToPath(self, fullPath=None):
        if fullPath :
            browserPath = os.path.realpath( fullPath )
            os.startfile( browserPath )
        else:
            print("Can't locate '",fullPath,"'")
            
    # -- -- --
        
    def openFolderDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialogFolder = QFileDialog.getExistingDirectory(self,"Select Image Root Director to Scan Through", options=options)
        
        dialogFolder = dialogFolder.replace("/", delimiter)
        
        return dialogFolder
    


    def loadProject(self):
        print(self.fileDataJsonPath)
        self.loadProjectData()
        if len(self.dirOrder) > 0 :
            
            self.createMenuBar()
            self.createStatusBar()
            
            
            toGeoSize = self.projectLoadMinSize.copy()
            # -- -- --
            toGeoPos = self.projectLoadMinSize.copy()
            toGeoPos[0] = int( self.screenCenter[0] - toGeoSize[0]*.5 )
            toGeoPos[1] = int( self.screenCenter[1] - toGeoSize[1]*.5 )
            # -- -- --
            self.setGeometry( toGeoPos[0], toGeoPos[1], toGeoSize[0], toGeoSize[1] )

            self.loadProjectBlockWidget.setParent(None)
            
            self.showStatus( "Loading Project - "+self.projectName, 1 )
            
            self.update()
            QApplication.processEvents()
            
            # -- -- --
            
            self.projectWidget = ImageLabelerProject( parent=self, outputPath = self.projectPath )
            
            #self.mainLayout.addWidget(self.projectWidget)
            self.curProjectBlockLayout.addWidget(self.projectWidget)
            #self.setCentralWidget(self.projectWidget)
            self.projectWidget.setupUI()
            
            
            self.showStatus( "Loaded Project - "+self.projectName )
            
            #self.curProjectBlockWidget.setSizeHint(self.projectWidget.sizeHint())
            
            #print(self.curProjectBlockWidget.geometry())
            #print(self.projectWidget.geometry())
            #print(self.curProjectBlockWidget.geometry())
            #print(self.curProjectBlockLayout.geometry())

            #print(" Finished Loading ", self.projectName )
            
            #curGeo = self.geometry()
            #self.setGeometry( curGeo.x(), curGeo.y(), max(self.projectLoadMinSize[0],curGeo.width()), max(self.projectLoadMinSize[1],curGeo.height()) )
        
        #self.projectName = curProjectName
        #self.projectPath = self.existingProjects[curProjectName]['ProjectPath']
        #self.fileDataJsonPath = self.existingProjects[curProjectName]['ProjectDataJsonPath']
        #self.settingsJsonPath = self.existingProjects[curProjectName]['SettingsJsonPath']
        #

    def setProjectViewGeometry( self, x, y, w, h ):
        #self.setGeometry( x, y, w, h )
        
        self.curProjectBlockWidget.setMinimumWidth(700)
        self.curProjectBlockWidget.setMinimumHeight(1000)
        self.curProjectBlockWidget.resize( w, h )
        

    def loadProjectData(self):
        if os.path.exists(self.fileDataJsonPath):
            with open(self.fileDataJsonPath) as json_file:
                data = json.load(json_file)
                
                self.imageList=data['imageList']
                # Ordered Director List
                self.dirOrder=data['dirOrder']
            print("Loaded Json; Folder Count - ",len(self.dirOrder))
        else:
            print("Project Data File Not Found")

    def saveProjectData(self):
            
        if not os.path.isdir( self.projectPath ) :
            os.mkdir( self.projectPath )
            
        jsonOut={"imageList":self.imageList,"dirOrder":self.dirOrder}


        f = open( self.fileDataJsonPath, "w")
        f.write(json.dumps(jsonOut, indent = 2))
        f.close()
        
        print("Project Data Json Updated")
            

        
    def scanDir(self, imagePath=""):
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
                    "fileData":{}
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
                
    def resizeEvent(self, event):
        if self.projectWidget :
            self.projectWidget.resize()
        #QtCore.QMainWindow.resizeEvent(self, event)
        
        

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
        self.infoTextBlockLayout.setContentsMargins(5,0,0,0)
        self.infoTextBlockLayout.setSpacing(2)
        self.folderNameLabel = QLabel()
        self.fileNameLabel = QLabel()
        self.infoTextBlockLayout.addWidget(self.folderNameLabel)
        self.infoTextBlockLayout.addWidget(self.fileNameLabel)
        
        self.fileItemBlockLayout = QHBoxLayout()
        self.fileItemBlockLayout.setContentsMargins(0,0,0,10)
        self.fileItemBlockLayout.setSpacing(1)
        self.dispImageLabel = QLabel()
        self.imageCountLabel = QLabel()
        self.imageCountLabel.setAlignment(QtCore.Qt.AlignRight)
        self.fileItemBlockLayout.addWidget(self.dispImageLabel, 0)
        self.fileItemBlockLayout.addLayout(self.infoTextBlockLayout, 1)
        self.fileItemBlockLayout.addWidget(self.imageCountLabel, 2)
        self.setLayout(self.fileItemBlockLayout)
        # setStyleSheet
        self.folderNameLabel.setStyleSheet('''
            font-style: italic;
            color: rgb(0, 0, 255);
        ''')
        self.fileNameLabel.setStyleSheet('''
            font-size : 110%;
            font-weight : bold;
            color : rgb(200, 0, 120);
        ''')
        self.imageCountLabel.setStyleSheet('''
            font-size : 110%;
            font-weight : bold;
            color : rgb(200, 0, 120);
        ''')

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
        self.infoTextBlockLayout.setContentsMargins(5,0,0,0)
        self.infoTextBlockLayout.setSpacing(2)
        self.folderNameLabel    = QLabel()
        self.fileNameLabel  = QLabel()
        self.infoTextBlockLayout.addWidget(self.folderNameLabel)
        self.infoTextBlockLayout.addWidget(self.fileNameLabel)
        
        self.fileItemBlockLayout  = QHBoxLayout()
        self.fileItemBlockLayout.setContentsMargins(0,0,0,10)
        self.fileItemBlockLayout.setSpacing(1)
        self.dispImageLabel      = QLabel()
        self.fileItemBlockLayout.addWidget(self.dispImageLabel, 0)
        self.fileItemBlockLayout.addLayout(self.infoTextBlockLayout, 1)
        self.setLayout(self.fileItemBlockLayout)
        # setStyleSheet
        self.folderNameLabel.setStyleSheet('''
            font-style: italic;
            color: rgb(0, 0, 255);
        ''')
        self.fileNameLabel.setStyleSheet('''
            font-size : 110%;
            font-weight : bold;
            color : rgb(200, 0, 120);
        ''')

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
        
class ImageLabelerProject(QWidget):
    def __init__( self, parent = None, outputPath = "Default" ):
        #super(ImageLabelerWindow, self).__init__(*args)
        super(ImageLabelerProject, self).__init__(parent)
        self.manager = parent
        
        
        self.mouseLocked = False
        self.mousePos = None
        self.mouseDelta = QtCore.QPoint(0,0)
        
        # Self Geometry Store
        self.geometryStore = None
        # Lower Shelf Geometry Store ... Eh.... I'll fix this later
        self.lShelfGeometryStore = None
        self.ulShelfAdjustLocked = False
        
        # Minimum size of Lower Shelf
        self.minLowShelfSize = 150
        
        self.resizeTimer = QtCore.QTimer(self)
        self.resizeTimer.setSingleShot(True)
        
        self.folderList = None
        self.fileList = None
        self.rawImageWidget = None
        self.curFileObject = None
        self.curPromptField = None
        self.curFolderPath = None
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

    # -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # -- User Interaction Helper Functions - -- --
    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    
    def keyPressEvent(self, event):
        #print(event)
        if event.key() == QtCore.Qt.Key_Delete :
            ret = QMessageBox.question(self,'', "Delete current image from disk?", QMessageBox.Yes | QMessageBox.No)
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
        # setting up the geometry
        pad = 15
 
        # image path
        imgPath = "assets/foundFacesTemp.jpg"
 
        imgExt = imgPath.split(".")[-1]
 
        # loading image
        imgData = open(imgPath, 'rb').read()
        
        pixmap = self.cropImage(
            imgData = imgData,
            imgType = imgExt,
            size = 512
        )
        
        pixres = [pixmap.width()*4, pixmap.height()*3]
        pixoffset = [240, 180]
    
    

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
        self.currentFileBlockWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding )
        upperShelfLayout.addWidget(self.currentFileBlockWidget)

        # Block 3
        currentDataBlock = QWidget()
        currentDataBlockLayout = QHBoxLayout()
        currentDataBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        currentDataBlockLayout.setContentsMargins(0,0,0,0)
        currentDataBlockLayout.setSpacing(1)
        currentDataBlock.setLayout(currentDataBlockLayout)
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
        rawImagePromptBarLayout.setAlignment(QtCore.Qt.AlignCenter)
        rawImagePromptBarLayout.setContentsMargins(1,1,1,1)
        rawImagePromptBarLayout.setSpacing(2)
        rawImagePromptBarBlock.setLayout(rawImagePromptBarLayout)
        currentFileBlockLayout.addWidget(rawImagePromptBarBlock)
        # -- -- --
        rawImagePromptLabelWidget = QLabel(" Image Prompt - ")
        rawImagePromptLabelWidget.setFont(QtGui.QFont("Tahoma",10,QtGui.QFont.Bold))
        #rawImagePromptLabelWidget.setMinimumWidth( 100 )
        #rawImagePromptLabelWidget.setMinimumHeight( 30 )
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
        self.generateImagePromptButton = QPushButton('Generate Image Prompt', self)
        self.generateImagePromptButton.setToolTip('Create Prompt from Image, BLIP Img2Txt')
        self.generateImagePromptButton.clicked.connect(self.generateImagePromptButton_onClick)
        rawImagePromptBarLayout.addWidget(self.generateImagePromptButton)
        # -- -- --
        self.findFaceButton = QPushButton('Find Faces in Photo', self)
        self.findFaceButton.setToolTip('Auto Find Faces in current image; Face Helper')
        self.findFaceButton.clicked.connect(self.findFaceButton_onClick)
        rawImagePromptBarLayout.addWidget(self.findFaceButton)
        # -- -- --
        
        # -- -- --
        # -- -- --
        # -- -- --
        self.rawImageBlockWidget = QWidget()
        rawImageBlockLayout = QHBoxLayout()
        rawImageBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        rawImageBlockLayout.setContentsMargins(1,1,1,1)
        rawImageBlockLayout.setSpacing(2)
        self.rawImageBlockWidget.setLayout(rawImageBlockLayout)
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Ignored )
        currentFileBlockLayout.addWidget(self.rawImageBlockWidget)
        #self.rawImageBlockWidget.setMinimumHeight( 512 )
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Fixed )
        #self.rawImageBlockWidget.setSizePolicy( QSizePolicy.Ignored, QSizePolicy.Minimum )
        
        self.rawImageWidget = QLabel(self)
        self.rawImageWidget.setPixmap(pixmap)
        #self.rawImageWidget.resize( 512, 512 )
        self.rawImageWidget.setMinimumWidth( 10 )
        self.rawImageWidget.setMinimumHeight( 512 )
        self.rawImageWidget.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Minimum )
        rawImageBlockLayout.addWidget(self.rawImageWidget)
        
        
        
        # -- -- --

        self.curImageButtonBlock = QWidget()
        self.curImageButtonBlock.setFixedHeight(30)
        curImageButtonLayout = QHBoxLayout()
        curImageButtonLayout.setAlignment(QtCore.Qt.AlignCenter)
        curImageButtonLayout.setContentsMargins(1,1,1,1)
        curImageButtonLayout.setSpacing(2)
        self.curImageButtonBlock.setLayout(curImageButtonLayout)
        currentFileBlockLayout.addWidget(self.curImageButtonBlock)
        
        removeImageEntryButton = QPushButton('Remove Entry From Project', self)
        removeImageEntryButton.setToolTip('Removes image from project,\n File is kept on disk.')
        removeImageEntryButton.clicked.connect(self.removeImageEntryButton_onClick)
        curImageButtonLayout.addWidget(removeImageEntryButton)
        
        removeDeleteImageButton = QPushButton('Remove & Delete Image', self)
        removeDeleteImageButton.setToolTip('Removes image from project,\n File is deleted from disk.')
        removeDeleteImageButton.clicked.connect(self.removeDeleteImageButton_onClick)
        curImageButtonLayout.addWidget(removeDeleteImageButton)
        
        curImageButtonLayout.addStretch(1)
        
        # -- -- --
        self.generateAllImagePromptButton = QPushButton('Generate ALL Image Prompts', self)
        self.generateAllImagePromptButton.setToolTip('Create Prompts from ALL Images, BLIP Img2Txt')
        self.generateAllImagePromptButton.clicked.connect(self.generateAllImagePromptButton_onClick)
        curImageButtonLayout.addWidget(self.generateAllImagePromptButton)
        
        curImageButtonLayout.addStretch(1)
        
        self.findAllFacesButton = QPushButton('Find ALL Faces', self)
        self.findAllFacesButton.setToolTip('Auto Find Faces in ALL Images; Face Helper')
        self.findAllFacesButton.clicked.connect(self.findAllFacesButton_onClick)
        curImageButtonLayout.addWidget(self.findAllFacesButton)
        
        curImageButtonLayout.addStretch(1)
        
        self.updateCropButton = QPushButton('Update GL Crop Window', self)
        self.updateCropButton.setToolTip('Load Image into GL Crop Window')
        self.updateCropButton.clicked.connect(self.updateCropButton_onClick)
        curImageButtonLayout.addWidget(self.updateCropButton)
        
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
        
        glSaveRenderPath = os.path.join( ImageLabelerScriptDir, "ViewportGLSaves" )
        
        self.glSmartBlur = ViewerGL.ViewportWidget(self,0,"smartBlur", "assets/glEdgeFinder_tmp1_alpha.png", saveImagePath=glSaveRenderPath )
        #self.glSmartBlur.resize( pixres[0], pixres[1] )
        self.glBlockLayout.addWidget(self.glSmartBlur)
        self.glSmartBlur.imageOffset(pixres[0], pixres[1])
        # -- -- --
        self.glEdgeFinding = ViewerGL.ViewportWidget(self,1,"edgeDetect", "assets/glEdgeFinder_tmp2_alpha.png", saveImagePath=glSaveRenderPath )
        #self.glEdgeFinding.resize( pixres[0], pixres[1] )
        self.glBlockLayout.addWidget(self.glEdgeFinding)
        self.glEdgeFinding.imageOffset(pixres[0], pixres[1])
        # -- -- --
        self.glSegmentation = ViewerGL.ViewportWidget(self,2,"segment", "assets/glSegmentation_tmp1_alpha.png", saveImagePath=glSaveRenderPath )
        #self.glSegmentation = ViewerBufferGL.ViewportBufferWidget(self,2,"segment", "assets/glSegmentation_tmp1_alpha.png" )
        #self.glSegmentation.resize( pixres[0], pixres[1] )
        self.glBlockLayout.addWidget(self.glSegmentation)
        self.glSegmentation.imageOffset(pixres[0], pixres[1])
        # -- -- --
        self.glTexture = ViewerGL.ViewportWidget(self,3,"default", saveImagePath=glSaveRenderPath )
        #self.glTexture.resize( pixres[0], pixres[1] )
        self.glBlockLayout.addWidget(self.glTexture)
        self.glTexture.imageOffset(pixres[0], pixres[1])
        
        
        # -- -- --
        
        
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
        addClassifierButton.clicked.connect(self.addClassifierButton_onClick)
        glSettingsBlockLayout.addWidget(addClassifierButton)
        # -- -- --
        cropButtonsBlockLayout.addStretch(1)
        # -- -- --
        self.saveCropButton = QPushButton('Save Crop', self)
        self.saveCropButton.setToolTip('Save cropped image above')
        self.saveCropButton.clicked.connect(self.saveCropButton_onClick)
        glSettingsBlockLayout.addWidget(self.saveCropButton)
        # -- -- --
        cropButtonsBlockLayout.addStretch(1)
        
        
        # -- -- --
        
        # -- -- --
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Set Final Self.Geometry Settings
        geopos = [ 0, 0 ]
        geosize = [ pixres[0] + pixres[0] + pixoffset[0]*2, pixres[1]+pixoffset[1]*2+pad*2 ]
        #self.setGeometry( geopos[0], geopos[1], geosize[0], geosize[1] )
        #self.manager.setProjectViewGeometry( geopos[0], geopos[1], geosize[0], geosize[1] )
        
        # Trip first item's onClick
        self.fileList_onSelectionChanged()
        
        #timer = QtCore.QTimer(self)
        #timer.timeout.connect(self.glTexture.update) 
        #timer.start(1000)
        
        # Connect Resize Timer Function
        self.resizeTimer.timeout.connect(self.fitRawResizeTimeout) 
    
        self.geometryStore = self.geometry()
        print( self.geometryStore )
    
    def resize(self):
        self.fitRawPixmapToView(True)
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
        import utils.ImageToPrompt as i2p
        #self.imagePrompter = "BLIP"
        #self.imagePromptFinder = None
        modelsDir = os.path.join( ImageLabelerScriptDir, "weights" )
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
        print( curWidget.fileName," -- " )
        print("  ",foundPrompt)
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
            import utils.FaceFinder as ff
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
        if self.glTexture != None :
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
        if curWidget:
            self.curFolderPath = curWidget.fullPath
            self.rebuildFileList(curWidget.fullPath)
        else:
            print("Failed to find current Folter Item")
        self.setFocus()
    
        
    @QtCore.pyqtSlot()
    def folderList_onItemDoubleClick(self):
        curItem = self.folderList.currentItem()
        curWidget = self.folderList.itemWidget(curItem)
        if curWidget:
            self.curFolderPath = curWidget.fullPath
            self.rebuildFileList(curWidget.fullPath)
        else:
            print("Failed to find current Folter Item")
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def fileList_onSelectionChanged(self):
        self.loadSelectedFile(False)
    @QtCore.pyqtSlot()
    def fileList_onItemDoubleClick(self):
        self.loadSelectedFile(True)
        
    def loadSelectedFile(self, loadToGL = False):
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        self.curFileObject = curWidget 
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
                print("Deleting ImageFile from Disk - ")
                print(fullPath)
                del self.manager.imageList[folderPath][curFileItemRow]
                if len( self.manager.imageList[folderPath] ) == 0:
                    del self.manager.imageList[folderPath]
                    print("Deleting Folder from Disk - ")
                    print(folderPath)
            else:
                print("ImageList <> DirectoryListing missmatch detected,\n Not deleting file or folder - ")
                print(folderPath)
                print(fullPath)
                deleteFileOnDisk = False
            print("SAVE DATA")
            self.manager.saveProjectData()
        
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