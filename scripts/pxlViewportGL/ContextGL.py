
# Built on Python 3.10.6 && PyQt5 5.15.9

# OpenGL Context Manager
#   Used for creating an OpenGL Shared Context
#   Passing the Context to subsiquent QOpenGL widgets
#
# Generating a PyQt5 OpenGL Context within a Widget
#   Requires the context be generated on an off-screen surface
#
#  **( Work In Progress )**
# Being a Shared Context, the Manager will also maintain
#   Texture-to-Texture Blitting
#   Texture Saves To Disk
#   And other sharable bindable objects
#     Which most will simply be a texture location
#       Passed from the child contexts
#         Currently only 'ViewportGL.py'
#
#
# Tread this Object as the Uploader and Resource Manager
#
# TODO : There is no check for when QtApp has Qt.AA_ShareOpenGLContexts 'True'
#          Yet fails to return a valid global context
#        Have seen situations where ContextGLManager never initializes
#          Causing other ViewportGLs to never build
#            Likely lack of Offscreen Shared Context Prep in __init__()
#        Needs for Threading and more ViewportGL Cross Talk

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


class ContextGLManager(QtWidgets.QOpenGLWidget):
#class TextureGLWidget(QtOpenGL.QGLWidget):
    contextCreated = QtCore.pyqtSignal( QtGui.QOpenGLContext )

    def __init__(self):
        #super().__init__()
        super(ContextGLManager, self).__init__() 
        
        # -- -- --
        
        self.globalContext = None
        self.globalFormat = None
        self.gl = None
        #self.context = None
        self.initialized = False
        
        # -- -- --
        
        #self.setSurfaceType(QWindow.OpenGLSurface)
        
        # -- -- --
        
        self.profile = QtGui.QOpenGLVersionProfile()
        self.profile.setVersion( 2, 1 )
        
        # -- -- --

        self.Shader = None
        self.glProgram = None
        
        self.offscreenVAO = None
        self.renderVAO = None
        self.positionVBO = None
        self.uvVBO = None
        
        self.curTexture = None
        
        #print( self.context() )
        #print( QtGui.QOpenGLContext.globalShareContext() )
        
        
        #if QApplication.testAttribute(QtCore.Qt.AA_ShareOpenGLContexts):
        #    print("Global Context Triggered")
        
        # Check for Global OpenGL Shared Context
        self.checkContextState()
            
    def checkContextState(self):
        print("eh?")
        print(self.globalContext, self.globalFormat)
        if self.globalContext and self.globalFormat :
            return self.globalContext, self.globalFormat
        if QApplication.testAttribute(QtCore.Qt.AA_ShareOpenGLContexts):
            print( " Share OpenGL Context Valid on QtApp; Verifying Global Shared State " )
            self.globalContext = QtGui.QOpenGLContext.globalShareContext()
            if self.globalContext.isValid() :
                print( "Valid Global Context, Propegating..." )
                self.globalFormat = self.globalContext.format()
                if self.globalFormat :
                    return self.globalContext, self.globalFormat
        # Failed to find global context
        #   Await initializeGL for created glContext to share
        return None,None
                
        
    def initializeGL(self):
        print("Init ContextGL")
        self.gl = self.context().versionFunctions( self.profile )
        
        # -- -- --
        
        self.offscreenVAO = QtGui.QOpenGLVertexArrayObject( self )
        self.offscreenVAO.create()
        self.renderVAO = QtGui.QOpenGLVertexArrayObject( self )
        self.renderVAO.create()

        # -- -- --
        
        self.glProgram = self.loadProgram()
        
        # -- -- --
        
        self.glProgram.bind()
        
        # screen render
        self.renderVAO.bind()
        posList = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
        uvList = [ 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0 ]
        self.positionVBO = self.setVertexBuffer( posList, 2, self.glProgram, "position" )
        self.uvVBO = self.setVertexBuffer( uvList, 2, self.glProgram, "uv" )
        self.renderVAO.release()
        
        # -- -- --
            
        self.initialized = True
        
        self.contextCreated.emit( self.context() )
        
        print("Context Initiated")
        
    def paintGL(self):
        print("ContextGL Render Triggered")
        
        
        
    def loadProgram(self, glEffect="default"):
    
        from .glShaders import defaultShader as Shader
        self.Shader = Shader
        
        toVertex = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Vertex, self )
        toVertex.compileSourceCode( self.Shader.vertex )

        toFragment = QtGui.QOpenGLShader( QtGui.QOpenGLShader.Fragment, self )
        toFragment.compileSourceCode( self.Shader.fragment )
        
        # -- -- -- --
        
        program = QtGui.QOpenGLShaderProgram( self )
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
        
        return program
        
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