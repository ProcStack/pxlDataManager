
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
    "edgeThickness" : {
        "type":"float",
        "default":0.1,
        "control":"visible",
        "range":[.0001,10]
    },
    "threshold" : {
        "type":"float",
        "default":0.19,
        "control":"visible",
        "range":[.001,1]
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
    uniform float edgeThickness;
    uniform float threshold;
    
    in vec3 newColor;
    in vec2 vUv;

    out vec4 outColor;



    // Manhattan / Taxi Cab Distance
    //   This was added for real time optimization
    //     Kinda needless here
    float manhattan(vec3 val){
        val = abs(val);
        return val.x+val.y+val.z;
    }
    float manhattan(vec3 v1, vec3 v2){
        vec3 val = abs(v2-v1);
        return val.x+val.y+val.z;
    }



    // Default Kuwahara Filter with Edge Sampling
    //   Edge Detection limited to a single step
    //     To aid with getting a desired style but also sharp edge detections
    //
    // Default Kuwahara; Sampling with limited Edge consideration
    //   baseMaxDelta - Current edge detection value
    void kuwaharaEdgeLimitSample( sampler2D tex, vec2 baseUv, vec2 stepSize, ivec2 stepCount, float edgeReach,
                             vec4 baseCd, vec2 quadrant, inout vec4 baseAvgCd, inout float baseMinDelta, inout float baseMaxDelta ){
      vec4 curAvgCd, curCd = vec4(0,0,0,0);
      vec2 curUvOffset;
      float curCdDelta;
      float doEdgeSample=0.0;
      float maxSampledDelta=0.0;
      int x,y;
      for( x=0; x < stepCount.x; ++x ){
          for( y=0; y < stepCount.y; ++y ){
              curUvOffset = stepSize * vec2( x, y ) * quadrant;
              curCd = texture(tex, baseUv + curUvOffset);
              curAvgCd += curCd;
              
              // Edge detection offset, should sample be desired outside of x == y == 0
              //   Sampling all quadrants, no matter weighting
              doEdgeSample = step( float(x+y), edgeReach+.1 );
              curCdDelta = min(1.0, manhattan( curCd.xyz - baseCd.xyz ) );
              maxSampledDelta = mix( maxSampledDelta, max( maxSampledDelta, curCdDelta ), doEdgeSample );
          }
      }
      
      curAvgCd /= float(stepCount.x * stepCount.y);
      curCdDelta = length( curAvgCd - baseCd );
      baseAvgCd = mix( curAvgCd, baseAvgCd, step( baseMinDelta, curCdDelta ) );
      
      curCdDelta = min(1.0, manhattan( curAvgCd.xyz - baseCd.xyz ) );
      // Agh... This is wrong, this is putting edge preference on lowest delta not highest
      //   I'll fix later, cause would be two different results
      doEdgeSample = step( .1, curCdDelta ) * step( curCdDelta, baseMinDelta );
      baseMaxDelta = mix( baseMaxDelta, maxSampledDelta, doEdgeSample );
      
      baseMinDelta = min( baseMinDelta, curCdDelta );

    }
    //
    // baseUv - current uv
    // stepSize - pixel ratio; 1.0/uv
    // stepCount - iteration steps per axis in quadrant
    void kuwaharaEdgeLimitFilter(  sampler2D tex, vec2 baseUv, vec2 stepSize, vec2 stepCount, float edgeReach, inout vec4 filterCd, inout float foundEdges ){

      vec2 curUv, curUvOffset;
      vec4 curCd;
      float curCdDelta;
      vec4 baseCd = texture(tex, baseUv);
      vec4 curAvgCd = vec4(0,0,0,0);
      
      vec2 reachMult = stepSize;
      
      ivec2 iStepCount = ivec2( int(stepCount.x), int(stepCount.y) );
      
      int x,y;
      float avgCount = 0.0;
      vec2 quadrant;
      
      float minDelta = 999.0; // Determines average color output
      float maxDelta = 0.0; // Edge value output
      
      vec4 minAvgCd = baseCd;
      
      // One quadrant at a time
      
      quadrant = vec2( 1, 1 );
      kuwaharaEdgeLimitSample( tex, baseUv, stepSize, iStepCount, edgeReach, baseCd, quadrant, minAvgCd, minDelta, maxDelta );
      
      quadrant = vec2( -1, 1 );
      kuwaharaEdgeLimitSample( tex, baseUv, stepSize, iStepCount, edgeReach, baseCd, quadrant, minAvgCd, minDelta, maxDelta );
      
      quadrant = vec2( -1, -1 );
      kuwaharaEdgeLimitSample( tex, baseUv, stepSize, iStepCount, edgeReach, baseCd, quadrant, minAvgCd, minDelta, maxDelta );
      
      quadrant = vec2( 1, -1 );
      kuwaharaEdgeLimitSample( tex, baseUv, stepSize, iStepCount, edgeReach, baseCd, quadrant, minAvgCd, minDelta, maxDelta );
      
      // -- -- -- --
      
       filterCd = minAvgCd;
       foundEdges = maxDelta;
      
    }








    void main() {
        vec2 scaledUv = vUv * texScale + texOffset;
        vec4 outCd = vec4(0.0,0.0,0.0,1.0);//texture( samplerTex, scaledUv );
        
        float foundEdges = 0.0;
        
        
        kuwaharaEdgeLimitFilter(  samplerTex, scaledUv, texelSize, reach, edgeThickness, outCd, foundEdges );
        foundEdges = step(threshold, foundEdges);
        
        outCd = mix( outCd, vec4(1.0,0.0,0.0,1.0), foundEdges);
        
        outColor = outCd;
    }

'''

