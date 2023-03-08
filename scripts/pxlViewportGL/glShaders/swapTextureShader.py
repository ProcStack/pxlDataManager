# DO NOT DELETE THIS FILE !!
#   Feel free to alter as needed though
#     As long as you keep -
#       "uniforms", "attributes", "vertex", & "fragment"

# This file will automatically load
#   When the primary glEffect requires "simulation"
#     If primary glEffect has `settings['hasSim'] = True`
#   Automatic load doesn't read any "fbo-" or "fboSwap-" variables


fboSwapUniforms = {
    "swapTex" : {"type":"fbo"},
}

attributes = [ "position", "uv" ]

fboSwapVertex = '''
    #version 330

    in vec2 position;
    in vec2 uv;

    out vec2 vUv;

    void main() {
    
        gl_Position = vec4(position, 0.0f, 1.0f);
        vUv = uv;
        
    }
'''

# -- -- --



fboSwapFragment = '''
    #version 330
    
    uniform sampler2D swapTex;
    
    in vec2 vUv;
    
    out vec4 outColor;
    
    void main() {
        // If buffer reading image bottom as 0
        //   ( Image appearing upside down )
        //outColor = texture( swapTex, vec2(vUv.x,1.0-vUv.y) );
        outColor = texture( swapTex, vUv );
    }

'''


