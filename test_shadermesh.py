import os, json, random
from panda3d.core import ShaderTerrainMesh, Texture as pTexture, Shader as pShader
from ursina import *
import numpy as np
from rain import TerrainGenerator, MeshWalker
from PIL import Image
from ursina.prefabs.first_person_controller import FirstPersonController
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
terrain_shader = pShader.load(pShader.SL_GLSL, "assets/shaders/terrain.vert", "assets/shaders/terrain.frag")
import array
class Chunk:
	def __init__(self, game, chunk_id, heightmap):
		self.chunk_id = chunk_id
		self.game = game
		# ShaderTerrainMesh.__init__(
		# 		self,
		# 	)
		l = len(heightmap)
		tris = np.arange(l * l).reshape((l, l))
		tris = np.repeat(tris, 4)
		tris[2::4] -= l+2
		tris=tris.ravel().astype(np.uint16)
		print(tris[0:3])

		zv, xv = np.meshgrid(np.arange(l), np.arange(l), indexing="ij")
		positions = []
		for z in range(l):
			for x in range(l):
				positions.extend([xv[x][z], heightmap[x][z], zv[x][z]])
		positions = np.asarray(positions)
		positions = positions.astype(np.float32)
		pos_data = positions

		vertex_format = GeomVertexFormat.get_v3()
		vertex_data = GeomVertexData("vertex_data", vertex_format, Geom.UH_static)
		vertex_data.unclean_set_num_rows(len(pos_data) // 3)
		pos_array = vertex_data.modify_array(0)
		memview = memoryview(pos_array).cast("B").cast("f")
		memview[:] = pos_data

		# tri_data = array.array("H", tris)
		tri_data = tris.astype(np.uint32)
		tris_prim = GeomTriangles(Geom.UH_static)
		tris_prim.reserve_num_vertices(len(tri_data))
		tris_array = tris_prim.modify_vertices()
		tris_array.unclean_set_num_rows(len(tri_data))
		memview = memoryview(tris_array)
		print('tri_data length : {}'.format(len(tri_data)))
		print('Memview length : {}'.format(len(memview)))
		memview[:] = tri_data

		geom = Geom(vertex_data)
		geom.addPrimitive(tris_prim)

		node = GeomNode("gnode")
		node.addGeom(geom)

		node_path = render.attachNewNode(node)

		self.taskMgr.add(self.spin_camera_task, "spin camera task")




		# self.tex = pTexture(f'chunk')
		# self.tex.setup2dTexture(self.game.settings.chunk_divisions+1, self.game.settings.chunk_divisions+1, pTexture.T_unsigned_byte, pTexture.F_luminance)
		# buf = Image.fromarray(heightmap).convert("RGBA").tobytes()
		# self.tex.setRamImageAs(buf, "RGBA")
		# self.heightfield = self.tex
		# self.generate()
		# self.terrain = self.game.render.attach_new_node(self)
		# self.terrain.set_scale(20, 20, 20)
		# self.terrain.set_pos(0, 0, 0)
		# self.terrain.set_hpr(0, 0, 0)
		# self.terrain.set_shader(terrain_shader)
		# self.terrain.set_shader_input("camera", self.game.player)
		# self.setChunkSize(32)



# class Chunk(ShaderTerrainMesh):
# 	def __init__(self, game, chunk_id, heightmap):
# 		self.chunk_id = chunk_id
# 		self.game = game
# 		ShaderTerrainMesh.__init__(
# 				self,
# 			)

# 		l = len(heightmap)
# 		tris = np.arange(l * l).reshape((l, l))
# 		tris = np.repeat(tris, 4)
# 		tris[2::4] -= l+2

		
# 		zv, xv = np.meshgrid(np.arange(l), np.arange(l), indexing="ij")
# 		positions = []
# 		for z in range(l):
# 			for x in range(l):
# 				positions.append((xv[x], heightmap[x][z], zv[z]))
# 		positions = np.array(positions).astype(np.float32)



class dummy_settings:
	def __init__(self):
		self.generator_scale = 2
		self.second_generator_scale= 1
		self.second_generator_weight= 0 #Disable
		self.third_generator_scale= 1
		self.third_generator_weight= 0 #Disable
		self.fourth_generator_scale= 1
		self.fourth_generator_weight= 0 #Disable
		self.chunk_divisions= 1023
		self.map_scale = 1024

class GameWithChunkloading(Ursina):
	def __init__(self,*args,**kwargs):
		#Set defaults
		self.radius = 100
		self.terrain_y_scale = 0
		self.seed = random.randint(1,9999999999) #Random overwritten by kwargs
		self.settings = dummy_settings()
		self.map_scale = self.settings.map_scale
		super().__init__(*args, **kwargs)
		self.terrain_generator = TerrainGenerator(self)
		self.player = FirstPersonController()
		self.chunk = Chunk(self, (0,0), self.terrain_generator.get_chunk_heightmap(0,0))

		self.ground = Entity(scale=100)
		self.ground.collider = Plane()



if __name__ == "__main__":
	app = GameWithChunkloading(vsync=False)
	# update = app.update
	app.run() 