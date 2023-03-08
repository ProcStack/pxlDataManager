
uniforms = {
    "samplerTex" : {"type":"texture"},
    "texOffset" : {
        "type":"vec2",
        "default":[0,0],
        "control":"userOffset"
    },
    "texScale" : {
        "type":"vec2",
        #"default":[1.0/512.0]*2,
        "default":[.1]*2,
        "control":"userScale"
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
    
    in vec3 newColor;
    in vec2 vUv;

    out vec4 outColor;

    void main() {
        vec2 scaledUv = vUv;// * texScale + texOffset;
        vec4 outCd = texture( samplerTex, scaledUv );
        outColor = outCd;
    }

'''

