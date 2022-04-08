from ursina import *
from panda3d.core import OmniBoundingVolume, LQuaterniond, LVecBase3d
from .shadergen import generate_foliage_shader, generate_portal_shader

if __name__ == '__main__':
	from settings import settings
else:
	from .settings import settings

class PortalSpawner(Entity):
	def __init__(self, world, model, shader, *args, **kwargs):
		Entity.__init__(self, *args, model=model, texture="assets/textures/tree_texture", **kwargs)
		self.world = world
		self.instances = []
		self._uid = 0
		self.model.uvs = [(v[0],v[1]) for v in self.model.vertices]
		# self.model.generate()
		self.shader = shader
		self.setInstanceCount(0)
		self.start = time.time()
		self.positions, self.scales, self.quaternions = [], [], []
		self.node().setBounds(OmniBoundingVolume())
		self.node().setFinal(True)
		self.set_shader_input('player_position', Vec3(0))
		self.set_shader_input('shadertime', 0)

	def get_uid(self):
		self._uid += 1
		return self._uid - 1

	def spawn_portal(self, position = Vec3(0,0,0), scale = Vec3(1), rotation = Vec3(0,0,0)):
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
		return uid

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
		self.set_shader_input('shadertime', time.time()-self.start)
		self.set_shader_input('position_offsets', self.positions)
		self.set_shader_input('rotation_offsets', self.quaternions)
		self.set_shader_input('scale_multipliers',self.scales)
		self.set_shader_input('player_position', self.world.game.player.position)

	def update_shadertime(self):
		self.set_shader_input('shadertime', time.time()-self.start)

class FoliageIdentifier:
	__slots__ = ['tind', 'sind', 'uid']
	def __init__(self, typeindex, spawnerindex, uid):
		self.tind = typeindex
		self.sind = spawnerindex
		self.uid = uid

class FoliageSpawner(Entity):
	def __init__(self, world, typeindex, spawnerindex, model, shader, *args, **kwargs):
		Entity.__init__(self, *args, model=model, texture="assets/textures/tree_texture", **kwargs)
		self.world = world
		self.typeindex, self.spawnerindex = typeindex, spawnerindex
		self.instances = []
		self._uid = 0
		self.model.uvs = [(v[0],v[1]) for v in self.model.vertices]
		# self.model.generate()
		self.shader = shader
		self.setInstanceCount(0)
		self.positions, self.scales, self.quaternions = [], [], []
		self.node().setBounds(OmniBoundingVolume())
		self.node().setFinal(True)
		self.set_shader_input('player_position', Vec3(0))
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
		self.set_shader_input('player_position', self.world.game.player.position)

class FoliageManager:
	def __init__(self, world):
		self.world = world
		self.tree_spawners = []
		self.big_tree_spawners = []
		self.mushroom_spawners = []
		portal_shader = generate_portal_shader(self.world)
		self.portal_spawner = PortalSpawner(self.world, load_model('assets/models/portal2'), portal_shader)
		foliage_shader = generate_foliage_shader(self.world)
		for i in range(31): self.tree_spawners.append(FoliageSpawner(self.world, 0, i, load_model(f"assets/models/tree{i}"), foliage_shader))
		for i in range(23): self.big_tree_spawners.append(FoliageSpawner(self.world, 1, i, load_model(f"assets/models/big_tree{i}"), foliage_shader))
		for i in range(6): self.mushroom_spawners.append(FoliageSpawner(self.world, 2, i, load_model(f"assets/models/smallmushroom{i}"), foliage_shader))
		self.spawners = [self.tree_spawners, self.big_tree_spawners, self.mushroom_spawners]
		self.tick = 0

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

	def update_shaders(self):
		if not self.tick % 2:
			for _s in self.spawners:
				for s in _s:
					if s.instances:
						s.set_shader_input('player_position', self.world.game.player.position)
		self.portal_spawner.update_shadertime()
		self.tick += 1

# if __name__ == '__main__':
# 	from ursina.prefabs.first_person_controller import FirstPersonController
# 	from pathlib import Path
# 	import os
# 	app = Ursina(vsync=False)
# 	app.map_scale = 100
# 	app.player = FirstPersonController(game=app, y=2)
# 	app.player.cursor.color = color.clear
# 	# app.player = dummy_player()
# 	# app.radius = 1
# 	foliage = FoliageManager(app)
# 	# camera = EditorCamera()
# 	ground = Entity(model='plane', texture='grass', scale=2*app.map_scale)
# 	ground.collider = ground.model
# 	app.run()