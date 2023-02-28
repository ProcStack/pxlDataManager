# pxlDataManager TODOs & Status
Major Issues & TODOs; smaller things are commented with `TODO` in their respective scripts.
<br>&nbsp;&nbsp;*( 'vim' auto highlighting 'TODO' has ruined me ... )*
<br>&nbsp;&nbsp;&nbsp;Like desired changes of working logic,
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Or dirty code that needs some cleaning behind it's ears

## Current known issues
### pxlDataManager -
<br>&nbsp;&nbsp;_Resizing Lower Shelf is janky as all the funking trumpet players...
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Seeming counter resizing between `QApplication.processEvents()` calls during resizing.

## TODOs 
### pxlDataManager -
<br>&nbsp;&nbsp;_Auto Load Face & Classified Crops isn't implemented

### Suplimental AIs -
<br>&nbsp;&nbsp;_Make AI's Async; FaceFinder & ImageToPrompt
<br>&nbsp;&nbsp;_Implement OpenPose finder for ControlNet prep

### ViewportGL -
<br>&nbsp;&nbsp;_Further develop the ViewportGL shaders
<br>&nbsp;&nbsp;_Shared GL Contexts may cause disconnecting textures from progam binds
<br>&nbsp;&nbsp;_Making an offscreen primary Context may eleviate active context switching issues
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Currently the first generated gl widget claims context generation
<br>&nbsp;&nbsp;_Currently the OpenGL system is in a Development state
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Shaders & Classes to be more modular and class extensions
<br>&nbsp;&nbsp;_Better system for loading shaders
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Currently just variables & functions in files
