
uniforms = {}


vertex = '''
    #version 330

    in vec2 position;
    in vec2 uv;

    out vec3 vCd;
    out vec2 vUv;

    void main() {

        gl_Position = vec4(position, 0.0f, 1.0f);
        vCd = vec3(uv.x, uv.y, 0.0f);
        vUv = uv;
    }
'''


fragment = '''
    #version 330

    in vec3 vCd;
    in vec2 vUv;

    out vec4 outColor;

    void main() {
        outColor = vec4( vUv.xy, 0.0, 1.0 );
    }
'''

