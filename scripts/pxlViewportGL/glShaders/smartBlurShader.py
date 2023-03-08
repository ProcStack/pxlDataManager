
uniforms = {
    "samplerTex" : {"type":"texture"},
    "texOffset" : {
        "type":"vec2",
        "default":[0,0],
        "control":"userOffset"
    },
    "texScale" : {
        "type":"vec2",
        "default":[1,1],
        "control":"userScale"
    },
    "texelSize" : {
        "type":"vec2",
        "default":[1.0/512.0]*2,
        "control":"texelSize"
    },
    "reach" : {
        "type":"vec2",
        "default":[10,10],
        "control":"visible",
        "range":[1,50]
    },
    "threshold" : {
        "type":"float",
        "default":0.1,
        "control":"visible",
        "range":[.0001,1]
    }
}


attributes = [ "position", "uv" ]


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


fragment = '''
    #version 330

    uniform sampler2D samplerTex;
    uniform vec2 texOffset;
    uniform vec2 texScale;
    uniform vec2 texelSize;
    uniform vec2 reach;
    uniform float threshold;
    
    in vec3 newColor;
    in vec2 vUv;

    out vec4 outColor;



    // Default Kuwahara Filter
    //
    // Default Kuwahara; Quadrant Sampling
    void kuwaharaSample( sampler2D tex, vec2 baseUv, vec2 stepSize, ivec2 stepCount,
                         vec4 baseCd, vec2 quadrant, inout vec4 baseAvgCd, inout float baseMinDelta ){
      vec4 curAvgCd, curCd = vec4(0,0,0,0);
      vec2 curUvOffset;
      int x,y;
      for( x=0; x < stepCount.x; ++x ){
          for( y=0; y < stepCount.y; ++y ){
              curUvOffset = stepSize * vec2( x, y ) * quadrant;
              curCd = texture(tex, baseUv + curUvOffset);
              curAvgCd += curCd;
          }
      }
      
      curAvgCd /= float(stepCount.x * stepCount.y);
      float curCdDelta = length( curAvgCd - baseCd );
      baseAvgCd = mix( curAvgCd, baseAvgCd, step( baseMinDelta, curCdDelta ) );
      baseMinDelta = min( baseMinDelta, curCdDelta );
    }
    //
    // baseUv - current uv
    // stepSize - pixel ratio; 1.0/uv
    // stepCount - iteration steps per axis in quadrant
    //
    vec4 kuwaharaFilter(  sampler2D tex, vec2 baseUv, vec2 stepSize, vec2 stepCount ){

      vec2 curUv, curUvOffset;
      vec4 curCd;
      float curCdDelta;
      vec4 baseCd = texture(tex, baseUv);
      vec4 curAvgCd = vec4(0,0,0,0);
      
      vec2 reachMult = stepSize;
      float blend = 1.0;
      
      ivec2 iStepCount = ivec2( int(stepCount.x), int(stepCount.y) );
      
      int x,y;
      float avgCount = 0.0;
      vec2 quadrant;
      
      float minDelta = 999.0;
      vec4 minAvgCd = baseCd;
      
      // One quadrant at a time
      
      quadrant = vec2( 1, 1 );
      kuwaharaSample( tex, baseUv, stepSize, iStepCount, baseCd, quadrant, minAvgCd, minDelta );
      
      quadrant = vec2( -1, 1 );
      kuwaharaSample( tex, baseUv, stepSize, iStepCount, baseCd, quadrant, minAvgCd, minDelta );
      
      quadrant = vec2( -1, -1 );
      kuwaharaSample( tex, baseUv, stepSize, iStepCount, baseCd, quadrant, minAvgCd, minDelta );
      
      quadrant = vec2( 1, -1 );
      kuwaharaSample( tex, baseUv, stepSize, iStepCount, baseCd, quadrant, minAvgCd, minDelta );
      
      // -- -- -- --
      
      vec4 blendCd = minAvgCd;
      return blendCd;
    }


    // -- -- -- --
    // -- -- -- --
    // -- -- -- --


    void main() {
        vec2 scaledUv = vUv * texScale + texOffset;
        vec4 outCd = texture( samplerTex, scaledUv );
        
        outCd = kuwaharaFilter(  samplerTex, scaledUv, texelSize, reach );
        
        outColor = outCd;
    }

'''

