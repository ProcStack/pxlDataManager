# pxlViewportGL; ImagerShaderGL v0.3
#   PyQt5 Dynamic Image Processing OpenGL Shader Pipeline
#     By Kevin Edzenga
#          gh - ProcStack
#     As of March 9th, 2023
#
# -- -- -- -- -- -- -- -- -- -- -- -- --
#
# Built on Python 3.10.6 && PyQt5 5.15.9
#
# -- -- -- -- -- -- -- -- -- -- -- -- --
#
# Currently Supports -
#   Dynamically generated OpenGL needs for custom written shaders in './glShaders'
#   Texture Image loading/changing for Sampler Uniforms in Render Passes
#   Different existing OpenGL shader math & utility functions
#     Such as color space swapping and bluring functions
#       See - './glShaders/shaderMath.py' & './glShaders/shaderUtils.py'
#   'FBO', 'FBO Swap', & 'To-Screen' Render Passes
#     'FBO' & 'FBO Swap' texture outputs can be used as Sampler Uniforms
#       Simply set the Unform's type to the render pass' name
#       To read the pass's prior output in itself,
#         You must use 'FBO Swap' as an intermediate for now
#
#
# Not Supported -
#   Texture swapping between "double buffers"
#     Soon to add single FBO A<>B Texture Swapping
#       For now, 'FBO Swap' is used to avoid using `glReadPixels()` functions
#         As `glReadPixels()` can be relatively slow
#   Multiple 'glEffect' shaders
#     Soon 'glEffect' will support Shader Lists [] for custom multi-shader pipelines
#       For now, custom shaders for 'FBO', 'FBO Swap, & 'To-Screen' can be written
#         Simple set a Shader Uniform's Type to the prior pass's name
#
# For more shader information,
#   Please see - `./glShaders/README.md`


import sys, os, importlib
from PIL import Image
from functools import partial
import math
import time

import ctypes
import numpy as np

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtOpenGL
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.uic import *


# Add local script directory to Module Paths
ImageShaderGLAbsPath = os.path.abspath( __file__ )
ImageShaderGLScriptDir = os.path.dirname( ImageShaderGLAbsPath )
if ImageShaderGLScriptDir not in sys.path:
    sys.path.insert( 0, ImageShaderGLScriptDir )



from LoggerGL import VerboseLevelEnum, PrintTimeEnum, LogManager






# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --

# To create a Image Shader Widget with User Controls
#   An Image displayed through OpenGL with gui controllers of Uniform values
# Run --
#   ImageShaderWidget(
#       glEffect = * Use one of the options listed below *
#       initTexturePath = * The path to an image to display *
#       saveImagePath = * The path to save images on disk *
#     )
#
#   '''
#   ImageShaderWidget(
#       glEffect = "smartBlur",
#       initTexturePath = "assets/glTempTex.jpg",
#       saveImagePath = "outputs/glImages/smarBlurImages"
#     )
#   '''
#
#   This returns a QWidget to add into a QLayout
#
# -- -- --
#
# Possible 'glEffect' options --
#   'Default'
#     - Displays the UVs of the render, no textures displayed, a black/red/green/yellow display
#     - Good for testing if the OpenGL widget is working
#
#   'Raw Texture'
#     - Displays the input image path, no effects applied
#
#   'Smart Blur'
#     - Blur subtle details of near by pixels together
#     - Good for sharpening edges as well
#     - Similar to Photoshops smart blur
#
#   'Edge Detect'
#     - Find edges in an image within a given threshold and thickness
#
#   'Segment'
#     - Find congruent shapes in your image
#     - These shapes are uniquely colored by region
#     - "Region Seeds" can be moved around for easier shape finding in your image
#
#   'Paint Mask'
#     - Interactive mask painting
#     - With brush hardness/blur/feathering
#
#   'Color Correct'
#     - Tweak image colors
#         Hue, Saturation, Brightness, Gamma, Vibrance, etc.
#
# You can use any formating and prefix- -suffix of the 'glEffect' name
#   If you want to use the 'Raw Texture' shader
#     It could be 'Raw Texture', 'rawTexture', 'ra W te x TU r e', or 'Raw Texture First View' even
#       Capitals, spaces, prefixes, and suffixes don't matter
#     But in file names saving to disk, spaces are converted to "_"
#       So 'ra W te x TU r e' becomes 'ra_W_te_x_TU_r_e' in file name
#
# -- -- --
#
# Custom shaders not yet supported
# Any edits/tweaks to existing shader.py files would require making a new Image Shader Widget
#   Or closing and re-opening your PyQt Application
#

# -- -- -- -- -- -- -- -- -- -- -- -- --

# For custom shaders -
#
# Built-In Uniform Control Types ---
#   ( As set in 'glShaders/SHADER_NAME.py' uniforms[UNIFORM_NAME]['control'] )
#
# -- -- --
#
# Uniform Controller Types -
#   "offset"    - Mouse Left Click Drag
#                   vec2( offsetX, offsetY)
#   "scale"     - Mouse Right Click Drag
#                   vec2( scaleX, scaleY )
#   "texelSize" - (1 / Image Resolution);
#                   vec2( 1/textureWidth, 1/textureHeight )
#   "visible"   - Will create a GUI element for the User to control the Uniform's value




# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --

# Major TODOs --
#
# TODO : As far as I can tell, GPU objects remain in memory after App closes
#          Methodology is known, implementation in progress!
#
# -- -- --
#
# Minor TODOs --
#
# TODO : Currently not utilizing swap buffers, opting for individual buffers
#          The primary GLWindow should use swap buffers for grabbing reasons
#            Don't want to restrict FBO renders, but would be helpful for sims
#              GL_FRONT & GL_BACK
# TODO : Get Render Passes set up for image editor "Effect Layers"
#          Makes it more similar to other graphics programs for workflow
#            Also allows for easy toggling at a GUI level, just don't render the pass
#          This should make use of swapping buffers though
# TODO : Store UserSettings per shader visual control values from {'current image' path : [Render Passes] } ???
#          Might get a bit messy, but easier "jump back in" to prior settings per-image
# TODO : With binds and releases, updating a later pass in the render order, to only render from that pass on?
#          Data retains on gpu, but have seen odd results from 'toScreen' renders requiring re-rendering before usage
# TODO : Would be nice to allow for blending between arbitrary custome uniforms
#          However, ImageShaderGL is not real time just yet
#            But for future capacity, would be useful
# TODO : Test if [*array] is fast into 2 arrays than for-in and setting individual elements....
#          Typing it out sounds like [*array} would be faster
# TODO : Make higher level Builtin Uniforms Blending Values,
#          As there is a lot of checks for needless functionality currently
#          Perhaps setting a {blend function} in the uniform dict itself
#          Bypassing 'self.lerpBuiltinUniformValues()'; see 'self.updateBuiltinUniformValues()' for now
# TODO : Investigate 'context.makeCurrent( QSurface )' and 'context.doneCurrent()' need with a shared GL Context
# TODO : Implement Rebuild Shader
#          For Uniform Array Length Changes
#            eg; 'segmentShader.py' --
#              #define SEGMENT_SEED_COUNT # 
#              uniform vec3 segmentSeeds[ ** SEGMENT_SEED_COUNT ** ];
# TODO : Implement Reload Shader File Rebuild
# TODO : Split QOpenGLTexture's and QImage Helper functions to 
#          Separate Modules, to clean up code and cross module redundant methods
# TODO : Split out Render Pass Functionality to separate Module
#          Or Class At Least
#
# -- -- --
#
# GPU State Management, Monitoring, Sanity Checks, Locked Context Function Delay, & Thread Locking --
#
# TODO : Implement a "TryAgain" List, 'self.glDelayFunctionList', if Context Busy & Switch Context Fails
#          Like when the context is pre/mid initiating and a mouse event or resize event is triggered
#            Also if 'paintGL()', bind/release events, context change, during GL Function;
#              Such as when a context is swapping buffers, as it seems relatively slow
# TODO : Variables 'self.glContextReleased', 'self.glDelayFunctionList', & 'self.allowGlFinish'
#          Should be managed in the 'ContextGLManager'; './ContextGL.py'
#            Since thats what it meant for!!
#
# -- -- --
#
# Functionality & Local Management to move to ContextGLManager
#
# TODO : The context management, delayed functions, & glFinish toggling (As listed above)
# TODO : Loaded Shader File Data, Imported Modules, for easy cross ViewportGL Sharing
#          Request Shade from the Manager
# TODO : Shader Program creation entirely ?


#class TextureGLWidget(QtWidgets.QOpenGLWidget):
class TextureGLWidget(QtGui.QOpenGLWindow):
#class TextureGLWidget(QtOpenGL.QGLWidget):

    ContextSurface_ToScreen = 0
    ContextSurface_OffScreen = 1

    def __init__(self,parent=None, glId=0, glFormat=None, sharingContext=None, glEffect="default", initTexturePath="assets/glTempTex.jpg", saveImagePath=None ):
        super(TextureGLWidget, self).__init__( sharingContext ) 
        
        # -- -- --
        
        self.id = glId
        self.parent = parent
        
        self.glEffect = glEffect
        
        # Widget based share context seemed to changed when not stored at some capacity
        #   Unsure if it was actually disconnecting
        #     But it returns a different value for `.shareContext()` at init
        # Global Shared Context still accessible
        self.glSourceContext = sharingContext
        
        self.glContext = None
        self.gl = None
        
        self.storedGlContext = None
        self.storedGlSurface = None
        
        self.initialized = False
        
        # -- -- --
        
        
        
        self.glFormat = glFormat
        if self.glFormat == None :
            if sharingContext != None:
                print("Is Sharing Context")
                self.glFormat = sharingContext.format()
                print( self.glFormat )
            else:
                print("Is Unique Context")
                self.glFormat = QtGui.QSurfaceFormat()
                self.glFormat.setProfile( QtGui.QSurfaceFormat.CompatibilityProfile )    
                #self.glFormat.setProfile( QtGui.QSurfaceFormat.CoreProfile )
                #self.glFormat.setVersion( 3, 3 )
                #self.glFormat.setVersion( 2, 1 )
                self.glFormat.setVersion( 4, 1 )
                self.glFormat.setRenderableType( QtGui.QSurfaceFormat.OpenGL )
                #self.setSurfaceType( QtGui.QSurface.OpenGLSurface )
            
            # Holding off for now
            #self.glFormat.setDoubleBuffer(True)
            
            #self.glFormat.setAlpha( True )
            #self.glFormat.setDepth( False )
            #self.glFormat.setStencil( False )
            
        self.glFormat.setSwapBehavior( QtGui.QSurfaceFormat.DoubleBuffer )

        self.setFormat( self.glFormat )
        self.setSurfaceType( QtGui.QSurface.OpenGLSurface )
            
        self.profile = QtGui.QOpenGLVersionProfile( self.glFormat )
        self.profile.setProfile( QtGui.QSurfaceFormat.CoreProfile )   
        #self.profile.setVersion( 2, 1 )
        self.profile.setVersion( 4, 1 )
        
        self.glSwapBufferBehavior = self.glFormat.swapBehavior()
        self.useDoubleBuffer = False # Not Implemented
        
        # -- -- --
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Debug & Render Pass Displays
        
        # Trigger Create OpenGL Debugger
        #   This is expensive on performance
        self.debugOpenGL = False
        
        # Trigger Create PyQt Gui Pixmap Labels & Sub-Text
        self.genRenderPassDisplays = False
        
            
        
        self.glLogger = None
        if self.debugOpenGL and self.glFormat:
            print("Enabling OpenGL Debugger")
            self.glFormat.setOption(QtGui.QSurfaceFormat.DebugContext)
            self.glLogger = QtGui.QOpenGLDebugLogger(self)
            


        # -- -- --
        
        """
        print("Context Printer")
        print( self.context() )
        print(sharingContext)
        # Setting Shared Context
        if sharingContext == None:
            self.glContext = QtGui.QOpenGLContext()
            #self.glContext.setShareContext( sharingContext )
            self.glContext.setFormat( self.glFormat )
            self.glContext.create()
        else:
            self.glContext = QtGui.QOpenGLContext()
            self.glContext.setShareContext( sharingContext )
            self.glContext.setFormat( self.glFormat )
            self.glContext.create()
        """
        
        # -- -- --
        
        
        # -- -- --
        
        """
        self.glOnScreenFormat = QtGui.QSurfaceFormat()
        self.glOnScreenFormat.setVersion(2, 1)
        self.glOnScreenFormat.setProfile( QtGui.QSurfaceFormat.CompatibilityProfile ) 
        #self.glOnScreenFormat.setProfile( QtGui.QSurfaceFormat.CoreProfile )
        self.glOnScreenFormat.setRenderableType( QtGui.QSurfaceFormat.OpenGL )
        """
        
        
        # Build GL Surface for To-Screen Rendering
        self.glToScreenSurface = None
        if self.glContext != None :
            self.glToScreenSurface = QtGui.QSurface()
            self.glToScreenSurface.setFormat( self.glFormat )
            self.glToScreenSurface.create()
        
        # -- -- --
        
        # FBOs seem better with offscreen render surfaces
        #   Not fully implement
        self.glOffScreenFormat = QtGui.QSurfaceFormat()
        #self.glOffScreenFormat.setVersion(2, 1)
        self.glOffScreenFormat.setVersion(4, 1)
        self.glOffScreenFormat.setProfile( QtGui.QSurfaceFormat.CompatibilityProfile ) 
        #self.glOffScreenFormat.setProfile( QtGui.QSurfaceFormat.CoreProfile )
        self.glOffScreenFormat.setRenderableType( QtGui.QSurfaceFormat.OpenGL )

        self.glOffScreenSurface = QtGui.QOffscreenSurface()
        self.glOffScreenSurface.setFormat( self.glOffScreenFormat )
        self.glOffScreenSurface.create()
        
        
        # -- -- --
        
        # Handle Locked or Busy GPU
        # TODO : These variables should be 'ContextGLManager' functionality; './ContextGL.py'
        #          Since thats what it meant for!!
        #            Get it rolling here for now...
        
        # Prevent undesired Context Release when GPU is still working.
        #   Currently - During Context SwapBuffer Event
        self.glContextReleased = False
        
        # Failed Function List when GL Contest was not in a Released State
        #   GPU Busy, hold updates till after current functions
        self.glDelayFunctionList = []
        
        # Toggle the usage of 'gl.glFinish()'
        #   As this is CPU Thread Blocking, leading to delays in PyQt Application responsiveness
        #     But would prevent Race Conditions / Premature Context Releases ( Program Crashes )
        #       Making the QtApp more stable, waiting for GPU Functions to complete safely
        self.allowGlFinish = True
        
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
        
        # Currently TextureGL only supports one Shader Effect at a time
        #   To be changes, but import held in self.Shader
        # TODO : Move to ContextGLManager
        self.Shader = None # Shader Import File
        self.shaderSettings = {}
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Render Passes & GL Shader Variables
        
        
        
        # Mostly for verbose reasons
        #  If you want to custom name your passes,
        #    Update these values
        # TODO : Update this to be set by the Shader File itself
        #          Allowing for custom shader pipeline
        #            Remove this variable entirely
        self.renderPassNames = {
                'fbo' : 'fbo',
                'fboSwap' : 'fboSwap',
                'toScreen' : 'toScreen'
            }
            
        self.glRenderPassList = [] # Render Pass Order
        self.glProgramList = {} # Render Pass Data
        
        
        
        # -- -- --
        
        # TODO: All of this needs to move to a 'RenderPassGL' Object
        #         Either Call Object or Pass Data to Object
        #
        # Order of 'self.glProgramList' Dict Keys to be set -
        #   'FBO', 'FBO Swap', 'Render To Screen'
        #     {'fbo'={}, 'fboSwap'={}, 'toScreen'={} }
        #   Key Order determines Render Order & Pass Type
        #   Holding required binds per pass
        #     Uniform Name/Types, Texture Locations
        # Dict Layout;
        #   Set from glShader File -
        #     {
        #       "fbo" : {
        #           "uniforms" : {
        #             "texOffset" : {
        #               "type":"vec2",
        #               "default":[0,0],
        #               "control":"userOffset"
        #             },
        #             *UNIFORM_NAME* : {
        #               [...]
        #             },
        #           },
        #           "program" : *QtGui.QOpenGLShaderProgram()*,
        #           "textures" : [
        #             {
        #               "uniformName" : *UNIFORM_NAME*,
        #               "glObject" : *QtGui.QOpenGLTexture()*,
        #               "filePath" : *Path, if from file*
        #             },
        #             [ {...} ]
        #           ],
        #           'fboObject' : FBO GL Object,
        #           'fboLocation' : FBO Location for Binding,
        #           'fboTexture' : FBO Texture Object for Binding/Updating,
        #           'geoObject' : VBO/VAO GL Object,
        #           *BIND_TYPE* : [...] 
        #       },
        #       *PASS_TYPE* : {...}
        #     }
        # Usage -
        #   self.glProgramList[ self.renderPassNames[ RENDER_PASS ] ] = self.glPassBaseDict.copy()
        self.glPassBaseDict = {
                "passType":None,
                "uniforms":None, # ShaderName.py Uniforms Dict
                "samplers":None, # { Uniform Name : {self.glPassSamplerDict.copy()} }
                "program":None,
                "builtins":None, # Easy lookup of "native builtin" uniform types { BuiltIn : Uniform Name }
                "textures":None, # [ self.glPassTextureDict.copy() ]
                "fboObject":None,
                "fboLocation":None,
                "fboTexture":None,
                "geoObject":None,
                "vboObjects":None, # Stored for Memory Cleanup reasons
                "debugSource":None,
                "debugTarget":None
            }
        # Copied when new texture is loaded
        #   Linked in 'self.glProgramList[ RENDER_PASS_NAME ]'; ['samplers'] & ['textures']
        self.glPassTextureDict = {
                "filePath":None,
                "texture":None, # QtGui.QOpenGLTexture
                "width":512,
                "height":512
            }
        # Copied when loading Render Pass Shader Program
        #   While sourcing Sampler Uniform Data
        self.glPassSamplerDict = {
                "type":None, # [ 'texture', 'fbo', 'fboSwap', 'toScreen' ]
                "location":0, # Uniform Sampler Bind Location
                "texture":None # Memory Linked 'self.glPassTextureDict.copy()' Object
            }
        
        
        
        # Found shader builtin Control Types set 'self.builtinControlledUniforms'
        #   ( See "./glShaders/README.md" for more information )
        # This holds "Known" functionality linked to shader program uniforms
        #   Such as mouse drag, texelSize, simulation step counts & percentage
        #     Set when loaded shader files make use of build-ins
        # Dict Layout -
        #   { Built-In Control Name : { Render Pass : [ Uniform Name:{}, [...] ] } }
        # Don't know why you'd have multiple uniforms using the same builtin,
        #   Storing the uniform names in an array,
        #     But I'm just going to assume for mistakes in development.
        #
        # Set from loaded glEffect Shader File -
        #     {
        #       "mousePos" : [],
        #       "userOffset" : [],
        #       "userScale" : [],
        #       "texelSize" : [],
        #       "isFBO" : [],
        #       "isSimStep" : [],
        #       "simStep" : [],
        #       "simStepTotal" : [],
        #       "simRunPercent" : []
        #     }
        #
        # Build-In Array Entry Dicts -
        #     {
        #       "userOffset" : [
        #         *RENDER PASS NAME* : {
        #           *UNIFORM_NAME* :
        #             "value" : * float / int / [] *,
        #             "prevValue" : * 'value' Type *,
        #             "blendRate" : * float *
        #         }
        #       ]
        #     }
        # 'blendRate' not implemented yet, defaults to '1' when loaded
        # TODO : Allow for 
        #  
        self.builtinControlledUniformTypes = {
                "mousePos" : { "type":"vec2", "value":[0.5,0.5] },
                "userOffset" : { "type":"vec2", "value":[0.0,0.0] },
                "userScale" : { "type":"vec2", "value":[1.0,1.0] },
                "texelSize" : { "type":"vec2", "value":[1.0/512.0]*2 },
                "isFBO" : { "type":"float", "value":0.0 },
                "isSimStep" : { "type":"float", "value":0.0 },
                "simStep" : { "type":"int", "value":0 },
                "simStepTotal" : { "type":"int", "value":1 }, # Allow sim shader code to run once by default, for mid dev shaders
                "simRunPercent" : { "type":"float", "value":0.0 }
            }
        self.builtinUniformBaseDict = {
                "type" : "vec2", # Reference, for when I forget what 'type' means
                "value" : None,
                "prevValue" : None,
                "blendRate" : 1
            }
            
        self.builtinControlledUniforms = {}
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
        
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Visible GUI Controls for Shader File Uniforms set to {'control':'visible'}
        self.glControls = {}
        
        
        self.frameBufferObject = None
        self.fboTexture = None
        self.swapFrameBufferObject = None
        
        
        
        # When glEffect's Shader File, in './glShaders', has -
        #   settings['fboShader']:True or settings['hasSim']:True
        self.hasFboProgram = False
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Render Pass Simulation State Data
        self.hasSim = False
        self.simTimer = QtCore.QTimer(self)
        self.simTimer.setSingleShot(True)
        self.simTimerIterval = 100
        self.simTimerRunCount = 10
        self.simTimerRunner = 0
        self.simRunnerPercent = 0.0
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Current Image File for Display & Processing
        self.glImagePath = initTexturePath
        self.glImageObject = None
        self.curImage = ""
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # TextureGL Viewport Widget Sizing
        self.imgWidth = 512
        self.imgHeight = 512
        
        self.maxWidth = 512
        self.maxHeight = 512
        self.setMaximumWidth( self.maxWidth )
        self.setMaximumHeight( self.maxHeight )
        #self.setFixedWidth( self.maxWidth )
        #self.setFixedHeight( self.maxHeight )
        
        
        # -- -- -- -- -- -- -- -- -- -- --
        # Image Save To Disk Variables
        self.saveAllRenders = False
        self.saveNextRender = False
        self.outImageFolderPath = saveImagePath
        if self.outImageFolderPath == None:
            scriptAbsPath = os.path.abspath(__file__)
            scriptPath = os.path.dirname(scriptAbsPath)
            self.outImageFolderPath = os.path.join( scriptPath, "ViewportGLSaves" )
        self.outImageName = self.glEffect.replace(" ","_")
        self.outImageFormat = "PNG"
        self.outImagePad = 4
        self.outImagePrefix = None
        
        self.outCurSaveCountPad = 5
        self.outCurSaveCount = -1
        
        # -- -- -- -- -- -- -- -- -- -- --
        # User Mouse Event Variables
        self.curOffset=[0,0]
        self.curScale=[1,1]
        #
        self.mouseLocked = False
        self.mouseMoved = False
        self.mouseOrigPos = None
        self.mouseLockedPos = None
        self.mouseDelta = None
        self.mouseOffsetFitted = None
        self.mouseScaleFitted = None
        self.mouseButton = 0
        self.hasMousePosUniform = False
        
    def setAttr( self, attrType, attrValue ):
        if attrType == 'glDebugger' :
            pass;
        elif attrType == 'glRenderPassDisplays':
            pass;
    
# -- -- -- -- -- -- -- -- -- -- -- -- -- --
# -- User Input Signal Event Handling -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    
    def mouseMoveEvent(self, e):
        if self.hasMousePosUniform:
            toVal=[]
            toVal.append( max( 0.0, min(1.0, float(e.pos().x()/self.imgWidth) ) ) )
            toVal.append( max( 0.0, min(1.0, float(e.pos().y()/self.imgHeight) ) ) )
            #print(toVal)
            self.setRenderPassValues( "mousePos", toVal, True, True )
            self.update()
        else:
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
        
    
# -- -- -- -- -- -- -- -- -- -- --
# -- Context Helper Functions - -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --

    # It comes to my attention that most of these functions,
    #   Are completely useless...
    #     While I'm using or intending for a shared context,
    #       PyQt handles context switching well enough
    #         Thus only Events or External Functions should Switch & Retain -> Restore existing contexts


    def isContextCurrent(self):
        return QtGui.QOpenGLContext.currentContext() == self.glContext

    # TextureGLWidget.ContextSurface_ToScreen == 0
    def getContextSurface( self, targetSurface = 0 ):
        if targetSurface == self.ContextSurface_OffScreen :
            #return self
            return self.glOffScreenSurface
        #elif targetSurface == self.ContextSurface_ToScreen :
        #    #return self.glContext.surface()
        return self.glToScreenSurface if self.glToScreenSurface else self
    
    # TODO : Should add a "Store prior context; then restore" ability
    def enableContext( self, targetSurface = 0 ):
        # Is the check needed?  Does Context switch occur if isCurrent?
        #if QtGui.QOpenGLContext.currentContext() != self.glContext:
        return self.glContext and self.glContext.makeCurrent( self.getContextSurface( targetSurface ) )
    
    def enableContextCheck( self, targetSurface = 0  ): #, targetSurface=None ):
        if self.initialized and self.glContextReleased:
            #if targetSurface==None:
            #    targetSurface = self.glContext.surface()
            return self.enableContext( targetSurface )
        return False
        
    def disableContext( self, gpuSourceEvent = False ):
        if self.glContext and ( self.glContextReleased or gpuSourceEvent ):
            self.glContext.doneCurrent()
            self.glContextReleased = True
        return False
    
    # Not Needed --
    def setContextState( self, toState = None ):
        self.glContextReleased = toState
    
    # Not Needed --
    def getContextState( self ):
        return self.glContextReleased
    
    # Currently, the only required by 'paintGL()'
    def isContextInitialized(self):
        return self.initialized
    
    
    # Context Swab Buffers
    def swapSurfaceBuffers( self ):
        # Set by glContext.format(); yielding QtGui.QSurfaceFormat.SwapBehavior enum
        if self.glSwapBufferBehavior > 1 :
            self.glContext.swapBuffers( self.getContextSurface() )
            #self.glContext.swapBuffers( self.glContext.surface() )
            #self.glContext.swapBuffers( self )
            #self.glContext.swapBuffers()
            # glFinish is thread locking, but swaps are needed prior to context release
            #self.gl.glFinish()
            
    # If another context is current, bind for temporary needs
    #   This only needed when multiple glContexts in QtApp
    # TODO : Requests should defer to 'ContextGL', if exists
    #          Should be retained, but redirected as needed
    def tempBindContext(self):
        if self.isContextCurrent():
            # Bypassing Temp Bind,  Self Already Current
            #   Race Conditions may exist, explore this behavior
            return;
        self.storedGlContext = QtGui.QOpenGLContext.currentContext()
        self.storedGlSurface = self.storedGlContext.surface()
        
    def tempReleaseContext(self):
        if self.storedGlContext != None:
            self.storedGlContext.makeCurrent( self.storedGlSurface )
            self.storedGlContext = None
            self.storedGlSurface = None
            
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- GPU Status Helper Functions -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

    # Quite expesive, as it parses GPU State
    #   But sometimes its needed for santity checks
    #     Would rather a delay than a program crash
    # Doesn't seem availible, at least in 2.1
    def getGPUBusyState( self ):
        gpuBusyState = None #self.gl.glGetInteger(GL_GPU_BUSY_NVX)
        print(" |-  GPU Busy State - ", gpuBusyState)
        return gpuBusyState
    
    # glFinish is Thread Locking
    #   Preventing the program from progressing until GPU commands have been processed
    #     Given that it locks the CPU thread, can be toggled with 'self.allowGlFinish = True/False'
    def glFinishedThreadLock( self ):
        if self.allowGlFinish :
            self.gl.glFinish()
            #QtGui.QOpenGLFunctions.
    
    # Send a glFence object and monitor its value
    #   If the glFense holds a value, current command queue has processed
    #     Non-Thread Blocking Monitoring
    def glAwaitCommandQueue( self ):
        #self.gl.glFenceSync( self.gl.GL_SYNC_GPU_COMMANDS_COMPLETE, GLbitfield flags)
        pass;
    
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- Image & Texture Helper Functions -- --
# -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
            
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
        
    # TODO : Set this up to share texture ids, prior loaded texture paths
    # TODO : Pass textures to pxlViewportGL ContextGL object for maintaining
    #          And requests for render binds
    def loadImageTex2D(self, filename, enableAlpha=True, enableMipMaps=False, pixelFiltering=1, wrapMode=2 ):
        
        mipMapSetting = QtGui.QOpenGLTexture.DontGenerateMipMaps
        if enableMipMaps:
            mipMapSetting = QtGui.QOpenGLTexture.GenerateMipMaps
        
        pixelFilterSetting = [
                QtGui.QOpenGLTexture.Nearest,
                QtGui.QOpenGLTexture.Linear,
                QtGui.QOpenGLTexture.NearestMipMapNearest,
                QtGui.QOpenGLTexture.NearestMipMapLinear,
                QtGui.QOpenGLTexture.LinearMipMapNearest,
                QtGui.QOpenGLTexture.LinearMipMapLinear
            ][ pixelFiltering ]
        
        textureWrapSetting = [
                QtGui.QOpenGLTexture.Repeat,
                QtGui.QOpenGLTexture.MirroredRepeat,
                QtGui.QOpenGLTexture.ClampToEdge,
                QtGui.QOpenGLTexture.ClampToBorder,
            ][ wrapMode ]
        
        
        
        
        curImage = None
        if filename == self.glImagePath:
            if self.glImageObject == None:
                self.glImageObject = QtGui.QImage( filename )
        
            curImage = self.glImageObject
        else:
            curImage = QtGui.QImage( filename )
            
        # TODO : Prep alpha channel if `enableAlpha`
        #curImage = Image.open(filename)
        #print(filename)
        #print(curImage.format, curImage.mode )
        #if curImage.mode == "RGB":
        #    newAlpha = Image.new('L', curImage.size, 255)
        #    curImage.putalpha( newAlpha )
        #curImgData = np.array(list(curImage.getdata()), np.uint8)
        
        
        #texture = QtGui.QOpenGLTexture( QtGui.QOpenGLTexture.Target2D )
        texture = QtGui.QOpenGLTexture( curImage, enableMipMaps )

        #texture.setAutoMipMapGenerationEnabled( False )
        #texture.setFormat( QtGui.QOpenGLTexture.RGBA8_UNorm )
        texture.setMinMagFilters( pixelFilterSetting, pixelFilterSetting )
        texture.setWrapMode( QtGui.QOpenGLTexture.DirectionS, textureWrapSetting )
        texture.setWrapMode( QtGui.QOpenGLTexture.DirectionT, textureWrapSetting )

        # Get this dynamically allocating based on image details
        texture.allocateStorage( QtGui.QOpenGLTexture.RGBA, QtGui.QOpenGLTexture.UInt8 )
        
        #texture.setData( QtGui.QImage( filename ), QtGui.QOpenGLTexture.DontGenerateMipMaps  )
        
        texture.create()

        
        #self.imgWidth = texture.width()
        #self.imgHeight = texture.height()
        self.curImage = filename
        
        curTextureDict = self.glPassTextureDict.copy()
        curTextureDict['filePath'] = filename
        curTextureDict['texture'] = texture
        curTextureDict['width'] = texture.width()
        curTextureDict['height'] = texture.height()
        
        
        return curTextureDict
    
    def setTextureFromImageData(self, samplerId=0, imageData=None):
        if imageData == None:
            print("Image data None")
            return;
        
        print("!!!! Attempting to run 'setTextureFromImageData'; Canceling !!!")
        print("       --- Old ImageShaderGL logic still implemented ---")
        return;
        
        samplerName = 'samplerTex'
        samplerTexIndex = 0
        #activeTexture = imageInfo['activeTexture']
        textureBind = imageInfo['texture']
        #textureLoc = imageInfo['location']
        samplerUniformBind = samplerTexIndex+1
        
        texWidth = imageInfo['width']
        texHeight = imageInfo['height']
        
        
        #imageData = np.array(list(imageData), np.uint8)
        #gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, texWidth, texHeight, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, imageData)
        
        textureBind.setData( imageData, QtGui.QOpenGLTexture.DontGenerateMipMaps )
        
        
        # self.gl.glActiveTexture( activeTexture )

        # self.gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT,1)
        # self.gl.glBindTexture(gl.GL_TEXTURE_2D, textureBind )
        
        self.paintGL()
        
        
# -- -- -- -- -- -- -- -- -- -- -- 
# -- FBO Helper Functions -- -- -- -- 
# -- -- -- -- -- -- -- -- -- -- -- -- --
    
    # Create Default PyQt5 QOpenGLFramebufferObject 
    def newQtFrameBuffer(self, fboSize=[512,512] ):
        
        frameBufferObject = QtGui.QOpenGLFramebufferObject( fboSize[0], fboSize[1])#, glFboFormat )
        
        if not frameBufferObject.isValid():
            print('framebuffer binding failed')
            
        return frameBufferObject
        
    # Create PyQt5 QOpenGLFramebufferObject
    #   With QOpenGLTexture Output Color Attachment
    def newQtTextureFrameBuffer(self, fboSize=[512,512] ):

        fboTargetImage = QtGui.QImage(fboSize[0], fboSize[1], QtGui.QImage.Format_RGBA8888)
        fboTargetImage.fill( QtGui.QColor(0,0,0,0) )
        
        
        fboTargetTexture = QtGui.QOpenGLTexture(fboTargetImage)

        fboTargetTexture.setMinMagFilters( QtGui.QOpenGLTexture.Nearest, QtGui.QOpenGLTexture.Nearest )
        fboTargetTexture.setWrapMode( QtGui.QOpenGLTexture.ClampToEdge )
        # To fix 0-1 border seam
        #fboTargetTexture.setWrapMode( QtGui.QOpenGLTexture.ClampToBorder )
        fboTargetTexture.setAutoMipMapGenerationEnabled( False )
        
        # -- -- --
        
        frameBufferObject = QtGui.QOpenGLFramebufferObject( fboSize[0], fboSize[1])#, glFboFormat )
        
        frameBufferObject.bind()
        
        self.gl.glFramebufferTexture2D( self.gl.GL_FRAMEBUFFER, self.gl.GL_COLOR_ATTACHMENT0, self.gl.GL_TEXTURE_2D, fboTargetTexture.textureId(), 0)
        
        # -- -- --
        
        if not frameBufferObject.isValid():
            print('framebuffer binding failed')
            
        return frameBufferObject, fboTargetTexture
        
        
    def setTargetGLObject(self, glTargetObject=None):
        print( "---------------------" )
        print( "Set TargetGL Object, Cancelling, Logic Updated" )
        print( glTargetObject )
        #if glTargetObject != None:
        #    self.glTargetObject = glTargetObject
        #    self.bufferToTargetGL()
    def bufferToTargetGL(self):
        if self.glTargetObject != None:
            print(" BUFFER TO TARGETGL, Cancelling, Logic Updated ")
            #displayImage = gl.glGetTexImage( gl.GL_TEXTURE_2D, self.fboTexture, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, outputType=None )
            #self.glTargetObject.setTextureFromImageData( 0, displayImage )
            
    def loadProgram(self, glEffect="default"):
        glEffect = glEffect.lower().replace(" ","")
        
        
        
        # TODO : Get these options sourced from 'listdir()' in 'glShaders'
        #          For user added shader file availability
        curShader = None
        if "rawtexture" in glEffect:
            #from .glShaders import rawTextureShader as Shader
            curShader = importlib.import_module(".glShaders.rawTextureShader", __package__ )
            
        elif "swaptexture" in glEffect:
            #from .glShaders import swapTextureShader as Shader
            curShader = importlib.import_module(".glShaders.swapTextureShader", __package__ )
            
        elif "smartblur" in glEffect:
            #from .glShaders import smartBlurShader as Shader
            curShader = importlib.import_module(".glShaders.smartBlurShader", __package__ )
            
        elif "edgedetect" in glEffect:
            #from .glShaders import edgeDetectShader as Shader
            curShader = importlib.import_module(".glShaders.edgeDetectShader", __package__ )
            
        elif "segment" in glEffect:
            #from .glShaders import segmentShader as Shader
            curShader = importlib.import_module(".glShaders.segmentShader", __package__ )
            
        elif "paintmask" in glEffect:
            #from .glShaders import paintMaskShader as Shader
            curShader = importlib.import_module(".glShaders.paintMaskShader", __package__ )
            
        elif "colorcorrect" in glEffect:
            #from .glShaders import colorCorrectShader as Shader
            curShader = importlib.import_module(".glShaders.colorCorrectShader", __package__ )
            
        else: # Default to "default"; This will cause issues during dev
            #from .glShaders import defaultShader as Shader
            curShader = importlib.import_module(".glShaders.defaultShader", __package__ )
        
        #self.Shader = Shader
        self.Shader = curShader
        
        hasFboShader = False
        hasSim = False
        
        if hasattr( self.Shader, "settings"):
            self.shaderSettings = self.Shader.settings.copy()
        
        if "fboShader" in self.shaderSettings:
            hasFboShader = self.shaderSettings['fboShader']
            self.hasFboProgram = hasFboShader
            
        if "hasSim" in self.shaderSettings:
            hasSim = self.shaderSettings['hasSim']
            self.hasSim = hasSim
            self.simTimer.timeout.connect(self.simTimeout)
        if "simTimerIterval" in self.shaderSettings:
            #print("Found 'simTimerIterval'")
            self.simTimerIterval = max(20, self.shaderSettings['simTimerIterval'] )
        if "simRunCount" in self.shaderSettings:
            #print("Found 'simRunCount'")
            self.simTimerRunCount = max(1, self.shaderSettings['simRunCount'] )


        # -- -- -- --
        # -- -- -- --
        # -- -- -- --

        # Set Render To Screen Program
        
        toVertex = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Vertex, self )
        toVertex.compileSourceCode( self.Shader.vertex )

        toFragment = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Fragment, self )
        toFragment.compileSourceCode( self.Shader.fragment )
        
        
        # -- -- -- --
        
        program = QtGui.QOpenGLShaderProgram()
        program.addShader( toVertex )
        program.addShader( toFragment )
        program.bindAttributeLocation('position',0)
        program.bindAttributeLocation('uv',1)
        program.link()
        
        # Free Ram, but is this potentiall problematic?
        self.gl.glDetachShader( program.programId(), toVertex.shaderId() )
        self.gl.glDetachShader( program.programId(), toFragment.shaderId() )
            
        
        curToScreenPassName = self.renderPassNames['toScreen']
        curProgramPass = self.glPassBaseDict.copy()
        curProgramPass['passType'] = "toScreen"
        curProgramPass['program'] = program
        curProgramPass['uniforms'] = self.Shader.uniforms.copy()
        curProgramPass['samplers'] = {}
        curProgramPass['textures'] = []
        curProgramPass['fboLocation'] = self.defaultFramebufferObject()
        self.glProgramList[ curToScreenPassName ] = curProgramPass
        
    

        # -- -- -- --
        
        if self.hasFboProgram or self.hasSim :
            fboUniforms = getattr( self.Shader, 'fboUniforms', self.Shader.uniforms)
            fboVertexSource = getattr( self.Shader, 'fboVertex', self.Shader.vertex)
            fboFragmentSource = getattr( self.Shader, 'fboFragment', self.Shader.fragment)
            
            fboVertex = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Vertex, self )
            fboVertex.compileSourceCode( fboVertexSource )

            fboFragment = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Fragment, self )
            fboFragment.compileSourceCode( fboFragmentSource )
            
            # -- -- -- --
            
            fboProgram = QtGui.QOpenGLShaderProgram()
            fboProgram.addShader( fboVertex )
            fboProgram.addShader( fboFragment )
            fboProgram.bindAttributeLocation('position',0)
            fboProgram.bindAttributeLocation('uv',1)
            fboProgram.link()
        
            # Free Ram, but is this potentiall problematic?
            self.gl.glDetachShader( fboProgram.programId(), fboVertex.shaderId() )
            self.gl.glDetachShader( fboProgram.programId(), fboFragment.shaderId() )
            
        
            
            fboBufferObject, fboTextureObject = self.newQtTextureFrameBuffer( [512,512] )

            curFboPassName = self.renderPassNames['fbo']
            curFboProgramPass = self.glPassBaseDict.copy()
            curFboProgramPass['passType'] = "fbo"
            curFboProgramPass['program'] = fboProgram
            curFboProgramPass['uniforms'] = fboUniforms.copy()
            curFboProgramPass['samplers'] = {}
            curFboProgramPass['textures'] = []
            curFboProgramPass['fboObject'] = fboBufferObject
            #curFboProgramPass['fboLocation'] = fboBufferObject.handle()
            curFboProgramPass['fboTexture'] = fboTextureObject
            self.glProgramList[ curFboPassName ] = curFboProgramPass
            # -- -- --
            self.glRenderPassList.append( curFboPassName )


        if self.hasSim :
            swapShaderUniforms = getattr( self.Shader, 'fboSwapUniforms', None)
            swapVertexSource = getattr( self.Shader, 'fboSwapVertex', None)
            swapFragmentSource = getattr( self.Shader, 'fboSwapFragment', None)
            
            if swapShaderUniforms==None or swapVertexSource==None or swapFragmentSource==None:
                from .glShaders import swapTextureShader as fboSwapShader
                if swapShaderUniforms == None :
                    swapShaderUniforms = getattr( fboSwapShader, 'fboSwapUniforms', fboSwapShader.fboSwapUniforms )
                if swapVertexSource == None :
                    swapVertexSource = getattr( fboSwapShader, 'fboSwapVertex', fboSwapShader.fboSwapVertex )
                if swapFragmentSource == None :
                    swapFragmentSource = getattr( fboSwapShader, 'fboSwapFragment', fboSwapShader.fboSwapFragment )
                
            fboSwapVertex = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Vertex, self )
            fboSwapVertex.compileSourceCode( swapVertexSource )

            fboSwapFragment = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Fragment, self )
            fboSwapFragment.compileSourceCode( swapFragmentSource )
            
            # -- -- -- --
            
            fboSwapProgram = QtGui.QOpenGLShaderProgram()
            fboSwapProgram.addShader( fboSwapVertex )
            fboSwapProgram.addShader( fboSwapFragment )
            fboSwapProgram.bindAttributeLocation('position',0)
            fboSwapProgram.bindAttributeLocation('uv',1)
            
            if not fboSwapProgram.link():
                print("!! Warning, fboSwap pass shader failed to link !!")
        
            # Free Ram, but is this potentiall problematic?
            self.gl.glDetachShader( fboSwapProgram.programId(), fboSwapVertex.shaderId() )
            self.gl.glDetachShader( fboSwapProgram.programId(), fboSwapFragment.shaderId() )
            
            fboSwapBufferObject,fboSwapTextureObject = self.newQtTextureFrameBuffer( [512,512] )

            
            curFboSwapPassName = self.renderPassNames['fboSwap']
            curFboSwapProgramPass = self.glPassBaseDict.copy()
            curFboSwapProgramPass['passType'] = "fboSwap"
            curFboSwapProgramPass['program'] = fboSwapProgram
            curFboSwapProgramPass['uniforms'] = swapShaderUniforms.copy()
            curFboSwapProgramPass['samplers'] = {}
            curFboSwapProgramPass['textures'] = []
            curFboSwapProgramPass['fboObject'] = fboSwapBufferObject
            #curFboSwapProgramPass['fboLocation'] = fboSwapBufferObject.handle()
            curFboSwapProgramPass['fboTexture'] = fboSwapTextureObject
            self.glProgramList[ curFboSwapPassName ] = curFboSwapProgramPass
            # -- -- --
            self.glRenderPassList.append( curFboSwapPassName )
        
        
        # -- -- -- --
        # -- -- -- --
        # -- -- -- --
        
        # To Screen Pass needs to render last
        #   ... Or should ...
        self.glRenderPassList.append( curToScreenPassName )


        # -- -- -- --
        
        return
        
        
    def buildUniforms(self, glProgramPassName, glProgramDataDict):
        # TODO : Remove this, not needed
        glUniformLocations = {}
        
        
        glProgramData = glProgramDataDict[ glProgramPassName ]
        
        glProgramPassType = glProgramData['passType']
        glProgram = glProgramData['program']
        glProgramUniforms = glProgramData['uniforms']
        glProgramFBO = glProgramData['fboObject']
        
        glProgramUniformsKeys = glProgramUniforms.keys()
        
        glProgram.bind()
        
        if glProgramFBO:
            glProgramFBO.bind()
        
        # program.bind()
        # self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
        # self.gl.glUniform1i( program.uniformLocation('samplerTex'), 0 )
        # self.gl.glActiveTexture( self.gl.GL_TEXTURE1 )
        # self.gl.glUniform1i( program.uniformLocation('bufferRefTex'), 1 )
        # program.release()
        
        # TODO : Need to verify if samplers are base 0 per shader program
        #          Or requires global offsets for shared context
        #        Base 0 in other situations I've encountered
        #          I'm new to Shared Contexts though
        samplerUniformIndex = -1 # textureIndex+=1 prior to setting sampler
        
        
        for x,curUniform in enumerate( glProgramUniformsKeys ):
            uSettings = glProgramUniforms[ curUniform ]
            
            # TODO : Clean up this mess of different if-elif's
            if uSettings['type'] == "float":
                uLocation = glProgram.uniformLocation( curUniform )
                uVal = uSettings[ 'default' ]
                glProgram.setUniformValue( uLocation, float(uVal) )
                # -- -- --
                # uLocKey = curUniform
                # glUniformLocations[ uLocKey ] = uLocation
                
            elif uSettings['type'] == "int":
                uLocation = glProgram.uniformLocation( curUniform )
                uVal = uSettings[ 'default' ]
                glProgram.setUniformValue( uLocation, int(uVal) )
                # -- -- --
                # uLocKey = curUniform
                # glUniformLocations[ uLocKey ] = uLocation
                
            elif uSettings['type'] == "vec2":
                uLocation = glProgram.uniformLocation( curUniform )
                uVal = uSettings[ 'default' ]
                glProgram.setUniformValue( uLocation, uVal[0], uVal[1] )
                # -- -- --
                # uLocKey = curUniform
                # glUniformLocations[ uLocKey ] = uLocation
                
            elif uSettings['type'] == "vec3":
                uLocation = glProgram.uniformLocation( curUniform )
                uVal = uSettings[ 'default' ]
                glProgram.setUniformValue( uLocation, uVal[0], uVal[1], uVal[2] )
                # -- -- --
                # uLocKey = curUniform
                # glUniformLocations[ uLocKey ] = uLocation
                
            elif uSettings['type'] == "vec4":
                uLocation = glProgram.uniformLocation( curUniform )
                uVal = uSettings[ 'default' ]
                glProgram.setUniformValue( uLocation, uVal[0], uVal[1], uVal[2], uVal[3] )
                # -- -- --
                # uLocKey = curUniform
                # glUniformLocations[ uLocKey ] = uLocation
                
            elif "[]" in uSettings['type']:
                uVal = uSettings[ 'default' ]
                
                uValFlat = []
                if curUniform == "segmentSeeds":
                    curElement = 0
                    for arrayDict in uVal:
                        dictToMat = self.Shader.seedDictToArray( arrayDict )
                        #uValFlat += dictToMat
                        for keyVal in dictToMat:
                            #print(keyVal)
                            curVarElementName = curUniform+"["+str(curElement)+"]"
                            uLocation = glProgram.uniformLocation( curVarElementName )
                            glProgram.setUniformValue( uLocation, keyVal[0], keyVal[1], keyVal[2] )
                            curElement+=1
                                
            elif uSettings['type'] == "texture" :
                # At Render Samplers Binds in `self.connectTextureSamplers()`
                
                
                #glProgramData['program']
                
                curTextureLoad = self.loadImageTex2D( self.glImagePath )
                
                # -- -- --
                
                uLocation = glProgram.uniformLocation( curUniform )
                
                
                # -- -- --
                
                if uLocation >= 0 :
                    # Set Shader Program's Uniform Bind Location
                    #samplerUniformIndex += 1
                    #glProgram.setUniformValue( curUniform, samplerUniformIndex )
                    #uSettings['samplerBind'] = samplerUniformIndex
                    
                    # Bind texture to texture location and bind uniform to texture
                    #glTexLocation = self.gl.GL_TEXTURE0 + uLocation
                    #self.gl.glActiveTexture( glTexLocation )
                    curTextureLoad['texture'].bind( uLocation )
                    #curTextureLoad['texture'].bind( samplerUniformIndex )
                    
                    #glProgram.setUniformValue( curUniform, curTextureLoad['texture'].textureId() )
                    glProgram.setUniformValue( curUniform, uLocation )
                    
                    curTextureLoad['texture'].release( uLocation )
                    
                    self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
                    
                    # -- -- --
                    
                    glProgramData['textures'].append( curTextureLoad )
                else:
                    print(" ! Warning, Failed to located Sampler Uniform '"+curUniform+"' in '"+glProgramPassName+"'; Uniform may not be used in Shader Code.")
                
                # -- -- --
                
                curSamplerDict = self.glPassSamplerDict.copy()
                curSamplerDict['type'] = uSettings['type']
                curSamplerDict['location'] = uLocation
                curSamplerDict['texture'] = curTextureLoad['texture']
                glProgramData['samplers'][ curUniform ] = curSamplerDict
                    
                    
            elif uSettings['type'] in ["fbo","fboSwap","toScreen"] :
                # At Render Samplers Binds in `self.connectTextureSamplers()`
                
                # Pass reading itself warning
                #   I need to set up double buffer swapping...
                if uSettings['type'] == glProgramPassType and not self.useDoubleBuffer :
                    warningSuggestion = ""
                    if uSettings['type'] == "fbo":
                        warningSuggestion = ", set 'fbo' to 'toScreen' or 'fboSwap' (for sims)"
                    elif uSettings['type'] == "fboSwap":
                        warningSuggestion = ", set 'fboSwap' to read 'fbo' output"
                    elif uSettings['type'] == "toScreen":
                        warningSuggestion = ", set 'toScreen' to read 'fbo' output"
                    
                    self.setStatusBar( "Warning, Sampler '"+curUniform+"' in '"+uSettings['type']+"' pass is reading itself without Double Buffers"+warningSuggestion, 1, False )
                        
                
                #samplerLocation = self.glProgram.uniformLocation( samplerName )
                #self.glProgram.setUniformValue( samplerLocation, self.swapFrameBufferObject.texture() )
            
                # Set Shader Program's Uniform Bind Location
                #   While other render passes,
                #     Default behavior is to bind the pass's output to a sampler
                
                
                #print( uSettings['type'] )
                #print( sourcePassType )
                #print( glProgramDataDict[ sourcePassType ] )
                
                #samplerUniformIndex += 1
                #glProgram.setUniformValue( curUniform, sourcePassTexture.textureId() )
                #uSettings['samplerBind'] = samplerUniformIndex
                #textureId()
                
                # -- -- --
                
                uLocation = glProgram.uniformLocation( curUniform )
                
                # -- -- --
                
                if uLocation >= 0 and 'fboObject' in glProgramData :
                    
                    
                
                    sourcePassType = self.renderPassNames[ uSettings['type'] ]
                    
                    if sourcePassType in glProgramDataDict and 'fboTexture' in glProgramDataDict[ sourcePassType ] : # and 'fboObject' in glProgramDataDict[ sourcePassType ] :
                        #sourcePassFBO = glProgramDataDict[ sourcePassType ]['fboObject']
                        sourcePassTexture = glProgramDataDict[ sourcePassType ]['fboTexture']
                        
                        #fboProgram.bind()
                        
                        sourcePassTexture.bind( uLocation )
                        
                        #self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + uLocation )
                        #self.gl.glUniform1i( curUniform, 0 )
                        glProgram.setUniformValue( curUniform, uLocation )
                        
                        sourcePassTexture.release( uLocation )
                        
                        #fboProgram.release()
                    """
                    glTexLocation = self.gl.GL_TEXTURE0 + uLocation
                    self.gl.glActiveTexture( glTexLocation )
                    #glProgramData['fboObject'].bind()
                    self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, sourcePassFBO.texture())
                    #curTextureLoad['texture'].bind( samplerUniformIndex )
                    
                    glProgram.setUniformValue( curUniform, glTexLocation )
                    
                    #curTextureLoad['texture'].release()
                    
                    self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, 0)
                    self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
                    """
                else:
                    print(" ! Warning, Failed to located Sampler Uniform '"+curUniform+"' in '"+glProgramPassName+"'; Uniform may not be used in Shader Code.")
                
                # -- -- --
                
                curSamplerDict = self.glPassSamplerDict.copy()
                curSamplerDict['type'] = uSettings['type']
                curSamplerDict['location'] = uLocation
                curSamplerDict['texture'] = sourcePassTexture
                glProgramData['samplers'][ curUniform ] = curSamplerDict
                
                    
            if 'control' in uSettings:
                if uSettings['control'] == "visible":
                    controlDict = {}
                    controlDict['passName'] = glProgramPassName
                    controlDict['type'] = uSettings['type']
                    controlDict['value'] = uSettings['default']
                    controlDict['range'] = uSettings['range'] if 'range' in uSettings else False
                    self.glControls[ curUniform ] = controlDict
                elif uSettings['control'] in self.builtinControlledUniformTypes :
                    if uSettings['control'] not in self.builtinControlledUniforms :
                        self.builtinControlledUniforms[ uSettings['control'] ] = {}
                        
                    if glProgramPassName not in self.builtinControlledUniforms[ uSettings['control'] ] :
                        self.builtinControlledUniforms[ uSettings['control'] ][ glProgramPassName ] = {}
                        
                    if curUniform not in self.builtinControlledUniforms[ uSettings['control'] ][ glProgramPassName ] :
                        newBuiltinData = self.newBuiltinDataDict( uSettings['control'], uSettings )
                        self.builtinControlledUniforms[ uSettings['control'] ][ glProgramPassName ][ curUniform ] = newBuiltinData
        
        if glProgramFBO:
            glProgramFBO.release()
            
        glProgram.release()  
        
        #
        
        #return glUniformLocations
    
    # Build a New Built-In Data Dict
    #   If custom default data, verify input Shader File 'uniform[UNIFORM_NAME]' dictionary
    #     Alert user as needed
    #       Overkill? Yes, but I'll forget or mess up, I'm sure
    def newBuiltinDataDict(self, controlType, refSettings=None ):
        newBuiltinData = self.builtinUniformBaseDict.copy()
        if controlType in self.builtinControlledUniformTypes :
            targetBuiltinType = self.builtinControlledUniformTypes[ controlType ]
            newBuiltinData['type'] = targetBuiltinType['type']
            if type(targetBuiltinType['value'])==list :
                newBuiltinData['value'] = targetBuiltinType['value'].copy()
                newBuiltinData['prevValue'] = targetBuiltinType['value'].copy()
            else:
                newBuiltinData['value'] = targetBuiltinType['value']
                newBuiltinData['prevValue'] = targetBuiltinType['value']
            newBuiltinData['blendRate'] = 1.0
            
            if type(refSettings)==dict :
                if 'type' in refSettings and newBuiltinData['type']==refSettings['type']:
                    if 'default' in refSettings :
                        refValue = refSettings['default']
                        refValueType = type(refValue)
                        # Fix Tuples and Sets
                        if refValueType in [tuple,set]:
                            refValue = list(refValue)
                            refValueType = type(refValue)
                            
                        targetValueType = type(newBuiltinData['value'])
                        if targetValueType == list :
                            targetValueLength = len( newBuiltinData['value'] )
                            # Set Float/Int to type list length
                            if refValueType in [float,int] :
                                refValue = [refValue] * targetValueLength
                            elif refValueType == list :
                                refValueLength = len(refValue)
                                # TODO : Catch more cases, handle mis-matching length arrays better
                                if refValueLength == 0:
                                    refValue = newBuiltinData['value']
                                elif refValueLength < targetValueLength :
                                    refValue = (refValue * targetValueLength)[0:targetValueLength]
                                elif refValueLength > targetValueLength :
                                    refValue = refValue[0:targetValueLength]
                            newBuiltinData['value'] = refValue.copy()
                            newBuiltinData['prevValue'] = refValue.copy()
                        elif targetValueType in [int,float] :
                            if targetValueType == int and refValueType == float :
                                refValue = int(refValue)
                            if refValueType == list :
                                if len(refValue) == 0:
                                    refValue = newBuiltinData['value']
                                else:
                                    refValue = refValue[0]
                                    refValue = int(refValue) if targetValueType == int else float(refValue)
                            newBuiltinData['value'] = refValue
                            newBuiltinData['prevValue'] = refValue
                elif 'type' in refSettings and newBuiltinData['type']!=refSettings['type'] :
                    print(" ! Warning ! Shader Uniform '"+controlType+"' is type '"+newBuiltinData['type']+"', but set as '"+refSettings['type']+"' in '"+self.glEffect+"' shader file." )
            elif refSettings != None :
                print(" ! Warning ! Shader Uniform '"+controlType+"' should be 'Dict', invalid type '"+(type(refSettings).__name__)+"'" )
        else:
            print(" !! Error !! in ImageShaderGL, creating new Built-In Uniform data;\n   Unknown control type - '"+controlType+"'" )
            newBuiltinData['type']="float"
            newBuiltinData['value']=1.0
            newBuiltinData['prevValue']=1.0
        return newBuiltinData
                
    def initializeGL(self):
        print( " -- GL Init Started" )
        if self.glLogger:
            self.glLogger.initialize()
            #self.glLogger.messageLogged.connect(lambda message: QtCore.qDebug(
            #    self.__tr("OpenGL debug message: {0}").fomat(message.message())
            #))
            self.glLogger.messageLogged.connect(lambda message: QtCore.qDebug(
                QtCore.QCoreApplication.translate("DDSWidget",("OpenGL debug message: {0}").format(message.message())
            )))
            self.glLogger.startLogging()
            
        # Seems all contexts are still sharing when checking
        #   But still mystery magic to me
        if self.glContext == None :
            print(" !! Warning; No self.glContext set before 'initializeGL()' !!")
            print(" !! '"+self.glEffect+"' ImageShaderGL may be Unstable !!")
            self.glContext = self.context()
            # print("Created Shared Context")
            # self.glContext = QtGui.QOpenGLContext()
            self.glContext.setShareContext( self.glSourceContext )
            self.glContext.setFormat( self.glFormat )
            self.glContext.create()
        #self.glContext.setShareContext( self.glContext )
        
        
        self.glToScreenSurface = self.glContext.surface()
        #self.enableContext()
        self.enableContext()
        self.glContext.aboutToBeDestroyed.connect( self.destroy )
        self.frameSwapped.connect( self.frameSwapComplete )

        self.gl = self.glContext.versionFunctions( self.profile )
        self.gl.initializeOpenGLFunctions()
        
        
        self.glSwapBufferBehavior = self.glContext.format().swapBehavior()
        
        
        # For future double output buffers, multiple render targets
        #  Check for - `self.gl.GL_ARB_draw_buffers`
        # And enable MRT with -
        #   glEnable(GL_BLEND);
        #   glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
        
        
        #self.gl.glClearColor(0.0, 0.0, 0.0, 0.0)

        # Load glEffect shader
        #   Sets render pass order; 'self.glRenderPassList'
        #   Sets shader data; 'self.glProgramList'
        self.loadProgram( self.glEffect )
        
        # Build render pass' shader needs and uniform binds
        #self.glProgramList[ curToScreenPassName ]
        
        # TODO : Move Calls to RenderPassGL Object
        for x,currentPassName in enumerate( self.glRenderPassList ):
            curPassDataDict = self.glProgramList[ currentPassName ]
            curPassProgram = curPassDataDict['program']

            self.buildUniforms( currentPassName, self.glProgramList )
            
            curPassProgram.bind()
            
            curPassVAO = QtGui.QOpenGLVertexArrayObject( self )
            curPassVAO.create()
            
            curPassVAO.bind()
            vaoPositionList = [ -1,1, 1,1, -1,-1, 1,-1 ]
            vaoTexCoordList = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
            positionVBO = self.setVertexBuffer( vaoPositionList, 2, curPassProgram, "position" )
            uvVBO = self.setVertexBuffer( vaoTexCoordList, 2, curPassProgram, "uv" )
            curPassVAO.release()
            
            curPassProgram.release()
            
            curPassDataDict['geoObject'] = curPassVAO
            
            if curPassDataDict['vboObjects'] == None:
                curPassDataDict['vboObjects'] = []
                
            # Holding for Memory Management needs
            curPassDataDict['vboObjects'].append( positionVBO )
            curPassDataDict['vboObjects'].append( uvVBO )
            """
            curDebugSource, curDebugTarget = self.buildRenderPassDebug( curPassDataDict )
            curPassDataDict['debugSource'] = curDebugSource
            curPassDataDict['debugTarget'] = curDebugTarget
            """
            
        
        
        self.gl.glViewport(0, 0, self.imgWidth, self.imgHeight) # Out res is [512,512] setting by default
        
        
        print("GL Init")
        self.findPrefixNumber()
        
        # If it exists, set the values
        if self.imgWidth>0 and self.imgHeight>0:
            self.setTexelSize( [self.imgWidth, self.imgHeight] )
        
        
        
            
        self.parent.createControls( self.glControls )
        
        self.initialized = True
        
        self.paintGL()
        
    def setVertexBuffer( self, dataList, stride, glProgram, glAttrName ):
        vbo = QtGui.QOpenGLBuffer( QtGui.QOpenGLBuffer.VertexBuffer )
        vbo.create()
        vbo.bind()
        
        vbo.setUsagePattern( QtGui.QOpenGLBuffer.StaticDraw ) # Setting - gl.GL_STATIC_DRAW

        vertices = np.array( dataList, np.float32 )
        vbo.allocate( vertices, vertices.shape[0] * vertices.itemsize )

        attributeLocation = glProgram.attributeLocation( glAttrName )
        glProgram.enableAttributeArray( attributeLocation )
        glProgram.setAttributeBuffer( attributeLocation, self.gl.GL_FLOAT, 0, stride )
        #vbo.release()

        return vbo
        
    # -- -- --
        
    def buildRenderPassDebug( self, debugLabel="Debug Display", renderPassDict=None ) :
        # Find Object with Supported 'object.toImage()'
        if self.parent :
            if hasattr( self.parent, "buildDebugDisplay" ) :
                self.parent.buildDebugDisplay(  )
            
        return None,None
        
        """
            curPassDataDict['debugTarget'] = self.buildRenderPassDebug( curPassDataDict )
            

        self.buildRenderPassDebug(  )
        self.glRenderPassList = [] # Render Pass Order
        self.glProgramList = {} # Render Pass Data
        self.targetDisplayQtWidgets = {}
        """
        
        
    def drawToDebugWidgets(self):
        if hasattr(self.parent,'bufferDisplay'):
            curFboObj=None
            try:
                curFboObj = self.glProgramList[self.renderPassNames['fbo']]['fboObject']
            except:
                pass;
            if curFboObj:
                curFboObj.bind()
                pix = QtGui.QPixmap.fromImage( curFboObj.toImage(True) )
                curFboObj.release()
                
                pix= pix.transformed(QtGui.QTransform().scale(1, -1))
                self.parent.bufferDisplay.setPixmap( pix )
            
        if hasattr(self.parent,'swapDisplay'):
            curFboObj=None
            try:
                curFboObj = self.glProgramList[self.renderPassNames['fboSwap']]['fboObject']
            except:
                pass;
            if curFboObj:
                curFboObj.bind()
                pix = QtGui.QPixmap.fromImage( curFboObj.toImage(True) )
                curFboObj.release()
                
                pix= pix.transformed(QtGui.QTransform().scale(1, 1))
                self.parent.swapDisplay.setPixmap( pix )
            

        #self.paintGL()
        if hasattr(self.parent,'renderDisplay'):
            outImage = self.grabFramebuffer()
            pix = QtGui.QPixmap.fromImage( outImage )
            self.parent.renderDisplay.setPixmap( pix )
            
        self.gl.glFinish()
        
        return;
    
    #def releaseTextureGL( self, activeTextureId, bindTextureId )
    
    # Bind exising textures to existing Shader Uniforms
    #   Its asumed the dictionary info is always up to date
    #     As it should be using memory linked objects
    # TODO : Support Double Buffer Swap Bindings, 'GL_BACK'
    def bindTextureSamplers(self, glProgramPassName, glProgramDataDict ):

        curPassDataDict = glProgramDataDict[ glProgramPassName ]
        curPassType = curPassDataDict['passType']
        curPassProgram = curPassDataDict['program']
        curPassSamplers = curPassDataDict['samplers']
        
        
        # This function should only run at render time
        #   Might be useful adding some checks, for custome bind needs
        #curPassProgram.bind()
        
        returnObjectReleaseFuncs = []
        samplerRunner=0
        #textureBind
        #print(" Bind Textures - ",glProgramPassName)
        #print(curPassSamplers.keys())
        for curSamplerUniform in curPassSamplers:
            curSamplerData = curPassSamplers[ curSamplerUniform ]
            curBindType = curSamplerData['type']
            curBindTexture = curSamplerData['texture']
            curBindLocation = curSamplerData['location']
            
            
            # TODO : Likely better to put this on some async "TryAgain" list at a sparse interval
            if curBindLocation < 0:
                # Attempt to parse unlocated Sampler Uniform durring 'buildUniforms()' 
                uLocation = curPassProgram.uniformLocation( curSamplerUniform )
                if uLocation >= 0 :
                    curBindLocation = uLocation
                    curSamplerData['location'] = uLocation
                else:
                    # Sampler Uniform location not found, bypass texture bind
                    #   May be developer error, leaving a Uniform Dict entry, or missspelling in shader,
                    #     More likely, the OpenGL compiler is optimizing out the Uniform, removing it
                    #       From lack of any contribution to the final output color in the code
                    continue;
            
            
            
            
            #curSamplerData['type']
            #curBindTexture.bind()# curSamplerData['location'] )
            #returnObjectReleaseFuncs.append( curBindTexture )
            
            #print(curSamplerUniform)
            #print(curSamplerData)
            #fboProgram.bind()
            #fboProgram.release()
            
            
            self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + curBindLocation )
            #texBindLocation = curBindLocation # self.gl.GL_TEXTURE0 + curBindLocation
            #print(texBindLocation)
            
            #curBindTexture.bind( curBindTexture.textureId() )
            curBindTexture.bind( curBindLocation )
            #curPassProgram.setUniformValue( curSamplerUniform, curBindTexture.textureId() )
            curPassProgram.setUniformValue( curSamplerUniform, curBindLocation )
            
            returnObjectReleaseFuncs.append( partial( curBindTexture.release, curBindLocation ) )
            
            
            """
            program.bind()
            self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
            self.gl.glUniform1i( program.uniformLocation('samplerTex'), 0 )
            self.gl.glActiveTexture( self.gl.GL_TEXTURE1 )
            self.gl.glUniform1i( program.uniformLocation('bufferRefTex'), 1 )
            program.release()
            """
            
            #partial( curBindTexture.release()
            
            """
            if curSamplerData['type'] == "texture" :
            
                #self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + curBindLocation )
                texBindLocation = curBindLocation # self.gl.GL_TEXTURE0 + curBindLocation
                #print(texBindLocation)
                
                #curBindTexture.bind( curBindTexture.textureId() )
                curBindTexture.bind( texBindLocation )
                #curPassProgram.setUniformValue( curSamplerUniform, curBindTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, texBindLocation )
                
                returnObjectReleaseFuncs.append( partial( curBindTexture.release, texBindLocation ) )
            elif curSamplerData['type'] == "fbo" :
                
                curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject']
                #curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboTexture']
                
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + curBindLocation )
                
                #curFboTexture.bind( curFboTexture.textureId() )
                #curFboTexture.bind( curBindLocation )
                self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, curFboTexture.texture())
                #curPassProgram.setUniformValue( curSamplerUniform, curFboTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, curBindLocation )
                
                returnObjectReleaseFuncs.append( curFboTexture )
                returnObjectReleaseFuncs.append( partial( self.releaseTextureGL, texBindLocation ) )
                
            
            elif curSamplerData['type'] == "fboSwap" :
                curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject']
                #curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboTexture']
                
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + curBindLocation )
                
                #curFboTexture.bind( curFboTexture.textureId() )
                #curFboTexture.bind( curBindLocation )
                self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, curFboTexture.texture())
                #curPassProgram.setUniformValue( curSamplerUniform, curFboTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, curBindLocation )
                
                returnObjectReleaseFuncs.append( curFboTexture )
                
            elif curSamplerData['type'] == "toScreen" :
                # Not implemented
                pass;
            """
        #curPassProgram.release()
        
        # Sampler Binds should be complete
        return returnObjectReleaseFuncs
    
    def bindRenderPass( self, glRenderPassName, glRenderPassesData=None ):
        if glRenderPassesData == None:
            # I don't like using self here, but fall back data
            #   Since most cases, this will be the dict to use
            # Intentions, to allow other Contexts to pass data externally
            glRenderPassesData = self.glProgramList
    
        #print(" -- -- -- -- -- -- -- --")
        
        glProgramData = glRenderPassesData[ glRenderPassName ]
        glPassType = glProgramData['passType']
        glPassProgram = glProgramData['program']
        #glPassUniforms = glProgramData['uniforms']
        glPassTextures = glProgramData['textures']
        glPassFBO = glProgramData['fboObject']
        glPassGeoObject = glProgramData['geoObject']
        
        """
        if glRenderPassName == glPassType:
            print( "Rendering '"+glRenderPassName+"' pass" )
        else:
            print( "Rendering '"+glRenderPassName+"' as '"+glPassType+"' pass" )
        """
        
        # -- -- --
        
        if not glPassProgram.isLinked() :
            print("Render Pass Shader has Unlinked")
        
        #print( glPassFBO )
        
        glPassProgram.bind()
        if glPassFBO:
            glPassFBO.bind()
        else:
            QtGui.QOpenGLFramebufferObject.bindDefault()
        
        """
        for textureData in glPassTextures:
            txUniform = textureData['uniformName']
            txUniformBind = textureData['uniformBind']
            txObject = textureData['texture']
            txObject.bind( txUniformBind )
        """
        
        
        curTextureReleaseList = self.bindTextureSamplers( glRenderPassName, glRenderPassesData )
        
        glPassGeoObject.bind()
        
            
        # -- -- --
        
        self.gl.glViewport( 0, 0, self.imgWidth, self.imgHeight )
        self.gl.glClear( self.gl.GL_COLOR_BUFFER_BIT )
        self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
        
        
        # -- -- --
            
            
        glPassGeoObject.release()
        
        
        for boundTextureFunc in curTextureReleaseList:
            boundTextureFunc()
            #boundTextureFunc.release()
            
        #self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, 0)
        #self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
        
        if glPassFBO:
            glPassFBO.release()
            
        glPassProgram.release()
            
        
        self.gl.glFinish()
        
        # -- -- --
        
        # -- -- --
        
        
        
    def paintGL(self):
        glContinue = False
        if self.isContextInitialized() :
            pass;
    
        # Lock Context to prevent Release and potential PyQt Application Crash
        self.glContextReleased = False
    
        #print("Init render")
        
        #print("Render ",self.glEffect," - ",str(self.id)," -- ")
        
        
        for renderPass in self.glRenderPassList:
            curPassDataDict = self.glProgramList[ renderPass ]
            curPassProgram = curPassDataDict['program']
            
            self.bindRenderPass( renderPass, self.glProgramList )
        
        
        #print("Did it draw?")
        if self.saveNextRender :
            self.saveBuffer( "current", saveName="colorOut", doPaint=False )
            
        self.saveNextRender = False
        
        self.drawToDebugWidgets()
        
        #self.swapSurfaceBuffers()
        
        self.gl.glFinish()
        
        #self.disableContext( True )
        
        #print("Render Completed")
            
    @QtCore.pyqtSlot()
    def frameSwapComplete(self):
        #print("Frame Swap Complete")
        #self.disableContext( True )
        
        return;
        
    @QtCore.pyqtSlot()
    def simTimeout(self):
        if self.hasSim :
            self.simTimerRunner += 1
            
            self.paintGL()
            
            if self.simTimerRunner <= self.simTimerRunCount :
                self.setStatusBar(" Shader '"+self.glEffect+"' run sim "+str(self.simTimerRunner), 0)
                #simStep
                self.simTimer.start( self.simTimerIterval )
            else:
                self.setStatusBar(" Shader '",self.glEffect,"' finished sim run")
                self.setStatusBar(" Shader '"+self.glEffect+"' finished "+str(self.simTimerRunCount)+" sim steps", 1)
                self.simTimerRunner = 0
        return;
        
    # For Saving -
    # http://bazaar.launchpad.net/~mcfletch/openglcontext/trunk/view/head:/tests/saveimage.py
    def resizeGL(self, w, h):
        self.gl.glViewport(0, 0, w, h)
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
        if 'userOffset' in self.builtinControlledUniforms : 
            if setOffset :
                self.curOffset=[x,y]
            #self.gl.glUseProgram(0)
    def imageScale(self,x,y, setScale=True):
        if 'userScale' in self.builtinControlledUniforms : 
            if setScale :
                self.curScale=[x,y]
            #self.gl.glUseProgram(0)
    def setTexelSize(self, imgRes=None ):
        # If it exists, set the values
        if 'texelSize' in self.builtinControlledUniforms:
            if type(imgRes) == list and len(imgRes)==2 :
                if imgRes[0]==0 or imgRes[1]==0:
                    print("Attempted to set Texel Size to [0,0], stopping Uniform update")
                    return;
                tx = 1.0 / float( imgRes[0] )
                ty = 1.0 / float( imgRes[1] )
                #print( "Set 'texelSize' - [",tx,",",ty,"]" )
                self.setBuiltinUniformValues( "texelSize", [tx,ty], True, False )
            else:
                print("Incorrect Image Resolution sent to 'setTexelSize'")
        #else:
        #    print("Shader '",self.glEffect,"'; No 'texelSize' in shader program uniforms")
    
    
    # Update found Builtin's Values, with blending influence per builtin uniform
    # TODO : Input 'toValue' is assumed to be correct shape, could lead to issues
    def lerpBuiltinUniformValues(self, builtinName, toValue, allPasses=True, doPaint=True ):
        if builtinName in self.builtinControlledUniforms:
            for renderPass in self.builtinControlledUniforms[builtinName]:
                for builtinControlled in self.builtinControlledUniforms[builtinName][renderPass]:
                    curBuiltinName = builtinControlled
                    curBuiltinData = self.builtinControlledUniforms[builtinName][renderPass][curBuiltinName]
                    curType = curBuiltinData['type']
                    curValue = curBuiltinData['value']
                    curPreviousValue = curBuiltinData['prevValue']
                    curBlendRate = curBuiltinData['blendRate']
                    curValueType = type(curValue)
                    if curBlendRate == 0.0: # No Blending, Holding Current Value
                        continue;
                    if curValueType == float:
                        curBuiltinData['prevValue'] = curValue
                        curBuiltinData['value'] = toValue
                    elif curValueType == int:
                        # No blending for now
                        curBuiltinData['prevValue'] = curValue
                        curBuiltinData['value'] = toValue
                    
                    elif curValueType == list :
                        if curBlendRate == 1.0: # No Blending, Set as 'toValue'
                            # would a copy through [*value] be better ??
                            for x,v in enumerate( toValue ):
                                curBuiltinData['prevValue'][x] = curValue[x]
                                curBuiltinData['value'][x] = v
                        else: # Has Blending, Mix Current Value with 'toValue'
                            for x,v in enumerate( toValue ):
                                curBuiltinData['prevValue'][x] = curValue[x]
                                curBuiltinData['value'][x] = curValue[x]*(1.0-curBlendRate) + v*curBlendRate
                    print( "prev val",curBuiltinData['prevValue']," - new val", curBuiltinData['value'])
            self.setRenderPassUniforms( self.builtinControlledUniforms[builtinName], [tx,ty], allPasses, doPaint )
        else:
            print(" ! Warning ! No previously assigned Builtin's Uniform Dict for '"+builtinName+"'")
            
    def setBuiltinUniformValues(self, builtinName, toValue, allPasses=True, doPaint=True ):
        if builtinName in self.builtinControlledUniforms:
            for renderPass in self.builtinControlledUniforms[builtinName]:
                for builtinControlled in self.builtinControlledUniforms[builtinName][renderPass]:
                    curBuiltinName = builtinControlled
                    curBuiltinData = self.builtinControlledUniforms[builtinName][renderPass][curBuiltinName]
                    curType = curBuiltinData['type']
                    curValue = curBuiltinData['value']
                    curPreviousValue = curBuiltinData['prevValue']
                    curValueType = type(curValue)
                    
                    if curValueType == float:
                        curBuiltinData['prevValue'] = curValue
                        curBuiltinData['value'] = toValue
                    elif curValueType == int:
                        # No blending for now
                        curBuiltinData['prevValue'] = curValue
                        curBuiltinData['value'] = toValue
                    elif curValueType == list :
                        for x,v in enumerate( toValue ):
                            curBuiltinData['prevValue'][x] = curValue[x]
                            curBuiltinData['value'][x] = v
                            
                    print( "prev val",curBuiltinData['prevValue']," - new val", curBuiltinData['value'])
            contextState = self.setRenderPassUniforms( self.builtinControlledUniforms[builtinName], allPasses, doPaint )
        else:
            print(" ! Warning ! No previously assigned Builtin's Uniform Dict for '"+builtinName+"'")
            
    # Seems overkill to have as a separate method, need to consider future needs
    def setRenderPassUniforms(self, uniformData, allPasses=True, doPaint=True ):
        if type(uniformData) == dict:
            if not self.enableContextCheck():
                print( " ! GL Context can't be made Current, Canceling ! ")
                return False
            
            for dataKey in uniformData:
                # { Render Pass Name : { Uniform Name : {Type, Value} } }
                #     Currently, Render Pass Builtin's Uniform Dict Passed
                #       From 'self.updateBuiltinUniformValues()'
                if dataKey in self.glRenderPassList:
                    print( " -- -- -- -- " )
                    targetProgramDict = self.glProgramList[ dataKey ]
                    targetProgram = targetProgramDict['program']
                    
                    targetProgram.bind()
                    
                    for targetUniform in uniformData[dataKey]:
                        curUniformName = targetUniform
                        curUniformType = uniformData[dataKey][targetUniform]['type']
                        curUniformValue = uniformData[dataKey][targetUniform]['value']
                        print("SetRenderPassUniforms", curUniformName,curUniformType,curUniformValue )
                        self.setUniformValue( targetProgram, curUniformName, curUniformType, curUniformValue )
                    
                    targetProgram.release()
                    
                # Specific Render Pass Uniform Dict Passed; `self.glProgramList`
                else:
                    print(" ! Warning ! Only Render Pass Dict accepted as 'uniformData' argument to 'self.setUniformValue()' *WIP*")
            
            self.disableContext()
                    
            if doPaint:
                self.update()
                self.paintGL()
            return True
        else:
            # Uhh.... Current shader program maybe?
            #   But not storing that, yet
            print(" ! Warning ! Please pass a render pass data dictionary as the 'uniformData' argument to 'self.setUniformValue()'")
            return None
    def setControllerUniformValue( self, renderPass, uniformName, toValue ):
        #print( renderPass, uniformName, toValue )
        #print( self.glProgramList )
        if renderPass in self.glProgramList and uniformName in self.glProgramList[renderPass]['uniforms']:
            # TODO : Set value for UserSettingsManager
            #          To maintain image values cross current images & sessions
            #self.glProgramList[renderPass]['uniforms'][uniformName]
            curProgram = self.glProgramList[renderPass]['program']
            
            curProgram.bind()
            
            curUniformData = self.glProgramList[renderPass]['uniforms'][uniformName]
            curUniformType = curUniformData['type']
            curUniformValue = toValue
            self.setUniformValue( curProgram, uniformName, curUniformType, curUniformValue )
            
            curProgram.release()
            
            self.update()
            self.paintGL()
            
    def setUniformValue(self, glProgram, uniformName, uniformType, uniformValue ):
        # Should check for current context and current program prior to setting values
        #   Currently, I want to reduce the ammount of context switching, even shared
        #     And binding/releasing of programs
        #   These are handled in 'self.setRenderPassUniforms()' as its the only function using this method
        #     There will be more soon though...
        if uniformType == "float":
            uniformValue = uniformValue[0] if type(uniformValue)==list else uniformValue
            glProgram.setUniformValue( uniformName, uniformValue )
        elif uniformType == "int":
            uniformValue = uniformValue[0] if type(uniformValue)==list else uniformValue
            glProgram.setUniformValue( uniformName, uniformValue )
        elif uniformType == "vec2":
            glProgram.setUniformValue( uniformName, uniformValue[0], uniformValue[1] )
        elif uniformType == "vec3":
            glProgram.setUniformValue( uniformName, uniformValue[0], uniformValue[1], uniformValue[2] )
        elif uniformType == "vec4":
            glProgram.setUniformValue( uniformName, uniformValue[0], uniformValue[1], uniformValue[2], uniformValue[3] )
        elif uniformType == "texture":
            print(" ! Warning ! Setting a texture to a target uniform through `setUniformValue()` is not supported.")
        elif uniformType in self.glRenderPassList:
            print(" ! Warning ! Setting a fbo's texture to a target uniform through `setUniformValue()` is not supported.")
        """
        toValue = [toValue] if type(toValue) == float else toValue
        if len(toValue) == 1:
            self.gl.glUniform1f( uLocation, toValue[0] )
        elif len(toValue) == 2:
            self.gl.glUniform2f( uLocation, toValue[0], toValue[1] )

            
        #self.gl.glUseProgram(0)
        """
    def saveNextPass(self):
        self.saveNextRender = True
        #self.textureGLWidget.paintGL()
        
    def saveBuffer(self, sourceBuffer=None, savePath=None, saveName="bufferOut", saveFormat=None, stepFrameCount=True, doPaint=True ):
        # Handle the new Context Locking for saving buffer renders
        #if doPaint:
        #    self.paintGL()
        
        #self.gl.glUseProgram(self.glProgram)
        outImage = None
        if self.outImagePrefix == None:
            self.findPrefixNumber( savePath )
        if sourceBuffer != "current":
            if self.hasFboProgram :
                foundImageData = False
                for renderPass in self.glProgramList :
                    curPassData = self.glProgramList[renderPass]
                    if 'passType' in curPassData and curPassData['passType'] == "fbo":
                        # Gonna be pretty slow here for fboTexture
                        #   Might be better to swap shader render it to a fbo  ::shrugs::
                        #     Needs testing it even works
                        if 'fboTexture' in curPassData and curPassData['fboTexture'] :
                            outImage = self.gl.glGetTexImage( self.gl.GL_TEXTURE_2D, curPassData['fboTexture'], self.gl.GL_RGB, self.gl.GL_UNSIGNED_BYTE, outputType=None )
                        elif 'fboObject' in curPassData and curPassData['fboObject'] :
                            outImage = curPassData['fboObject'].toImage()
                        if outImage != None:
                            foundImageData = True
                            break;
                if not foundImageData:
                    outImage = self.grabFramebuffer()
            else:
                try:
                    sourceBuffer.bind()
                    outImage = sourceBuffer.toImage(True)
                except:
                    print("Failed to bind buffer")
                    outImage = self.grabFramebuffer()
        else:
            outImage = self.grabFramebuffer()
        
        
        if savePath == None:
            savePath = self.outImageFolderPath
        if saveFormat == None:
            saveFormat = self.outImageFormat
        
        extDict = {}
        extDict['JPEG'] = "jpg"
        extDict['PNG'] = "png"
        
        print( savePath )
        print( saveFormat )
        
        # TODO : Detect Buffer Format, GL_RGB vs GL_RGBA
        # TODO : Catch and correct JPEG output when Buffer has Alpha Channel
        
        saveExt = extDict[saveFormat]
        
        savePrefix = self.outImagePrefix
        
        if stepFrameCount:
            self.outCurSaveCount += 1
            
        saveFrameNumber = str( self.outCurSaveCount ).zfill( self.outCurSaveCountPad )
        
        saveFileName = savePrefix + "_" + saveName + "_" + saveFrameNumber + "."+saveExt
        saveOutPath = os.path.join( savePath, saveFileName )
        
        print( saveOutPath )
        
        try:
            outImage.save( saveOutPath, saveFormat )
            print( "Finished Saving - ", saveOutPath )
        except OSError as err:
            print("Error saving '",saveName,"' to - ", saveOutPath )
            
        #if sourceBuffer != "current":
        #    sourceBuffer.release()
        #self.gl.glUseProgram(0)
        
    def findPrefixNumber( self, scanFolder=None ):
        if scanFolder == None:
            scanFolder = self.outImageFolderPath
        #print("Scan Folder Prefixes")
        
        if os.path.isdir( scanFolder ):
            folderList=os.listdir( scanFolder )
            
            prefixValue = 0
            if len(folderList)>0:
                def parseIntPrefix( inStr ):
                    curPrefix = ""
                    for x in range( len(inStr) ):
                        if inStr[x].isnumeric() :
                            curPrefix += inStr[x]
                        else:
                            break;
                    return int(curPrefix) if curPrefix != "" else 0
                
                foundPrefixes = list(map(lambda x: parseIntPrefix(x), folderList))
                foundPrefixes = list(set(foundPrefixes))
                
                curFoundPrefix = foundPrefixes[-1] if len(foundPrefixes)>0 and foundPrefixes[-1]!=None else -1
                prefixValue = curFoundPrefix+1
            
            self.outImagePrefix = str( prefixValue ).zfill( self.outImagePad )
            print( "Current Prefix - '", self.outImagePrefix, "'" )
        else:
            print( "Failed to find save folder - ", scanFolder )
            self.outImagePrefix = "0".zfill( self.outImagePad )
    
    def setStatusBar( self, message=None, importance=0, setTimeout=True ):
        if message == None:
            print( "Message==None passed to set window status bar" )
            return;
        if hasattr( self.parent, 'setStatusBar') :
            self.parent.setStatusBar( message, importance, setTimeout )
        else:
            print( message )
    
    def destroyTypedObject( self, glObject = None ):
        print("Destroy type - "+str(type(glObject)))
        
        # self.gl.glIsBuffer
        # self.gl.glIsEnabled
        # self.gl.glIsList
        # self.gl.glIsProgram
        # self.gl.glIsQuery
        # self.gl.glIsShader
        # self.gl.glIsTexture
        return;
    
    # Assume - Destory All; GPU & CPU Objects
    # 'objectToDestroy' should be a Render Pass Dict
    #   To properly clean memory links in dicts
    # But OpenGL or QOpenGL objects will still dump and destroy
    #   This is the primary concern when destroying any pxlViewportGL Object
    def destroy( self, objectToDestroy=None ):
        print("!! pxlViewportGL.ImageShaderGL.destroy() !!")
        print( type(objectToDestroy) )
        
        renderPassCleanupList = []
        
        # TODO : Develop !None Checks
        if objectToDestroy != None:
            destroyObjType = type(objectToDestroy)
            if destroyObjType == str:
                if destroyObjType in self.glRenderPassList:
                    renderPassCleanupList.append( objectToDestroy )
                else:
                    #Add more cases
                    pass;
            elif destroyObjType == dict:
                destroyObjKeys = list(objectToDestroy.keys())
        else:
            # glRenderPassList and glProgramList should be in-sync
            #   If not, merge keys for cleaning up stragglers
            #     If there are stragglers, I messed up somewhere
            # Known Render Pass Names
            renderPassCleanupList = [*self.glRenderPassList]
            # Merge Program List Render Pass Data
            renderPassCleanupList = list(set( list(objectToDestroy.keys()) + self.glProgramList.keys() ))
            
        # TODO : Add deletion for non RenderPass Objects
        for renderPass in renderPassCleanupList:
            print("Destroy "+renderPass)
            if renderPass in self.glProgramList:
                for passEntry in self.glProgramList[renderPass]:
                    print(" - Destory '"+passEntry+"'  '"+str(type(self.glProgramList[renderPass][passEntry]))) 
        """
        'geoObject'
        QOpenGLVertexArrayObject.destroy()
        ['vboObjects']
        QOpenGLBuffer.destroy()
        :
            curPassDataDict = self.glProgramList[ currentPassName ]
                "passType":None,
                "uniforms":None, # ShaderName.py Uniforms Dict
                "samplers":None, # { Uniform Name : {self.glPassSamplerDict.copy()} }
                "program":None,
                "builtins":None, # Easy lookup of "native builtin" uniform types { BuiltIn : Uniform Name }
                "textures":None, # [ self.glPassTextureDict.copy() ]
                "fboObject":None,
                "fboLocation":None,
                "fboTexture":None,
                "geoObject":None,
                "vboObjects":None # Stored for Memory Cleanup reasons
        """
        """
        self.glContext
        
        if objectToDestroy == None:
            #Delete All
            pass;
        self.gl.glDeleteVertexArrays( 1, vaos );
        self.gl.glDeleteBuffers( 1, vbos );
        self.gl.glDeleteBuffers( 1, fbos );
        
        QOpenGLTexture.destroy()
        """
        
        self.destroyLater()
        
        
class ImageShaderWidget(QWidget):
    def __init__(self,parent=None, glId=0, glContextManager=None, glEffect="default", initTexturePath="assets/glTempTex.jpg", saveImagePath=None ):
        super(ImageShaderWidget, self).__init__(parent)
        
        self.id=glId
        self.fullPath = ""
        self.fileName = ""
        self.folderName = ""
        self.folderPath = ""
        self.dispImagePath = ""
        self.data = {}
        
        
        # TODO : Check For Global Shared Context if no glContextManager
        #          Else, create non-shared context
        self.glContextManager = glContextManager
        self.glSharedContext = None
        self.glFormat = None
        
        if glContextManager :
            self.glSharedContext, self.glFormat = glContextManager.checkContextState()

        
        self.glEffect = glEffect
        self.initTexturePath = initTexturePath
        self.saveImagePath = saveImagePath
        
        self.textureGLWidget = None
        
        # -- -- --
        
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setSpacing(2)
        
        self.viewportLayout = QHBoxLayout()
        self.viewportLayout.setContentsMargins(0,0,0,0)
        self.viewportLayout.setSpacing(2)
        self.mainLayout.addLayout(self.viewportLayout)
        
        # -- -- --
        
        textureGLWidgetBlock = QWidget()
        self.textureGLWidgetLayout = QHBoxLayout()
        self.textureGLWidgetLayout.setContentsMargins(0,0,0,0)
        self.textureGLWidgetLayout.setSpacing(0)
        textureGLWidgetBlock.setLayout( self.textureGLWidgetLayout )
        self.viewportLayout.addWidget( textureGLWidgetBlock )
        
        # -- -- --
        
        shaderSideBarBlock = QWidget()
        self.shaderSideBarLayout = QVBoxLayout()
        self.shaderSideBarLayout.setContentsMargins(0,2,0,2)
        self.shaderSideBarLayout.setSpacing(5)
        shaderSideBarBlock.setLayout(self.shaderSideBarLayout)
        shaderSideBarBlock.setMaximumWidth(250)
        self.viewportLayout.addWidget(shaderSideBarBlock)
        
        # -- -- --
        
        self.shaderSideBarLayout.addStretch(1)
        
        # -- -- --
        
        shaderOptionsBlock = QWidget()
        self.shaderOptionsLayout = QVBoxLayout()
        self.shaderOptionsLayout.setContentsMargins(0,2,0,2)
        self.shaderOptionsLayout.setSpacing(5)
        shaderOptionsBlock.setLayout(self.shaderOptionsLayout)
        #shaderSideBarBlock.setMaximumWidth(250)
        self.shaderSideBarLayout.addWidget(shaderOptionsBlock)
        
        # -- -- --
        
        self.glButtonLayout = QHBoxLayout()
        self.glButtonLayout.setContentsMargins(0,0,0,0)
        self.glButtonLayout.setSpacing(5)
        self.shaderSideBarLayout.addLayout(self.glButtonLayout)
        
        saveRenderButton = QPushButton('Save Image', self)
        saveRenderButton.setToolTip('Save current ViewportGL to Image File')
        saveRenderButton.setFixedHeight(35)
        saveRenderButton.clicked.connect(self.saveRenderButton_onClick)
        self.glButtonLayout.addWidget(saveRenderButton)

        # -- -- --
        
        self.setLayout(self.mainLayout)
        
        # -- -- --
        
        # Global Shared Context Failed to Return
        #   Await Shared Context or Futher Instructions from ContextGLManager
        if self.glFormat == None:
            self.glContextManager.contextCreated.connect( self.setSharedGlContext )
            
        # Global Context Returned
        #   Continue building ImageShaderGL WindowContainer Widget
        else:
            print("Found Global Context")
            self.setSharedGlContext( self.glSharedContext )
        
    
    # Check if context already exists
    #   At that rate, context should just be passed anyway
    def getSharedGlContext(self):
        return;
    
    @QtCore.pyqtSlot( QtGui.QOpenGLContext )
    def setSharedGlContext(self, curContext=None ):
        print( " ImageShaderGL ",self.glEffect," - ",str(self.id)," recieved context; Valid - ", curContext.isValid() )
        if not self.textureGLWidget:
        
            textureGLDisplayBlock = QWidget()
            self.textureGLDisplayLayout = QVBoxLayout()
            self.textureGLDisplayLayout.setAlignment(QtCore.Qt.AlignCenter)
            self.textureGLDisplayLayout.setContentsMargins(0,0,0,0)
            self.textureGLDisplayLayout.setSpacing(2)
            textureGLDisplayBlock.setLayout(self.textureGLDisplayLayout)
            self.textureGLWidgetLayout.addWidget(textureGLDisplayBlock)
        
            self.textureGLWidget = TextureGLWidget( self, self.id, self.glFormat, curContext, self.glEffect, self.initTexturePath, self.saveImagePath )
            self.windowView = QWidget.createWindowContainer( self.textureGLWidget )
            self.windowView.setFixedWidth(512)
            self.windowView.setMinimumHeight(512)
            self.windowView.setMaximumHeight(512)
            self.textureGLDisplayLayout.addWidget(self.windowView)
            
            curLabel = QLabel('Final Output Pass', self)
            curLabel.setMaximumHeight(30)
            curLabel.setAlignment(QtCore.Qt.AlignCenter)
            self.textureGLDisplayLayout.addWidget( curLabel )
            
            # -- -- --
            
            bufferDisplayBlock = QWidget()
            self.bufferDisplayLayout = QVBoxLayout()
            self.bufferDisplayLayout.setAlignment(QtCore.Qt.AlignCenter)
            self.bufferDisplayLayout.setContentsMargins(0,0,0,0)
            self.bufferDisplayLayout.setSpacing(2)
            bufferDisplayBlock.setLayout(self.bufferDisplayLayout)
            self.textureGLWidgetLayout.addWidget(bufferDisplayBlock)
            
            self.bufferDisplay = QLabel(self)
            self.bufferDisplay.setFixedWidth(512)
            self.bufferDisplay.setMinimumHeight(512)
            self.bufferDisplay.setMaximumHeight(512)
            self.bufferDisplayLayout.addWidget(self.bufferDisplay)
            
            curLabel = QLabel('#1 Render Pass, FBO', self)
            curLabel.setMaximumHeight(30)
            curLabel.setAlignment(QtCore.Qt.AlignCenter)
            self.bufferDisplayLayout.addWidget( curLabel )
        
            # -- -- --
            
            swapDisplayBlock = QWidget()
            self.swapDisplayLayout = QVBoxLayout()
            self.swapDisplayLayout.setAlignment(QtCore.Qt.AlignCenter)
            self.swapDisplayLayout.setContentsMargins(0,0,0,0)
            self.swapDisplayLayout.setSpacing(2)
            swapDisplayBlock.setLayout(self.swapDisplayLayout)
            self.textureGLWidgetLayout.addWidget(swapDisplayBlock)
            
            self.swapDisplay = QLabel(self)
            self.swapDisplay.setFixedWidth(512)
            self.swapDisplay.setMinimumHeight(512)
            self.swapDisplay.setMaximumHeight(512)
            self.swapDisplayLayout.addWidget(self.swapDisplay)
            
            curLabel = QLabel('#2 Render Pass, FBO Swap', self)
            curLabel.setMaximumHeight(30)
            curLabel.setAlignment(QtCore.Qt.AlignCenter)
            self.swapDisplayLayout.addWidget( curLabel )
            
            # -- -- --
            
            renderDisplayBlock = QWidget()
            self.renderDisplayLayout = QVBoxLayout()
            self.renderDisplayLayout.setAlignment(QtCore.Qt.AlignCenter)
            self.renderDisplayLayout.setContentsMargins(0,0,0,0)
            self.renderDisplayLayout.setSpacing(2)
            renderDisplayBlock.setLayout(self.renderDisplayLayout)
            self.textureGLWidgetLayout.addWidget(renderDisplayBlock)
            
            self.renderDisplay = QLabel(self)
            self.renderDisplay.setFixedWidth(512)
            self.renderDisplay.setMinimumHeight(512)
            self.renderDisplay.setMaximumHeight(512)
            self.renderDisplayLayout.addWidget(self.renderDisplay)
            
            curLabel = QLabel('glReadPixel After Final Pass Swap Buffer', self)
            curLabel.setMaximumHeight(30)
            curLabel.setAlignment(QtCore.Qt.AlignCenter)
            self.renderDisplayLayout.addWidget( curLabel )
    
        
    def imageOffset(self,x,y, setOffset=True):
        if self.textureGLWidget:
            self.textureGLWidget.imageOffset(x,y,setOffset)
    def imageScale(self,x,y, setScale=True):
        if self.textureGLWidget:
            self.textureGLWidget.imageScale(x,y,setScale)
    def createControls( self, controls ):
    
        if self.textureGLWidget.hasSim :
            runSimButton = QPushButton('Run Sim', self)
            runSimButton.setToolTip('Run sim a set number of times')
            runSimButton.setFixedHeight(35)
            runSimButton.clicked.connect(self.textureGLWidget.simTimeout)
            self.glButtonLayout.addWidget(runSimButton)
            
            """
            # Commented to reduced confusion for non-developer users
            setTargetGLButton = QPushButton('Set TargetGL', self)
            setTargetGLButton.setToolTip('Pass swap buffer texture to another GL Context')
            setTargetGLButton.setFixedHeight(35)
            setTargetGLButton.clicked.connect(self.setTargetGLButton_onClick)
            self.glButtonLayout.addWidget(setTargetGLButton)
            """
    
        for uniform in controls:
            #print(uniform)
            uData = controls[uniform]
            controlLayout = QHBoxLayout()
            controlLayout.setContentsMargins(0,0,0,10)
            controlLayout.setSpacing(5)
            # -- -- --
            uLabelText = uniform
            uLabelText = "".join(list(map(lambda x: " "+x if x.isupper() else x, uLabelText)))
            uLabelText = uLabelText[0].capitalize() + uLabelText[1::]
            controlLabelText = QLabel( uLabelText, self)
            controlLabelText.setFont(QtGui.QFont("Tahoma",9,QtGui.QFont.Bold))
            #controlLabelText.setAlignment(QtCore.Qt.AlignCenter)
            #controlLabelText.setStyleSheet("border: 1px solid black;")
            controlLayout.addWidget(controlLabelText)
            # -- -- --
            self.shaderOptionsLayout.addLayout(controlLayout)
            # -- -- --
            
            if "[]" in uData['type']:
                continue;
            
            valList = [uData['value']] if type(uData['value']) in [float,int] else uData['value']
            valLimits = uData['range']
            multVal = max(list(map(lambda x: len(str(x)) if "." in str(x) else 1, valLimits)))
            sliderList = []
            for val in valList:
                curSlider = QSlider( QtCore.Qt.Horizontal )
                curSlider.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                #curSlider.setGeometry(30, 40, 200, 30)
                curSlider.setMinimum( int(valLimits[0]*(10**multVal)) )
                curSlider.setMaximum( int(valLimits[1]*(10**multVal)) )
                curSlider.setValue( int(val*(10**multVal)) )
                #curSlider.valueChanged[float].connect(lambda: self.updateUniformValue(curSlider,uniform))
                controlLayout.addWidget(curSlider)
                sliderList.append(curSlider)
            for slider in sliderList:
                slider.valueChanged.connect(partial(self.updateUniformValue,uData['passName'],uniform,sliderList,multVal))
    
    @QtCore.pyqtSlot()
    def saveRenderButton_onClick(self):
        print("Save ViewportGL to Disk")
        print( self.saveImagePath )
        
        #self.textureGLWidget.saveNextPass()
        #return;
        
        colorFileName = self.glEffect+"Out"
        
        if self.textureGLWidget.hasFrameBuffer :
            colorFileName = self.glEffect+"_colorOut"
            bufferFileName = self.glEffect+"_bufferOut"
            self.textureGLWidget.saveBuffer( sourceBuffer=self.textureGLWidget.frameBufferObject, saveName=bufferFileName )
        self.textureGLWidget.saveBuffer( sourceBuffer=0, saveName=self.glEffect+"Out" )
        
    @QtCore.pyqtSlot()
    def setTargetGLButton_onClick(self):
        glTextureWidget = None
        
        try:
            glTextureWidget = super().parent().parent().parent().glTexture
        except:
            pass;
            
        #if glTextureWidget != None:
        #    print( "Passing Target GL Context" )
        #    self.textureGLWidget.setTargetGLObject( glTextureWidget.textureGLWidget )
        print( "-- Not Setting TargetGL, Logic Has Changed, Cancelling --" )
            
    def updateUniformValue(self, renderPass, uniform, sliderList, decimalCount):
        toValue = []
        for slider in sliderList:
            toValue.append( slider.value()/(10**decimalCount) )
        self.textureGLWidget.setControllerUniformValue( renderPass, uniform, toValue )
        
    def grabFrameBuffer(self, withAlpha=False):
        return self.textureGLWidget.grabFrameBuffer(withAlpha=withAlpha)
    
    def passTargetGL( self, targetGL = None ):
        print( "Passing TargetGL To GL Viewport Object" )
        print( targetGL )
        print( "-- Not Passing To Target, Logic Has Changed, Cancelling --" )
        #if targetGL != None:
        #    self.textureGLWidget.setTargetGLObject( targetGL )
    
    def setStatusBar( self, message=None, importance=0, noTimeout=False ):
        if message == None:
            print( "Message==None passed to set window status bar" )
            return;
        if hasattr( self.parent, 'setStatusBar') :
            self.parent.setStatusBar( message, importance, noTimeout )
        else:
            print( message )
            
    def destroy( self ):
        print("pxlViewportGL.ImageShaderGL.destroy() not fully implement yet")
        if self.textureGLWidget:
            self.textureGLWidget.destroy()
        self.destroyLater()
            
# main function
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
 
    # app created
    app = QApplication(sys.argv)
    w = TextureGLWidget()
    w.setupUI()
    w.show()
    
    #w = ImageLabelerWindow()
    #w.setupUI()
    #w.show()
    
    # begin the app
    sys.exit(app.exec_())