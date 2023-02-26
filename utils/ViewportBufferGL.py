
# Built on Python 3.10.6 && PyQt5 5.15.9

import sys, os
from PIL import Image
from functools import partial
import math

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




# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --




# Handled Uniform Control Types ---
#   ( As set in 'glShaders/SHADER_NAME.py' uniforms[UNIFORM_NAME]['control'] )
# -- -- --
# Uniform Control Type -
#   "offset"    - Mouse Left Click Drag; Shift UVs;
#                   vec2( offsetX, offsetY)
#   "scale"     - Mouse Right Click Drag; Scale UVs;
#                   vec2( scaleX, scaleY )
#   "texelSize" - (1 / Image Resolution);
#                   vec2( 1/textureWidth, 1/textureHeight )
#   "visible"   - Will create a GUI element for the User to control the uniform value




# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --
# -- -- -- -- -- -- -- -- -- -- -- -- --





# -- -- --
#print("Effector GL")
#print(__name__)

# TODO: Add stand alone module parsing
# TODO'TODO : I don't like this one bit....
if __name__ != '__main__':
    glShadersPath = os.path.abspath(__file__)
    glShadersPath = os.path.dirname(glShadersPath)
    glShadersPath = os.path.join(glShadersPath, "glShaders")
    
    #print(glShadersPath)
    sys.path.append(glShadersPath)


# -- -- -- -- -- -- -- -- -- -- -- -- --


class TextureBufferGLWidget(QtOpenGL.QGLWidget):
    def __init__(self,parent=None, glId=0, glEffect="default", initTexturePath="assets/glTempTex.jpg"):
        QtOpenGL.QGLWidget.__init__(self,parent)
        # -- -- --
        self.id = glId
        self.imageTexture = []
        self.bufferRefImage = None
        self.runner = 0
        
        self.Shader = None # Shader Import File
        self.hasFrameBuffer = False
        self.fboLocation = None
        
        self.glProgram = None
        self.glUniformLocations = {}
        self.glEffect = glEffect
        self.glUniforms = {}
        self.glControls = {}
        
        self.samplerUniforms = []
        
        self.frameBufferObject = None
        self.fboTexture = None
        self.colorBuffer = None
        
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
        self.hasMousePosUniform = False

    def mouseMoveEvent(self, e):
        if self.hasMousePosUniform:
            toVal=[]
            toVal.append( max( 0.0, min(1.0, float(e.pos().x()/self.imgWidth) ) ) )
            toVal.append( max( 0.0, min(1.0, float(e.pos().y()/self.imgHeight) ) ) )
            print(toVal)
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
        
    def loadImageTex2D(self, filename, samplerId=0 ):
        curImg = None
        curImgData = None
        if filename in self.imgData :
            curImg = self.imgData[filename]['image']
            curImgData = self.imgData[filename]['data']
        else:
            curImg = Image.open(filename)
            curImg.putalpha(255)
            curImgData = np.array(list(curImg.getdata()), np.uint8)
            #self.imgData[filename] = {'image':curImg,'data':curImgData}

        
        #prevTextureId = gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D)
        activeTexture = gl.GL_TEXTURE0 + samplerId + 1
        gl.glActiveTexture( activeTexture )
        texture = gl.glGenTextures(1)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT,1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        
        # TODO : Should maintain sampler name and active id in a map
        samplerUniformLocation = gl.glGetUniformLocation(self.glProgram, self.samplerUniforms[samplerId] )
        gl.glUniform1i(samplerUniformLocation, samplerId+1)

        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameterf(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, curImg.size[0], curImg.size[1], 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, curImgData)
        
        self.imgWidth=curImg.size[0]
        self.imgHeight=curImg.size[1]
        self.curImage = filename
        
        return {'width':curImg.size[0],'height':curImg.size[1],'texture':texture,'location':samplerUniformLocation,'activeTexture':activeTexture}
    
    
    def newFrameBuffer(self, fboSize=[512,512], samplerId=0 ):
        print( "Binding Data Frame Buffer")
        #imgWidth = self.imageTexture[0]['width']
        #imgHeight = self.imageTexture[0]['height']
        
        #print(self.renderFrameBuffer)
        
        # GL_DRAW_FRAMEBUFFER
        #gl.glFramebufferParameteri(gl.GL_FRAMEBUFFER, gl.GL_FRAMEBUFFER_DEFAULT_WIDTH, 512)
        #gl.glFramebufferParameteri(gl.GL_FRAMEBUFFER, gl.GL_FRAMEBUFFER_DEFAULT_HEIGHT, 512)
        #gl.glFramebufferParameteri(gl.GL_FRAMEBUFFER, gl.GL_FRAMEBUFFER_DEFAULT_SAMPLES, 4)
        
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
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER,
            gl.GL_COLOR_ATTACHMENT0,
            gl.GL_TEXTURE_2D,
            self.fboTexture,
            0
        )
        

        if not gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) == gl.GL_FRAMEBUFFER_COMPLETE:
            print('framebuffer binding failed')
            
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0 )
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        
        
    
    def loadProgram(self, glEffect="default"):
        toUniforms = {}
        toVert = ""
        toFrag = ""
        
        if glEffect == "smartBlur":
            import smartBlurShader as Shader
            
        elif glEffect == "edgeDetect":
            import edgeDetectShader as Shader
            
        elif glEffect == "segment":
            import segmentShader as Shader
            
        elif glEffect == "paintMask":
            import paintMaskShader as Shader
            
        elif glEffect == "colorCorrect":
            import colorCorrectShader as Shader
            
        else: # Default to "default"; This will cause issues during dev
            import defaultShader as Shader
        
        toUniforms = Shader.uniforms
        toVert = Shader.vertex
        toFrag = Shader.fragment
        
        self.Shader = Shader
        
        # -- -- -- --
        
        program = gl.glCreateProgram()
        vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)

        # Set shaders source
        gl.glShaderSource(vertex, toVert)
        gl.glShaderSource(fragment, toFrag)

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
        
        # -- -- -- --
        
        return program,toUniforms
        
        
    def buildUniforms(self, glProgram, toUniforms):
        glUniformLocations = {}
        
        uniformKeys = toUniforms.keys()
        
        for x,curUniform in enumerate( toUniforms ):
            uSettings = toUniforms[ curUniform ]
            if uSettings['type'] == "float":
                uLocation = gl.glGetUniformLocation( glProgram, curUniform )
                uVal = uSettings[ 'default' ]
                gl.glUniform1f( uLocation, uVal )
                # -- -- --
                uLocKey = curUniform
                glUniformLocations[ uLocKey ] = uLocation
                
            elif uSettings['type'] == "vec2":
                uLocation = gl.glGetUniformLocation( glProgram, curUniform )
                uVal = uSettings[ 'default' ]
                gl.glUniform2f( uLocation, uVal[0], uVal[1] )
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
                            print(keyVal)
                            curVarElementName = curUniform+"["+str(curElement)+"]"
                            uLocation = gl.glGetUniformLocation( glProgram, curVarElementName )
                            gl.glUniform3fv( uLocation, 1, keyVal )
                            curElement+=1
                
            elif uSettings['type'] in ["texture","fbo"]:
                self.samplerUniforms.append( curUniform )
                
                texId = len(self.samplerUniforms)-1
                self.imageTexture.append( self.loadImageTex2D( self.glTempTex, texId ) )
                if uSettings['type'] == "fbo":
                    curImgTexture = self.imageTexture[-1]
                    self.fboLocation = self.newFrameBuffer( [curImgTexture['width'],curImgTexture['height']], texId )
                    self.hasFrameBuffer = True
            
            if 'control' in uSettings:
                if uSettings['control'] == "visible":
                    controlDict = {}
                    controlDict['type'] = uSettings['type']
                    controlDict['value'] = uSettings['default']
                    controlDict['range'] = uSettings['range'] if 'range' in uSettings else False
                    self.glControls[ curUniform ] = controlDict
                elif uSettings['control'] == "mousePos":
                    self.hasMousePosUniform = True
        
        #gl.glUseProgram(self.glProgram)
        #gl.glActiveTexture(gl.GL_TEXTURE1)
        #
        #gl.glBindTexture(gl.GL_TEXTURE_2D, self.displayImage['texture']) 
        
        #
        
        return glUniformLocations
        
    def initializeGL(self):
        
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        
        #glut.glutInitDisplayMode(glut.GLUT_RGB | glut.GLUT_DOUBLE)
    
        self.glProgram, self.glUniforms = self.loadProgram( self.glEffect )
        
        self.glUniformLocations = self.buildUniforms( self.glProgram, self.glUniforms )
        
        
        
        #gl.glBegin( gl.GL_TRIANGLE_STRIP )
        
        # Build data
        #data = np.zeros((4, 2), dtype=np.float32)
        # From another -
        data = np.zeros(4, [("position", np.float32, 2),("uv", np.float32, 2)])
        data['position'] = [(-1,+1), (+1,+1), (-1,-1), (+1,-1)]
        data['uv'] = [(0,0), (1,0), (0,1), (1,1)]

        indices = [0, 1, 2, 2, 3, 0]
        indices = np.array(indices, dtype=np.uint32)
        
        # TODO : I implemented a VBO and EBO without quite knowing why they were needed
        #          Opposed to a VAO, aside from UV support, which uhhhh
        #            Look into this more
        
        self.VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.itemsize * len(data), data, gl.GL_STATIC_DRAW)

        self.EBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.itemsize * len(indices), indices, gl.GL_STATIC_DRAW)
        

        stride = data.strides[0]
        offset = ctypes.c_void_p(0)
        posLocation = gl.glGetAttribLocation( self.glProgram, "position")
        gl.glEnableVertexAttribArray(posLocation)
        gl.glVertexAttribPointer(posLocation, 2, gl.GL_FLOAT, False, stride, offset)
        
        
        texCoordsLocation = gl.glGetAttribLocation( self.glProgram, "uv")
        gl.glVertexAttribPointer(texCoordsLocation, 2, gl.GL_FLOAT, False,  stride, ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(texCoordsLocation)
        #glBindFragDataLocation( self.glProgram , color , name )
        
        #
        # https://gist.github.com/MorganBorman/4243336
        #
        # Unbind buffers to prevent other GLWidget feet stepping
            
        # Unbind the VAO first (Important)
        #gl.glBindVertexArray( 0 )

        # Unbind other stuff
        #gl.glDisableVertexAttribArray(posLocation)
        #gl.glDisableVertexAttribArray(texCoordsLocation)
        #gl.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        #gl.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
            
        #gl.glEnd
        
        
        
        
        
        gl.glViewport(0, 0, self.imgWidth, self.imgHeight) # Out res is [512,512] setting by default
        
        print("GL Init")
        
        # If it exists, set the values
        if len(self.imageTexture) > 0:
            tx = float( 1/self.imageTexture[0]['width'] )
            ty = float( 1/self.imageTexture[0]['height'] )
            self.setUniformValue( "texelSize", [tx,ty] )
        
        self.parent().createControls( self.glControls )
        
    def paintGL(self):
        gl.glUseProgram(self.glProgram)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        if self.hasFrameBuffer :
            if "isFBO" in self.glUniformLocations:
                self.setUniformValue("isFBO", 1.0, False )
            print( self.frameBufferObject )
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frameBufferObject)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            # -- -- --
            gl.glBindTexture( gl.GL_TEXTURE_2D, self.fboTexture )
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
            # -- -- --
            data = gl.glReadPixels(0, 0, self.imgWidth, self.imgHeight, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, outputType=None)
            outImage = Image.frombytes( 'RGBA', (self.imgWidth,self.imgHeight), data.tobytes() )
            #outImage = Image.frombuffer( 'RGB', (self.imgWidth,self.imgHeight), data )
            outImage = outImage.transpose( Image.FLIP_TOP_BOTTOM)
            saveBufferPath = "F:\\AIGen\\trainingData\\pxlImageLabeler\\bufferOut.png" #.jpg"
            saveBufferFormat = "PNG" # "JPEG"
            try:
                outImage.save( saveBufferPath, saveBufferFormat )
            except OSError as err:
                print("Error saving Buffer to - ", saveBufferPath )
            # -- -- --
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        
        if "isFBO" in self.glUniformLocations:
            self.setUniformValue("isFBO", 0.0, False )
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)
        data = gl.glReadPixels(0, 0, self.imgWidth, self.imgHeight, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, outputType=None)
        outImage = Image.frombytes( 'RGBA', (self.imgWidth,self.imgHeight), data.tobytes() )
        outImage = outImage.transpose( Image.FLIP_TOP_BOTTOM)
        saveColorPath = "F:\\AIGen\\trainingData\\pxlImageLabeler\\colorOut.png" #.jpg"
        saveColorFormat = "PNG" # "JPEG"
        try:
            outImage.save( saveColorPath, saveColorFormat )
        except OSError as err:
            print("Error saving Color to - ", saveColorPath )
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            
        #gl.glUseProgram(0)
    # For Saving -
    # http://bazaar.launchpad.net/~mcfletch/openglcontext/trunk/view/head:/tests/saveimage.py
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
            #print(self.id, self.glUniformLocations['texOffset'])
            uLocation = gl.glGetUniformLocation( self.glProgram, 'texOffset' )
            #print(uLocation)
            #gl.glUseProgram( self.glProgram )
            #uVal = uSettings[ 'default' ]
            #gl.glUniform2f( uLocation, uVal[0], uVal[1] )
            #gl.glUniform2f( self.glUniformLocations['texOffset'], x, y )
            gl.glUniform2f( uLocation, x, y )
            if setOffset :
                self.curOffset=[x,y]
    def imageScale(self,x,y, setScale=True):
        if 'texScale' in self.glUniformLocations :
            #print(self.id, self.glUniformLocations['texScale'])
            uLocation = gl.glGetUniformLocation( self.glProgram, 'texScale' )
            #print(uLocation)
            #gl.glUseProgram( self.glProgram )
            #gl.glUniform2f( self.glUniformLocations['texScale'], x, y )
            gl.glUniform2f( uLocation, x, y )
            if setScale :
                self.curScale=[x,y]

    def setUniformValue(self, uniformName, toValue, doPaint=True ):
        #print("Set uniform value")
        if uniformName in self.glUniforms:
            #gl.glUseProgram(self.glProgram)
            uLocation = gl.glGetUniformLocation( self.glProgram, uniformName )
            
            toValue = [toValue] if type(toValue) == float else toValue
            if len(toValue) == 1:
                gl.glUniform1f( uLocation, toValue[0] )
            elif len(toValue) == 2:
                gl.glUniform2f( uLocation, toValue[0], toValue[1] )
                
            if doPaint:
                self.update()
                self.paintGL()
            #gl.glUseProgram(0)

class ViewportBufferWidget(QWidget):
    def __init__(self,parent=None, glId=0, glEffect="default", initTexturePath="assets/glTempTex.jpg"):
        super(ViewportBufferWidget, self).__init__(parent)
        
        self.id=glId
        self.fullPath = ""
        self.fileName = ""
        self.folderName = ""
        self.folderPath = ""
        self.dispImagePath = ""
        self.data = {}
        
        self.textureGLWidget = None
        
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setContentsMargins(0,0,0,0)
        self.mainLayout.setSpacing(2)
        
        self.textureGLWidget = TextureBufferGLWidget( self, glId, glEffect, initTexturePath )
        self.textureGLWidget.setFixedWidth(512)
        self.mainLayout.addWidget(self.textureGLWidget)
        
        shaderOptionsBlock = QWidget()
        self.shaderOptionsLayout = QVBoxLayout()
        self.shaderOptionsLayout.setContentsMargins(0,2,0,2)
        self.shaderOptionsLayout.setSpacing(2)
        shaderOptionsBlock.setLayout(self.shaderOptionsLayout)
        self.textureGLWidget.setMaximumWidth(250)
        self.mainLayout.addWidget(shaderOptionsBlock)

        self.setLayout(self.mainLayout)

    def imageOffset(self,x,y, setOffset=True):
        if self.textureGLWidget:
            self.textureGLWidget.imageOffset(x,y,setOffset)
    def imageScale(self,x,y, setScale=True):
        if self.textureGLWidget:
            self.textureGLWidget.imageScale(x,y,setScale)
    def createControls( self, controls ):
        for uniform in controls:
            print(uniform)
            uData = controls[uniform]
            controlLayout = QHBoxLayout()
            controlLayout.setContentsMargins(0,0,0,10)
            controlLayout.setSpacing(2)
            # -- -- --
            uLabelText = uniform
            uLabelText = "".join(list(map(lambda x: " "+x if x.isupper() else x, uLabelText)))
            uLabelText = uLabelText[0].capitalize() + uLabelText[1::]
            controlLabelText = QLabel( uLabelText, self)
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
                #curSlider.setGeometry(30, 40, 200, 30)
                curSlider.setMinimum( int(valLimits[0]*(10**multVal)) )
                curSlider.setMaximum( int(valLimits[1]*(10**multVal)) )
                curSlider.setValue( int(val*(10**multVal)) )
                #curSlider.valueChanged[float].connect(lambda: self.updateUniformValue(curSlider,uniform))
                controlLayout.addWidget(curSlider)
                sliderList.append(curSlider)
            for slider in sliderList:
                slider.valueChanged.connect(partial(self.updateUniformValue,sliderList,uniform,multVal))
    
    def updateUniformValue(self,sliderList,uniform,decimalCount):
        toValue = []
        for slider in sliderList:
            toValue.append( slider.value()/(10**decimalCount) )
        self.textureGLWidget.setUniformValue( uniform, toValue )
        
# main function
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
 
    # app created
    app = QApplication(sys.argv)
    w = TextureBufferGLWidget()
    w.setupUI()
    w.show()
    
    #w = ImageLabelerWindow()
    #w.setupUI()
    #w.show()
    
    # begin the app
    sys.exit(app.exec_())