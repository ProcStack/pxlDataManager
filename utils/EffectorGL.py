
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
        self.glTempTex = "assets/glTempTex.jpg"
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