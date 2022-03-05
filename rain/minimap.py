from ursina import *
from PIL import Image
from numpy import uint8, asarray, swapaxes


MAP_SIZE = 100

# Not implemented yet
# map_shader=Shader(language=Shader.GLSL,
# vertex='''
# #version 140
# in vec4 p3d_Vertex;
# out vec4 map_color;
# uniform vec2 texture_scale;
# uniform vec2 texture_offset;
# uniform mat4 p3d_ModelViewProjectionMatrix;
# uniform float mapdata[256];
# uniform int map_size;
# void main() {
# 	gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
# 	float luma = mapdata[gl_VertexID];
# 	map_color = vec4(luma,luma,luma,1.0);
# }
# ''',
# fragment='''
# #version 140
# in vec2 texcoords;
# in vec4 map_color;
# out vec4 fragColor;
# void main() {
# 	fragColor = map_color.rgba;
# }
# ''',
# default_input={
# 	'texture_scale' : Vec2(1,1),
# 	'texture_offset' : Vec2(0.0, 0.0),
# 	'map_size': MAP_SIZE,
# }
# )

class MiniMap(Entity):
	def __init__(self, game):
		self.game = game
		self.image = None
		Entity.__init__(self,
				name='minimap',
				model="quad",
				texture="white_cube",
				parent=camera.ui,
				scale=0.25,
				color=color.rgba(255,255,255,255),
				position = (0.725,0.35),
			)
		self.z -=0.1

		self.minimap_frame = Entity(
				name='minimap_frame',
				model="quad",
				texture="assets/textures/map_frame.png",
				parent=self,
				scale=1,
				color=color.white,
				position = (0,0)
			)
		self.minimap_frame.z -=0.1

		self.minimap_cursor = Entity(
				name='minimap_cursor',
				model="quad",
				texture="assets/textures/minimap_cursor.png",
				parent=self,
				scale=0.4,
				origin = (0,0),
				color=color.white,
				position = (0,0)
			)
		self.minimap_cursor.z -=0.1

		self.minimap_needs_update = True

	def update_minimap(self, data):
		self.texture = Texture(Image.fromarray(data).convert("RGBA"))
		self.minimap_cursor.rotation_z = self.game.player.rotation_y

	def rotation_update(self):
		self.minimap_cursor.rotation_z = self.game.player.rotation_y

	def disable(self):
		self.visible = False
		for c in self.children:
			c.visible = False

	def enable(self):
		self.visible = True
		for c in self.children:
			c.visible = True