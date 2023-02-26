# Many utilities below are pulled from prior projects
#   A mixture of OpenGL and OpenGL ES;
#     And a variety of GLSL versions
# This in mind, I tend toward OpenGL ES and OpenGL 120 for cross platform needs

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

# TODO : Add stochastic sampling array and function
#          Mostly since, as the sampler reaches out,
#            It retains its diagnal or axis locked sampling
#   OR : If not stochastic sampling, a random scatter sampler array and function
#   OR : Java's Random(), as it's a rotating random value, literally rotating...
#          I really don't get why Java is using a rotating random
#            There've been so many exploits of Java's default `random()`
#              While uniform in it's `random`, it yeilds a reasonable sampler array set

# -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

# `boxBlurSampleBase` REQUIRES A BOXSAMPLE ARRAY !!
#   Requiring -
#     const int boxSamplesCount = #
#     const vec2 boxSamples[#]
# 
#   ( See `boxBlurSampler` function below for proper usage )
boxBlurSampleBase = """

vec4 boxBlurSample( sampler2D tx, vec2 uv, vec2 texelRes){
  vec4 sampleCd = texture2D(tx, uv);
  
  vec2 curUV;
  vec2 curId;
  float curUVDist=0.0;
  vec4 curCd;
  vec3 curMix;
  float delta=0.0;
  for( int x=0; x<boxSamplesCount; ++x){
    curUV =  uv + boxSamples[x]*texelRes ;
		
    curCd = texture2D(tx, curUV);
    sampleCd = mix( sampleCd, curCd, .5);
  }
  return sampleCd;
}
"""  


# Get a sample array
def getBoxSamples( sampleArray = 3 ):
    sampleArray = max( 1, min( 3, sampleArray ) )
    retSamples = ""
    if sampleArray == 1: # Samples in + shape
        retSamples = """
        const int boxSamplesCount = 4;
        const vec2 boxSamples[4] = vec2[4](
                                      vec2( 0.0, -1.0 ),
                                      
                                      vec2( -1.0, 0.0 ),
                                      vec2( 1.0, 0.0 ),

                                      vec2( 0.0, 1.0 )
                                    );
        """
    elif sampleArray == 2: # Samples in X shape
        retSamples = """
        const int boxSamplesCount = 4;
        const vec2 boxSamples[4] = vec2[4](
                                      vec2( -1.0, -1.0 ),
                                      vec2( -1.0, 1.0 ),

                                      vec2( 1.0, -1.0 ),
                                      vec2( 1.0, 1.0 )
                                    );
        """
    elif sampleArray == 3: # All neighboring samples; [] shape
        retSamples =  """
        const int boxSamplesCount = 8;
        const vec2 boxSamples[8] = vec2[8](
                                      vec2( -1.0, -1.0 ),
                                      vec2( -1.0, 0.0 ),
                                      vec2( -1.0, 1.0 ),

                                      vec2( 0.0, -1.0 ),
                                      vec2( 0.0, 1.0 ),

                                      vec2( 1.0, -1.0 ),
                                      vec2( 1.0, 0.0 ),
                                      vec2( 1.0, 1.0 )
                                    );
        """
    return retSamples

# Return Box Sampler Function
#   Defaults to 3x3
def getBoxBlur( samplesArray="3x3" ):
    samplerType = samplesArray[0]
    samplerType = int(samplerType) if samplerType.isnumeric() else 3
    return getBoxSamples( samplerType ) + boxBlurSampleBase