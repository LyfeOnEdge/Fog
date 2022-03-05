# raise not implemented


from ursina import *
from panda3d.core import OmniBoundingVolume, LQuaterniond, LVecBase3d

if __name__ == '__main__':
	from settings import settings
else:
	from .settings import settings

foliage_shader=Shader(language=Shader.GLSL, vertex='''#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 texcoords;
uniform vec2 texture_scale;
uniform vec2 texture_offset;
uniform vec3 position_offsets[256];
uniform vec4 rotation_offsets[256];
uniform vec3 scale_multipliers[256];
uniform vec3 base_position;
uniform mat4 p3d_ModelMatrix;
out vec4 world_pos;
void main() {
	vec3 v = p3d_Vertex.xyz * scale_multipliers[gl_InstanceID];
	vec4 q = rotation_offsets[gl_InstanceID];
	v = v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
	vec4 displacement = vec4(v+position_offsets[gl_InstanceID], 1.0);
	gl_Position = p3d_ModelViewProjectionMatrix * displacement;
	texcoords = (p3d_MultiTexCoord0 * texture_scale) + texture_offset;
	world_pos = p3d_ModelMatrix * displacement;
}
''',
fragment='''
#version 140
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
in vec2 texcoords;
out vec4 fragColor;
uniform float fog_max;
uniform vec4 fog_color;
uniform vec3 player_position;
in vec4 world_pos;
void main() {
	float fog_mult = min(1,length(player_position-world_pos.xyz)/fog_max);
	vec4 color = mix(texture(p3d_Texture0, texcoords) * p3d_ColorScale, fog_color, fog_mult);
	fragColor = color.rgba;
}
''',
default_input={
	'texture_scale' : Vec2(1,1),
	'texture_offset' : Vec2(0.0, 0.0),
	'position_offsets' : [Vec3(0.0)],
	'rotation_offsets' : [Vec4(0.0)],
	'scale_multipliers' : [Vec3(1)],
	'fog_color': color.rgba(120,120,120,255),
	'fog_max': float(settings.map_scale)*(float(settings.render_distance)-0.5),
}
)


class FoliageIdentifier:
	__slots__ = ['tind', 'sind', 'uid']
	def __init__(self, typeindex, spawnerindex, uid):
		self.tind = typeindex
		self.sind = spawnerindex
		self.uid = uid

class FoliageSpawner(Entity):
	def __init__(self, game, typeindex, spawnerindex, model, *args, **kwargs):
		Entity.__init__(self, *args, model=model, texture="assets/textures/tree_texture", **kwargs)
		self.game = game
		self.typeindex, self.spawnerindex = typeindex, spawnerindex
		self.instances = []
		self._uid = 0
		self.model.uvs = [(v[0],v[1]) for v in self.model.vertices]
		# self.model.generate()
		self.shader = foliage_shader
		self.setInstanceCount(0)
		self.start = time.time()
		self.positions, self.scales, self.quaternions = [], [], []
		self.node().setBounds(OmniBoundingVolume())
		self.node().setFinal(True)
		# self.set_shader_input('base_position', self.position)

	def get_uid(self):
		self._uid += 1
		return self._uid - 1

	def spawn_entity(self, position = Vec3(0,0,0), scale = Vec3(1), rotation = Vec3(0,0,0)):
		uid = self.get_uid()
		self.positions.append(position)
		self.setInstanceCount(len(self.positions))
		self.scales.append(scale)
		q = LQuaterniond()
		q.setHpr(LVecBase3d(rotation.x,rotation.y,180+rotation.z))
		self.quaternions.append(q)
		self.instances.append(uid)
		self.update_shader()
		self.enabled = True
		return FoliageIdentifier(self.typeindex, self.spawnerindex, uid)

	def remove_entity(self, uid):
		index = self.instances.index(uid)
		self.instances.pop(index)
		self.quaternions.pop(index)
		self.scales.pop(index)
		self.positions.pop(index)
		lp = len(self.positions)
		self.setInstanceCount(lp)
		self.enabled = lp != 0 #Disable if nothing to render


		self.update_shader()

	def update_shader(self):
		self.set_shader_input('position_offsets', self.positions)
		self.set_shader_input('rotation_offsets', self.quaternions)
		self.set_shader_input('scale_multipliers',self.scales)
		self.set_shader_input('player_position', self.game.player.position)

	def update(self):
		self.set_shader_input('player_position', self.game.player.position)

class FoliageManager:
	def __init__(self, game):
		self.game = game
		self.tree_spawners = []
		self.big_tree_spawners = []
		self.mushroom_spawners = []
		
		for i in range(31):
			self.tree_spawners.append(FoliageSpawner(self.game, 0, i, load_model(f"assets/models/tree{i}")))
		for i in range(23):
			self.big_tree_spawners.append(FoliageSpawner(self.game, 1, i, load_model(f"assets/models/big_tree{i}")))
		for i in range(6):
			self.mushroom_spawners.append(FoliageSpawner(self.game, 2, i, load_model(f"assets/models/smallmushroom{i}")))
		self.spawners = [self.tree_spawners, self.big_tree_spawners, self.mushroom_spawners]

	def spawn_mushroom(self, position, scale, rotation):
		spawner = random.choice(self.mushroom_spawners)
		return spawner.spawn_entity(position, scale, rotation)

	def spawn_tree(self, position, scale, rotation):
		spawner = random.choice(self.tree_spawners)
		return spawner.spawn_entity(position, scale, rotation)

	def spawn_big_tree(self, position, scale, rotation):
		spawner = random.choice(self.big_tree_spawners)
		return spawner.spawn_entity(position, scale, rotation)

	def destroy_foliage(self, id):
		self.spawners[id.tind][id.sind].remove_entity(id.uid)

	def set_fog_distance(self, dist):
		self.fog_max = dist
		for s in self.tree_spawners: s.set_shader_input('fog_max', dist)
		for s in self.big_tree_spawners: s.set_shader_input('fog_max', dist)
		for s in self.mushroom_spawners: s.set_shader_input('fog_max', dist)



if __name__ == '__main__':
	from ursina.prefabs.first_person_controller import FirstPersonController
	from pathlib import Path
	import os
	app = Ursina(vsync=False)
	app.map_scale = 100
	app.player = FirstPersonController(game=app, y=2)
	app.player.cursor.color = color.clear
	# app.player = dummy_player()
	# app.radius = 1
	foliage = FoliageManager(app)
	# camera = EditorCamera()
	ground = Entity(model='plane', texture='grass', scale=2*app.map_scale)
	ground.collider = ground.model
	app.run()