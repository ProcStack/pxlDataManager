# General GLSL Math
#   Math Defines & Functions


# -- -- --

def_PI="""
#define PI 3.14159265358979323
"""
def_TAU="""
#define TAU 6.2831853071958646
"""

# -- -- --

clamp="""
float clamp( float inVal, float inMin, float inMax ){
    return min( inMax, max( inMin, inVal ) );
}
"""

clamp01="""
float clamp01( float inVal ){
    return min( 1.0, max( 0.0, inVal ) );
}
"""


biasToOne="""
float biasToOne( float value ){
  return 1.0-(1.0-value)*(1.0-value);
}
float biasToOne( float value, float bias ){
  return 1.0-(1.0-min(1.0,value*bias))*(1.0-min(1.0,value*bias));
}
"""

# -- -- --

maxComponent="""
// Return max vector component
float maxComponent(vec2 val){
  return max(val.x,val.y);
}
float maxComponent(vec3 val){
  return max(val.x,max(val.y,val.z));
}
float maxComponent(vec4 val){
  return max(val.x,max(val.y,max(val.z,val.w)));
}
"""

addComponents="""
// Add all of a vectors component values together
float addComponents(vec2 val){
  return val.x+val.y;
}
float addComponents(vec3 val){
  return val.x+val.y+val.z;
}
float addComponents(vec4 val){
  return val.x+val.y+val.z+val.w;
}
"""

# Rotation Vec3 to UV value
rotToUV="""
vec2 rotToUV(vec3 direction){
    vec2 uv = vec2(atan(direction.z, direction.x), asin(direction.y));
    uv *= vec2(0.1591, 0.3183);
    uv += 0.5;
    return uv;
}
"""

# -- -- --

# Convert vec3 color to luminance
#   Given Green prominance in eye color perception
luma="""
float luma(vec3 color) {
	return dot(color,vec3(0.299, 0.587, 0.114));
}
"""

# Convert vec3 color to raw luminance; (r+g+b)/3.0
# TODO : Correct trailing double precision values over 1.0
greyScale="""
float greyScale(vec3 color) {
	return (color[0]+color[1]+color[2])*0.3333333333333333;
}
"""


# `rgb2hsv` & `hsv2rgb` from -
#   https://stackoverflow.com/questions/15095909/from-rgb-to-hsv-in-opengl-glsl
rgb2hsv = """
vec3 rgb2hsv(vec3 c){
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
"""
hsv2rgb = """
vec3 hsv2rgb(vec3 c){
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}
"""



# -- -- -- -- --
# -- -- -- -- --
# -- -- -- -- --


# AB Blender Functions

deltaDivToBlender = """
float DeltaDivTo(float s1, float s2, float b){
  // Second from top
  float deltaTo = abs(((s1-b)-(s2-b)) / b) - b;
  //float deltaDivTo = abs((s1-b)*(s2-b) / b)-b;
  return deltaTo;
}
"""

sinToBlender = """
float SinTo(float s1, float s2, float p){
  // Top
  float sd = (s2-s1);
  float d = sd*p ;
  d = clamp(d, -1.0, 1.0) * PI ;
  float divTo = 1.0-cos( d );
  return divTo;
}
"""

logPowToBlender = """
float LogPowTo(float s1, float s2, float j){  // j => 0.0 - 1.5
  float sd = (s2-s1);
  float logPowTo = 1.0-abs( log(pow(abs(sd),j)) );
  return logPowTo;
}
"""

powToBlender = """
float PowTo(float s1, float s2, float k){  // k => 0.0 - 9.0
  float sd = (s2-s1);
  float powTo = pow(abs(sd),k);
  return powTo;
}
"""


# -- -- -- -- --
# -- -- -- -- --
# -- -- -- -- --


# TODO : Add function to return a dynamically generated rotation matrix

# Return a 3x3 or 4x4 matrix with given rotation and optional positional values
def getRotationMatrix( matName="xRotMat", rotAxis="x", matSize="3x3", rotVal=-1.5707963267948966, posVal=None ):
    import math
    rotAxis = rotAxis.lower()
    
    # Python's `math` module only returns float, not double precision
    sinRot = math.sin( rotVal )
    cosRot = math.cos( rotVal )
    
    matType = "mat3"
    rowType = "vec3"
    isVec4 = False
    if matSize == "4x4":
        matType = "mat4"
        rowType = "vec4"
        isVec4 = True
        
    wVal = ", 0.0" if isVec4 else ""
    
    curPosVal = []
    if isVec4:
        if type(posVal) == None:
            curPosVal = [0.0,0.0,0.0,1.0]
        else:
            curPosVal = posVal.copy()
        if isVec4 and len(curPosVal) == 3:
            curPosVal.append(1.0)
        curPosVal = """,
                vec4( {curPosVal[0]}, {curPosVal[1]}, {curPosVal[2]}, {curPosVal[3]})"""
    
    retMat = ""
    
    if rotAxis == "x":
        retMat = f"""
            {matType} {matName} = {matType}(
                {rowType}( 1.0, 0.0, 0.0{wVal} ),
                {rowType}( 0.0, {cosRot}, -{sinRot}{wVal} ),
                {rowType}( 0.0, {sinRot}, {cosRot}{wVal} ){curPosVal}
            );
            """
    elif rotAxis == "y":
        retMat = f"""
            {matType} {matName} = {matType}(
                {rowType}( {cosRot}, 0.0, {sinRot}{wVal} ),
                {rowType}( 0.0, 1.0, 0.0{wVal} ),
                {rowType}( -{sinRot}, 0.0, {cosRot}{wVal} ){curPosVal}
            );
            """
    elif rotAxis == "z":
        retMat = f"""
            {matType} {matName} = {matType}(
                {rowType}( {cosRot}, -{sinRot}, 0.0{wVal} ),
                {rowType}( {sinRot}, {cosRot}, 0.0{wVal} ),
                {rowType}( 0.0, 0.0, 1.0{wVal} ){curPosVal}
            );
            """
        
    return retMat
    
    
    
    
# -- -- -- -- --
# -- -- -- -- --
# -- -- -- -- --

# sRGB, Linear RGB, & CIE LAB Conversion Math


sRGBtoLinear_verbose = """
vec3 sRGBtoLinear(vec3 sRGB) {
    vec3 cutoff = vec3(0.04045);
    vec3 scale = vec3( 0.07739938080495357 ); // 1.0 / 12.92
    vec3 a = vec3(0.055);
    vec3 b = vec3( 0.9478672985781991 ); // 1.0 / 1.055
    vec3 c = vec3(0.0031308);

    vec3 cutoffBlender = step( cutoff, sRGB );
    vec3 belowCutoff = sRGB * scale;
    vec3 aboveCutoff = pow((sRGB + a) * b, vec3(2.4)) - c;

    vec3 linear = mix( belowCutoff, aboveCutoff, cutoffBlender );
    return linear;
}
"""

sRGBtoLinear = """
vec3 sRGBtoLinear(vec3 sRGB) {
    vec3 belowCutoff = sRGB * 0.07739938080495357 ;
    vec4 aboveCutoff = pow((sRGB + 0.055) * 0.9478672985781991, vec3(2.4) );
    
    return mix( belowCutoff, aboveCutoff, step(vec3(0.04045), sRGB) );
}
"""


rgbToXYZMat3 = """
mat3 rgbToXYZ = mat3( vec3( 0.4124  0.3576  0.1805 ),
                      vec3( 0.2126  0.7152  0.0722 ),
                      vec3( 0.0193  0.1192  0.9505 ) );
"""

xyzReferenceWhite = """
vec3 labRefWhite = vec3( .95047, 1.0, 1.08883 );
"""

def convertRGBtoLAB( sRGBColorInput=True ):
    retFunction=""
    
    if sRGBColorInput:
        retFunction+=sRGBtoLinear
    
    retFunction+="""
        vec3 rgbToLab( vec3 rgb ){
        """
    
    if sRGBColorInput:
        retFunction+="""
            rgb = sRGBtoLinear( rgb );
            """

    retFunction+="""
        rgb = sRGBtoLinear( rgb );
        
        // vec3 labRefWhite = vec3( .95047, 1.0, 1.08883 );
        
        float refX = 
        
        """
        
# Work In Progress ---
"""
    X / Xn = f(X)
    Y / Yn = f(Y)
    Z / Zn = f(Z)

    L* = 116 * f(Y) - 16
    a* = 500 * (f(X) - f(Y))
    b* = 200 * (f(Y) - f(Z))
Xr = X / Xw
Yr = Y / Yw
Zr = Z / Zw

if (Yr > 0.008856) {
L = 116 * pow(Yr, 1.0 / 3.0) - 16;
} else {
L = 903.3 * Yr;
}

if (Xr > 0.008856) {
xr = pow(Xr, 1.0 / 3.0);
} else {
xr = (7.787 * Xr) + (16.0 / 116.0);
}

if (Yr > 0.008856) {
yr = pow(Yr, 1.0 / 3.0);
} else {
yr = (7.787 * Yr) + (16.0 / 116.0);
}

if (Zr > 0.008856) {
zr = pow(Zr, 1.0 / 3.0);
} else {
zr = (7.787 * Zr) + (16.0 / 116.0);
}

a_star = 500 * (xr - yr);
b_star = 200 * (yr - zr)
"""



