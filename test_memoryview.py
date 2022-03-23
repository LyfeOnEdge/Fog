from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
import array
import math
import numpy as np

from rain import TerrainGenerator

# class FastHeightMesh():
#     def __init__(self, heightmap):
#         # pos_data = array.array('f', np.swapaxes(heightmap,0,1).reshape(21*21))
#         # pos_data = np.swapaxes(heightmap,0,1).reshape(21*21).astype(np.float32)
#         pos_data = np.swapaxes(heightmap,0,1).ravel().astype(np.float32)

#         # self.triangles = list()
#         lhm = len(pos_data)
#         l=lhm-1
#         i=0
#         # for z in range(1,lhm):
#         #     for x in range(1, lhm):
#         #         self.triangles.append((i, i-1, i-l-2, i-l-1))
#         # self.triangles = np.asarray(self.triangles).astype(np.uint16).ravel()

#         vertex_format = GeomVertexFormat.get_v3()
#         vertex_data = GeomVertexData("vertex_data", vertex_format, Geom.UH_static)
#         vertex_data.unclean_set_num_rows(len(pos_data) // 21)
#         pos_array = vertex_data.modify_array(0)
#         memview = memoryview(pos_array).cast("B").cast("f")
#         memview[:] = pos_data
#         print("Verticies:")
#         print(vertex_data.get_array(0))

#         tri_data = array.array("H", tris)
#         tris_prim = GeomTriangles(Geom.UH_static)
#         tris_prim.reserve_num_vertices(len(tri_data))
#         tris_array = tris_prim.modify_vertices()
#         tris_array.unclean_set_num_rows(len(tri_data))
#         memview = memoryview(tris_array)

#         print('Memview content : {}'.format(memview.tolist()))
#         print('Memview format : {}'.format(memview.format))
#         print('Memview length : {}'.format(len(memview)))
#         memview[:] = tri_data
#         print('Copy to memview : {}'.format(memview.tolist()))
#         print('tri_data :')
#         print(tris_prim)

#         geom = Geom(vertex_data)
#         geom.addPrimitive(tris_prim)

#         node = GeomNode("gnode")
#         node.addGeom(geom)

#         node_path = render.attachNewNode(node)

# class MyApp(ShowBase):

#     def __init__(self):
#         from rain import settings
#         self.settings = settings
#         self.seed = 0
#         ShowBase.__init__(self)
#         generator = TerrainGenerator(self)
#         self.heightmap = FastHeightMesh(generator.get_chunk_heightmap(0,0))

#         self.taskMgr.add(self.heightmap.spin_camera_task, "spin camera task")

#     # def spin_camera_task(self, task):
#     #     angleDeg = task.time * 30.0
#     #     angleRad = angleDeg * (math.pi / 180.0)
#     #     self.camera.setPos(20 * math.sin(angleRad), -20 * math.cos(angleRad), 3)
#     #     self.camera.setHpr(angleDeg, 0, 0)
#     #     return Task.cont


class MyApp(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		from rain import settings
		self.settings = settings
		self.seed = 0
		
		generator = TerrainGenerator(self)

		#Returns a 4 x 4 heightmap array
		heightmap = generator.get_chunk_heightmap(0,0)
		lhm = len(heightmap)
		# pos_data = heightmap.copy().ravel().astype(np.float32)
		pos_data = np.full((lhm*lhm, 3), (0,0,0), dtype=np.float32)
		# print(len(pos_data)) #Length 16
		lhm = len(heightmap)
		l=lhm-1
		i=0
		tris = []
		for z in range(lhm):
		    for x in range(lhm):
		    	if x > 0 and z > 0:
		    		tris.extend([i-1, i, i+1, i-1, i+1, i+2])
		    	pos_data[i]=(x,heightmap[z][x],z)	
		    	i += 1
		pos_data=pos_data.ravel()
		print(len(pos_data))
		
		# l = 10
		# tris = np.arange(l * l).reshape((l, l))
		# tris = np.repeat(tris, 4)
		# tris[2::4] -= l+2


		# tris = np.asarray(tris).astype(np.uint16)
		# print(len(tris)) #900
		# print(tris)
		



		vertex_format = GeomVertexFormat.get_v3()
		vertex_data = GeomVertexData("vertex_data", vertex_format, Geom.UH_static)
		vertex_data.unclean_set_num_rows(lhm)
		pos_array = vertex_data.modify_array(0)
		memview = memoryview(pos_array).cast("B").cast("f") 
		print(len(memview)) #Length 12
		memview[:] = pos_data
		print("Verticies:")
		print(vertex_data.get_array(0))

		#tri_data = array.array("H", tris)
		tri_data = tris

		tris_prim = GeomTriangles(Geom.UH_static)
		tris_prim.reserve_num_vertices(len(tri_data))
		tris_array = tris_prim.modify_vertices()
		tris_array.unclean_set_num_rows(len(tri_data))
		memview = memoryview(tris_array)

		print('Memview content : {}'.format(memview.tolist()))
		print('Memview format : {}'.format(memview.format))
		print('Memview length : {}'.format(len(memview)))
		memview[:] = tri_data
		print('Copy to memview : {}'.format(memview.tolist()))
		print('tri_data :')
		print(tris_prim)

		geom = Geom(vertex_data)
		geom.addPrimitive(tris_prim)

		node = GeomNode("gnode")
		node.addGeom(geom)

		node_path = render.attachNewNode(node)

		self.taskMgr.add(self.spin_camera_task, "spin camera task")

	def spin_camera_task(self, task):
		angleDeg = task.time * 30.0
		angleRad = angleDeg * (math.pi / 180.0)
		self.camera.setPos(20 * math.sin(angleRad), -20 * math.cos(angleRad), 3)
		self.camera.setHpr(angleDeg, 0, 0)
		return Task.cont






app = MyApp()
app.run()