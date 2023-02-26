 ## OpenGL Shader Python Files; `./utils/glShaders`
 

### `shaderMath.py`
 - General OpenGL Math Functions
 - Program `#defines`
   - `def_PI` - Pi Define
   - `def_TAU` - Tau Define ( Pi x 2 )
 - Variable Value Functions
   - `clamp`
   - `clamp01`
   - `biasToOne`
   - `maxComponent`
   - `addComponents`
   - `rotToUV`
 - Color Space Changing Functions
   - `luma`
   - `greyScale`
   - `rgb2hsv`
   - `hsv2rgb`
 - A-to-B Blending Functions
   - `deltaDivToBlender`
   - `sinToBlender`
   - `logPowToBlender`
   - `powToBlender`
 - Matrix Functions
   - `getRotationMatrix()`
<br><br>

### `shaderUtils.py`
 - General  Utility Functions
 - Box Blur Samples Array
   - `getBoxSamples( 1, 2, or 3 )`
     - `getBoxSamples( 1 )` - Returns + Samples; Up, Down, Left, & Right vec2[]
     - `getBoxSamples( 2 )` - Returns X Samples; Diagnal vec2[]
     - `getBoxSamples( 3 )` - Returns [] Samples; 3x3 Box vec2[]
 - Box Blur Sampling
   - `getBoxBlur( 1, 2, or 3 )` - Returns a box blur function; with required `getBoxSamples()` constants
<br><br>

### `defaultShader.py`
 - Default Vertex & Fragment Shaders
 - Sample & Output Texture Color
<br><br>

<hr>

### `colorCorrectShader.py` **WIP**
 - Color Correct Texture Shader
<br><br>

### `edgeDetectShader.py` **WIP**
 - Find Edges In Texture Shader
 - Currently only using an adapted Kuwahara function
<br><br>

### `paintMaskShader.py` **WIP**
 - User Interactive Masking Shader
<br><br>


### `segmentShader.py` **WIP**
 - Segmentation FBO Feedback Shader
 - Find provided Segment Region Seeds & Write to FBO
   - Subsequent FBO renders grows Region by 1 pixel *(currently)*
 - On 'Render To Screen' pass of same shader simply merges Region Data with Source Texture *(currently)*
<br><br>

### `smartBlurShader.py` **WIP**
 - Blur Pixel Samples Based On Threshold
 - Currently only using an adapted Kuwahara function
<br><br>

