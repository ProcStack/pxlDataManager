# Printer with Tracing Support
#   Developed for Windows CMD Coloring
#     Linux command prompt colors to come

import time
#from enum import Enum

class VerboseLevelEnum():#(Enum):
    NONE = 1
    ERROR = 2
    WARNING = 3
    STATES = 4
    INFO = 5
    DEBUG = 6
    TRACER = 7
    
class PrintTimeEnum():#(Enum):
    NONE = 1
    DISABLED = 2
    EPOCH = 3
    HUMAN_READABLE = 4
    
class LogManager():
    def __init__(self, parent=None, prefix=None, logLevel=VerboseLevelEnum.WARNING, logTime=PrintTimeEnum.DISABLED):
        self.parent = parent
        
        self.prefix = prefix
        
        self.logLevel = logLevel
        self.printTime = logTime
        self.onceLevel = VerboseLevelEnum.NONE
    
    def getTimeStr( self ):
        if self.printTime <= PrintTimeEnum.DISABLED :
            return ""
            
        if self.printTime > PrintTimeEnum.EPOCH :
            return str(time.time())+"; "
        else: #elif self.printTime > PrintTimeEnum.HUMAN :
            return str(time.ctime( time.time() ))+"; "
            
    
    def formatMessage( self ):
        return self.getTimeStr()+" "+self.prefix
    
    def printMsg( self, *msgArgs ):
        msgPrint = self.formatMessage()
        print( msgPrint )
        print( msgArgs )
    
    def print( self, logLevel=1, *msgArgs ):
        if logLevel > self.logLevel :
            self.printMsg( msgArgs )
    