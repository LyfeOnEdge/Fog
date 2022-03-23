from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
import array
import math

import numpy as np

class MyApp(ShowBase):

    def __init__(self):

        ShowBase.__init__(self)

        positions = np.array([
            -0.5, 0, -0.5,
             0.5, 0, -0.5,
             0.5, 0,  0.5,
            -0.5, 0,  0.5,
        ]).astype(np.float32)
        tris = np.array([0, 1, 2, 0, 2, 3]).astype(np.uint16)

        #pos_data = array.array("f", positions)
        pos_data = positions

        vertex_format = GeomVertexFormat.get_v3()
        vertex_data = GeomVertexData("vertex_data", vertex_format, Geom.UH_static)
        vertex_data.unclean_set_num_rows(len(pos_data) // 3)
        pos_array = vertex_data.modify_array(0)
        memview = memoryview(pos_array).cast("B").cast("f")
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