#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 texcoords;
out vec4 draw_color;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoords = p3d_MultiTexCoord0.xy;
    draw_color = vec4(0.5,0.5,1.,1.);
}




// varying vec2 v_texCoord2D;
// varying vec3 v_texCoord3D;
// varying vec4 v_color;
// void main()
// { 
//   gl_Position = gl_ModelViewProjectionMatrix * 
//                    gl_Vertex.xyz;
//   v_texCoord2D = gl_MultiTexCoord0.xy;
//   v_texCoord3D = gl_Vertex.xyz * 0.05;
//   v_color = gl_Color;  
// }