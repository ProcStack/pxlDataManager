 ## OpenGL Shader Python Files
 #### GL Shader Files - `./utils/glShaders`
 
Most Math & Utility functions aren't used in pxlDataManager,
<br>&nbsp;&nbsp;They are just my ussualy swiss army knife of go-to functions
<br>&nbsp;&nbsp;&nbsp;&nbsp;So I add them out of habbit

<hr>

### `shaderMath.py`
 - General OpenGL Math Functions
 - Program `#defines`
   - `def_PI` - `#define PI`
   - `def_TAU` - `#define TAU` *( Pi x 2 )*
 - Variable Value Functions
   - `clamp` - `clamp( VALUE, MIN, MAX )`
     - *(Prior to OpenGL 4 / OpenGL ES 3, `clamp()` doesn't exist)*
   - `clamp01`- `clamp01( VALUE )`
   - `biasToOne`
     - `biasToOne( VALUE )` - 1 - ( VALUE * VALUE ), Biasing to 1.0
     - `biasToOne( VALUE, BIAS )` - 1 - ( (VALUE*BIAS) * (VALUE*BIAS) ), Biasing to 1.0 with BIAS multiplier
   - `maxComponent` - Maximum component of provided `vec2`, `vec3`, or `vec4`
   - `addComponents` - Add all components of provided `vec2`, `vec3`, or `vec4`
   - `rotToUV` - Vec3 direction vector to UV Vec2
     - Useful for casting Normalized Direction Vector to Texture Space
       - eg. Camera direction to Texture for 360 sphere
       - eg. Surface Reflection Vector to Texture for PBR environment map
 - Color Space Changing Functions
   - `luma` - Color Vec3 to Greyscale with color prominance adjustment
     - Visually looks like Color to Actual Greyscale, but isn't
   - `greyScale`- Raw Color Vec3 to Literal Greyscale
   - `rgb2hsv` - Color Vec3 RGB to vec3( Hue, Sturation, Value )
   - `hsv2rgb` - HSV to RGB Vec3
 - A-to-B Blending Functions
   - `deltaDivToBlender` - Soft Out, Soft In; 3rd argument is div & subtractor bias
   - `sinToBlender` - Linear Out, Smooth In, 3rd argument is Sine Wave Magnitude, pre 0-1 clamp
   - `logPowToBlender` - Slower Out, Sharp In, 3rd argument is log(value, ARG)
   - `powToBlender` - Slow Out, Slight Slow In, 3rd argument is value^ARG
 - Matrix Functions
   - `getRotationMatrix()` - Create static Rotation Matrix, 3x3 or 4x4 with optional Position Vector
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

<hr>

### `defaultShader.py`
 - Default Vertex & Fragment Shaders
 - Sample & Output Texture Color
<br><br>


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

