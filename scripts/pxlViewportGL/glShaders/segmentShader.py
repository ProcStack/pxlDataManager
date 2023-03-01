# Its shaders like this that makes me think I should just
#   Extend the `TextureGLWidget()` class
#     Yay...
#
# Segmentation Shader sets FBO requirements and Buffer Swapping
#   Determined below with -
#     uniforms["bufferRefTex"]["type"] = "fbo"
#       FBO swap, using the same Shader Program
#
# Primary source texture -
#   `uniform sampler2D samplerTex;`
# Data Pass, FBO feedback -
#   `uniform sampler2D bufferRefTex;`
#
# Fragment Shader below uses uniform `isFBO` variable to determine
#   Out color `out vec4 outColor` fbo or to-screen render
# In `ViewportGL.py` -
#   See `buildUniforms()`, `newFrameBuffer()`, and `paintGL()` for usage of -
#     RGBA - FBO, FBO Texture, and Screen Render
#
# Do note --
#   This shader was created with ill-regard for FPS
#     Nested For-Loops and multiple "box" sampling per texel per frame
#       FPS has been disregarded for the whole of pxlDataManager


import os, sys
from random import random

if __name__ != '__main__':
    glShadersRoot = os.path.abspath(__file__)
    glShadersRoot = os.path.dirname(glShadersRoot)
    sys.path.append(glShadersRoot)
    
from shaderUtils import getBoxSamples
from shaderMath import clamp01

# -- -- --
# -- -- --
# -- -- --

def newSeedDict( region=0.0, inWeight=1.0, inPos=[.5,.5], inColor=None ):
    toPos = inPos.copy()
    toColor = inColor
    
    if type(toColor) == list and len(toColor)>=3:
        toColor = toColor[0:3]
    else:
        toColor = [random(), random(), random()]
        
    newSeed={
        "region":region,
        "weight":inWeight,
        "color":toColor,
        "pos":toPos
    }
    
    return newSeed;
    
# TODO : Likely need an array(dict) to array(float)
#          As `ViewportGL` is flattening `segmentSeedDictList` to array in -
#            `buildUniforms()`
def seedDictToArray( seedDict ):

    outMat = [ [float(seedDict['region']),   seedDict['weight'],   0.0 ], 
               [seedDict['color'][0], seedDict['color'][1], seedDict['color'][2]],
               [seedDict['pos'][0],   seedDict['pos'][1],   0.0 ] ]
               
    return outMat

# Defualt OpenGL Array Run Size
#   Can't be larger than 6 seeded regions withough rebuilding Shader
segmentSeedDictList=[]
segmentSeedDictList.append( newSeedDict(0, 1.0, [.5,.5]) )
segmentSeedDictList.append( newSeedDict(1, 1.0, [.25,.75]) )
segmentSeedDictList.append( newSeedDict(2, 1.0, [.75,.25]) )
segmentSeedDictList.append( newSeedDict(3, 0.0, [.25,.25]) )
segmentSeedDictList.append( newSeedDict(4, 0.0, [.75,.75]) )
segmentSeedDictList.append( newSeedDict(5, 0.0, [.25,.5]) )

# -- -- --
# -- -- --
# -- -- --


settings = {
    "hasSim" : True,
    "timerIterval" : 100,
    "runSimCount" : 10
}

uniforms = {
    "samplerTex" : {"type":"texture"},
    "bufferRefTex" : {"type":"fbo"},
    "texOffset" : {
        "type":"vec2",
        "default":[0,0],
        "control":"texOffset"
    },
    "texScale" : {
        "type":"vec2",
        "default":[1,1],
        "control":"texScale"
    },
    "texelSize" : {
        "type":"vec2",
        "default":[1,1],
        "control":"texelSize"
    },
    "mousePos" : {
        "type":"vec2",
        "default":[1,1],
        "control":"mousePos"
    },
    "seedDist" : {
        "type":"float",
        "default":0.1,
        "control":"visible",
        "range":[.001,1]
    },
    "segmentSeeds" : {
        "type":"vec3[]",
        "default":segmentSeedDictList,
        "control":"visible"
    },
    "isFBO" : {
        "type":"float",
        "default":0.0,
        "control":"isFBO"
    }
}

# -- -- --
# -- -- --
# -- -- --

vertex = '''
    #version 330

    in vec2 position;
    in vec2 uv;

    out vec3 newColor;
    out vec2 vUv;

    uniform mat4 transform; 

    void main() {

        gl_Position = vec4(position, 0.0f, 1.0f);
        newColor = vec3(uv.x, uv.y, 0.0f);
        vUv = uv;

    }
'''

# -- -- --

# Max Seed Count Read Array
#   uniform vec3 segmentSeeds[#} = Region,Color,Pos, Region,Color,Pos, .....
# TODO : Add dynamic User Defined Region Positions
#
# Run = [ vec3(Region), vec3(Color), vec3(Position) ]
#   Size of 3 x Vec3()
segSeedRun = '3'
# Existing Default Seed List Size * Run Size
segSeedCount = str( len(segmentSeedDictList) * 3 )

# -- -- --


# -- -- -- -- -- -- --
#
#  From 'shaderUtils.py'; ` getBoxSamples(3) `
#    For sampling neighboring pixel directions
#    Adds -
#      const int boxSamplesCount = 8;
#      const vec2 boxSamples[8]
#
# -- -- -- -- -- -- --
#
# For separate layout(location=#) in TYPE VARIABLE;
#   #extension GL_ARB_separate_shader_objects : enable
#
# TODO : Add dynamic OGL version
# TODO : Add quad-region sampling default OGL functions
#

fragment = '''
    #version 330
    
    #define SEGMENT_SEED_COUNT ''' + segSeedCount + ''' 

    uniform sampler2D samplerTex;
    uniform sampler2D bufferRefTex;
    uniform vec2 texOffset;
    uniform vec2 texScale;
    uniform vec2 texelSize;
    uniform vec2 mousePos;
    uniform float seedDist;
    uniform float isFBO;
    uniform vec3 segmentSeeds[''' + segSeedCount + '''];
    
    in vec3 newColor;
    in vec2 vUv;

    out vec4 outColor;
    
    // Add `int boxSamplesCount` and `vec2[] boxSamples`
    ''' + getBoxSamples(3) + '''
    
    // Add `float clamp01(val,min,max){}`
    //   `clamp()` introduced in OpenGL4 / OpenGLES3
    //     Currently using OpenGL 330
    // TODO : Any reason not to use `#version 420` ???
    //          Find limited hardware for later GL versions
    ''' + clamp01 + '''
    
    // No cross preferencing or sample checking yet
    //   Currently, if data has data, pull data
    vec4 reagionReachSample( sampler2D colorTx, sampler2D dataTx, vec2 uv ){
      //vec4 sampleCd = texture(dataTx, uv);
      vec4 sampleCd = texture(colorTx, uv);
      return sampleCd;
    }

    void main() {
        vec2 scaledUv = vUv * texScale + texOffset;
        vec4 outCd = texture( samplerTex, scaledUv );
        vec4 dataCd = texture( bufferRefTex, scaledUv );
        
        // I don't like using If-Else's
        //   But Uniforms don't cause desync in gpu cores
        //     Still annoys me though...
        //       And too lazy to make another shader program for swap
        //         Eh, not lazy, just know it'll reveal more issues
        //           In PyOpenGL....
        if( isFBO>0.5 ){ // Data Pass
        
            int REGION_WEIGHT = 0;
            int SEED_COLOR = 1;
            int SEED_POSITION = 2;
            
            //float disToSeed = 0.0;
            //float curDisToSeed = 0.0;
            
            int x=0;
            float curSeedWeight;
            float foundSeed = dataCd.a;
            vec3 minDistSeedColor = mix( vec3(0.0), dataCd.rgb, foundSeed );
            for( x=0; x<SEGMENT_SEED_COUNT; x=x+'''+segSeedRun+'''){
                vec2 curRegionWeight = segmentSeeds[ x + REGION_WEIGHT ].xy;
                vec2 curSeedPos = segmentSeeds[ x + SEED_POSITION ].xy;
                vec3 curSeedColor = segmentSeeds[ x + SEED_COLOR ];
                
                curSeedWeight = step( length(curSeedPos-vUv), length(texelSize) );
                minDistSeedColor = mix( minDistSeedColor, curSeedColor, step(foundSeed, curSeedWeight) );
                foundSeed = max( foundSeed, curSeedWeight );
                
                // curDisToSeed = max(curDisToSeed, max(0.0, 1.0-length( vUv - curSeedPos )/seedDist));
                // float colorStep = step( curDisToSeed, disToSeed );
                // colorStep = step( curDisToSeed, seedDist );
                // minDistSeedColor = mix( minDistSeedColor, curSeedColor, colorStep );
                // disToSeed = min( disToSeed, curDisToSeed) ;
            }
            
            // -- -- --
            
            // Prior frame allowed current frame influence
            float inWeight = 1.0-foundSeed;
            
            // Neighbor Sampler
            // TODO : Is there an unroller for PyOpenGL ??
            //          Thats core OpenGL, no?
            //            Gotta go searching
            //              Or just Python it
            
            vec2 reachMult = texelSize * vec2( 1.0, 1.0 );
            float reachWeight;
            vec2 reachPos;
            vec4 regionSample;
            int c=0;
            for( c=0; c<boxSamplesCount; ++c){
                reachPos = vUv + boxSamples[c] * reachMult;
                regionSample = reagionReachSample( samplerTex, bufferRefTex, reachPos );
                reachWeight = regionSample.a;//*inWeight;
                minDistSeedColor = mix( minDistSeedColor, regionSample.rgb, step( foundSeed, reachWeight ) );
                foundSeed = max( foundSeed, reachWeight );
            }
            
            //curDisToSeed = max( curDisToSeed, max( 0.0, 1.0-length( vUv-mousePos )/seedDist )); 
            //disToSeed = max( disToSeed, curDisToSeed );
            //disToSeed = step(0.0, length(minDistSeedColor) );
            //disToSeed = clamp01( disToSeed );
            
            //dataCd*=.9;
            //vec4 nearSeedColor = max( vec4(minDistSeedColor,foundSeed), dataCd);
            //outCd.rgb = min( vec4(1.0), outCd+nearSeedColor );
            
            outCd = vec4(minDistSeedColor,foundSeed);
            
            
        }else{ // Combine Data & Color Pass
        
            //outCd = outCd*(1.0-disToSeed);
            
            //outCd = mix( outCd, nearSeedColor, isFBO);
            float blender = 1.0;//dataCd.a;
            dataCd.a = 1.0;
            outCd = mix( outCd, dataCd, blender) ;
            
        }
        outColor = outCd;
    }

'''