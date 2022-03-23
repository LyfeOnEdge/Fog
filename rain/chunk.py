from ursina import *
from panda3d.core import OmniBoundingVolume, LQuaterniond, LVecBase3d
import numpy as np
from .settings import settings
chunk_shader=Shader(language=Shader.GLSL,
vertex=f'''
#version 140
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform float mapdata[{settings.chunk_divisions+1}*{settings.chunk_divisions+1}];
''' + '''
out vec2 texcoords;
out float map_luma;
out vec4 world_pos;
void main() {
	gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
	//map_luma = 0.8+(mapdata[gl_VertexID])/3.0;
	map_luma = mapdata[gl_VertexID];
	texcoords = p3d_MultiTexCoord0;
	world_pos = p3d_ModelMatrix * p3d_Vertex;
}
''',
fragment='''
#version 140
in vec2 texcoords;
in float map_luma;
out vec4 fragColor;
in vec4 world_pos;
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform float fog_max;
uniform vec4 fog_color;
uniform vec3 player_position;
void main() {
	float fog_mult = min(1,length(player_position-world_pos.xyz)/fog_max);
	float luma = 0.8+map_luma/3.0;
	vec4 color = mix(vec4(luma,luma,luma,1) * texture(p3d_Texture0, texcoords) * p3d_ColorScale, fog_color, fog_mult);
	fragColor = color.rgba;
}
''',
default_input={
	'texture_scale' : Vec2(1,1),
	'texture_offset' : Vec2(0.0, 0.0),
	'fog_color': color.rgba(120,120,120,255),
	'fog_max': settings.map_scale*(settings.render_distance-0.5)
}
)

from panda3d.core import ShaderTerrainMesh



#This entity is a base, when writing a game you would want to do stuff like spawning foliage etc when the chunk is initialized.
# class Chunk(Entity):
# 	def __init__(self, game, chunk_id, heightmap, **kwargs):
# 		Entity.__init__(
# 				self,
# 				model=HeightMesh(heightmap),
# 				texture="assets/textures/grass.png",
# 				shader=chunk_shader,
# 				color=color.rgb(80,100,100),
# 				**kwargs,
# 			)
# 		self.game, self.chunk_id, self.heightmap = game, chunk_id, heightmap
# 		# self.collider = self.model
# 		if self.collider: del self.collider
# 		self.collider = None
# 		self.chunk_entities = []
# 		self.foliage_tokens = []
# 		lhm = len(self.heightmap)
# 		self.set_shader_input('mapdata', self.heightmap.copy().reshape(lhm*lhm).tolist())
# 		self.set_shader_input('base_position', self.position)
# 	# def save(self):
# 	# 	x,z = self.chunk_id
# 	# 	filename = self.game.saves_dir+f"{x}x{z}#{self.game.seed}.json"
# 	# 	with open(filename, "w+") as f:
# 	# 		json.dump({"heightmap":self.heightmap}, f)
# 	def update(self):
# 		self.set_shader_input('player_position', self.game.player.position)


class chunk(ShaderTerrainMesh):
	def __init__(self, game, chunk_id, heightmap, **kwargs):
		ShaderTerrainMesh.__init__(
				self,
				# model=HeightMesh(heightmap),
				# texture="assets/textures/grass.png",
				# shader=chunk_shader,
				# color=color.rgb(80,100,100),
				**kwargs,
			)


		
	# 	self.game, self.chunk_id, self.heightmap = game, chunk_id, heightmap
	# 	# self.collider = self.model
	# 	if self.collider: del self.collider
	# 	self.collider = None
	# 	self.chunk_entities = []
	# 	self.foliage_tokens = []
	# 	lhm = len(self.heightmap)
	# 	self.set_shader_input('mapdata', self.heightmap.copy().reshape(lhm*lhm).tolist())
	# 	self.set_shader_input('base_position', self.position)
	# # def save(self):
	# # 	x,z = self.chunk_id
	# # 	filename = self.game.saves_dir+f"{x}x{z}#{self.game.seed}.json"
	# # 	with open(filename, "w+") as f:
	# # 		json.dump({"heightmap":self.heightmap}, f)
	# def update(self):
	# 	self.set_shader_input('player_position', self.game.player.position)