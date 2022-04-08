from ursina import Shader, Vec2, Vec3, Vec4
import os
VERSION = '''#version 140
'''
STANDARD_VERT_HEAD = '''
//STANDARD_HEADER
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
uniform vec2 texture_scale;
uniform vec2 texture_offset;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
out vec2 texcoords;
out vec4 world_pos;
void main() {
'''
INSTANCING_VERT_HEAD = '''
uniform vec3 position_offsets[250];
uniform vec4 rotation_offsets[250];
uniform vec3 scale_multipliers[250];
'''
SNOW_VERT_HEAD = '''
uniform vec3 fallscale_multipliers[250];
uniform float snow_height;
'''
TIMED_VERT_HEAD = '''
uniform float shadertime;
'''
STANDARD_VERT_BODY = '''
texcoords = (p3d_MultiTexCoord0 * texture_scale) + texture_offset;
'''
STANDARD_VERT_BODY_NON_INSTANCED = '''
gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
world_pos = p3d_ModelMatrix * p3d_Vertex;
'''
STANDARD_VERT_BODY_INSTANCED = '''
vec3 v = p3d_Vertex.xyz * scale_multipliers[gl_InstanceID];
vec4 q = rotation_offsets[gl_InstanceID];
v = v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
{} //Format with snow displacement code when needed
vec4 displacement = vec4(v+position_offsets[gl_InstanceID], 1.0);
gl_Position = p3d_ModelViewProjectionMatrix * displacement;
world_pos = p3d_ModelMatrix * displacement;
'''
SNOW_VERT_BODY_INSERTION = '''
float y_displacement = fallscale_multipliers[gl_InstanceID].y*shadertime*0.1;
int false_mod = int(y_displacement) / int(snow_height) + 1;
v.y -= y_displacement - (false_mod * snow_height);
'''
STANDARD_FRAG_HEAD = '''
in vec4 world_pos;
in vec2 texcoords;
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
out vec4 fragColor;
void main() {
'''
STANDARD_FRAG_BODY = '''
fragColor = texture(p3d_Texture0, texcoords) * p3d_ColorScale;
'''
TIMED_FRAG_HEAD = '''
uniform float shadertime;
'''
PORTAL_FRAG_HEADER = """
/*
author: [Ian McEwan, Ashima Arts]
description: Simplex Noise https://github.com/ashima/webgl-noise
use: snoise(<vec2|vec3|vec4> pos)
license: |
    Copyright (C) 2011 Ashima Arts. All rights reserved.
    Copyright (C) 2011-2016 by Stefan Gustavson (Classic noise and others)
    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the GPUImage framework nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  
*/

vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

float rand(vec2 co){
		return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

float snoise(vec3 v){ 
	const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
	const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);

// First corner
	vec3 i  = floor(v + dot(v, C.yyy) );
	vec3 x0 =   v - i + dot(i, C.xxx) ;

// Other corners
	vec3 g = step(x0.yzx, x0.xyz);
	vec3 l = 1.0 - g;
	vec3 i1 = min( g.xyz, l.zxy );
	vec3 i2 = max( g.xyz, l.zxy );

	//  x0 = x0 - 0. + 0.0 * C 
	vec3 x1 = x0 - i1 + 1.0 * C.xxx;
	vec3 x2 = x0 - i2 + 2.0 * C.xxx;
	vec3 x3 = x0 - 1. + 3.0 * C.xxx;

// Permutations
	i = mod(i, 289.0 ); 
	vec4 p = permute( permute( permute( 
						 i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
					 + i.y + vec4(0.0, i1.y, i2.y, 1.0 )) 
					 + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));

// Gradients
// ( N*N points uniformly over a square, mapped onto an octahedron.)
	float n_ = 1.0/7.0; // N=7
	vec3  ns = n_ * D.wyz - D.xzx;

	vec4 j = p - 49.0 * floor(p * ns.z *ns.z);  //  mod(p,N*N)

	vec4 x_ = floor(j * ns.z);
	vec4 y_ = floor(j - 7.0 * x_ );    // mod(j,N)

	vec4 x = x_ *ns.x + ns.yyyy;
	vec4 y = y_ *ns.x + ns.yyyy;
	vec4 h = 1.0 - abs(x) - abs(y);

	vec4 b0 = vec4( x.xy, y.xy );
	vec4 b1 = vec4( x.zw, y.zw );

	vec4 s0 = floor(b0)*2.0 + 1.0;
	vec4 s1 = floor(b1)*2.0 + 1.0;
	vec4 sh = -step(h, vec4(0.0));

	vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
	vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;

	vec3 p0 = vec3(a0.xy,h.x);
	vec3 p1 = vec3(a0.zw,h.y);
	vec3 p2 = vec3(a1.xy,h.z);
	vec3 p3 = vec3(a1.zw,h.w);

//Normalise gradients
	vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
	p0 *= norm.x;
	p1 *= norm.y;
	p2 *= norm.z;
	p3 *= norm.w;

// Mix final noise value
	vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
	m = m * m;
	return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
"""
PORTAL_FRAG_BODY = """
float x = (texcoords.x - 0.5);
float y = (texcoords.y - 0.5);
float len = sqrt(x*x + y*y);
fragColor = fragColor * vec4(vec3(sin(len*3.14*20-16*shadertime)+1)/2, 1)*sin(asin(sin(len+shadertime)));
vec4 color_2 = vec4((vec3(snoise(vec3(texcoords.xy/0.01, shadertime)))+1)/2.,1.);
fragColor = mix(fragColor,color_2, 0.3);
vec4 noise_color = vec4(vec3(rand(texcoords.xy*shadertime)), 1);
fragColor = mix(fragColor, noise_color, 0.3);
vec4 fade_color = vec4(fog_color.rgb, 0);
fragColor = mix(fragColor,fade_color,(2*len)*(2*len));
"""
CHUNK_FRAG_HEAD = '''
uniform float terrain_y_scale;
uniform float map_scale;
'''
CHUNK_FRAG_BODY = '''
float map_luma = world_pos.y / (map_scale * terrain_y_scale);
fragColor *= vec4(map_luma,map_luma,map_luma,1);
'''
FOG_FRAG_HEAD = '''
uniform float fog_max;
uniform vec4 fog_color;
uniform vec3 player_position;
'''
FOG_FRAG_BODY = ''' //Apply Fog
float fog_mult = min(1,length(player_position-world_pos.xyz)/fog_max);
fragColor = mix(fragColor,fog_color,fog_mult);
'''
END_SECTION = '''
}
'''

def save_generated_shaders(name, vert, frag):
	if not os.path.isdir('generated/shaders'):
		os.makedirs('generated/shaders')
	with open(os.path.join('generated/shaders', f'{name}.vert'), 'w+') as v:
		v.write(vert)
	with open(os.path.join('generated/shaders', f'{name}.frag'), 'w+') as f:
		f.write(frag)

def generate_snow_shader(world):
	vert = VERSION
	vert += INSTANCING_VERT_HEAD
	vert += SNOW_VERT_HEAD
	vert += TIMED_VERT_HEAD
	vert += STANDARD_VERT_HEAD
	vert += STANDARD_VERT_BODY
	vert += STANDARD_VERT_BODY_INSTANCED.format(SNOW_VERT_BODY_INSERTION)
	vert += END_SECTION
	frag = VERSION
	frag += FOG_FRAG_HEAD
	frag += STANDARD_FRAG_HEAD
	frag += STANDARD_FRAG_BODY
	frag += FOG_FRAG_BODY
	frag += END_SECTION
	defaults = {
		'texture_scale' : Vec2(1,1),
		'texture_offset' : Vec2(0.0, 0.0),
		'fog_color': world.fog_color,
		'fog_max': world.map_scale*(world.radius-0.5),
		'position_offsets' : [Vec3(0.0)],
		'rotation_offsets' : [Vec4(0.0)],
		'scale_multipliers' : [Vec3(1)],
		'fallscale_multipliers' : [Vec3(1)],
		'snow_height' : world.snow_height,
		'shadertime' : 0,
	}
	shader = Shader(language=Shader.GLSL,
		vertex=vert,
		fragment=frag,
		default_input=defaults,
	)
	return shader

def generate_foliage_shader(world):
	vert = VERSION
	vert += INSTANCING_VERT_HEAD
	vert += STANDARD_VERT_HEAD
	vert += STANDARD_VERT_BODY
	vert += STANDARD_VERT_BODY_INSTANCED
	vert += END_SECTION
	frag = VERSION
	frag += FOG_FRAG_HEAD
	frag += STANDARD_FRAG_HEAD
	frag += STANDARD_FRAG_BODY
	frag += FOG_FRAG_BODY
	frag += END_SECTION
	defaults = {
		'texture_scale' : Vec2(1,1),
		'texture_offset' : Vec2(0.0, 0.0),
		'fog_color': world.fog_color,
		'fog_max': world.map_scale*(world.radius-0.5),
		'terrain_y_scale': world.terrain_y_scale,
		'position_offsets' : [Vec3(0.0)],
		'rotation_offsets' : [Vec4(0.0)],
		'scale_multipliers' : [Vec3(1)],
	}
	shader = Shader(language=Shader.GLSL,
		vertex=vert,
		fragment=frag,
		default_input=defaults,
	)
	return shader

def generate_chunk_shader(world):
	vert = VERSION
	vert += STANDARD_VERT_HEAD
	vert += STANDARD_VERT_BODY
	vert += STANDARD_VERT_BODY_NON_INSTANCED
	vert += END_SECTION
	frag = VERSION
	frag += CHUNK_FRAG_HEAD
	frag += FOG_FRAG_HEAD
	frag += STANDARD_FRAG_HEAD
	frag += STANDARD_FRAG_BODY
	frag += CHUNK_FRAG_BODY
	frag += FOG_FRAG_BODY
	frag += END_SECTION
	defaults = {
		'texture_scale' : Vec2(1,1),
		'texture_offset' : Vec2(0.0, 0.0),
		'fog_color': world.fog_color,
		'fog_max': world.map_scale*(world.radius-0.5),
		'map_scale': world.map_scale,
		'terrain_y_scale': world.terrain_y_scale
	}
	shader = Shader(language=Shader.GLSL,
		vertex=vert,
		fragment=frag,
		default_input=defaults,
	)
	return shader

def generate_portal_shader(world):
	vert = VERSION
	vert += INSTANCING_VERT_HEAD
	vert += STANDARD_VERT_HEAD
	vert += STANDARD_VERT_BODY
	vert += STANDARD_VERT_BODY_INSTANCED
	vert += END_SECTION
	frag = VERSION
	frag += TIMED_FRAG_HEAD
	frag += PORTAL_FRAG_HEADER
	frag += FOG_FRAG_HEAD
	frag += STANDARD_FRAG_HEAD
	frag += STANDARD_FRAG_BODY
	frag += PORTAL_FRAG_BODY
	frag += FOG_FRAG_BODY
	frag += END_SECTION
	defaults = {
		'texture_scale' : Vec2(1,1),
		'texture_offset' : Vec2(0.0, 0.0),
		'fog_color': world.fog_color,
		'fog_max': world.map_scale*(world.radius-0.5),
		'position_offsets' : [Vec3(0.0)],
		'rotation_offsets' : [Vec4(0.0)],
		'scale_multipliers' : [Vec3(1)],
		'shadertime' : 0,
	}
	shader = Shader(language=Shader.GLSL,
		vertex=vert,
		fragment=frag,
		default_input=defaults,
	)
	save_generated_shaders('portal', vert, frag)
	return shader


def generate_world_shaders(world):
	return generate_chunk_shader(), generate_foliage_shader(), generate_snow_shader(), generate_portal_shader()
