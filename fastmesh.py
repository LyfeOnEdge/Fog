from ursina import *
from panda3d.core import MeshDrawer, NodePath
from panda3d.core import GeomVertexData, GeomVertexFormat, Geom, GeomNode
from panda3d.core import GeomTriangles, GeomTristrips, GeomTrifans
from panda3d.core import GeomLines, GeomLinestrips, GeomPoints
from panda3d.core import TexGenAttrib, TextureStage
import numpy as np
 
window.borderless = False
window.size = (800, 600)
# app = Ursina()
 
from opensimplex import OpenSimplex
import numpy as np
import numba

class dummy_settings:
    generator_scale =  1
    second_generator_scale = 4 #Fine details
    second_generator_weight =  0.3 #Fine details
    third_generator_scale = 0.05 #Big details
    third_generator_weight =  8 #Big details
    fourth_generator_scale = 0.3 #Big details
    fourth_generator_weight =  5 #Big details
    chunk_divisions= 30
    map_scale = 1024
    def __init__(self):
        pass

chunk_shader=Shader(language=Shader.GLSL,
vertex=f'''
#version 140
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform float mapdata[{dummy_settings.chunk_divisions+1}*{dummy_settings.chunk_divisions+1}];
''' + '''
out vec2 texcoords;
out float map_luma;
out vec4 world_pos;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
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
void main() {
    fragColor = vec4(map_luma,map_luma,map_luma,1);
}
''',
default_input={
    'texture_scale' : Vec2(1,1),
    'texture_offset' : Vec2(0.0, 0.0),
}
)


class TerrainGenerator:
    def __init__(self, game):
        self.game = game
        print(f"Using seed {self.game.seed}")
        print("Using Open Simplex")
        self.generator = OpenSimplex(seed=(self.game.seed)).noise2
        self.generator2 = OpenSimplex(seed=(self.game.seed+7)).noise2
        self.generator3 = OpenSimplex(seed=(self.game.seed+13)).noise2
        self.generator4 = OpenSimplex(seed=(self.game.seed+19)).noise2
        self.array_generator = OpenSimplex(seed=(self.game.seed)).noise2array
        self.array_generator2 = OpenSimplex(seed=(self.game.seed+7)).noise2array
        self.array_generator3 = OpenSimplex(seed=(self.game.seed+13)).noise2array
        self.array_generator4 = OpenSimplex(seed=(self.game.seed+19)).noise2array
        self.combined_weight = 1+self.game.settings.second_generator_weight+self.game.settings.third_generator_weight+self.game.settings.fourth_generator_weight

    def get_heightmap(self,x,z):
        height = self.generator(x*self.game.settings.generator_scale,z*self.game.settings.generator_scale)
        height = height + self.generator2(x*self.game.settings.second_generator_scale,z*self.game.settings.second_generator_scale) * self.game.settings.second_generator_weight
        height = height + self.generator3(x*self.game.settings.third_generator_scale,z*self.game.settings.third_generator_scale) * self.game.settings.third_generator_weight
        height = height + self.generator4(x*self.game.settings.fourth_generator_scale,z*self.game.settings.fourth_generator_scale) * self.game.settings.fourth_generator_weight
        return ((height / self.combined_weight)+1)/2.

    # def get_chunk_heightmap(self,x,z):
    #     z_values = np.linspace(z, z+1, self.game.settings.chunk_divisions+1, endpoint=True)
    #     z_values = np.repeat(z_values,self.game.settings.chunk_divisions+1,axis=0)
    #     x_values = np.linspace(x, x+1, self.game.settings.chunk_divisions+1, endpoint=True)
    #     x_values = np.hstack((x_values, ) * (self.game.settings.chunk_divisions+1))
    #     out = self.array_generator(x_values*self.game.settings.generator_scale,z_values*self.game.settings.generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
    #     out2 = self.array_generator2(x_values*self.game.settings.second_generator_scale,z_values*self.game.settings.second_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
    #     out3 = self.array_generator3(x_values*self.game.settings.third_generator_scale,z_values*self.game.settings.third_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
    #     out4 = self.array_generator4(x_values*self.game.settings.fourth_generator_scale,z_values*self.game.settings.fourth_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
    #     return (((out + (out2 * self.game.settings.second_generator_weight) + (out3 * self.game.settings.third_generator_weight) + (out4 * self.game.settings.fourth_generator_weight)) / self.combined_weight)+1)/2.
    def get_chunk_heightmap(self,x_values,z_values):
        # z_values = np.linspace(z, z+1, self.game.settings.chunk_divisions+1, endpoint=True)
        # z_values = np.repeat(z_values,self.game.settings.chunk_divisions+1,axis=0)
        # x_values = np.linspace(x, x+1, self.game.settings.chunk_divisions+1, endpoint=True)
        # x_values = np.hstack((x_values, ) * (self.game.settings.chunk_divisions+1))
        print(x_values)
        out = self.array_generator(x_values*self.game.settings.generator_scale,z_values*self.game.settings.generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
        out2 = self.array_generator2(x_values*self.game.settings.second_generator_scale,z_values*self.game.settings.second_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
        out3 = self.array_generator3(x_values*self.game.settings.third_generator_scale,z_values*self.game.settings.third_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
        out4 = self.array_generator4(x_values*self.game.settings.fourth_generator_scale,z_values*self.game.settings.fourth_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
        return (((out + (out2 * self.game.settings.second_generator_weight) + (out3 * self.game.settings.third_generator_weight) + (out4 * self.game.settings.fourth_generator_weight)) / self.combined_weight)+1)/2.









class FastMesh(NodePath):
 
    _formats = {
        (0,0,0) : GeomVertexFormat.getV3(),
        (1,0,0) : GeomVertexFormat.getV3c4(),
        (0,1,0) : GeomVertexFormat.getV3t2(),
        (0,0,1) : GeomVertexFormat.getV3n3(),
        (1,0,1) : GeomVertexFormat.getV3n3c4(),
        (1,1,0) : GeomVertexFormat.getV3c4t2(),
        (0,1,1) : GeomVertexFormat.getV3n3t2(),
        (1,1,1) : GeomVertexFormat.getV3n3c4t2(),
        }
 
    _modes = {
        'triangle' : GeomTriangles,
        'tristrip' : GeomTristrips,
        }
 
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
 
        # for var in (('vertices', vertices), ('triangles', triangles), ('colors', colors), ('uvs', uvs), ('normals', normals)):
        #     name, value = var
        #     if value is None:
        #         setattr(self, name, list())
 
        if self.vertices is not None:
            self.generate()
 
 
    def generate(self):  # call this after setting some of the variables to update it
        if hasattr(self, 'geomNode'):
            self.geomNode.removeAllGeoms()
 
        # prim.modify_vertices()
 
        static_mode = Geom.UHStatic if self.static else Geom.UHDynamic
        vertex_format = Mesh._formats[(bool(self.colors), bool(self.uvs), bool(self.normals))]
        self.vdata = GeomVertexData('name', vertex_format, static_mode)
        self.vdata.setNumRows(len(self.vertices)//3) # for speed
 
        arrayHandle0: core.GeomVertexArrayData = self.vdata.modifyArray(0)
        # arrayHandle1: core.GeomVertexArrayData = self.vdata.modifyArray(1)
        prim = Mesh._modes[self.mode](static_mode)
        # coords = [1., -3., 7., -4., 12., 5., 8., 2., -1., -6., 14., -11.]
        # either convert this sequence to an array of bytes...
        # (note that if you call tobytes() on it, you don't need to call
        # cast("f") on the memoryview, below)
        # pos_data = array.array("f", self.vertices)#.tobytes()
 
 
        pos_array = self.vdata.modify_array(0)
        memview = memoryview(pos_array).cast("B").cast("f")
        # memview = memoryview(pos_array).cast("B")
        memview[:] = self.vertices
        # print(pos_array)
 
        if not hasattr(self, 'geomNode'):
            self.geomNode = GeomNode('mesh')
            self.attachNewNode(self.geomNode)
 
        # self.generated_vertices = [self.vertices[i] for i in self.indices]
        # for i in len(self.vertices):
        #     prim.addVertex(v)
 
        # prim.addVertex((0,1,2))
        # prim.addVertex((3,4,5))
        prim.reserve_num_vertices(len(self.triangles))
        prim_array = prim.modify_vertices()
        prim_array.unclean_set_num_rows(len(self.triangles))
        memview = memoryview(prim_array)
        memview[:] = self.triangles
 
        # print(prim)
        geom = Geom(self.vdata)
        geom.addPrimitive(prim)
        self.geomNode.addGeom(geom)
 
# grid_size = 100
# grid_indices = np.arange(grid_size + 1)
# xs, zs = np.meshgrid(grid_indices, grid_indices)
# positions = np.zeros((grid_size + 1, grid_size + 1, 3), dtype=np.float32)
# positions[:, :, 0] = xs
# positions[:, :, 2] = zs
# print(positions[:5,:5])
# # Random heights per row for fun.
# # positions[:, :, 1] = np.tile(np.random.random(xs.shape[1]) * 2.0 - 2.0, xs.shape[0]).astype(np.float32).reshape(xs.shape)
# tris = np.zeros(grid_size * grid_size * 6)
# if len(tris) > 2**16-1:
#     tris = tris.astype(np.uint32)
# else:
#     tris = tris.astype(np.uint16)
# tris = tris.reshape((grid_size, grid_size, 6))
 
# # This can be done faster with numpy and/or numba, etc.
# for row in range(grid_size):
#     for col in range(grid_size):
#         i = col + row * positions.shape[1]
#         tris[row, col, 0] = i
#         tris[row, col, 1] = i + 1
#         tris[row, col, 2] = i + positions.shape[1]
#         tris[row, col, 3] = i + positions.shape[1]
#         tris[row, col, 4] = i + 1
#         tris[row, col, 5] = i + 1 + positions.shape[1]
 
# import time
 
# fast = True
# mesh = None
# if fast:
#     s = time.time()
#     mesh = FastMesh(vertices=positions.ravel(), triangles=tris.ravel())
#     print("dt: {0} ms".format((time.time() - s) * 1000.0))
# else:
#     poses = positions.ravel().astype(float).view([("x", float), ("y", float), ("z", float)]).tolist()
#     indices = tris.ravel().tolist()
#     s = time.time()
#     mesh = Mesh(vertices=poses, triangles=indices)
#     print("dt: {0} ms".format((time.time() - s) * 1000.0))
 
#grid = Entity(model=Mesh(vertices=positions.ravel().astype(np.float).tolist(), triangles=tris.astype(np.int).tolist()))

class Chunk(Entity):
    # def __init__(self, game, position, heightmap):
    def __init__(self, game):
        grid_size = game.settings.chunk_divisions
        grid_indices = np.arange(grid_size + 1)
        xs, zs = np.meshgrid(grid_indices, grid_indices)
        positions = np.zeros((grid_size + 1, grid_size + 1, 3), dtype=np.float32)
        positions[:, :, 0] = xs
        positions[:, :, 2] = zs
        heights = game.terrain_generator.get_chunk_heightmap(xs.ravel(),zs.ravel())
        positions[:, :, 1] = heights * 8
        # print(positions[:5,:5])
        # Random heights per row for fun.
        # positions[:, :, 1] = np.tile(np.random.random(xs.shape[1]) * 2.0 - 2.0, xs.shape[0]).astype(np.float32).reshape(xs.shape)
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
        mesh = FastMesh(vertices=positions.ravel(), triangles=tris.ravel())
        Entity.__init__(self, model=mesh, shader=chunk_shader, texture='assets/textures/grass', color=color.blue)
        self.set_shader_input('mapdata', heights.ravel().tolist())

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
        # self.player = FirstPersonController()
        self.chunk = Chunk(self)

        self.ground = Entity(scale=100)
        self.ground.collider = Plane()

if __name__ == "__main__":
    grid = Entity(model=mesh)
    ed = EditorCamera(position=(0,0,10))
    app = GameWithChunkloading(vsync=False)
    # update = app.update
    app.run() 