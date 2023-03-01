 ## OpenGL Python Files; `./scripts/pxlViewportGL`
 
### `ContextGL.py`
 - **WIP** Shared OpenGL Context Generator
<br><br>


### `ViewportGL.py`
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
