
# Built on Python 3.10.6 && PyQt5 5.15.9

import sys, os
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




#class TextureGLWidget(QtWidgets.QOpenGLWidget):
class TextureGLWidget(QtGui.QOpenGLWindow):
#class TextureGLWidget(QtOpenGL.QGLWidget):
    def __init__(self,parent=None, glId=0, glFormat=None, sharingContext=None, glEffect="default", initTexturePath="assets/glTempTex.jpg", saveImagePath=None ):
        #QtWidgets.QOpenGLWidget.__init__(self,parent)
        #QtOpenGL.QGLWidget.__init__(self,parent)
        #QtOpenGL.QGLWidget.__init__(self, QtOpenGL.QGLFormat(), parent)
        #super(TextureGLWidget, self).__init__(parent) 
        super(TextureGLWidget, self).__init__() 
        
        # -- -- --
        
        self.id = glId
        self.parent = parent
        self.glEffect = glEffect
        self.context = None
        self.gl = None
        self.initialized = False
        
        # -- -- --
        
        self.profile = QtGui.QOpenGLVersionProfile()
        self.profile.setVersion( 2, 1 )
        
        self.format = glFormat
        if self.format == None :
            self.format = QtGui.QSurfaceFormat()
            self.format.setProfile( QtGui.QSurfaceFormat.CompatibilityProfile )    
            #self.format.setProfile( QtGui.QSurfaceFormat.CoreProfile )
            self.format.setVersion( 3, 3 )
            self.format.setRenderableType( QtGui.QSurfaceFormat.OpenGL )
            #self.setSurfaceType( QtGui.QSurface.OpenGLSurface )
            self.setFormat( self.format )
        """
        
        self.format = QtOpenGL.QGLFormat()
        self.format.setProfile( QtOpenGL.QGLFormat.CoreProfile )
        self.format.setVersion( 3, 3 )
        self.format.setAlpha( True )
        self.format.setDepth( False )
        self.format.setStencil( False )
        """
        #self.format.setSampleBuffers(True)
        
        #QtOpenGL.QGLWidget.__init__(self.format,None)
        
        #QtOpenGL.QGLWidget.__init__(self,parent=parent,format=self.format,context=self.format.profile(),shareWidget=self) 
        
        
        # Context must be set before drawing to screen
        if sharingContext != None :
            self.context = QtGui.QOpenGLContext()
            self.context.setShareContext( sharingContext )
            self.context.setFormat( self.format )
            self.context.create()
        else:
            print( "No context passed to GL id '",str(self.id),"'" )
        #    # Not tested, as developing for Shared Context
        #    #   self.context()
        #    self.setFormat( self.format )
        #    self.create()
        
        
        # -- -- --
        
        
        self.surface = QtGui.QOffscreenSurface()
        self.surface.setFormat( self.format )
        self.surface.create()
        print( dir(self.surface))
        
        # -- -- --
        
        """
        if self.id == 0:
        
            self.old_context = QtGui.QOpenGLContext.currentContext()
            self.old_surface = None if self.old_context is None else self.old_context.surface()

            self.surface = QtGui.QOffscreenSurface()
            self.surface.create()
        
            self.context = QtGui.QOpenGLContext( self )
            self.context.setFormat( self.format )
            self.context.create()
        """
        
        self.imageTexture = []
        self.bufferRefImage = None
        self.runner = 0
        
        
        self.simTimer = QtCore.QTimer(self)
        self.simTimer.setSingleShot(True)
        self.simTimerIterval = 100
        self.simTimerRunCount = 10
        self.simTimerRunner = 0
        self.hasSimTimer = False
        
        self.Shader = None # Shader Import File
        self.shaderSettings = {}
        self.hasFrameBuffer = False
        self.fboLocation = None
        
        self.glProgram = None
        self.glUniformLocations = {}
        self.glUniforms = {}
        self.glControls = {}
        
        self.samplerUniforms = []
        self.builtinUniforms = {}
        
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
        
        self.imgWidth=0
        self.imgHeight=0
        
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
        
            
        
        
    def mouseMoveEvent(self, e):
        if self.hasMousePosUniform:
            toVal=[]
            toVal.append( max( 0.0, min(1.0, float(e.pos().x()/self.imgWidth) ) ) )
            toVal.append( max( 0.0, min(1.0, float(e.pos().y()/self.imgHeight) ) ) )
            #print(toVal)
            #self.setUniformValue( "mousePos", toVal )
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
        self.context.makeCurrent( self )
        pix = QtGui.QPixmap.fromImage( self.frameBufferObject.toImage(True) )
        pix= pix.transformed(QtGui.QTransform().scale(1, -1))
        if hasattr(self.parent,'bufferDisplay'):
            self.parent.bufferDisplay.setPixmap( pix )
            
        self.paintGL()
        
        outImage = self.grabFramebuffer()
        pix = QtGui.QPixmap.fromImage( outImage )
        if hasattr(self.parent,'fboDisplay'):
            self.parent.fboDisplay.setPixmap( pix )
        return;
        
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
        
    def loadImageTex2D(self, filename, enableAlpha=True ):
    
        #texture = QtGui.QOpenGLTexture( QtGui.QOpenGLTexture.Target2D )
        texture = QtGui.QOpenGLTexture( QtGui.QImage( filename ), QtGui.QOpenGLTexture.DontGenerateMipMaps )
        texture.bind()
        #texture.setAutoMipMapGenerationEnabled( False )
        #texture.setFormat( QtGui.QOpenGLTexture.RGBA8_UNorm )
        texture.setMinMagFilters( QtGui.QOpenGLTexture.Linear, QtGui.QOpenGLTexture.Linear )
        texture.setWrapMode( QtGui.QOpenGLTexture.DirectionS, QtGui.QOpenGLTexture.ClampToEdge )
        texture.setWrapMode( QtGui.QOpenGLTexture.DirectionT, QtGui.QOpenGLTexture.ClampToEdge )

        texture.allocateStorage( QtGui.QOpenGLTexture.RGBA, QtGui.QOpenGLTexture.UInt8 )
        
        #texture.setData( QtGui.QImage( filename ), QtGui.QOpenGLTexture.DontGenerateMipMaps  )
        
        
        texture.release()
        
        self.imgWidth = texture.width()
        self.imgHeight = texture.height()
        self.curImage = filename
        
        return {'width':texture.width(),'height':texture.height(),'texture':texture}
    
    def setTextureFromImageData(self, samplerId=0, imageData=None):
        if imageData == None:
            print("Image data None")
            return;
        
        
        #print( self.glEffect," Recieved Image Data" )

        #print( self.samplerUniforms )
        #print( self.samplerUniforms.index( 'samplerTex' ) )
        samplerName = 'samplerTex'
        samplerTexIndex = self.samplerUniforms.index( samplerName )
        #print( self.imageTexture[samplerTexIndex] )
        imageInfo = self.imageTexture[samplerTexIndex]
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
        
    
    def newFrameBuffer(self, fboSize=[512,512], samplerName=None ):
        print( "Binding Data Frame Buffer")
                    
        self.frameBufferObject = QtGui.QOpenGLFramebufferObject( fboSize[0], fboSize[1] )
        
        # -- -- --
        
        self.swapFrameBufferObject = QtGui.QOpenGLFramebufferObject( fboSize[0], fboSize[1] )
        
        samplerLocation = self.glProgram.uniformLocation( samplerName )
        self.glProgram.setUniformValue( samplerLocation, self.swapFrameBufferObject.texture() )
        
        # -- -- --
        
        #if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
        #    print('framebuffer binding failed')
        
    
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
        
        if "rawtexture" in glEffect:
            from .glShaders import rawTextureShader as Shader
            
        elif "smartblur" in glEffect:
            from .glShaders import smartBlurShader as Shader
            
        elif "edgedetect" in glEffect:
            from .glShaders import edgeDetectShader as Shader
            
        elif "segment" in glEffect:
            from .glShaders import segmentShader as Shader
            
        elif "paintmask" in glEffect:
            from .glShaders import paintMaskShader as Shader
            
        elif "colorcorrect" in glEffect:
            from .glShaders import colorCorrectShader as Shader
            
        else: # Default to "default"; This will cause issues during dev
            from .glShaders import defaultShader as Shader
        
        self.Shader = Shader
        
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
        

        """
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
        
        return program, self.Shader.uniforms
        
        
    def buildUniforms(self, glProgram, toUniforms):
        glUniformLocations = {}
        
        uniformKeys = toUniforms.keys()
        
        for x,curUniform in enumerate( toUniforms ):
            uSettings = toUniforms[ curUniform ]
            if uSettings['type'] == "float":
                uLocation = glProgram.uniformLocation( curUniform )
                uVal = uSettings[ 'default' ]
                glProgram.setUniformValue( uLocation, uVal )
                # -- -- --
                uLocKey = curUniform
                glUniformLocations[ uLocKey ] = uLocation
                
            elif uSettings['type'] == "vec2":
                uLocation = glProgram.uniformLocation( curUniform )
                uVal = uSettings[ 'default' ]
                glProgram.setUniformValue( uLocation, uVal[0], uVal[1] )
                # -- -- --
                uLocKey = curUniform
                glUniformLocations[ uLocKey ] = uLocation
                
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
                self.samplerUniforms.append( curUniform )
                
                self.imageTexture.append( self.loadImageTex2D( self.glTempTex ) )
                
                self.imageTexture[-1]['texture'].bind()
                glProgram.setUniformValue( curUniform, self.imageTexture[-1]['texture'].textureId() )
                #self.imageTexture[-1]['texture'].release()
                    
            elif uSettings['type'] == "fbo" :
                self.samplerUniforms.append( curUniform )
                curImgTexture = self.imageTexture[-1]
                #print( curImgTexture )
                
                self.fboLocation = self.newFrameBuffer( [curImgTexture['width'],curImgTexture['height']], curUniform )
                self.hasFrameBuffer = True
                #print(self.fboLocation)
            
            if 'control' in uSettings:
                if uSettings['control'] == "visible":
                    controlDict = {}
                    controlDict['type'] = uSettings['type']
                    controlDict['value'] = uSettings['default']
                    controlDict['range'] = uSettings['range'] if 'range' in uSettings else False
                    self.glControls[ curUniform ] = controlDict
                elif uSettings['control'] == "mousePos":
                    self.builtinUniforms[ 'mousePos' ] = curUniform
                elif uSettings['control'] == "texOffset":
                    self.builtinUniforms[ 'texOffset' ] = curUniform
                elif uSettings['control'] == "texScale":
                    self.builtinUniforms[ 'texScale' ] = curUniform
                elif uSettings['control'] == "texelSize":
                    self.builtinUniforms[ 'texelSize' ] = curUniform
        
        print("Ccc 18")
        #gl.glUseProgram(self.glProgram)
        #gl.glActiveTexture(gl.GL_TEXTURE1)
        #
        #gl.glBindTexture(gl.GL_TEXTURE_2D, self.displayImage['texture']) 
        
        #
        
        return glUniformLocations
        
        
    def initializeGL(self):
        #self.context.makeCurrent( self.surface )
        self.context.makeCurrent( self )
        
        #if self.id == 0:
        #    self.gl = self.context().versionFunctions( self.profile )
        #else:
        #    self.gl = self.context.versionFunctions( self.profile )
        #    self.gl.initializeOpenGLFunctions()
        #self.gl = self.context().versionFunctions( self.profile )
        #self.gl.initializeOpenGLFunctions()
        
        self.gl = self.context.versionFunctions( self.profile )
        self.gl.initializeOpenGLFunctions()
        
        #glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
        #glEnable(GL_BLEND);
        
        #self.gl.glClearColor(0.0, 0.0, 0.0, 0.0)

    
        self.glProgram, self.glUniforms = self.loadProgram( self.glEffect )
        
        self.glUniformLocations = self.buildUniforms( self.glProgram, self.glUniforms )
        
        
        self.glProgram.bind()
        
        
        self.glTempImage = QtGui.QImage( self.glTempTex ).mirrored()
        self.frameBufferObject = QtGui.QOpenGLFramebufferObject( self.glTempImage.width(), self.glTempImage.height() )
        self.fboTexture = QtGui.QOpenGLTexture( self.glTempImage )
        #self.fboTexture.create()
        
        
        self.offscreenVAO = QtGui.QOpenGLVertexArrayObject( self )
        self.offscreenVAO.create()
        self.renderVAO = QtGui.QOpenGLVertexArrayObject( self )
        self.renderVAO.create()
        
        
        #self.imageTexture.append( self.loadImageTex2D( self.glTempTex ) )
        #print( self.imageTexture[-1]['texture'] )
        
        self.offscreenVAO.bind()
        self.posListOff = [ -1,1, 1,1, -1,-1, 1,-1 ]
        self.uvListOff = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
        self.positionVBOOff = self.setVertexBuffer( self.posListOff, 2, self.glProgram, "position" )
        self.uvVBOOff = self.setVertexBuffer( self.uvListOff, 2, self.glProgram, "uv" )
        self.offscreenVAO.release()
        
        self.renderVAO.bind()
        self.posList = [ -1,1, 1,1, -1,-1, 1,-1 ]
        self.uvList = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
        self.positionVBO = self.setVertexBuffer( self.posList, 2, self.glProgram, "position" )
        self.uvVBO = self.setVertexBuffer( self.uvList, 2, self.glProgram, "uv" )
        self.renderVAO.release()
        
        
        
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
        
        self.gl.glViewport(0, 0, self.imgWidth, self.imgHeight) # Out res is [512,512] setting by default
        
        
        print("GL Init")
        self.findPrefixNumber()
        
        # If it exists, set the values
        if len(self.imageTexture) > 0:
            self.setTexelSize( [self.imageTexture[0]['width'], self.imageTexture[0]['height']] )
        
        
        
        if hasattr( self.Shader, "settings"):
            #print("Settings Exist; ", self.glEffect )
            self.shaderSettings = self.Shader.settings.copy()
            #print(self.shaderSettings)
        
        if "hasSim" in self.shaderSettings:
            #print("Found 'hasSim'")
            self.hasSimTimer = self.shaderSettings['hasSim']
            self.simTimer.timeout.connect(self.simTimeout)
        if "timerIterval" in self.shaderSettings:
            #print("Found 'timerIterval'")
            self.simTimerIterval = self.shaderSettings['timerIterval']
        if "runSimCount" in self.shaderSettings:
            #print("Found 'runSimCount'")
            self.simTimerRunCount = self.shaderSettings['runSimCount']
            
        self.parent.createControls( self.glControls )
        
        self.initialized = True
        """
        if self.id == 0:
            #self.context.doneCurrent()
            #if self.old_context and self.old_surface :
            #    self.old_context.makeCurrent( self.old_surface )
            #
            self.contextCreated.emit( self.context )
        """
        self.glProgram.bind()
        for x,s in enumerate( self.samplerUniforms ):
            print( x,s )
            if x < len(self.imageTexture):
                print(self.imageTexture[x])
                self.imageTexture[x]['texture'].bind()
                self.glProgram.setUniformValue( "samplerTex", x )
        
        self.paintGL()
        
    def setVertexBuffer( self, dataList, stride, glProgram, glAttrName ):
        vbo = QtGui.QOpenGLBuffer( QtGui.QOpenGLBuffer.VertexBuffer )
        vbo.create()
        vbo.bind()

        vertices = np.array( dataList, np.float32 )
        vbo.allocate( vertices, vertices.shape[0] * vertices.itemsize )

        attr_loc = glProgram.attributeLocation( glAttrName )
        glProgram.enableAttributeArray( attr_loc )
        glProgram.setAttributeBuffer( attr_loc, self.gl.GL_FLOAT, 0, stride )
        vbo.release()

        return vbo
        
    def paintGL(self):
        if self.initialized and self.context:
            print("Render ",self.glEffect," - ",str(self.id)," -- ")
            self.context.makeCurrent( self )
            
            self.gl.glViewport( 0, 0, self.glTempImage.width(), self.glTempImage.height() )

            self.glProgram.bind()

            # offscreen render
            self.fboTexture.bind()
            self.frameBufferObject.bind()
            self.offscreenVAO.bind()
            self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            self.offscreenVAO.release()
            self.frameBufferObject.release()

            # screen render
            self.gl.glBindTexture( self.gl.GL_TEXTURE_2D, self.frameBufferObject.texture() )
            self.renderVAO.bind()
            self.gl.glDrawArrays( self.gl.GL_TRIANGLE_STRIP, 0, 4 )
            self.renderVAO.release()

            self.glProgram.release()
            
            """
            #self.context.makeCurrent( self )
            self.context.makeCurrent( self.surface )
            
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
            if self.saveNextRender :
                self.saveBuffer( "current", saveName="colorOut", doPaint=False )
                
            self.saveNextRender = False
            
    def paintOverlayGL(self):
        print( "Paint Overlay GL " )
        
    @QtCore.pyqtSlot()
    def simTimeout(self):
        if self.hasSimTimer :
            self.simTimerRunner += 1
            
            self.paintGL()
            
            if self.simTimerRunner <= self.simTimerRunCount :
                print(" Shader '",self.glEffect,"' run sim ",str(self.simTimerRunner))
                self.simTimer.start( self.simTimerIterval )
            else:
                print(" Shader '",self.glEffect,"' finished sim run")
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
        if 'texOffset' in self.builtinUniforms and 'texOffset' in self.glUniformLocations :
            #self.gl.glUseProgram(self.glProgram)
            #print(self.id, self.glUniformLocations['texOffset'])
            uLocation = self.glProgram.attributeLocation( self.builtinUniforms[ 'texOffset' ] )
            #print(uLocation)
            #self.gl.glUseProgram( self.glProgram )
            #uVal = uSettings[ 'default' ]
            #self.gl.glUniform2f( uLocation, uVal[0], uVal[1] )
            #self.gl.glUniform2f( self.glUniformLocations['texOffset'], x, y )
            self.gl.glUniform2f( uLocation, x, y )
            if setOffset :
                self.curOffset=[x,y]
            #self.gl.glUseProgram(0)
    def imageScale(self,x,y, setScale=True):
        if 'texScale' in self.builtinUniforms and 'texScale' in self.glUniformLocations :
            #self.gl.glUseProgram(self.glProgram)
            #print(self.id, self.glUniformLocations['texScale'])
            uLocation = self.glProgram.attributeLocation( self.builtinUniforms[ 'texScale' ] )
            #print(uLocation)
            #self.gl.glUseProgram( self.glProgram )
            #self.gl.glUniform2f( self.glUniformLocations['texScale'], x, y )
            self.gl.glUniform2f( uLocation, x, y )
            if setScale :
                self.curScale=[x,y]
            #self.gl.glUseProgram(0)
    def setTexelSize(self, imgRes=None ):
        # If it exists, set the values
        if 'texelSize' in self.builtinUniforms:
            if type(imgRes) == list and len(imgRes)==2 :
                if imgRes[0]==0 or imgRes[1]==0:
                    print("Attempted to set Texel Size to [0,0], stopping Uniform update")
                    return;
                tx = 1.0 / float( imgRes[0] )
                ty = 1.0 / float( imgRes[1] )
                #print( "Set 'texelSize' - [",tx,",",ty,"]" )
                self.setUniformValue( self.builtinUniforms['texelSize'], [tx,ty] )
            else:
                print("Incorrect Image Resolution sent to 'setTexelSize'")
        #else:
        #    print("Shader '",self.glEffect,"'; No 'texelSize' in shader program uniforms")
            
    def setUniformValue(self, uniformName, toValue, doPaint=True ):
        #print("Set uniform value")
        if uniformName in self.glUniforms:
            #self.gl.glUseProgram(self.glProgram)
            
            uLocation = self.glProgram.attributeLocation( uniformName )
            
            toValue = [toValue] if type(toValue) == float else toValue
            if len(toValue) == 1:
                self.gl.glUniform1f( uLocation, toValue[0] )
            elif len(toValue) == 2:
                self.gl.glUniform2f( uLocation, toValue[0], toValue[1] )

            if doPaint:
                self.update()
                self.paintGL()
                
            #self.gl.glUseProgram(0)
        else:
            print("No registered Uniform '",uniformName,"'")
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
        
        
class ImageShaderWidget(QWidget):
    def __init__(self,parent=None, glId=0, glFormat=None, glEffect="default", initTexturePath="assets/glTempTex.jpg", saveImagePath=None ):
        super(ImageShaderWidget, self).__init__(parent)
        
        self.id=glId
        self.fullPath = ""
        self.fileName = ""
        self.folderName = ""
        self.folderPath = ""
        self.dispImagePath = ""
        self.data = {}
        
        self.glFormat = glFormat
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
        
    # Check if context already exists
    #   At that rate, context should just be passed anyway
    def getSharedGlContext(self):
        return;
    
    @QtCore.pyqtSlot( QtGui.QOpenGLContext )
    def setSharedGlContext(self, curContext=None ):
        print( " ImageShaderGL ",self.glEffect," - ",str(self.id)," recieved context" )
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
            
            self.fboDisplay = QLabel(self)
            self.fboDisplay.setFixedWidth(512)
            self.fboDisplay.setMinimumHeight(512)
            self.fboDisplay.setMaximumHeight(600)
            self.textureGLWidgetLayout.addWidget(self.fboDisplay)
        
        
    def imageOffset(self,x,y, setOffset=True):
        if self.textureGLWidget:
            self.textureGLWidget.imageOffset(x,y,setOffset)
    def imageScale(self,x,y, setScale=True):
        if self.textureGLWidget:
            self.textureGLWidget.imageScale(x,y,setScale)
    def createControls( self, controls ):
    
        if self.textureGLWidget.hasSimTimer :
            runSimButton = QPushButton('Run Sim', self)
            runSimButton.setToolTip('Run sim a set number of times')
            runSimButton.setFixedHeight(35)
            runSimButton.clicked.connect(self.textureGLWidget.simTimeout)
            self.glButtonLayout.addWidget(runSimButton)
            
            setTargetGLButton = QPushButton('Set TargetGL', self)
            setTargetGLButton.setToolTip('Pass swap buffer texture to another GL Context')
            setTargetGLButton.setFixedHeight(35)
            setTargetGLButton.clicked.connect(self.setTargetGLButton_onClick)
            self.glButtonLayout.addWidget(setTargetGLButton)
    
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
                slider.valueChanged.connect(partial(self.updateUniformValue,sliderList,uniform,multVal))
    
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
            
    def updateUniformValue(self,sliderList,uniform,decimalCount):
        toValue = []
        for slider in sliderList:
            toValue.append( slider.value()/(10**decimalCount) )
        self.textureGLWidget.setUniformValue( uniform, toValue )
        
    def grabFrameBuffer(self, withAlpha=False):
        return self.textureGLWidget.grabFrameBuffer(withAlpha=withAlpha)
    
    def passTargetGL( self, targetGL = None ):
        print( "Passing TargetGL To GL Viewport Object" )
        print( targetGL )
        if targetGL != None:
            self.textureGLWidget.setTargetGLObject( targetGL )
    
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