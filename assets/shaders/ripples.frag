#version 140
in vec2 texcoords;
in vec4 draw_color;
out vec4 fragColor;
uniform float shadertime;
void main() {
	float x = (texcoords.x - 0.5);
	float y = (texcoords.y - 0.5);
	float len = sqrt(x*x + y*y);
	vec3 out_color = draw_color.xyz * vec3(sin(len*3.14*10-5*shadertime)*sin(shadertime+len)+1)/2;
	fragColor = vec4(out_color, 1.).rgba;
}