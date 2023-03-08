# Persistent User Settings Manager

import os, sys
import json

# Yar, QSettings exists in PyQt5, but ::shrugs::
#   Not a fan of the whole saving to disk under a company name and hidden to the user
#     You wanna reset these settings? Just delete the userSettings.json file!
#   Don't really want to be tied to PyQt for this either
#
# Arg `linkedValueDict` can be an existing dictionary
#   Memory linked, so the dict will always be up to date
#     Exists for '.newSubData()' to persist parent settings
#       While also allowing saving settings at any level of nested '.newSubData()' objects
#
# Subscriptions & 'hasChanges' emits pass to the top level UserSettingsManager

class UserSettingsManager():
    def __init__(self, name="userSettings", linkedValueDict=None, subDataEntry=[]):
        self._parent = None
        self.name = name
        self.file = name + ".json"
        self.fileFullPath = os.path.abspath( self.file )
        self.fileRoot = os.path.dirname( self.fileFullPath )
        
        self.hasChanges = False
        
        self._values = linkedValueDict
        
        fixCurEntry = subDataEntry if type(subDataEntry) == list else [subDataEntry]
        self._curEntry = list( filter( None, fixCurEntry ) )
        
        self._subscribers = []
        
        if linkedValueDict == None:
            self.load()
        
    def load( self ):
        if os.path.isfile( self.fileFullPath ):
            with open( self.fileFullPath, "r", encoding="utf-8" ) as curJson:
                data = json.load(curJson)
                self._values = data
        elif self._values == None:
            self._values = {}
            
    def save( self ):
        if self.hasChanges:
            f = open( self.fileFullPath, "w")
            f.write(json.dumps(self._values, indent = 2))
            f.close()
            self.newChanges(False)
        return True
        
    # I keep typing '.read()' ...
    def read( self, settingName, default=None ):
        return self.value( settingName, default )
        
    def _currentValueDict( self ):
        ret = self._values
        for x in self._curEntry :
            ret = ret.get( x, ret )
        return ret
        
    # TODO : Combine '.set()' and '.value()'
    def value( self, settingName, default=None ):
        curValues = self._currentValueDict()
        if settingName in curValues:
            return curValues[ settingName ]
        else:
            self.set( settingName, default )
        return default
        
    def set( self, settingName, settingValue ):
        curValues = self._currentValueDict()
        if settingName in curValues and curValues[settingName] == settingValue:
            return settingValue
        curValues[ settingName ] = settingValue
        self.newChanges(True)
        return settingValue
        
    """
    # Create SettingsManager at a sub-class / sub-module depth
    #   Value dict persists and maintains depth level
    # TODO : Same `subDataName` names at the same depth will overwrite each other
    #          Currently, the developer should just pass unique names for duplicate nested iterations
    #            Should just pass a 'subDataName' value anyway for organization reasons
    """
    def newSubData( self, subDataName = None ):
        if subDataName == None :
            curStack = sys._getframe(1)
            if 'self' in curStack.f_locals :
                try:
                    subDataName = curStack.f_locals['self'].__class__.__name__
                except:
                    try:
                        subDataName = curStack.f_code.co_name
                    except:
                        subDataName = "SubData"
            print(" ** UserSettingsManager; No 'subDataName' passed, setting to '",subDataName,"' ** ")
            
        dataToPersist = self._currentValueDict()
        if subDataName not in dataToPersist :
            dataToPersist[ subDataName ] = {}
        
        # Step sub-data path
        dataPath = self._curEntry.copy()
        dataPath.append( subDataName )
        
        subSettingsManager = UserSettingsManager( self.name, self._values, dataPath )
        subSettingsManager._parent = self
        return subSettingsManager
    
    def newChanges( self, newHasChanges=False ):
        if self._parent != None :
            self._parent.newChanges( newHasChanges )
        else:
            self.hasChanges = newHasChanges
            self.emitChangesValue( self.hasChanges )
        
    # HasChanges Event Listener Subscriptions & Emits
    # TODO : Make this a typed checking dict / collections' defaultdict
    def subscribe( self, func ):
        if self._parent != None :
            self._parent.subscribe( func )
        else:
            self._subscribers.append( func )
        
    def emitChangesValue( self, emitState ):
        if self._parent != None :
            self._parent.emitChangesValue( emitState )
        else:
            for func in self._subscribers:
                func( emitState )
        
        