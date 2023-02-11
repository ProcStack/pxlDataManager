
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

import utils.FaceFinder as ff


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
    def __init__(self, *args):
        super(ImageLabelerProjectManager, self).__init__(*args)
        
        self.menuBar = None
        self.mouseLocked = False
        self.mouseMoved = False

        
        self.sourceDir = "_unprepped"
        self.outputDir = "OutputData"
        
        self.projectRootDirName = "Projects"
        self.projectName = "No Project Selected"
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
            'classifierJson':"",
            'name':"",
            'name':""
        }

        self.extList=["jpg","jpeg","gif","png", "bmp"]#, "svg"] # Check SVG, since it likes vector postions
        self.fileDataJsonName = "ProjectData.json"
        self.fileDataJsonPath = None # os.path.join(outputDir, self.fileDataJsonName)
        self.settingsJsonName = "ProjectSettings.json"
        self.settingsJsonPath = None # = os.path.join(outputDir, "Classifiers.json")

        self.sourceAbsDir = os.path.join(ImageLabelerScriptDir, self.sourceDir)


        # Images by Folder Path
        self.imageList={}
        # Ordered Director List
        self.dirOrder=[]
        self.foundFileCount=0
 
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
        self.setMenuBar(self.menuBar)
        
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
        self.scanDirWidget = QLineEdit()
        self.scanDirWidget.setAlignment(QtCore.Qt.AlignLeft)
        self.scanDirWidget.setFont(QtGui.QFont("Tahoma",12))
        self.scanDirBlockLayout.addWidget( self.scanDirWidget )
        # -- -- --
        self.loadScanDirButton = QPushButton('Find...', self)
        self.loadScanDirButton.setToolTip('Locate Folder to Scan for Images')
        self.loadScanDirButton.clicked.connect(self.loadScanDirButton_onClick)
        self.scanDirBlockLayout.addWidget(self.loadScanDirButton)
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
        geopos = [ 200, 200 ]
        geosize = [ 600, 450 ]
        self.setGeometry( geopos[0], geopos[1], geosize[0], geosize[1] )
        
    
    @QtCore.pyqtSlot()
    def projectName_editingFinished(self):
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        self.loadImageFile( curWidget.fullPath, False )
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
        #self.openFolderDialog()
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def loadButton_onClick(self):
        self.loadProject()
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def newProjectButton_onClick(self):
        print( "New Project" )
        #self.loadProject(self.curProjectData)
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
        
    def openFolderDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialogFolder = QFileDialog.getExistingDirectory(self,"Select Image Root Director to Scan Through", options=options)
        return dialogFolder
    


    def loadProject(self):
        print(self.fileDataJsonPath)
        self.loadProjectData()
        if len(self.dirOrder) > 0 :
            self.loadProjectBlockWidget.setParent(None)
            self.projectWidget = ImageLabelerProject( parent=self )
            
            #self.mainLayout.addWidget(self.projectWidget)
            self.curProjectBlockLayout.addWidget(self.projectWidget)
            #self.setCentralWidget(self.projectWidget)
            self.projectWidget.setupUI()
            
            #self.curProjectBlockWidget.setSizeHint(self.projectWidget.sizeHint())
            
            #print(self.curProjectBlockWidget.geometry())
            print(self.projectWidget.geometry())
            #print(self.curProjectBlockWidget.geometry())
            #print(self.curProjectBlockLayout.geometry())

            print(" Finished Loading ", self.projectName )
        
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
            #scanDir(self.sourceAbsDir)

            #print("Found File Count - ",self.foundFileCount)
            
            jsonOut={"imageList":self.imageList,"dirOrder":self.dirOrder}


            f = open( self.fileDataJsonPath, "w")
            f.write(json.dumps(jsonOut, indent = 2))
            f.close()
            
            print("Project Data Json Updated")
            

        
    def scanDir(self, imagePath=""):
        if imagePath != "":
            activeList=[]
            if os.path.isdir(imagePath):
                self.dirOrder.append(imagePath)
                self.imageList[imagePath]=[]
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
                        scanDir( curFullPath )
                    else:
                        curExt=x.split(".")[-1]
                        if curExt.lower() in extList:
                            self.foundFileCount+=1
                            curImageDict = defaultImageDict.copy()
                            curImageDict["fileName"]=x
                            curImageDict["filePath"]=curFullPath
                            curImageDict["folderName"]=parentFolder
                            curImageDict["folderPath"]=imagePath
                            self.imageList[imagePath].append(curImageDict)

    def resizeEvent(self, event):
        if self.projectWidget :
            self.projectWidget.resize()
        #QtCore.QMainWindow.resizeEvent(self, event)
        
        


vertex_code = '''

    #version 330

    in vec2 position;
    in vec2 uv;

    out vec3 newColor;
    out vec2 vUv;

    uniform mat4 transform; 

    void main() {

        gl_Position = vec4(position, 0.0f, 1.0f);
        newColor = vec3(uv.x, uv.y, 0.0f);
        vUv = uv;

    }
'''


fragment_code = '''
    #version 330

    uniform sampler2D samplerTex;
    uniform vec2 texOffset;
    uniform vec2 texScale;
    
    in vec3 newColor;
    in vec2 vUv;

    out vec4 outColor;

    void main() {
        vec2 scaledUv = vUv * texScale + texOffset;
        outColor = texture(samplerTex, scaledUv);

    }

'''

class TextureGLWidget(QtOpenGL.QGLWidget):
    def __init__(self,parent):
        QtOpenGL.QGLWidget.__init__(self,parent)
        # -- -- --
        self.displayImage = None
        self.runner = 0
        
        self.glProgram = None
        self.glUniformLocations = {}
        
        self.imgId = 0
        self.glTempTex = "glTempTex.jpg"
        self.imgData = {}
        self.curImage = ""
        
        self.curOffset=[0,0]
        self.curScale=[1,1]
        
        self.imgWidth=0
        self.imgHeight=0
        
        self.maxWidth = 512
        self.maxHeight = 512
        self.setMaximumWidth( self.maxWidth )
        self.setMaximumHeight( self.maxHeight )
        self.setFixedWidth( self.maxWidth )
        self.setFixedHeight( self.maxHeight )
        
        self.mouseLocked = False
        self.mouseMoved = False
        self.mouseOrigPos = None
        self.mouseLockedPos = None
        self.mouseDelta = None
        self.mouseOffsetFitted = None
        self.mouseScaleFitted = None
        self.mouseButton = 0

    def mouseMoveEvent(self, e):
        if self.mouseLocked :
            self.mouseLockedPos = e.pos()
            self.mouseDelta = self.mouseOrigPos - self.mouseLockedPos
            if self.mouseButton == 1:
                dX = float(self.mouseDelta.x()/self.maxWidth) * self.curScale[0] + self.curOffset[0]
                dY = float(self.mouseDelta.y()/self.maxHeight) * self.curScale[1] + self.curOffset[1]
                self.mouseOffsetFitted = [dX,dY]
                self.imageOffset(dX,dY,False)
            elif self.mouseButton == 3:
                dLen = math.sqrt(math.pow(float(self.mouseDelta.x()),2)+math.pow(float(self.mouseDelta.y()),2))
                dLen = dLen if self.mouseDelta.x()>0 else -dLen
                dLenX = dLen/float(self.maxWidth) * self.curScale[0]
                dLenY = dLen/float(self.maxHeight) * self.curScale[1]
                dX = dLenX + self.curScale[0]
                dY = dLenY + self.curScale[1]
                self.mouseScaleFitted = [dX,dY]
                self.imageScale(dX,dY,False)
                
                dXOff = -dLenX + self.curOffset[0]
                dYOff = -dLenY + self.curOffset[1]
                self.imageOffset(dXOff,dYOff,False)
                self.mouseOffsetFitted = [dXOff,dYOff]
                #print(self.mouseOrigPos)
                #print(self.mouseOffsetFitted)
            
            self.mouseMoved = True
            self.update()

    def mousePressEvent(self, e):
        self.mouseLocked = True
        self.mouseOrigPos = e.pos()
        
        if e.button() == QtCore.Qt.LeftButton:
            self.mouseButton = 1
        elif e.button() == QtCore.Qt.RightButton:
            self.mouseButton = 3

    def mouseReleaseEvent(self, e):
        self.mouseLocked = False
        if self.mouseMoved :
            if self.mouseButton == 1:
                self.imageOffset(self.mouseOffsetFitted[0],self.mouseOffsetFitted[1],True)
            elif self.mouseButton == 3:
                self.imageOffset(self.mouseOffsetFitted[0],self.mouseOffsetFitted[1],True)
                self.imageScale(self.mouseScaleFitted[0],self.mouseScaleFitted[1],True)
        self.mouseMoved = False
        

    def loadImage( self, filePath ):
        curImgData = self.loadImageTex2D( filePath )
        wFit = float( self.maxWidth / curImgData['width'] )
        hFit = float( self.maxHeight / curImgData['height'] )
        self.imageScale( wFit, hFit )
        
        #xOff = float(curImgData['width'])*.5 - float(self.maxWidth)*.5
        #yOff = float(curImgData['height'])*.5 - float(self.maxHei
        xOff = .5-wFit*.5
        yOff = .5-hFit*.5
        self.imageOffset( xOff, yOff )
        
        self.update()
        
    def loadImageTex2D(self, filename):
        img = None
        img_data = None
        if filename in self.imgData :
            img = self.imgData[filename]['image']
            img_data = self.imgData[filename]['data']
        else:
            img = Image.open(filename)
            img_data = np.array(list(img.getdata()), np.uint8)
            #self.imgData[filename] = {'image':img,'data':img_data}

        texture = gl.glGenTextures(1)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT,1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, img.size[0], img.size[1], 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, img_data)
        
        self.imgWidth=img.size[0]
        self.imgHeight=img.size[1]
        self.curImage = filename
        
        return {'width':img.size[0],'height':img.size[1],'data':texture}
    
    def initializeGL(self):
    
        program = gl.glCreateProgram()
        vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)

        # Set shaders source
        gl.glShaderSource(vertex, vertex_code)
        gl.glShaderSource(fragment, fragment_code)

        # Compile shaders
        gl.glCompileShader(vertex)
        if not gl.glGetShaderiv(vertex, gl.GL_COMPILE_STATUS):
            error = gl.glGetShaderInfoLog(vertex).decode()
            print("Vertex shader compilation error: ", error)

        gl.glCompileShader(fragment)
        if not gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS):
            error = gl.glGetShaderInfoLog(fragment).decode()
            print(error)
            raise RuntimeError("Fragment shader compilation error")

        gl.glAttachShader(program, vertex)
        gl.glAttachShader(program, fragment)
        gl.glLinkProgram(program)

        if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
            print(gl.glGetProgramInfoLog(program))
            raise RuntimeError('Linking error')

        # Shader not needed, free ram
        gl.glDetachShader(program, vertex)
        gl.glDetachShader(program, fragment)

        gl.glUseProgram(program)
        self.glProgram = program
        
        self.glUniformLocations = {
            'texOffset': gl.glGetUniformLocation( self.glProgram, 'texOffset' ),
            'texScale': gl.glGetUniformLocation( self.glProgram, 'texScale' )
        }
        
        gl.glUniform2f( self.glUniformLocations['texOffset'], 0, 0 )
        gl.glUniform2f( self.glUniformLocations['texScale'], 1, 1 )
        
        # Build data
        #data = np.zeros((4, 2), dtype=np.float32)
        # From another -
        data = np.zeros(4, [("position", np.float32, 2),("uv", np.float32, 2)])
        data['position'] = [(-1,+1), (+1,+1), (-1,-1), (+1,-1)]
        data['uv'] = [(0,0), (1,0), (0,1), (1,1)]

        indices = [0, 1, 2, 2, 3, 0]
        indices = np.array(indices, dtype=np.uint32)
        
        
        
        self.VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.itemsize * len(data), data, gl.GL_STATIC_DRAW)

        self.EBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.itemsize * len(indices), indices, gl.GL_STATIC_DRAW)
        

        stride = data.strides[0]
        offset = ctypes.c_void_p(0)
        loc = gl.glGetAttribLocation(program, "position")
        gl.glEnableVertexAttribArray(loc)
        gl.glVertexAttribPointer(loc, 2, gl.GL_FLOAT, False, stride, offset)
        
        
 
        texCoords = gl.glGetAttribLocation(program, "uv")
        gl.glVertexAttribPointer(texCoords, 2, gl.GL_FLOAT, False,  stride, ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(texCoords)
    
        self.displayImage = self.loadImageTex2D( self.glTempTex )
        
        gl.glEnable(gl.GL_TEXTURE_2D)
        
        
        gl.glViewport(0, 0, 512, 512) # Out res is [512,512] setting by default
        print("GL Init")
        
    def paintGL(self):
        #self.drawGL()
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        
    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)
    def fitBounds(self,bounds=None):
        if type(bounds) != type(None):
            overScale=1.2
            sizeXY = [ bounds[2]-bounds[0], bounds[3]-bounds[1] ]
            size=max(sizeXY[0],sizeXY[1])*overScale
            corner = [(bounds[0]+bounds[2])*.5 - size*.5,(bounds[1]+bounds[3])*.5 - size*.5]
            toOffsetX = corner[0]/self.imgWidth
            toOffsetY = corner[1]/self.imgHeight
            toScaleX = size/self.imgWidth
            toScaleY = size/self.imgHeight
            self.imageOffset( toOffsetX, toOffsetY )
            self.imageScale( toScaleX, toScaleY )
            self.update()
    def imageOffset(self,x,y, setOffset=True):
        if 'texOffset' in self.glUniformLocations :
            gl.glUniform2f( self.glUniformLocations['texOffset'], x, y )
            if setOffset :
                self.curOffset=[x,y]
    def imageScale(self,x,y, setScale=True):
        if 'texScale' in self.glUniformLocations :
            gl.glUniform2f( self.glUniformLocations['texScale'], x, y )
            if setScale :
                self.curScale=[x,y]
            
            
# -- -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- --

# I should probably be using QListView or QTreeView
#   But I'm incorrigible
class FolderListItem(QWidget):
    def __init__(self,parent = None):
        #super(TextureGLWidget,self).__init__()
        #QListWidgetItem.__init__(self,parent)
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
        parentFolderText = splitPath[-2]
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
    def __init__(self,parent = None):
        #super(TextureGLWidget,self).__init__()
        #QListWidgetItem.__init__(self,parent)
        super(FileListItem, self).__init__(parent)
        
        self.fullPath = ""
        self.fileName = ""
        self.folderName = ""
        self.folderPath = ""
        self.dispImagePath = ""
        self.data = []
        
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
    def __init__( self, parent = None ):
        #super(ImageLabelerWindow, self).__init__(*args)
        super(ImageLabelerProject, self).__init__(parent)
        self.manager = parent
        
        self.resizeTimer = QtCore.QTimer(self)
        self.resizeTimer.setSingleShot(True)
        
        self.folderList = None
        self.fileList = None
        self.rawImageWidget = None
        self.curRawPixmap = None
        
        
        
        # TODO : Handle FaceFinder object load & build dynamically for faster main program init
        self.faceFinder = ff.FaceFinder()
        self.inputPath = "cropped_faces"
        self.outputPath = "cropped_faces"
        self.outputFolder = "cropped_faces"
        
        self.projectDataJson = ""
        self.projectClassifierJson = ""
 
    def keyPressEvent(self, event):
        print(event)
        if event.key() in [QtCore.Qt.Key_A,QtCore.Qt.Key_Up,QtCore.Qt.Key_Left]:
            self.changeSelectedFile(-1)
            print("Prev Key")
        elif event.key() in [QtCore.Qt.Key_D,QtCore.Qt.Key_Down,QtCore.Qt.Key_Right]:
            self.changeSelectedFile(1)
            print("Next Key")
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
        
    def setupUI(self):
        # setting up the geometry
        pad = 15
 
        # image path
        imgPath = "foundFacesTemp.jpg"
 
        imgExt = imgPath.split(".")[-1]
 
        # loading image
        imgData = open(imgPath, 'rb').read()
        
        pixmap = self.cropImage(
            imgData = imgData,
            imgType = imgExt,
            size = 512
        )
        
        pixres = [pixmap.width(), pixmap.height()]
        pixoffset = [240, 180]
    
    

        #mainWidget = QWidget()
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.setSpacing(1)
        #mainWidget.setLayout(mainLayout)
        self.setLayout(mainLayout)
        #  Not needed when QWidget, uncomment for QMainWindow
        #self.setCentralWidget(mainWidget)
        
        """  __________
            |   |      |
            | 1 |  2   |
            |   |      |
            |----------|
            |   3  | 4 |
            |______|___|
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
        self.upperShelfWidget.setSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding )
        mainLayout.addWidget(self.upperShelfWidget)
        # -- -- --
        line = QLabel('', self)
        line.setMaximumHeight(1)
        line.setStyleSheet("background-color:#555555;")
        line.setContentsMargins(0,3,0,3)
        mainLayout.addWidget(line)
        # -- -- --
        # Lower Shelf, Block 3 & 4
        lowShelfWidget = QWidget()
        lowShelfWidget.setMinimumHeight(512)
        lowShelfWidget.setMaximumHeight(512)
        lowShelfLayout = QHBoxLayout()
        lowShelfLayout.setAlignment(QtCore.Qt.AlignCenter)
        lowShelfLayout.setContentsMargins(0,0,0,0)
        lowShelfLayout.setSpacing(1)
        lowShelfWidget.setLayout(lowShelfLayout)
        mainLayout.addWidget(lowShelfWidget)
        
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
        lowShelfLayout.addWidget(currentDataBlock)
        
        # -- -- --
        line = QLabel('', self)
        line.setMaximumWidth(5)
        line.setStyleSheet("background-color:#555555;")
        line.setContentsMargins(3,0,3,0)
        lowShelfLayout.addWidget(line)
        # -- -- --
        
        # Block 4
        glBlock = QWidget()
        glBlock.setMinimumWidth(512)
        glBlock.setMaximumWidth(512)
        glBlockLayout = QVBoxLayout()
        glBlockLayout.setAlignment(QtCore.Qt.AlignCenter)
        glBlockLayout.setContentsMargins(0,0,0,0)
        glBlockLayout.setSpacing(1)
        glBlock.setLayout(glBlockLayout)
        lowShelfLayout.addWidget(glBlock)
        
        
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
        
        #self.folderList.itemSelectionChanged.connect( self.folderList_onSelectionChanged )
        self.folderList.itemDoubleClicked.connect( self.folderList_onItemDoubleClick )
        
        # -- -- --
        
        # File List
        self.fileList = QListWidget(self)

        fileBlockLayout.addWidget(self.fileList)
        
        self.fileList.itemSelectionChanged.connect( self.fileList_onSelectionChanged )
        self.fileList.itemDoubleClicked.connect( self.fileList_onItemDoubleClick )
        
        curFolderPath = self.folderList.itemWidget(self.curFolderListItem).fullPath
        self.rebuildFileList(curFolderPath)
        
        # -- -- --
        """
        fileListButtonBlock = QWidget()
        fileListButtonBlock.setFixedHeight(30)
        fileListButtonLayout = QHBoxLayout()
        fileListButtonLayout.setAlignment(QtCore.Qt.AlignCenter)
        fileListButtonLayout.setContentsMargins(1,1,1,1)
        fileListButtonLayout.setSpacing(2)
        fileListButtonBlock.setLayout(fileListButtonLayout)
        currentFileBlockLayout.addWidget(fileListButtonBlock)
        
        delFileButton = QPushButton('Find Face', self)
        findFaceButton.setToolTip('Auto Find Face; Face Helper')
        findFaceButton.clicked.connect(findFaceButton_onClick)
        fileListButtonLayout.addWidget(findFaceButton)
        
        updateCropButton = QPushButton('Update Crop', self)
        updateCropButton.setToolTip('Auto Find Face; Face Helper')
        updateCropButton.clicked.connect(self.updateCropButton_onClick)
        fileListButtonLayout.addWidget(updateCropButton)
        """
    
    
        # -- -- -- -- -- -- -- -- -- -- --
        # Current File Layout Block
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
        
        self.findFaceButton = QPushButton('Find Face', self)
        self.findFaceButton.setToolTip('Auto Find Face; Face Helper')
        self.findFaceButton.clicked.connect(self.findFaceButton_onClick)
        curImageButtonLayout.addWidget(self.findFaceButton)
        
        curImageButtonLayout.addStretch(1)
        
        self.updateCropButton = QPushButton('Update GL Crop Window', self)
        self.updateCropButton.setToolTip('Load Image into GL Crop Window')
        self.updateCropButton.clicked.connect(self.updateCropButton_onClick)
        curImageButtonLayout.addWidget(self.updateCropButton)
        
        # -- -- --
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Current Found Image Data Block
        #   eg, Cropped Face & Aligned Crop Face
        
        faceImageAlignedBlock = QWidget()
        faceImageAlignedLayout = QVBoxLayout()
        faceImageAlignedLayout.setAlignment(QtCore.Qt.AlignCenter)
        faceImageAlignedLayout.setContentsMargins(1,1,1,1)
        faceImageAlignedLayout.setSpacing(2)
        faceImageAlignedBlock.setLayout(faceImageAlignedLayout)
        currentDataBlockLayout.addWidget(faceImageAlignedBlock)
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
        currentDataBlockLayout.addWidget(faceImageUnalignedBlock)
        # -- -- --
        self.faceUnalignedImage = QLabel(self)
        self.faceUnalignedImage.setPixmap(pixmap)
        self.faceUnalignedImage.resize( 512, 512 )
        faceImageUnalignedLayout.addWidget(self.faceUnalignedImage)
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Current GL Loaded File Layout Block
        #self.glTexture = TextureGLWidget(self)
        self.glTexture = TextureGLWidget(self)
        #self.glTexture.initializeGL()
        self.glTexture.resize( pixres[0], pixres[1] )
        #self.glTexture.move( pixoffset[0]+pixres[0] + pad, pixoffset[1] )
        #self.glTexture.update
        glBlockLayout.addWidget(self.glTexture)
        self.glTexture.imageOffset(pixres[0], pixres[1])
        # -- -- --
        self.outputClassifier = QListWidget()
        QListWidgetItem("Classifier1", self.outputClassifier)
        QListWidgetItem("Classifier2", self.outputClassifier)
        QListWidgetItem("Classifier3", self.outputClassifier)
        QListWidgetItem("Classifier4", self.outputClassifier)
        QListWidgetItem("Classifier5", self.outputClassifier)
        glBlockLayout.addWidget(self.outputClassifier)
        # -- -- --
        self.saveButton = QPushButton('Save Crop', self)
        self.saveButton.setToolTip('Save cropped image above')
        #self.saveButton.move( pixoffset[0]+pixres[0] + pad, pixres[1]+pixoffset[1]+pad )
        self.saveButton.clicked.connect(self.saveButton_onClick)
        glBlockLayout.addWidget(self.saveButton)
        
        
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
    
    
    def resize(self):
        self.fitRawPixmapToView(True)
        self.glTexture.update()
        
    @QtCore.pyqtSlot()
    def removeImageEntryButton_onClick(self):
        self.removeFileEntry(False, False, True)
            
    @QtCore.pyqtSlot()
    def removeDeleteImageButton_onClick(self):
        self.removeFileEntry(True, True, True)
        
            
    # FaceFinder is using numpy array data
    #   Should return all found faces as arrays, shouldn't be saving faces by default
    # TODO : Saving cropped & aligned faces when finding in FaceFinder
    #          Image saving should be handled in Main
    @QtCore.pyqtSlot()
    def findFaceButton_onClick(self):
        print('Find Face')
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        curImageFullPath = curWidget.fullPath
        detFaces,croppedFacePaths = self.faceFinder.input(curImageFullPath)
        if len(detFaces) > 0:
            pixmap = QtGui.QPixmap( croppedFacePaths[0] )
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
                bounds = detFaces[0],
                boundsScalar = 1.2
            )
        
            
            self.faceUnalignedImage.setPixmap(pixmap)
            outUnalignSplit = croppedFacePaths[0].split(".")
            outUnalignPath = f'{outUnalignSplit[0]}_unaligned.{imgext}'
            pixmap.save(outUnalignPath)
            
            """
            if self.glTexture.curImage != curImageFullPath:
                self.glTexture.loadImage( curImageFullPath )
            self.glTexture.fitBounds(detFaces[0][0:4])
            self.glTexture.update()
            
            baseImageNameExt = os.path.basename(curImageFullPath)
            baseImageName, ext = os.path.splitext(baseImageNameExt)
            
            curBuffer = self.glTexture.grabFrameBuffer(withAlpha=False)
            outFilePath = os.path.join(self.outputFolder, f'{baseImageName}_unaligned.png')
            print( outFilePath )
            curBuffer.save( outFilePath )
            """
        self.setFocus()
            
    @QtCore.pyqtSlot()
    def updateCropButton_onClick(self):
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        curImageFullPath = curWidget.fullPath
        self.glTexture.loadImage( curImageFullPath )
        self.setFocus()
            
    @QtCore.pyqtSlot()
    def saveButton_onClick(self):
        if self.glTexture != None :
            curBuffer = self.glTexture.grabFrameBuffer(withAlpha=False)
            curItem = self.outputClassifier.currentItem()
            curClassFolder = curItem.text()
            curClassPath = os.path.join(ImageLabelerScriptDir, self.outputFolder, curClassFolder)
            os.makedirs(curClassPath, exist_ok = True) 
            imgList=os.listdir(curClassPath)
            id = len(imgList)
            
            curClassPath = os.path.join(curClassPath, f'{curClassFolder}_{id:03d}.jpg')
            print("Saving to ",curClassPath)
            curBuffer.save(curClassPath)
        self.setFocus()
            
        
    """
    @QtCore.pyqtSlot()
    def folderList_onSelectionChanged(self):
        print('List Item Selection Changed')
        curItem = self.folderList.currentItem()
        curWidget = self.folderList.itemWidget(curItem)
        
        print( curWidget.fullPath )
        print( curWidget.fileName )
        print( curWidget.folderName )
        print( curWidget.dispImagePath )
    """
        
    @QtCore.pyqtSlot()
    def folderList_onItemDoubleClick(self):
        curItem = self.folderList.currentItem()
        curWidget = self.folderList.itemWidget(curItem)
        if curWidget:
            self.rebuildFileList(curWidget.fullPath)
        else:
            print("Failed to find current Folter Item")
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def fileList_onSelectionChanged(self):
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        if curWidget:
            self.loadImageFile( curWidget.fullPath, False )
        else:
            print("Failed to find current File Item")
        self.setFocus()
        
    @QtCore.pyqtSlot()
    def fileList_onItemDoubleClick(self):
        curItem = self.fileList.currentItem()
        curWidget = self.fileList.itemWidget(curItem)
        self.loadImageFile( curWidget.fullPath, True )
        self.setFocus()
        
    
    def rebuildFileList(self,folderPath=None):
        curFolderPath = folderPath
        if curFolderPath == None:
            curItem = self.folderList.currentItem()
            curWidget = self.folderList.itemWidget(curItem)
            curFolderPath = curWidget.fullPath
        
        # File List
        self.fileList.clear()
        self.curFileListItem = None
        for folderImageData in self.manager.imageList[curFolderPath]:
            # Create QCustomQWidget
            curFileItem = FileListItem()
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
            self.folderList_onItemDoubleClick()
            self.fileList.setCurrentRow(self.fileList.count()-1)
            self.fileList_onSelectionChanged()
        elif toValue>=self.fileList.count():
            value = self.folderList.currentRow()
            toValue = value+dir
            if toValue>=self.folderList.count():
                toValue = 0
            self.folderList.setCurrentRow(toValue)
            self.folderList_onItemDoubleClick()
        else:
            self.fileList.setCurrentRow( toValue )
        print(value)
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
        #curFileItem = self.fileList.takeItem(curFileItemRow)
        curFileWidget = self.fileList.itemWidget( curFileItem )
        # Current Folder
        folderListCount = self.folderList.count()
        curFolderItemRow = self.folderList.currentRow()
        curFolderItem = self.folderList.item( curFolderItemRow )
        print(folderListCount)
        print(curFolderItemRow)
        print(curFolderItem)
        curFolderWidget = self.folderList.itemWidget( curFolderItem )
        print(curFolderWidget)
        updatedImageCount = curFolderWidget.imageCount
        updatedImageCount -= 1
        
        
        
        curFolderWidget.setImageCount( updatedImageCount )
        
        if self.fileList.count() == 0:
            print( curFolderWidget.imageCount )
            
            toFolderRow = curFolderItemRow+1 if curFolderItemRow < folderListCount else max(0,curFolderItemRow-1)
            print( toFolderRow )
            #self.folderList.setCurrentRow(toFolderRow)
            #self.folderList_onItemDoubleClick()
        
        
        fileName = curFileWidget.fileName
        folderName = curFileWidget.folderName
        fullPath = curFileWidget.fullPath
        folderPath = curFileWidget.folderPath
        print( self.fileList.count()," - ", updatedImageCount )
        print( fileName )
        print( folderName )
        print( fullPath )
        print( folderPath )
        
        if deleteFileOnDisk :
            print( "Delete File on Disk" )
            print( fullPath )
            
        if saveProjectDataJson :
            
            print( curFileItemRow,"; " )
            print( self.manager.imageList[folderPath][curFileItemRow] )
            #self.manager.imageList[curFolderPath]
            print("SAVE DATA")
            #self.manager.saveProjectData()
        
        """
        value = self.folderList.currentRow()
        toValue = value+dir
        if toValue<0:
            toValue = self.folderList.count()-1
        self.folderList.setCurrentRow(toValue)
        self.folderList_onItemDoubleClick()
        self.fileList.setCurrentRow(self.fileList.count()-1)
        self.fileList_onSelectionChanged()
        """
        #curItem = self.fileList.currentItem()
        #curWidget = self.fileList.itemWidget(curItem)
        #curImageFullPath = curWidget.fullPath
        self.setFocus()


# main function
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
 
    # app created
    app = QApplication(sys.argv)
    w = ImageLabelerProjectManager()
    w.setupUI()
    w.show()
    
    #w = ImageLabelerWindow()
    #w.setupUI()
    #w.show()
    
    # begin the app
    sys.exit(app.exec_())