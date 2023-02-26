# Persistent User Settings Manager

import os
import json



# Yar, QSettings exists in PyQt5, but ::shrugs::
#   Not a fan of the whole saving to disk under a company name and kinda hidden to the user
#     Wanna reset these settings, just delete the userSettings.json file!
class UserSettingsManager():
    def __init__(self, name="userSettings"):
        self.name = name
        self.file = name + ".json"
        self.fileFullPath = os.path.abspath( self.file )
        self.fileRoot = os.path.dirname( self.fileFullPath )
        
        self.hasChanges = False
        self._values = {}
        
        self._subscribers = []
        
        self.load()
        
    def load(self):
        if os.path.isfile( self.fileFullPath ):
            with open( self.fileFullPath, "r", encoding="utf-8" ) as curJson:
                data = json.load(curJson)
                self._values = data
    def save(self):
        if self.hasChanges:
            f = open( self.fileFullPath, "w")
            f.write(json.dumps(self._values, indent = 2))
            f.close()
            self.newChanges(False)
        return True
    # I keep typing '.read()' ...
    def read(self, settingName, default=None ):
        return self.value( settingName, default )
    def value(self, settingName, default=None ):
        if settingName in self._values:
            return self._values[ settingName ]
        else:
            self.set( settingName, default )
        return default
    def set(self, settingName, settingValue ):
        if settingName in self._values and self._values[settingName] == settingValue:
            return settingValue
        self._values[ settingName ] = settingValue
        self.newChanges(True)
        return settingValue
    def newChanges(self, newHasChanges=False ):
        self.hasChanges = newHasChanges
        self.emitChangesValue( self.hasChanges )
        
    # Has Changes Event Listeners
    def subscribe(self, func):
        self._subscribers.append( func )
    def emitChangesValue(self, emitState ):
        for func in self._subscribers:
            func( emitState )
        
        