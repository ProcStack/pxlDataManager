 ## Utility Python Files; `./scripts/utils`
 
### `ControlNetGenerator.py`
 - **WIP** Run Image Path through ControlNet pre-processor models
 - Generation Modes -
   - `Canny`
   - `MLSD`
   - `HED`
   - `Depth`
   - `Normal`
   - `OpenPose`
<br><br>

### `FaceFinder.py`
 - Find all faces in an image path
 - Automatically save Aligned faces to Path
   - 'Aligned' meaning upright and cropped to size
 - `FaceFinder.input( IMAGE_PATH )` returns Faces[]
   - `return[#]['alignedPath']` - Cropped aligned face image file path
   - `return[#]['unalignedPath']` - Cropped unaligned face image file path
   - `return[#]['detFace']` - Found faces Bounding Box, by Pixels, [ X, Y, Width, Height ]
<br><br>


### `ImageToPrompt.py`
 - Generate `BLIP` prompt from image, Image2Prompt
<br><br>


### `UserSettingsManager.py`
 - Store arbitrary values to a `./userSettings.json` *(default name)* file
 - Opted against PyQt stored data object for accessable settings from access outside of runtime
 - `UserSettingsManager.read( 'toggleableSetting', True )`
   - Read stored 'toggleableSetting', if doesn't exist, default to 'True' and store to Settings File
   - Stored Setting Type is second passed argument
 - Holds `self.hasChanges` bool for 'Unsaved Changes' on Exit check, if added
<br><br>
