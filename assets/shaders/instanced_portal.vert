/*
Modified by Lyfe for use with Panda3d with instancing
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
#version 140

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
uniform vec2 texture_offset;
uniform vec2 texture_scale;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform vec3 position_offsets[256];
uniform vec4 rotation_offsets[256];
uniform vec3 scale_multipliers[256];
out vec2 texcoords;
out vec4 draw_color;
out vec4 world_pos;

void main() {
        vec3 v = p3d_Vertex.xyz * scale_multipliers[gl_InstanceID];
		vec4 q = rotation_offsets[gl_InstanceID];
		v = v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
		vec4 displacement = vec4(v+position_offsets[gl_InstanceID], 1.0);
		gl_Position = p3d_ModelViewProjectionMatrix * displacement;
		texcoords = (p3d_MultiTexCoord0 * texture_scale) + texture_offset;
		world_pos = p3d_ModelMatrix * displacement;
        draw_color = vec4(0.5,0.5,1.,1.);
}