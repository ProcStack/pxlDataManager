#
# ** Work In Progress **
#
# Custom PyQt5 QOpenGLFramebufferObject
#   For easy Image and Bind handling 
#
# Less micromanagement of texture needs from other ViewportGL contexts
# 


from PyQt5 import QtGui



class pvgTextureFBO( QtGui.QOpenGLFramebufferObject ):
    
    # Dump GL Texture Objects from VRAM and Destroy; Keep QImage Objects
    DestroyGL_Textures = 0
    # Dump GL FBO Objects from VRAM and Destroy; Keep QImage Objects
    DestroyGL_FBO = 1
    # Dump GL Textures & FBO Objects from VRAM and Destroy; Keep QImage Objects
    DestroyGL_All = 2
    # Dump All GL Objects from VRAM and Destroy; Destroy QImage Objects
    DestroyAllData = 3
    
    def __init__(self, glScope=None, sImage=None, sSize=[0,0]):
        
        self._className = self.__class__.__name__
        
        self.gl = glScope
        self._image = None
        self._size = sSize
        self._texture = None
        self.bindings = {}
        
        self._genImageFormat = QtGui.QImage.Format_RGBA8888
        self._genMipMaps = QtGui.QOpenGLTexture.DontGenerateMipMaps
        
        
        super(pvgTextureFBO, self).__init__( self._size[0], self._size[1] )
    # QtGui.QImage(fboSize[0], fboSize[1], QtGui.QImage.Format_RGBA8888)
    # QtGui.QOpenGLTexture
    # QtGui.QOpenGLFramebufferObject( fboSize[0], fboSize[1])
    
    def setTexture( self, sourceImage = None ):
        sourceType = type(sourceImage)
        if sourceType == QOpenGLTexture:
            print( "Passing QOpenGLTexture to "+self._className+" no supported" )
            
            return;
        if sourceType == str:
            # Treat as Image Disk Path
            imageData = QtGui.QImage.load( sourceImage )
        elif sourceType == QImage:
            imageData = sourceImage
            
        #self._image.swap( imageData )
        self._image = imageData
        self._texture.setData(self._image, genMipMaps = self._genMipMaps )
    
    def texture( self ):
        return self._texture
        
    def bind( self ):
        super().bind()
        
    def release( self ):
        super().release()
        
    def getQPixmap( self ):
        return QtGui.QPixmap.fromImage( self._image )
        
    def getQImage( self ):
        return self._image
    
    # Delete all by default
    def destroy( self, byType = 3 ):
        if byType == self.DestroyGL_Textures :
            pass;
        elif byType == self.DestroyGL_FBO :
            pass;
        elif byType == self.DestroyGL_All :
            pass;
        elif byType == self.DestroyAllData :
            pass;
        
        
        