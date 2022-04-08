from ursina import *

import numpy as np
import numba

from panda3d.core import NodePath
from panda3d.core import GeomVertexData, GeomVertexFormat, Geom, GeomNode
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, TextureStage, TexGenAttrib, GeomVertexWriter, GeomVertexArrayFormat

from opensimplex import OpenSimplex


if __name__ == '__main__':
	from settings import settings
else:
	from .settings import settings

window.borderless = False

chunk_shader=Shader(language=Shader.GLSL,
vertex=f'''
#version 140
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;

''' + '''
out vec2 texcoords;
out vec4 world_pos;
void main() {
	{}
	gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
	texcoords = p3d_MultiTexCoord0;
	world_pos = p3d_ModelMatrix * p3d_Vertex;
}
''',
fragment='''
#version 140
in vec2 texcoords;
out vec4 fragColor;
in vec4 world_pos;
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform float fog_max;
uniform vec4 fog_color;
uniform vec3 player_position;
uniform float map_scale;
uniform float terrain_y_scale;
void main() {
	float fog_mult = min(1,length(player_position-world_pos.xyz)/fog_max);
	float map_luma = world_pos.y / (map_scale * terrain_y_scale);
	//vec4 color = mix(vec4(map_luma,map_luma,map_luma,1) * texture(p3d_Texture0, texcoords) * p3d_ColorScale, fog_color, fog_mult);
	
	fragColor = texture(p3d_Texture0, texcoords) * p3d_ColorScale;
	fragColor *= vec4(map_luma,map_luma,map_luma,1);
	fragColor = mix(fragColor, fog_color, fog_mult);
	//fragColor = color.rgba;
}
''',
default_input={
	'texture_scale' : Vec2(1,1),
	'texture_offset' : Vec2(0.0, 0.0),
	'fog_color': color.rgba(120,120,120,255),
	'fog_max': settings.map_scale*(settings.render_distance-0.5),
	'map_scale': settings.map_scale,
	'terrain_y_scale': 1
}
)

class Chunk(Entity):
	grid_size = settings.chunk_divisions
	grid_indices = np.arange(grid_size + 1) / (grid_size)
	xs, zs = np.meshgrid(grid_indices, grid_indices)  
	positions = np.zeros((grid_size + 1, grid_size + 1, 3), dtype=np.float32)
	positions[:, :, 0] = xs
	positions[:, :, 2] = zs
	uvs = np.zeros(((grid_size+1)**2, 2), dtype=np.float32)
	uvs[:, 0] = np.hstack((np.linspace(0,1,grid_size+1,endpoint=True),)*(grid_size+1))
	uvs[:, 1] = np.repeat(np.linspace(0,1,grid_size+1, endpoint=True),grid_size+1, axis=0)
	uvs = uvs.ravel()
	tris = np.zeros(grid_size * grid_size * 6)
	if len(tris) > 2**16-1:
		tris = tris.astype(np.uint32)
	else:
		tris = tris.astype(np.uint16)
	tris = tris.reshape((grid_size, grid_size, 6))
	
	# This can be done faster with numpy and/or numba, etc.
	for row in range(grid_size):
		for col in range(grid_size):
			i = col + row * positions.shape[1]
			tris[row, col, 0] = i
			tris[row, col, 1] = i + 1
			tris[row, col, 2] = i + positions.shape[1]
			tris[row, col, 3] = i + positions.shape[1]
			tris[row, col, 4] = i + 1
			tris[row, col, 5] = i + 1 + positions.shape[1]
	tris = tris.ravel()

	def __init__(self, world, chunk_id, shader = chunk_shader):
		self.world, self.chunk_id = world, chunk_id
		x,z = chunk_id
		heights = world.terrain_generator.get_chunk_heightmap(self.xs.ravel()+x,self.zs.ravel()+z)
		positions = self.positions.copy()
		# positions[:, :, 0] += x
		positions[:, :, 1] = heights * world.terrain_y_scale
		# positions[:, :, 2] += z
		self.heightmap = heights
		
		mesh = FastMesh(vertices=positions.ravel(), triangles=self.tris.copy(), uvs=self.uvs.copy())
		Entity.__init__(self, model=mesh, shader=shader, color=world.color, scale = world.map_scale, position=(x*self.world.map_scale,0,z*self.world.map_scale))
		self.set_shader_input('player_position', (0,0,0))
		self.set_shader_input('terrain_y_scale', world.terrain_y_scale)
		# self.set_shader_input('mapdata', heights.ravel().tolist())
		self.chunk_entities = []
		self.foliage_tokens = []
		self.portals = []

	# def update(self):
	# 	self.set_shader_input('player_position', self.world.game.player.position)

class FastMesh(NodePath):
	def __init__(self, vertices=None, triangles=None, colors=None, uvs=None, normals=None, static=True, mode='triangle', thickness=1, render_points_in_3d=True):
		super().__init__('mesh')
		self.name = 'mesh'
		self.vertices = vertices
		self.triangles = triangles
		self.colors = colors
		self.uvs = uvs
		self.normals = normals
		self.static = static
		self.mode = mode
		self.thickness = thickness
		self.render_points_in_3d = render_points_in_3d
 
		if self.vertices is not None:
			self.generate()

		tex = loader.loadTexture('assets/textures/grass.png')
		# self.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
		self.setTexture(tex)
 
	def generate(self):  # call this after setting some of the variables to update it
		if hasattr(self, 'geomNode'):
			self.geomNode.removeAllGeoms()

		v_array = GeomVertexArrayFormat()
		v_array.addColumn("vertex", 3, Geom.NTFloat32, Geom.CPoint)
		t_array = GeomVertexArrayFormat()
		t_array.addColumn("texcoord", 2, Geom.NTFloat32, Geom.CTexcoord)
		vertex_format = GeomVertexFormat()
		vertex_format.addArray(v_array)
		vertex_format.addArray(t_array)
		vertex_format = GeomVertexFormat.registerFormat(vertex_format)
		self.vdata = GeomVertexData('name', vertex_format, Geom.UHStatic)
		self.vdata.setNumRows(len(self.vertices))

		arrayHandle0: core.GeomVertexArrayData = self.vdata.modifyArray(0)
		prim = GeomTriangles(Geom.UHStatic)
		 
		pos_array = self.vdata.modifyArray(0)
		memview = memoryview(pos_array).cast("B").cast("f")
		memview[:len(self.vertices)] = self.vertices

		tex_array = self.vdata.modifyArray(1)
		memview = memoryview(tex_array).cast("B").cast("f")
		memview[:len(self.uvs)] = self.uvs

		if not hasattr(self, 'geomNode'):
			self.geomNode = GeomNode('mesh')
			self.attachNewNode(self.geomNode)

		prim.reserve_num_vertices(len(self.triangles))
		prim_array = prim.modify_vertices()
		prim_array.unclean_set_num_rows(len(self.triangles))
		memview = memoryview(prim_array)
		memview[:] = self.triangles

		geom = Geom(self.vdata)
		geom.addPrimitive(prim)
		self.geomNode.addGeom(geom)


if __name__ == "__main__":
	from terrain_generation import TerrainGenerator

	class GameWithChunkloading(Ursina):
		def __init__(self,*args,**kwargs):
			#Set defaults
			self.radius = 100
			self.seed = random.randint(1,9999999999)
			self.settings = settings
			self.map_scale = settings.map_scale
			super().__init__(*args, **kwargs)
			self.terrain_generator = TerrainGenerator(self)
			self.chunks=[]
			for x in range(-self.settings.render_distance,self.settings.render_distance):
				for z in range(-self.settings.render_distance,self.settings.render_distance):
					self.chunks.append(Chunk(self,(x,z)))

	grid = Entity(model=mesh)
	
	app = GameWithChunkloading(vsync=False)
	ed = EditorCamera(position=(0,0,0))
	app.run() 