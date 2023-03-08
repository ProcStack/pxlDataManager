 ## OpenGL Shader Python Files
 #### GL Shader Files - `./glShaders`
 
Most Math & Utility functions aren't used in pxlViewportGL,
<br>&nbsp;&nbsp;They are just my ussualy swiss army knife of go-to functions
<br>&nbsp;&nbsp;&nbsp;&nbsp;So I add them out of habbit
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If I need em, they're there


Currently, variables are at script root level
<br>&nbsp;&nbsp;Plans for nesting variables into a singular dictionary
<br>&nbsp;&nbsp;&nbsp;&nbsp;But the shader workflow is in dev, so holding off for now

<hr>

## Shader Variables / Settings -
&nbsp;&nbsp;The understood built-ins of shader files
<br>&nbsp;&nbsp;&nbsp;&nbsp;Custom variables can be added,
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;But wont be understood natively

#### `settings` - Dictionary Variable; Optional Settings
 - `fboShader`; Boolean;
   - When **True**, attempts to read and compile `fboVertex` and `fboFragment` for offscreen rendering
   - If either variable doesn't exist in the shader.py file
       <br>&nbsp;&nbsp;It will default to using its respective `vertex` or `fragment` shader
 - `hasSim`; Boolean;
   - When **True**, a feedback buffer will be created
   - This feedback texture will be your FBO results
   - To read this feedback texture, set a Uniform to `{'type':'fbo'}`
 - `simTimerIterval`; Int;
   - Required when `hasSim` = True
   - Forced minimum of 20
   - Millisecond delay between simulation steps
 - `simRunCount`; Int;
   - Required when `hasSim` = True
   - Forced minimum of 1
   - Number of times the simulation runs before the timer stops
   - If your shader reaches out 2 pixels per sim step, with a sim count of 10
       <br>&nbsp;&nbsp;The end render will have reach out 20 pixels per simulation run

#### `uniforms` - Dictionary Variable
 - There should be an Key:{Value} entry for every Uniform in your shaders
 - Uniform Name : {Value Entries} -
   - 'type'
     - `float`, `int`, `vec2`, `vec3`, and `vec4`
       - **WIP** Each variable type support arrays `[]`; eg, `vec3[]`
         - Make sure your shader has a constant array length set
         - See `segmentShader.py` for a vec3 array example
       - **WIP** More variable types to be added
     - `texture`; `uniform sampler2D UNIFORM_NAME`
     - `fbo`; `uniform sampler2D UNIFORM_NAME`
       - Sets FBO off screen render buffer and when `settings['hasSim']=True`
       - This the output render from the 'fbo' render pass
           <br>&nbsp;&nbsp;The previous fbo render's output
     - `fboSwap`; `uniform sampler2D UNIFORM_NAME`
       - Sets FBO off screen render & FBO Swap buffers and when `settings['hasSim']=True`
       - This the output render from the 'fboSwap' render pass
           <br>&nbsp;&nbsp;The previous fboSwap render's output
       - Use `fboSwap` in your `fboVertex` or `fboFragment` shader
           <br>&nbsp;&nbsp;To have access to the prior frames render
     - `toScreen`; `uniform sampler2D UNIFORM_NAME` **WIP, not implemented**
       - Sets the prior render shown to screen as the sampler's texture
       - This is the final output of all render passes from the previous frame
           <br>&nbsp;&nbsp;The previous visible render seen in your window's widget
   - 'default'
     - The value of your uniform when created; initial value
     - When using a vector or array type, pass a flat or nested python list/tuple/dict the size of the type
       - If `'type':'float'`
         - Then `'default' : 2.0`
       - If `'type':'vec3'`
         - Then `'default' : [ 0,1,2 ]`
       - If `'type':'vec3[]'` and `uniform vec3 UNIFORM_NAME[3];`
         - Then `'default' : [ [0,1,2], [3,4,5], [6,7,8] ]`
         - Or `'default' : {'pos':[3,6,4],'color':[.1,.4,1],'offset':[1,8,9]}`
             - Converts to - `'default' : [ [3,6,4], [.1,.4,1], [1,8,9] ]`
         - **WIP** Only `vec3[]` supported currently
         - **WIP** See `segmentShader.py` for a vec3 array example
   - 'control'
     - `texelSize`; `vec2()`
       - Automatically set to `vec2( 1.0 / Render Width, 1.0 / Render Height )`
       - Currently no support for Image Texel Sizes natively
         - For sampler based texel sizes or sampling neighboring pixels, in your shader, use -
             <br>&nbsp;&nbsp;`vec2 texelSize = 1.0 / vec2( textureSize(SAMPLER,0) );
             <br>&nbsp;&nbsp;&nbsp;&nbsp;*- or -*
             <br>&nbsp;&nbsp;`vec4 offsetColorSample = textureOffset( SAMPLER, uv, ivec2(OFFSET_X_PIXELS, OFFSET_Y_PIXELS) );
         - *A performance note*, if you are redrawing your shader in requently / real time *( Not native behaviour )*
             <br>&nbsp;&nbsp;And plan on using `1.0 / vec2( textureSize(SAMPLER,0) )`
             <br>&nbsp;&nbsp;&nbsp;&nbsp;Run this in your `vertex` shader and set a varying/out variable
             <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;As division functions are expensive
       - Must be `'type':'vec2'` & `uniform vec2 UNIFORM_NAME;`
     - `userOffset`; `vec2()`
       - This value is set by the user's Left Click + Drag offset
         - A vec2 of click drag aggregate in uv space
           - Left click drag of 64 pixels X and 256 pixels Y in a 512x512 view
               <br>&nbsp;&nbsp;Will be a UNIFORM_NAME value of `vec2( 0.125, .5 )`
       - Must be `'type':'vec2'` & `uniform vec2 UNIFORM_NAME;`
     - `userScale`; `vec2()`
       - This value is set by the user's Right Click + Drag offset
         - A vec2 of click drag aggregate in a `vec2( 1, 1 )` based space
           - Right click drag Left will go below 1
               <br>&nbsp;&nbsp;UNIFORM_NAME value could be `vec2( 0.85, 0.85 )`
           - Right click drag Right will go above 1
               <br>&nbsp;&nbsp;UNIFORM_NAME value could be `vec2( 1.125, 1.125 )`
       - Must be `'type':'vec2'` & `uniform vec2 UNIFORM_NAME;`
     - `mousePos`; `vec2()`
       - As a user moves their mouse over the window
           <br>&nbsp;&nbsp;Their mouse position will set UNIFORM_NAME as -
           <br>&nbsp;&nbsp;&nbsp;&nbsp;`vec2( POSITION_X / Render Width, POSITION_Y / Render Height )`
     - `visible`
       - This Uniform will automatically create slider(s) gui elements
           <br>&nbsp;&nbsp;For user controlable values
       - Slider value changes automatically re-render the viewport
           <br>&nbsp;&nbsp;Do watch out about shaders used for simulations
     - `isFBO`; `float`
       - If using the same shaders for both FBO and to-screen renders
           <br>&nbsp;&nbsp;Use this variable for offscreen specific math/logic
       - Must be `'type':'float'` & `uniform float UNIFORM_NAME;`
           <br>&nbsp;&nbsp;`float` for easy use in `mix()` functions
     - `isSimStep`; `float` **WIP**
       - **Currently not implemented**
       - Since some functions require redrawing the viewport context
           <br>&nbsp;&nbsp;Use this variable for simulation specific math/logic
       - Situations when the viewport will re-render itself -
         - Visible controller gui values have changed
         - Saving image to disk
         - If using pxlDataManager, when passing viewport render between other viewport contexts
           <br>&nbsp;&nbsp;Viewport Contexts are shared,
           <br>&nbsp;&nbsp;&nbsp;&nbsp;But done to make sure the texture is up-to-date for QImage/QPixmap needs
       - Must be `'type':'float'` & `uniform float UNIFORM_NAME;`
           <br>&nbsp;&nbsp;`float` for easy use in `mix()` functions
     - `simStep`; `int` **WIP**
       - **Currently not implemented**
       - Current sim count; starting at 0, stepping up by 1 until `settings['simRunCount']` value
       - Max value will be `settings['simRunCount'] - 1`; non-inclusive
     - `simStepTotal`; `int` **WIP**
       - **Currently not implemented**
       - Total steps of current simulation; 0 to Total
     - `simRunPercent`; `float` **WIP**
       - **Currently not implemented**
       - UNIFORM_NAME value set as - `simStep / (simStepTotal-1)`
       - Since `simStep` will never equal `simStepTotal`,
           <br>&nbsp;&nbsp;This allows for a 0.0 to 1.0 simulation percentage
   - 'range'
     - The slider(s) min/max value range when UNIFORM_NAME is set `'control':'visible'`
       - Should be a list with a size of 2; [ Min Int/Float, Max Int/Float ]
     - Currently, for multi-component types, like vec2, vec3, vec4
         <br>&nbsp;&nbsp;This range is set for all component sliders

#### `attributes` - List Variable
 - Order of attribute bindings when building shader program
     <br>&nbsp;&nbsp;Attribute order must match your `attribute` or `in` order
 - Currently hard-coded as - 
     <br>&nbsp;&nbsp;`attributes[0] = gl_Position`
     <br>&nbsp;&nbsp;`attributes[1] = gl_TexCoord`
     <br>&nbsp;&nbsp;&nbsp;&nbsp;So set position first and texCoord second

#### `fboUniforms` - Dictionary Variable
 - Used when `settings['fboShader'] = True`
 - If not set, `uniform` will be used for FBO shader uniforms

#### `vertex` - String Variable
 - This is the shader that will be used for the Vertex stage in the viewport OpenGL Shader Program
 - Also the default Vertex stage for FBO renders when `settings['fboShader'] = True`
 
#### `fragment` - String Variable
 - This is the shader that will be used for the Fragment stage in the viewport OpenGL Shader Program
 - Also the default Fragment stage for FBO renders when `settings['fboShader'] = True`
 
#### `fboVertex` - String Variable
 - Used when `settings['fboShader'] = True`
 - This is the shader that will be used for the Vertex stage in the viewport OpenGL Shader Program
 - If not set, `vertex` will be used for FBO renders
 
#### `fboFragment` - String Variable
 - Used when `settings['fboShader'] = True`
 - This is the shader that will be used for the Fragment stage in the viewport OpenGL Shader Program
 - If not set, `fragment` will be used for FBO renders

<hr>

## Shader Python Files -

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

### `defaultShader.py`; `glEffect="default"`
 - Default Vertex & Fragment Shaders
 - Draws UV quardinates as its output
     <br>&nbsp;&nbsp;Appearing as an image blending between black, red, green, and yellow
 - Good for testing if your pxlViewportGL widget is working
<br><br>

### `rawTextureShader.py`; `glEffect="rawTexture"`
 - Draws an image with no effects, just a raw display
 - Good for testing file paths and image is supported
   - Currently, images in pxlViewportGL are assumed to be -
     - Jpeg, png, or bmp
     - 8-bit RGB or RGBA
   - Untested formats, *may work, just untested* -
     - Any bit depth other than 8-bit images
     - Unsigned Int or (un)signed Float images
     - R or RG ( 1 or 2 channel ) images
     - Gif, tif, webp, exr
<br><br>

### `swapTextureShader.py`; `glEffect="swapTexture"`
 - Akin to `rawTextureShader.py`
 - Auto-loads when `settings['hasSim'] = True`
 - This file will automatically load for FBO render swaps
     <br>&nbsp;&nbsp;With intention to reduce latency in the render process
     <br>&nbsp;&nbsp;&nbsp;&nbsp;Blitting would work as well,
     <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Figured binding FBO textures would be quicker
     <br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*( Benchmarking needed )*
     <br>&nbsp;&nbsp;*( FBO Double Buffer, Buffer Swapping may be the correct option here )*
 
<br><br>


### `colorCorrectShader.py`; `glEffect="colorCorrect"` **WIP**
 - Color Correct Texture Shader
 - Tweak image colors
   - Hue, Saturation, Brightness, Gamma, Vibrance, etc.
<br><br>

### `edgeDetectShader.py`; `glEffect="edgeDetect"` **WIP**
 - Find Edges In Texture Shader
 - Currently only using an adapted Kuwahara Filtering function
<br><br>

### `paintMaskShader.py`; `glEffect="paintMask"` **WIP**
 - User Interactive Masking Shader
 - With brush hardness/blur/feathering
<br><br>


### `segmentShader.py`; `glEffect="segment"` **WIP**
 - Segmentation FBO Feedback Shader
 - Find provided Segment Region Seeds & Write to FBO
   - Subsequent FBO renders grows Region by 1 pixel *(currently)*
 - On 'Render To Screen' pass of same shader simply merges Region Data with Source Texture *(currently)*
<br><br>

### `smartBlurShader.py`; `glEffect="smartBlur"` **WIP**
 - Blur Pixel Samples Based On Threshold
 - Currently only using an adapted Kuwahara Filtering function
<br><br>

<hr>

## Future Plans
I'd like to add "render shader sequence" support, automatically setting up a render pass pipeline in the Viewport widget.
<br>&nbsp;&nbsp;This will likely be partnered with passing an array of glEffects to `ImageShaderWidget()` as well,
<br>&nbsp;&nbsp;&nbsp;&nbsp;But would allow for custom shaders using the result from the prior shader easier.
<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Instead of loading & parsing multiple sets of uniforms & settings
