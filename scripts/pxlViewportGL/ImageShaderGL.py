
# Built on Python 3.10.6 && PyQt5 5.15.9

import sys, os, importlib
from PIL import Image
from functools import partial
import math

import ctypes
import numpy as np

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtOpenGL
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.uic import *

PVGL_ModuleName = os.path.basename( __file__ ).split(".")[0]


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

# TODO : Currently not utilizing swap buffers, opting for individual buffers
#          The primary GLWindow should use swap buffers for grabbing reasons
#            Don't want to restrict FBO renders, but would be helpful for sims
#              GL_FRONT & GL_BACK
# TODO : Get Render Passes set up for image editor "Effect Layers"
#          Makes it more similar to other graphics programs for workflow
#            Also allows for easy toggling at a GUI level, just don't render the pass
#          This should make use of swapping buffers though
# TODO : Store per shader visual control values from {'current image' path : [Render Passes] } ???
#          Might get a bit messy, but easier "jump back in" to prior settings per-image
# TODO : With binds and releases, updating a later pass in the render order, to only render from that pass on?
#          Data retains on gpu, but have seen odd results from 'toScreen' renders requiring re-rendering before usage
# TODO : Would be nice to allow for blending between arbitrary custome uniforms
#          However, ImageShaderGL is not real time just yet
#            But for future capacity, would be useful
# TODO : Test if [*array] is fast into 2 arrays than for-in and setting individual elements....
#          Typing it out sounds like [*array} would be faster
# TODO : Make higher level Builtin Uniforms Blending Values, as there is a lot of checks for needless functionality currently
#          Perhaps setting a {blend function} for updating the value per builtin dict entry
#            Bypassing 'self.lerpBuiltinUniformValues()'; see 'self.updateBuiltinUniformValues()' for now
# TODO : Investigate 'context.makeCurrent( QSurface )' and 'context.doneCurrent()' need with a shared GL Context

#class TextureGLWidget(QtWidgets.QOpenGLWidget):
class TextureGLWidget(QtGui.QOpenGLWindow):
#class TextureGLWidget(QtOpenGL.QGLWidget):
    def __init__(self,parent=None, glId=0, glFormat=None, sharingContext=None, glEffect="default", initTexturePath="assets/glTempTex.jpg", saveImagePath=None ):
        #QtWidgets.QOpenGLWidget.__init__(self,parent)
        #QtOpenGL.QGLWidget.__init__(self,parent)
        #QtOpenGL.QGLWidget.__init__(self, QtOpenGL.QGLFormat(), parent)
        #super(TextureGLWidget, self).__init__(parent) 
        super(TextureGLWidget, self).__init__( sharingContext ) 
        
        # -- -- --
        
        self.id = glId
        self.parent = parent
        self.glEffect = glEffect
        # The share context seemed to changed when not stored to some capacity
        #   Unsure if it was actually disconnecting
        #     But it returns a different value for `.shareContext()` at init
        self.glSourceContext = sharingContext
        self.glContext = None
        self.gl = None
        self.initialized = False
        
        
        
        # -- -- --
        
        self.profile = QtGui.QOpenGLVersionProfile()
        self.profile.setVersion( 2, 1 )
        
        
        self.glFormat = glFormat
        if self.glFormat == None :
            if sharingContext != None:
                self.glFormat = sharingContext.format()
            else:
                self.glFormat = QtGui.QSurfaceFormat()
                self.glFormat.setProfile( QtGui.QSurfaceFormat.CompatibilityProfile )    
                #self.glFormat.setProfile( QtGui.QSurfaceFormat.CoreProfile )
                self.glFormat.setVersion( 3, 3 )
                self.glFormat.setRenderableType( QtGui.QSurfaceFormat.OpenGL )
                #self.setSurfaceType( QtGui.QSurface.OpenGLSurface )
            
            # Holding off for now
            #self.glFormat.setDoubleBuffer(True)
            
            #self.glFormat.setAlpha( True )
            #self.glFormat.setDepth( False )
            #self.glFormat.setStencil( False )
            
        # -- -- --
        
        self.debugOpenGL = True
        self.glLogger = None
        if self.debugOpenGL and self.glFormat:
            print("Enabling OpenGL Debugger")
            self.glFormat.setOption(QtGui.QSurfaceFormat.DebugContext)
            self.glLogger = QtGui.QOpenGLDebugLogger(self)
            
        # -- -- --
            
        self.setFormat( self.glFormat )
        self.setSurfaceType( QtGui.QSurface.OpenGLSurface )
        
        print( self.glFormat.options() )
        
        self.useDoubleBuffer = False
        
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
        
        # Should FBO's be making an offscreen surface current context durring render passes?
        #self.glSrface = QtGui.QOffscreenSurface()
        #self.glSurface.setFormat( self.glFormat )
        #self.glSurface.create()
        
        
        # -- -- --
        
        # Mostly for verbose reasons
        #  If you want to custom name your passes,
        #    Update these values
        # TODO : Update this to be set by the Shader File itself
        #          Allowing for custom shader pipeline
        self.renderPassNames = {
                'fbo' : 'fbo',
                'fboSwap' : 'fboSwap',
                'toScreen' : 'toScreen'
            }
        
        
        
        self.hasSim = False
        self.simTimer = QtCore.QTimer(self)
        self.simTimer.setSingleShot(True)
        self.simTimerIterval = 100
        self.simTimerRunCount = 10
        self.simTimerRunner = 0
        self.simRunnerPercent = 0.0
        
        self.Shader = None # Shader Import File
        self.shaderSettings = {}
        self.hasFrameBuffer = False
        self.fboLocation = None
        
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        # -- -- -- -- -- -- -- -- -- -- --
        
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
                "geoObject":None
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
        
        self.glProgramList = {}
        self.glRenderPassList = []
        
        
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
        #       "userOffset" : [],
        #       "userScale" : [],
        #       "mousePos" : [],
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
        
        
        # When this file was setup through PyOpenGL
        #   Binding VBOs/EBOs & Texture at creation stayed connected
        #     Assuming since I was using `gl.GL_STATIC_DRAW`
        #   Seems I need to set more GL settings in this version of the script
        # For now, Binds will be done at render time, with expense
        self.glBindAtRender = True
        
        self.hasFboProgram = False
        self.glFboProgram = None
        self.glFboUniformLocations = {}
        self.glFboUniforms = {}
        
        self.glBufferSwapProgram = None
        
        self.glControls = {}
        
        
        self.glTempImage = None
        self.frameBufferObject = None
        self.fboTexture = None
        self.swapFrameBufferObject = None
        self.fboSwapTexture = None
        
        self.glTargetObject = None
        
        self.imgId = 0
        self.glTempTex = initTexturePath
        self.imgData = {}
        self.curImage = ""
        
        self.curOffset=[0,0]
        self.curScale=[1,1]
        
        self.imgWidth = 512
        self.imgHeight = 512
        
        self.maxWidth = 512
        self.maxHeight = 512
        self.setMaximumWidth( self.maxWidth )
        self.setMaximumHeight( self.maxHeight )
        #self.setFixedWidth( self.maxWidth )
        #self.setFixedHeight( self.maxHeight )
        
        # -- -- --
        
        self.offscreenVAO = None
        self.renderVAO = None
        self.positionVBO = None
        self.uvVBO = None
        
        # -- -- --
        
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
        
        # -- -- --
        
        self.mouseLocked = False
        self.mouseMoved = False
        self.mouseOrigPos = None
        self.mouseLockedPos = None
        self.mouseDelta = None
        self.mouseOffsetFitted = None
        self.mouseScaleFitted = None
        self.mouseButton = 0
        self.hasMousePosUniform = False
        
            
    # -- -- --
    
    def screenChanged(self):
        print("screenChanged")
    
    def frameSwapped(self):
        print("frameSwapped")
    
    
    # -- -- --
    
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
        
        print( curTextureDict )
        
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
        
    
    def newFrameBuffer(self, fboSize=[512,512], samplerName=None, isTargetOrSampler=False ):
        print( "Binding Data Frame Buffer")
        
        # Makes more logical sense to set up the fbo target manually
        #   Wanted to access it as a pyqt object at random times
        #     Not just a GL Texture Name, I know, I know, gl functions exist
        
        fboTargetImage = QtGui.QImage(fboSize[0], fboSize[1], QtGui.QImage.Format_RGBA8888)
        fboTargetImage.fill( QtGui.QColor(0,0,0,0) )
        
        #fboTargetTexture = QtGui.QOpenGLTexture(image=fboTargetImage, target=QtGui.QOpenGLTexture.Target2D, genMipMaps=QtGui.QOpenGLTexture.DontGenerateMipMaps )
        fboTargetTexture = QtGui.QOpenGLTexture(fboTargetImage)#, genMipMaps=QtGui.QOpenGLTexture.DontGenerateMipMaps )

        #else:
        #    fboTargetTexture.create()
        
        
        #print( "fboTargetTexture" )
        #print( fboTargetTexture.isCreated() )
        
        fboAttachment = QtGui.QOpenGLFramebufferObject.NoAttachment
        
        glFboFormat = QtGui.QOpenGLFramebufferObjectFormat()
        glFboFormat.setInternalTextureFormat( fboTargetTexture.format() )
        glFboFormat.setTextureTarget( fboTargetTexture.textureId() )
        glFboFormat.setMipmap( False )
        #glFboFormat.setAttachment( fboAttachment )        
        
        frameBufferObject = QtGui.QOpenGLFramebufferObject( fboSize[0], fboSize[1])#, glFboFormat )
        
        #print(frameBufferObject)
        #print(dir(frameBufferObject))
        # -- -- --
        """
        
        
        
        self.frameBufferObject = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frameBufferObject)
         
        # attach color
        #gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, colorTex, 0);
                    
        self.fboTexture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.fboTexture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        #gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
        #gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, fboSize[0], fboSize[1], 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        
        #gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, fboSize[0], fboSize[1], 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.imgData[self.glTempTex]['data'] )
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER,
            gl.GL_COLOR_ATTACHMENT0, #gl.GL_COLOR_ATTACHMENT0,
            gl.GL_TEXTURE_2D,
            self.fboTexture,
            0
        )
        
        
        
        """
        """
        # FBO Render Target Texture -
        if isTargetOrSampler :
            fboTargetTexture = QtGui.QOpenGLTexture( QtGui.QOpenGLTexture.Target2D )
            fboTargetTexture.setSize( fboSize[0], fboSize[1] )
            fboTargetTexture.setFormat( QtGui.QOpenGLTexture.RGBA8_UNorm )
            fboTargetTexture.allocateStorage()
            
            fboTargetImage = QtGui.QImage(fboSize[0], fboSize[1], QtGui.QImage.Format_RGBA8888)
            fboTargetImage.fill( QtGui.QColor(0,0,0,0) )
            fboTargetTexture.setData( fboTargetImage )
            
            frameBufferObject.bind()
            frameBufferObject.addColorAttachment( fboTargetTexture )
        
        else:
        
            fboSamplerTexture = QtGui.QOpenGLTexture( QtGui.QOpenGLTexture.Target2D )
            fboSamplerTexture.setFormat( QtGui.QOpenGLTexture.RGBA8_UNorm )
            fboSamplerTexture.setSize( fboSize[0], fboSize[1] )
            fboSamplerTexture.create()
        """
        # -- -- --
        
        if not frameBufferObject.isValid():
            print('framebuffer binding failed')
            
        return frameBufferObject, None# fboTargetTexture
        
    
    def fboTransferData(self):
        QtGui.QOpenGLFramebufferObject.blitFramebuffer( self.frameBufferObject, self.swapFrameBufferObject )
        
    def setTargetGLObject(self, glTargetObject=None):
        print( "---------------------" )
        print( "Set TargetGL Object" )
        print( glTargetObject )
        if glTargetObject != None:
            self.glTargetObject = glTargetObject
            self.bufferToTargetGL()
    def bufferToTargetGL(self):
        if self.glTargetObject != None:
            print(" BUFFER TO TARGETGL ")
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
            
        elif "swapTexture" in glEffect:
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
        
            #fboProgram.bind()
            #self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
            #self.gl.glUniform1i( fboProgram.uniformLocation('samplerTex'), 0 )
            #self.gl.glActiveTexture( self.gl.GL_TEXTURE1 )
            #self.gl.glUniform1i( fboProgram.uniformLocation('bufferRefTex'), 1 )
            #fboProgram.release()
        
            #self.glFboProgram = fboProgram
            #self.glFboUniforms = fboUniforms
            
            fboBufferObject, fboTextureObject = self.newFrameBuffer( [512,512] )
            print(fboBufferObject)
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
            fboSwapProgram.link()
        
            # swapProgram.bind()
            # self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
            # self.gl.glUniform1i( swapProgram.uniformLocation('samplerTex'), 0 )
            # swapProgram.release()
            
            fboSwapBufferObject,fboSwapTextureObject = self.newFrameBuffer( [512,512] )
            
            self.glBufferSwapProgram = fboSwapProgram
            
            print(fboSwapBufferObject)
            
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


        """
        # Original PyOpenGL known working binding for reference
        
        vshader = QOpenGLShader(QOpenGLShader.Vertex, self)
        vshader.compileSourceCode(self.vsrc)

        fshader = QOpenGLShader(QOpenGLShader.Fragment, self)
        fshader.compileSourceCode(self.fsrc)

        self.program = QOpenGLShaderProgram()
        self.program.addShader(vshader)
        self.program.addShader(fshader)
        self.program.bindAttributeLocation('vertex',
                self.PROGRAM_VERTEX_ATTRIBUTE)
        self.program.bindAttributeLocation('texCoord',
                self.PROGRAM_TEXCOORD_ATTRIBUTE)
        self.program.link()

        self.program.bind()
        self.program.setUniformValue('texture', 0)

        self.program.enableAttributeArray(self.PROGRAM_VERTEX_ATTRIBUTE)
        self.program.enableAttributeArray(self.PROGRAM_TEXCOORD_ATTRIBUTE)
        self.program.setAttributeArray(self.PROGRAM_VERTEX_ATTRIBUTE,
                self.vertices)
        self.program.setAttributeArray(self.PROGRAM_TEXCOORD_ATTRIBUTE,
                self.texCoords)
        """
        # -- -- -- --
        
        return
        
        
    def buildUniforms(self, glProgramPassName, glProgramDataDict):
        # TODO : Remove this, not needed
        glUniformLocations = {}
        
        
        glProgramData = glProgramDataDict[ glProgramPassName ]
        
        glProgramPassType = glProgramData['passType']
        glProgram = glProgramData['program']
        glProgramUniforms = glProgramData['uniforms']
        
        glProgramUniformsKeys = glProgramUniforms.keys()
        
        glProgram.bind()
        
        
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
                
                curTextureLoad = self.loadImageTex2D( self.glTempTex )
                
                # -- -- --
                
                uLocation = glProgram.uniformLocation( curUniform )
                
                # -- -- --
                
                # Set Shader Program's Uniform Bind Location
                #samplerUniformIndex += 1
                #glProgram.setUniformValue( curUniform, samplerUniformIndex )
                #uSettings['samplerBind'] = samplerUniformIndex
                
                # Bind texture to texture location and bind uniform to texture
                glTexLocation = self.gl.GL_TEXTURE0 + uLocation
                self.gl.glActiveTexture( glTexLocation )
                curTextureLoad['texture'].bind()
                #curTextureLoad['texture'].bind( samplerUniformIndex )
                
                glProgram.setUniformValue( curUniform, curTextureLoad['texture'].textureId() )
                
                curTextureLoad['texture'].release()
                
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
                
                # -- -- --
                
                glProgramData['textures'].append( curTextureLoad )
                
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
                        
                
                self.hasFrameBuffer = True
                #print(self.fboLocation)
                
                #samplerLocation = self.glProgram.uniformLocation( samplerName )
                #self.glProgram.setUniformValue( samplerLocation, self.swapFrameBufferObject.texture() )
            
                # Set Shader Program's Uniform Bind Location
                #   While other render passes,
                #     Default behaviour is to bind the pass's output to a sampler
                
                sourcePassType = self.renderPassNames[uSettings['type']]
                sourcePassTexture = glProgramDataDict[ sourcePassType ]['fboTexture']
                
                #samplerUniformIndex += 1
                #glProgram.setUniformValue( curUniform, sourcePassTexture.textureId() )
                #uSettings['samplerBind'] = samplerUniformIndex
                #textureId()
                
                # -- -- --
                
                uLocation = glProgram.uniformLocation( curUniform )
                
                # -- -- --
                print(glProgramData)
                glTexLocation = self.gl.GL_TEXTURE0 + uLocation
                self.gl.glActiveTexture( glTexLocation )
                #glProgramData['fboObject'].bind()
                self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, glProgramData['fboObject'].texture())
                #curTextureLoad['texture'].bind( samplerUniformIndex )
                
                glProgram.setUniformValue( curUniform, glTexLocation )
                
                #curTextureLoad['texture'].release()
                
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
                
                # -- -- --
                
                curSamplerDict = self.glPassSamplerDict.copy()
                curSamplerDict['type'] = uSettings['type']
                curSamplerDict['location'] = glProgram.uniformLocation( curUniform )
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
            self.glContext = self.context()
            # print("Created Shared Context")
            # self.glContext = QtGui.QOpenGLContext()
            # self.glContext.setShareContext( self.glSourceContext )
            # self.glContext.setFormat( self.glFormat )
            # self.glContext.create()
        #self.glContext.setShareContext( self.glContext )
        
        self.glContext.makeCurrent( self.glContext.surface() )
        #self.glContext.aboutToBeDestroyed.connect( self.destroy )
            
        self.gl = self.glContext.versionFunctions( self.profile )
        self.gl.initializeOpenGLFunctions()
        
        
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
        
        
        for currentPassName in self.glRenderPassList:
            curPassDataDict = self.glProgramList[ currentPassName ]
            curPassProgram = curPassDataDict['program']

            self.buildUniforms( currentPassName, self.glProgramList )
            
            curPassVAO = QtGui.QOpenGLVertexArrayObject( self )
            curPassVAO.create()
            
            curPassVAO.bind()
            vaoPositionList = [ -1,1, 1,1, -1,-1, 1,-1 ]
            vaoTexCoordList = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
            self.positionVBOOff = self.setVertexBuffer( vaoPositionList, 2, curPassProgram, "position" )
            self.uvVBOOff = self.setVertexBuffer( vaoTexCoordList, 2, curPassProgram, "uv" )
            curPassVAO.release()
            
            curPassDataDict['geoObject'] = curPassVAO

        
        
        print(self.glRenderPassList)
        
        
        # Uniforms processed, connect any FBO Buffers to Uniforms
        #   Setting at render time for now
        #self.connectTextureSamplers()
        
        
        # fboImagePath = "assets/glEdgeFinder_tmp2_alpha.png"
        # #self.glTempImage = QtGui.QImage( self.glTempTex ).mirrored()
        # self.glTempImage = QtGui.QImage( fboImagePath ).mirrored()
        # self.frameBufferObject = QtGui.QOpenGLFramebufferObject( self.glTempImage.width(), self.glTempImage.height() )
        # self.frameSwapBufferObject = QtGui.QOpenGLFramebufferObject( self.glTempImage.width(), self.glTempImage.height() )
        # self.fboTexture = QtGui.QOpenGLTexture( self.glTempImage )
        # #self.fboTexture.create()
        
        
        
        
        
        
        #self.gl.glBegin( self.gl.GL_TRIANGLE_STRIP )
        
        # Build data
        #data = np.zeros((4, 2), dtype=np.float32)
        # From another -
        """
        data = np.zeros(4, [("position", np.float32, 2),("uv", np.float32, 2)])
        data['position'] = [(-1,+1), (+1,+1), (-1,-1), (+1,-1)]
        data['uv'] = [(0,0), (1,0), (0,1), (1,1)]
        #posData = [ -1,1, 1,1, -1,-1, 1,-1 ]
        #uvData = [ 0,0, 1,0, 0,1, 1,1 ]

        indices = [0, 1, 2, 2, 3, 0]
        indices = np.array(indices, dtype=np.uint32)
        
        # TODO : I implemented a VBO and EBO without quite knowing why they were needed
        #          Opposed to a VAO, aside from UV support, which uhhhh
        #            Look into this more
        
        self.VBO = QtGui.QOpenGLBuffer( QtGui.QOpenGLBuffer.VertexBuffer )
        self.VBO.create()
        self.VBO.bind()
        self.VBO.allocate( data, data.itemsize * len(data) )

        stride = data.strides[0]
        offset = 0 #ctypes.c_void_p(0)
        
        posAttrLoc = self.glProgram.attributeLocation( "position" )
        print(posAttrLoc)
        self.glProgram.enableAttributeArray( posAttrLoc )
        self.glProgram.setAttributeBuffer( posAttrLoc, self.gl.GL_FLOAT, offset, 2, stride )
        
        offset = 8 #ctypes.c_void_p(8)
        uvAttrLoc = self.glProgram.attributeLocation( "uv" )
        print(uvAttrLoc)
        self.glProgram.enableAttributeArray( uvAttrLoc )
        self.glProgram.setAttributeBuffer( uvAttrLoc, self.gl.GL_FLOAT, offset, 2, stride )
        
        self.VBO.release()

        # -- -- --

        self.EBO = QtGui.QOpenGLBuffer( QtGui.QOpenGLBuffer.IndexBuffer )
        self.EBO.create()
        self.EBO.bind()
        self.EBO.allocate(indices, len(indices) * indices.itemsize)
        self.EBO.release()
        """
        # -- -- --
        
        # Needed??
        #self.gl.glEnable(self.gl.GL_TEXTURE_2D) 
        
        # -- -- --
        
        print("pre viewport shift")
        
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

        vertices = np.array( dataList, np.float32 )
        vbo.allocate( vertices, vertices.shape[0] * vertices.itemsize )

        attributeLocation = glProgram.attributeLocation( glAttrName )
        glProgram.enableAttributeArray( attributeLocation )
        glProgram.setAttributeBuffer( attributeLocation, self.gl.GL_FLOAT, 0, stride )
        vbo.release()

        return vbo
        
    def drawToDebugWidgets(self):
        if hasattr(self.parent,'bufferDisplay'):
            curFboObj=None
            try:
                curFboObj = self.glProgramList[self.renderPassNames['fbo']]['fboObject']
            except:
                pass;
            if curFboObj:
                print(curFboObj)
                pix = QtGui.QPixmap.fromImage( curFboObj.toImage(True) )
                pix= pix.transformed(QtGui.QTransform().scale(1, -1))
                self.parent.bufferDisplay.setPixmap( pix )
            
        if hasattr(self.parent,'swapDisplay'):
            curFboObj=None
            try:
                curFboObj = self.glProgramList[self.renderPassNames['fboSwap']]['fboObject']
            except:
                pass;
            if curFboObj:
                pix = QtGui.QPixmap.fromImage( curFboObj.toImage(True) )
                pix= pix.transformed(QtGui.QTransform().scale(1, 1))
                self.parent.swapDisplay.setPixmap( pix )
            

        #self.paintGL()
        if hasattr(self.parent,'renderDisplay'):
            outImage = self.grabFramebuffer()
            pix = QtGui.QPixmap.fromImage( outImage )
            self.parent.renderDisplay.setPixmap( pix )
            
        return;
    
    
    # Bind exising textures to existing Shader Uniforms
    #   Its asumed the dictionary info is always up to date
    #     As it should be using memory linked objects
    # TODO : Support Double Buffer Swap Bindings, 'GL_BACK'
    def bindTextureSamplers(self, glProgramPassName, glProgramDataDict ):
        #if self.hasFrameBuffer :
        curPassDataDict = glProgramDataDict[ glProgramPassName ]
        curPassType = curPassDataDict['passType']
        curPassProgram = curPassDataDict['program']
        curPassSamplers = curPassDataDict['samplers']
        
        
        # This function should only run at render time
        #   Might be useful adding some checks, for custome bind needs
        #curPassProgram.bind()
        
        returnBoundObjects = []
        samplerRunner=0
        #textureBind
        print(" Bind Textures ")
        #print(curPassSamplers.keys())
        for curSamplerUniform in curPassSamplers:
            curSamplerData = curPassSamplers[ curSamplerUniform ]
            curBindType = curSamplerData['type']
            curBindTexture = curSamplerData['texture']
            curBindLocation = curSamplerData['location']
            #print( curSamplerUniform )
            #print( curSamplerData )
            #print( curPassProgram.uniformLocation( curSamplerUniform) )
            #print( curSamplerData['texture'].textureId() )
            
            
            
            
            #curSamplerData['type']
            #curBindTexture.bind()# curSamplerData['location'] )
            #returnBoundObjects.append( curBindTexture )
            
            #print(curSamplerUniform)
            #print(curSamplerData)
            #fboProgram.bind()
            #fboProgram.release()
            
            """
            program.bind()
            self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
            self.gl.glUniform1i( program.uniformLocation('samplerTex'), 0 )
            self.gl.glActiveTexture( self.gl.GL_TEXTURE1 )
            self.gl.glUniform1i( program.uniformLocation('bufferRefTex'), 1 )
            program.release()
            """
            
            #partial( curBindTexture.release()
            
            if curSamplerData['type'] == "texture" :
            
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + curBindLocation )
                
                curBindTexture.bind( curBindTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, curBindTexture.textureId() )
                
                returnBoundObjects.append( curBindTexture )
                
            elif curSamplerData['type'] == "fbo" :
                
                curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject']
                #curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboTexture']
                
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + curBindLocation )
                
                #curFboTexture.bind( curFboTexture.textureId() )
                #curFboTexture.bind( curBindLocation )
                self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, curFboTexture.texture())
                #curPassProgram.setUniformValue( curSamplerUniform, curFboTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, curBindLocation )
                
                returnBoundObjects.append( curFboTexture )
                
            
            
                """print( glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'].texture() )
                glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'].bind()
                returnBoundObjects.append( glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'] )
                #curPassProgram.setUniformValue( curSamplerUniform, curBindTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'].texture() )"""
            elif curSamplerData['type'] == "fboSwap" :
                curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject']
                #curFboTexture = glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboTexture']
                
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 + curBindLocation )
                
                #curFboTexture.bind( curFboTexture.textureId() )
                #curFboTexture.bind( curBindLocation )
                self.gl.glBindTexture(self.gl.GL_TEXTURE_2D, curFboTexture.texture())
                #curPassProgram.setUniformValue( curSamplerUniform, curFboTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, curBindLocation )
                
                returnBoundObjects.append( curFboTexture )
                
                """print( glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'].texture() )
                glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'].bind()
                returnBoundObjects.append( glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'] )
                #curPassProgram.setUniformValue( curSamplerUniform, curBindTexture.textureId() )
                curPassProgram.setUniformValue( curSamplerUniform, glProgramDataDict[ self.renderPassNames[curSamplerData['type']] ]['fboObject'].texture() )"""
            elif curSamplerData['type'] == "toScreen" :
                # Not implemented
                pass;
        
        #curPassProgram.release()
        
        # Sampler Binds should be complete
        return returnBoundObjects
    
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
        
        
        if glRenderPassName == glPassType:
            print( "Rendering '"+glRenderPassName+"' pass" )
        else:
            print( "Rendering '"+glRenderPassName+"' as '"+glPassType+"' pass" )
        
        
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
        
        
        curTextureBinds = self.bindTextureSamplers( glRenderPassName, glRenderPassesData )
        
        glPassGeoObject.bind()
            
        # -- -- --
            
        #self.gl.glClear( self.gl.GL_COLOR_BUFFER_BIT )
        self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            
        # -- -- --
            
            
        glPassGeoObject.release()
        
        for boundTexture in curTextureBinds:
            boundTexture.release()
            
        if glPassFBO:
            glPassFBO.release()
            
        glPassProgram.release()
            
        
        # offscreen render
        #self.fboTexture.bind()
        """
        self.frameBufferObject.bind()
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)
        self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
        #self.fboTexture.bind()
        #self.imageTexture[0]['texture'].bind()
        #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameSwapBufferObject.texture() )
        self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.fboTexture.textureId() )
        self.gl.glActiveTexture( self.gl.GL_TEXTURE1 )
        #self.imageTexture[0]['texture'].bind()
        self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameSwapBufferObject.texture() )
        #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.imageTexture[0]['texture'].textureId() )
        
        self.offscreenVAO.bind()
        """
        
        
        """
        gl.glActiveTexture( activeTexture )

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT,1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, textureBind )
        
        samplerUniformLocation = gl.glGetUniformLocation(self.glProgram, samplerName )
        gl.glUniform1i( samplerUniformLocation, samplerUniformBind )
        """
        
        
        
        """
        self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
        self.offscreenVAO.release()
        self.frameBufferObject.release()
        
        self.fboTexture.release()
        self.imageTexture[0]['texture'].release()
        """
        
        # -- -- --
        
        # -- -- --
        
        
        
    def paintGL(self):
        if self.initialized and self.glContext:
        
            #print("Init render")
            
            #print("Render ",self.glEffect," - ",str(self.id)," -- ")
            
            #self.glContext.makeCurrent( self.glContext.surface() )
            self.glContext.makeCurrent( self )
            
            self.gl.glViewport( 0, 0, self.imgWidth, self.imgHeight )
            
            
            for renderPass in self.glRenderPassList:
                curPassDataDict = self.glProgramList[ renderPass ]
                curPassProgram = curPassDataDict['program']
                
                self.bindRenderPass( renderPass, self.glProgramList )
            
            
            
            
            """
            
            for currentPassName in self.glRenderPassList:
                curPassDataDict = self.glProgramList[ currentPassName ]
                curPassProgram = curPassDataDict['program']
                self.buildUniforms( curPassDataDict )
                
                curPassVAO = QtGui.QOpenGLVertexArrayObject( self )
                curPassVAO.create()
                
                curPassVAO.bind()
                vaoPositionList = [ -1,1, 1,1, -1,-1, 1,-1 ]
                vaoTexCoordList = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
                self.positionVBOOff = self.setVertexBuffer( vaoPositionList, 2, curPassProgram, "position" )
                self.uvVBOOff = self.setVertexBuffer( vaoTexCoordList, 2, curPassProgram, "uv" )
                curPassVAO.release()
                
                curPassDataDict['geoObject'] = curPassVAO
            
            
            """
            
            
            
            
            
            
            
            """
            if self.hasFboProgram :
                self.glFboProgram.bind()
            else:
                self.glProgram.bind()
                
            
            # offscreen render
            #self.fboTexture.bind()
            
            self.frameBufferObject.bind()
            self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)
            self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
            #self.fboTexture.bind()
            #self.imageTexture[0]['texture'].bind()
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameSwapBufferObject.texture() )
            self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.fboTexture.textureId() )
            self.gl.glActiveTexture( self.gl.GL_TEXTURE1 )
            #self.imageTexture[0]['texture'].bind()
            self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameSwapBufferObject.texture() )
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.imageTexture[0]['texture'].textureId() )
            
            self.offscreenVAO.bind()
            """
            
            
            """
            gl.glActiveTexture( activeTexture )

            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT,1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, textureBind )
            
            samplerUniformLocation = gl.glGetUniformLocation(self.glProgram, samplerName )
            gl.glUniform1i( samplerUniformLocation, samplerUniformBind )
            """
            
            
            
            """
            self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            self.offscreenVAO.release()
            self.frameBufferObject.release()
            
            self.fboTexture.release()
            self.imageTexture[0]['texture'].release()
            
            
            
            #QtGui.QOpenGLFramebufferObject.blitFramebuffer( self.frameSwapBufferObject, self.frameBufferObject )
            
            if self.hasFboProgram :
                self.glFboProgram.release()
            
            if self.glBufferSwapProgram :
                print("render swap")
                self.glBufferSwapProgram.bind()
                self.frameSwapBufferObject.bind()
                self.offscreenVAO.bind()
                self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
                self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameBufferObject.texture() )
                #self.gl.glUniform1i( self.glBufferSwapProgram.uniformLocation('samplerTex'), self.frameBufferObject.texture() )
                
                #self.fboTexture.bind()
                self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)
                self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            
                #self.fboTexture.release()
                self.offscreenVAO.release()
                self.frameSwapBufferObject.release()
                self.glBufferSwapProgram.release()
            
            
            
            
            self.glProgram.bind()

            self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
            # screen render
            #self.fboTexture.bind()
            #self.gl.glActiveTexture( self.gl.GL_TEXTURE0 )
            #self.imageTexture[0]['texture'].bind()
            #self.fboTexture.bind()
            self.imageTexture[0]['texture'].bind()
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameBufferObject.texture() )
            #self.gl.glUniform1i( self.glProgram.uniformLocation('samplerTex'), self.frameSwapBufferObject.texture() )
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameBufferObject.texture() )
            #self.gl.glActiveTexture( self.gl.GL_TEXTURE1 )
            #self.fboTexture.bind()
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameSwapBufferObject.texture() )
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameSwapBufferObject.texture() )
            
            self.renderVAO.bind()
            self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)
            self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            self.renderVAO.release()
            #self.fboTexture.release()
            self.imageTexture[0]['texture'].release()
            self.glProgram.release()
            """
            
            
            
            """
            #self.glContext.makeCurrent( self )
            self.glContext.makeCurrent( self.surface )
            
            self.glProgram.bind()
            self.renderVAO.bind()
            #self.imageTexture[-1]['texture'].bind()
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.texture_id )
            #self.VBO.bind()
            #self.imageTexture[-1]['texture'].bind()
            #self.glProgram.setUniformValue( "samplerTex", 0 )
            #self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT)
            self.fboTexture.bind()
            self.frameBufferObject.bind()
            self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            self.renderVAO.release()
            self.frameBufferObject.release()
            
            
            #self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameBufferObject.texture() )
            self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.fboTexture.textureId() )
            self.renderVAO.bind()
             
            self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            
                
            #self.renderVAO.release()
            #self.imageTexture[-1]['texture'].release()
            #self.glProgram.release()
            """
            
            self.drawToDebugWidgets()
            
            #print("Did it draw?")
            if self.saveNextRender :
                self.saveBuffer( "current", saveName="colorOut", doPaint=False )
                
            self.saveNextRender = False
            
            #self.glContext.makeCurrent()
            
            self.glContext.swapBuffers( self.glContext.surface() )
            #self.glContext.doneCurrent()
            
            #print("Did context done?")
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
            self.setRenderPassUniforms( self.builtinControlledUniforms[builtinName], allPasses, doPaint )
        else:
            print(" ! Warning ! No previously assigned Builtin's Uniform Dict for '"+builtinName+"'")
            
    # Seems overkill to have as a separate method, need to consider future needs
    def setRenderPassUniforms(self, uniformData, allPasses=True, doPaint=True ):
        if type(uniformData) == dict:
            if QtGui.QOpenGLContext.currentContext() != self.glContext:
            #    #self.glContext.makeCurrent( self.glContext.surface() )
                self.glContext.makeCurrent( self )
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
            
            self.glContext.doneCurrent()
                    
            if doPaint:
                self.update()
                self.paintGL()
        else:
            # Uhh.... Current shader program maybe?
            #   But not storing that, yet
            print(" ! Warning ! Please pass a render pass data dictionary as the 'uniformData' argument to 'self.setUniformValue()'")
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
        if doPaint:
            self.paintGL()
        
        print( savePath )
        print( saveFormat )
        #self.gl.glUseProgram(self.glProgram)
        outImage = None
        if self.outImagePrefix == None:
            self.findPrefixNumber( savePath )
        if sourceBuffer != "current":
            try:
                sourceBuffer.bind()
                outImage = sourceBuffer.toImage(True)
            except:
                print("Failed to bind buffer")
        else:
            outImage = self.grabFramebuffer()
        outImage = self.grabFramebuffer()
        
        self.fboTexture.bind()
        outImage = self.frameBufferObject.toImage()
        outImage = self.glTempImage
        #    self.fboTexture.bind()
        #    self.frameBufferObject.bind()
        
        print( self.frameBufferObject.textures() )
        print( self.fboTexture.textureId() )
        
        pix = QtGui.QPixmap.fromImage( self.frameBufferObject.toImage() )
        pix = QtGui.QPixmap.fromImage( self.glTempImage )
        tmpLabel = QtWidgets.QLabel()
        tmpLabel.setPixmap( pix )
        tmpLabel.show()
        
        
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
        
        self.textureGLWidget = None
        
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
            self.textureGLWidget = TextureGLWidget( self, self.id, self.glFormat, curContext, self.glEffect, self.initTexturePath, self.saveImagePath )
            self.windowView = QWidget.createWindowContainer( self.textureGLWidget )
            self.windowView.setFixedWidth(512)
            self.windowView.setMinimumHeight(512)
            self.windowView.setMaximumHeight(600)
            self.textureGLWidgetLayout.addWidget(self.windowView)
            
            self.bufferDisplay = QLabel(self)
            self.bufferDisplay.setFixedWidth(512)
            self.bufferDisplay.setMinimumHeight(512)
            self.bufferDisplay.setMaximumHeight(600)
            self.textureGLWidgetLayout.addWidget(self.bufferDisplay)
            
            self.swapDisplay = QLabel(self)
            self.swapDisplay.setFixedWidth(512)
            self.swapDisplay.setMinimumHeight(512)
            self.swapDisplay.setMaximumHeight(600)
            self.textureGLWidgetLayout.addWidget(self.swapDisplay)
            
            self.renderDisplay = QLabel(self)
            self.renderDisplay.setFixedWidth(512)
            self.renderDisplay.setMinimumHeight(512)
            self.renderDisplay.setMaximumHeight(600)
            self.textureGLWidgetLayout.addWidget(self.renderDisplay)
        
        
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
            
            valList = [uData['value']] if type(uData['value']) == float else uData['value']
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
            
        if glTextureWidget != None:
            print( "Passing Target GL Context" )
            self.textureGLWidget.setTargetGLObject( glTextureWidget.textureGLWidget )
            
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
        if targetGL != None:
            self.textureGLWidget.setTargetGLObject( targetGL )
    
    def setStatusBar( self, message=None, importance=0, noTimeout=False ):
        if message == None:
            print( "Message==None passed to set window status bar" )
            return;
        if hasattr( self.parent, 'setStatusBar') :
            self.parent.setStatusBar( message, importance, noTimeout )
        else:
            print( message )
            
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