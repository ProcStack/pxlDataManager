
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

import scripts.utils.UserSettingsManager as pxlSettings
import scripts.pxlDataProject as pxlDataProject

# -- -- --


# See 'TODOs.md' for current scripts states


# -- -- --

# 'os' doesn't always handle extensions or other path specific needs correctly
#   Reference delimiter where needed
delimiter = "/"
if platform.system() == 'Windows':
    delimiter = "\\"

# -- -- --

ImageLabelerAbsPath = os.path.abspath(__file__)
ImageLabelerScriptDir = os.path.dirname(ImageLabelerAbsPath)

ImageLabelerActiveProject = "No Project Loaded"
ImageLabelerProjectData = {}


# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --

# Project Outputs are in './Projects'
#   Might be nice having Custom Output paths
class ImageDataProjectManager(QMainWindow):
    def __init__(self, screenRes=[600,450], settingsManager=None, *args):
        super(ImageDataProjectManager, self).__init__(*args)
        
        
        self.settings = settingsManager
        self.setStyle(QStyleFactory.create('Fusion'))
        
        # TODO : Read CSS assets folder
        self.styleFiles = {}
        self.styleFiles['Light'] = "assets/StyleSheets/Light.css"
        self.styleFiles['Dark'] = "assets/StyleSheets/Dark.css"
        self.styleSheets = {}
        self.activeStyle = self.settings.read( "AppActiveStyle", "Light" )
        self.activeStyleMenuItem = None
        
        # TODO : Setup Framlessness for Title Bar style
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        
        self.menuBar = None
        self.statusBar = None
        # Look into QtWidgets.QToolBar
        
        self.mouseLocked = False
        self.mouseMoved = False

        self.screenRes = screenRes
        self.screenCenter = [int(screenRes[0]*.5), int(screenRes[1]*.5)]
        
        self.managerInitSize = [ 600, 450 ]
        self.managerInitSize = self.settings.read( "managerInitSize", self.managerInitSize )
        
        self.managerInitPos = [
            int( self.screenCenter[0] - self.managerInitSize[0]*.5 ),
            int( self.screenCenter[1] - self.managerInitSize[1]*.5 )
        ]
        self.managerInitPos = self.settings.read( "managerInitPos", self.managerInitPos )
        
        defaultProjectLoadSize = [ int(self.screenRes[0]*.75), int(self.screenRes[1]*.75) ]
        self.projectLoadMinSize = self.settings.read( "projectLoadMinSize", defaultProjectLoadSize )
        self.projectLoadFullScreen = self.settings.read( "projectLoadFullScreen", False )

        #self.projectLoadMinWidth = [min( screenRes[0], 1000 ),min( screenRes[1], 700 )]
        
        
        self.sourceDir = ""
        self.outputDir = ""
        
        
        self.previousProjectName = self.settings.read( "previousProjectName", "" )
        
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
        # TODO : Add checkbox in Manager window for this option
        self.bypassEmptyAndFoldersOnly = self.settings.read( "bypassEmptyAndFoldersOnly", True )
        
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
        
        # TODO : Needs implementation in for-loops and AI processes
        self.exiting = False
        
        
        self.settings.save()

        
    # TODO : Check if OpenGL textures, FBOs, VBOs, and programs need unbinding & deletion prior to exit 
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            print("Project Manager; Enter Key")
            self.proceed()
        elif event.key() == QtCore.Qt.Key_Escape:
            print( "Exiting" )
            self.exiting = True
            self.settings.save()
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
        fileMenu.addSeparator()
        # -- -- --
        self.openProjectAction = QAction("Open Project", self)
        fileMenu.addAction(self.openProjectAction)
        #self.openProjectAction.triggered.connect( self.menu_file_newProject )
        # -- -- --
        self.saveProjectFolderAction = QAction("Save Project", self)
        fileMenu.addAction(self.saveProjectFolderAction)
        self.saveProjectFolderAction.triggered.connect( self.menu_file_saveProject )
        # -- -- --
        fileMenu.addSeparator()
        # -- -- --
        # TODO : Add Recent Projects List
        # -- -- --
        self.openProjectFolderAction = QAction("Open Project Folder in Explorer", self)
        fileMenu.addAction(self.openProjectFolderAction)
        self.openProjectFolderAction.triggered.connect( self.menu_file_openFolderInExplorer )
        # -- -- --
        # -- -- --
        fileMenu.addSeparator()
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
        setStylesMenu = QMenu("Set Style Profile ...", self)
        optionsMenu.addMenu( setStylesMenu )
        
 
        # creating a action group
        styleActionGroup = QActionGroup(self)
        styleActionGroup.setExclusive( True )
        
        #def findStyleSheetFiles(self, path="assets/StyleSheets"):
        #def createStyleSheetMenu(self):
        for s in self.styleFiles:
            styleEntryName = s
            styleEntryPath = self.styleFiles[s]
            
            styleEntryAction = QAction( styleEntryName, self )
            styleEntryAction.setCheckable(True)
            styleEntryAction.triggered.connect(partial(self.loadStyleSheets,styleEntryName,styleEntryPath))
            
            
            self.styleSheets[ s ]={}
            self.styleSheets[ s ]['menuItem'] = styleEntryAction
            
            setStylesMenu.addAction( styleEntryAction )
            styleActionGroup.addAction(styleEntryAction)

        
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
        self.settings.save()
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
        
    def findStyleSheetFiles(self, path="assets/StyleSheets"):
        return;
        
    def createStyleSheetMenu(self):
        if len(self.styleFiles) == 0:
            self.findStyleSheetFiles()
        #self.styleFiles
        
        
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
            # Changes set by '#identifiers' in './assets/StyleSheets' css files
            toName = f"importance_{importance}"
            self.statusBar.setObjectName( toName )
            self.statusBar.style().unpolish( self.statusBar )
            self.statusBar.style().polish( self.statusBar )
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
    
    # TODO : Add 'toStylePath' support
    def loadStyleSheets( self, toStyleName, toStylePath = None ):
        # Use `.setObjectName()` for css #id specific css
        curStyle = ""
        if toStyleName not in self.styleSheets or 'style' not in self.styleSheets[toStyleName] :
            cssFile = self.styleFiles[toStyleName]
            f = open(cssFile,"r")
            curStyle = f.read()
            #self.styleSheets[ toStyleName ] = curStyle
            #self.styleSheets[ toStyleName ]['style'] = curStyle
        else:
            curStyle = self.styleSheets[ toStyleName ]
            
        self.setStyleSheet( curStyle ) 
        
        self.activeStyle = self.settings.set( "AppActiveStyle", toStyleName )
        
        #if self.projectWidget :
        #    self.projectWidget.fileList.verticalScrollBar().setStyleSheet("QScrollBar{background:#000000;}")
        self.showStatus( "Loaded '"+toStyleName+"' Style Profile" )

    def setupUI(self):
            
        self.setWindowTitle("Image & AI Labeling Tools")
        
        self.loadStyleSheets( self.activeStyle )
        
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
        currentSelection = 0
        projectsRootDir = os.path.join(ImageLabelerScriptDir, self.projectRootDirName)
        #print(projectsRootDir)
        if not os.path.isdir( projectsRootDir ) :
            print(" No '",self.projectRootDirName,"' folder found, making -\n  ",projectsRootDir)
            os.mkdir( projectsRootDir )
        projectsRootDirList=os.listdir(projectsRootDir)
        for x,curProjectDir in enumerate( projectsRootDirList ):
            curFullPath = os.path.join( projectsRootDir, curProjectDir )
            if os.path.isdir(curFullPath):
                projectDirFileList=os.listdir(curFullPath)
                if self.fileDataJsonName in projectDirFileList:
                    itemKeys.append( curProjectDir )
                    # -- -- --
                    if curProjectDir == self.previousProjectName :
                        currentSelection = x
                    # -- -- --
                    self.existingProjects[curProjectDir]={}
                    # -- -- --
                    self.existingProjects[curProjectDir]['ProjectPath'] = curFullPath
                    # -- -- --
                    pdJsonPath = os.path.join(curFullPath,self.fileDataJsonName)
                    self.existingProjects[curProjectDir]['ProjectDataJsonPath'] = pdJsonPath
                    # -- -- --
                    settingsJsonPath = os.path.join(curFullPath,self.settingsJsonName)
                    settingsJsonPath = settingsJsonPath if os.path.isfile( settingsJsonPath ) else None
                    self.existingProjects[curProjectDir]['SettingsJsonPath'] = settingsJsonPath
        # -- -- --
        if len(itemKeys) > 0:
            for project in itemKeys:
                QListWidgetItem( project, self.foundProjectsList )
            self.foundProjectsList.setCurrentRow( currentSelection )
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
        #print( "Load Project" )
        selectedFolder = self.openFolderDialog()
        if selectedFolder :
            self.scanDirWidget.setText(selectedFolder)
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def scanDirButton_onClick(self):
        #print( "Scan Dir... " )
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
        #print( "New Project" )
        
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
        #print( curProjectName )
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
        #print(" Verify Images Exist ")
        #curItem = self.foundProjectsList.currentItem()
        #self.rebuildFileList(curWidget.fullPath)
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def cullEmptyFoldersButton_onClick(self):
        #print(" Cull Empty Folders ")
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
        #print(self.fileDataJsonPath)
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
            
            self.projectWidget = pxlDataProject.ImageDataProject(
                parent = self,
                settingsManager = self.settings.newSubData('ImageDataProject'),
                dataManagmentRootPath = ImageLabelerScriptDir,
                outputPath = self.projectPath
            )
            

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
            
            self.settings.set( "previousProjectName", self.projectName )
            
        else:
            print("Project Data File Not Found")

    def saveProjectData(self):
            
        if not os.path.isdir( self.projectPath ) :
            os.mkdir( self.projectPath )
            
        jsonOut={"imageList":self.imageList,"dirOrder":self.dirOrder}


        f = open( self.fileDataJsonPath, "w")
        f.write(json.dumps(jsonOut, indent = 2))
        f.close()
        
        self.settings.save()
        
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
        
        


# main function
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
 
    settingsManager = pxlSettings.UserSettingsManager("userSettings")
    # app created
    #QApplication.setAttribute( QtCore.Qt.AA_ShareOpenGLContexts, True )
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    screenRes = screen.size()
    userScreenRes = [ screenRes.width(), screenRes.height() ]
    
    
    w = ImageDataProjectManager( userScreenRes, settingsManager )
    w.setupUI()
    w.show()
    
    #w = ImageLabelerWindow()
    #w.setupUI()
    #w.show()
    
    # begin the app
    sys.exit(app.exec_())