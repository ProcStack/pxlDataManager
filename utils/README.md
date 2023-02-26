 ## Utility Python Files; `./utils`
 
 - `ControlNetGenerator.py`
  - **WIP** Run Image Path through ControlNet pre-processor models
  - Generation Modes -
   - `Canny`
   - `MLSD`
   - `HED`
   - `Depth`
   - `Normal`
   - `OpenPose`
   
 - `FaceFinder.py`
  - Find all faces in an image path
  - Automatically save Aligned faces to Path
   - 'Aligned' meaning upright and cropped to size
  - `FaceFinder.input( IMAGE_PATH )` returns Faces[]
   - `return[#]['alignedPath']` - Cropped aligned face image file path
   - `return[#]['unalignedPath']` - Cropped unaligned face image file path
   - `return[#]['detFace']` - Found faces Bounding Box, by Pixels, [ X, Y, Width, Height ]
   
 - `FileIngester.py`
  - Find Folder images & correlated data
  - Add, save, modify User Data per image
  
 - `ImageToPrompt.py`
  - Generate `BLIP` prompt from image, Image2Prompt
  
 - `TrainingLabelGenerator.py`
  - Image + Prompt File Pair Manager & Editor
  
 - `UserSettingsManager.py`
  - Store arbitrary values to a `./userSettings.json` *(default name)* file
  - Opted against PyQt stored data object for accessable settings from access outside of runtime
  - `UserSettingsManager.read( 'toggleableSetting', True )`
   - Read stored 'toggleableSetting', if doesn't exist, default to 'True' and store to Settings File
   - Stored Setting Type is second passed argument
  - Holds `self.hasChanges` bool for 'Unsaved Changes' on Exit check, if added
  
 - `ViewportBufferGL.py`
  - **Not used, to be deleted.**
  - Was created for testing PyOpenGL + PyQt5 Frame Buffer Feedback Rendering & Reading
  
 - `ViewportGL.py`
  - OpenGL widget generator reading shaders from `./glShaders`
   - These shaders determine functionality of `ViewportWidget` objects
  - Example Python -
   - Create VBO & EBO with Vertex Attributes
    - `initializeGL()`
   - Create OpenGL Shader Program
    - `loadProgram()`
   - Read & Build Texutures from Image Files Paths
    - `loadImage()`
    - `loadImageTex2D()`
   - Create & Bind FBO for Shader Feedback
    - `newFrameBuffer()`
   - Dynamically Build & Connect Controls to Shader Uniforms
    - `createControls()`
   - Update & Feedback FBO into Shader
    - `paintGL()`
   - User Mouse Move events to update shader Texture Offset & Scale Uniforms
    - `mousePressEvent()`
    - `mouseMoveEvent()`
    - `mouseReleaseEvent()`
   - Save Screen or Buffer to Image File
    - `saveBuffer()`
