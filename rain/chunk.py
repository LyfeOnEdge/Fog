from ursina import *
from ursina.scripts.generate_normals import normalize_v3
import numpy as np

from panda3d.core import NodePath, SamplerState, Geom, GeomNode, GeomTriangles
from panda3d.core import GeomVertexData, GeomVertexFormat, GeomVertexArrayFormat
from opensimplex import OpenSimplex

if __name__ == '__main__':
	from settings import settings
else:
	from .settings import settings

#Optimized version of the function from Ursina's generate normals script
def generate_normals(vertices, triangles, norm_scale=1):
	vertices[:,1]*=norm_scale #Adjust the input verticies y scale 
	normals = np.zeros(vertices.shape, dtype=vertices.dtype)
	tris = vertices[triangles]
	n = np.cross(tris[::,1] - tris[::,0] ,tris[::,2] - tris[::,0])
	normalize_v3(n)
	normals[triangles[:,0]] -= n
	normals[triangles[:,1]] -= n
	normals[triangles[:,2]] -= n
	normalize_v3(normals)
	return normals

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
	
	normal_tris = []
	shp = positions.shape[1]
	for row in range(grid_size):
		for col in range(grid_size):
			i = col + row * shp
			tris[row, col, 0] = i
			tris[row, col, 1] = i + 1
			tris[row, col, 2] = i + shp
			tris[row, col, 3] = i + shp
			tris[row, col, 4] = i + 1
			tris[row, col, 5] = i + 1 + shp
			normal_tris.extend([(i, i+1, i+shp), (i+shp,i+1,i+1+shp)])
	normal_tris = np.asarray(normal_tris)
	tris = tris.ravel()

	len_triangles = len(tris)
	prim = GeomTriangles(Geom.UHStatic)
	prim.reserve_num_vertices(len_triangles)
	prim_array = prim.modify_vertices()
	prim_array.unclean_set_num_rows(len_triangles)

	def __init__(self, world, chunk_id, shader):
		self.world, self.chunk_id = world, chunk_id
		x,z = chunk_id
		self.heightmap = heights = world.terrain_generator.get_chunk_heightmap(self.xs.ravel()+x,self.zs.ravel()+z)
		positions = self.positions.copy()
		positions[:, :, 1] = heights
		normals = generate_normals(positions.copy().reshape((self.grid_size + 1) * (self.grid_size + 1), 3), self.normal_tris, norm_scale=3)
		positions[:, :, 1] *= world.terrain_y_scale #Apply world deformation scale
		
		mesh = FastMesh(self.prim, self.prim_array, positions.ravel(), self.tris, self.uvs, np.asarray(normals, dtype=np.float32).ravel())
		# tex = loader.loadTexture('assets/textures/grass_light.png')
		# tex.setMagfilter(SamplerState.FT_nearest_mipmap_linear)
		# tex.setMinfilter(SamplerState.FT_nearest_mipmap_linear)
		# tex.setAnisotropicDegree(2)
		# mesh.setTexture(tex)
		Entity.__init__(self, model=mesh, shader=shader, color=world.color, scale = world.map_scale, position=(x*self.world.map_scale,0,z*self.world.map_scale), texture_scale=(14,14))
		self.set_shader_input('player_position', (0,0,0))
		self.set_shader_input('terrain_y_scale', world.terrain_y_scale)
		self.chunk_entities = []
		self.foliage_tokens = []
		self.portals = []

class FastMesh(NodePath):
	v_array = GeomVertexArrayFormat()
	v_array.addColumn("vertex", 3, Geom.NTFloat32, Geom.CPoint)
	t_array = GeomVertexArrayFormat()
	t_array.addColumn("texcoord", 2, Geom.NTFloat32, Geom.CTexcoord)
	n_array = GeomVertexArrayFormat()
	n_array.addColumn("normal", 3, Geom.NTFloat32, Geom.CPoint)
	vertex_format = GeomVertexFormat()
	vertex_format.addArray(v_array)
	vertex_format.addArray(t_array)
	vertex_format.addArray(n_array)
	vertex_format = GeomVertexFormat.registerFormat(vertex_format)
	def __init__(self, prim, prim_array, vertices, triangles, uvs, normals):
		super().__init__('mesh')
		self.name = 'mesh'
		self.vertices = vertices
		self.triangles = triangles
		self.uvs = uvs
		self.normals = normals
		self.prim, self.prim_array = prim, prim_array
		self.generate()
 
	def generate(self):
		self.vdata = GeomVertexData('name', self.vertex_format, Geom.UHStatic)
		self.vdata.setNumRows(len(self.vertices))

		#Write Verts
		memview = memoryview(self.vdata.modifyArray(0)).cast("B").cast("f")
		memview[:len(self.vertices)] = self.vertices
		#Write UVs
		memview = memoryview(self.vdata.modifyArray(1)).cast("B").cast("f")
		memview[:len(self.uvs)] = self.uvs
		#Write Normals
		memview = memoryview(self.vdata.modifyArray(2)).cast("B").cast("f")
		memview[:len(self.normals)] = self.normals

		self.geomNode = GeomNode('mesh')
		self.attachNewNode(self.geomNode)

		memview = memoryview(self.prim_array)
		memview[:] = self.triangles

		geom = Geom(self.vdata)
		geom.addPrimitive(self.prim)
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