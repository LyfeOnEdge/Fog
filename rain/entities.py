from ursina import *
from .settings import settings
# from .lighting import LitObject, LitPointLight
import numpy as np
from .inventory import LaserWand, ZapWand, ImpWand
from .chunk_shader import chunk_shader

FAIRY_MAX_VELOCITY = 25
FAIRY_THRUST = 2.2
FAIRY_COOLDOWN = 0.4
FAIRY_MAX_HEIGHT = settings.terrain_y_scale*settings.map_scale

TIKI_NOTICE_RANGE = 2.2*settings.map_scale
TIKI_ATTACK_RANGE = 1*settings.map_scale
TIKI_MIN_RANGE = 0.75*settings.map_scale

# NORMAL = 0
# ALERT = 1
NORMAL = 0
FIRING_1 = 1
FIRING_2 = 2
FIRING_3 = 3
# FIRING_4 = 6
 
KEY_DROP_CHANCE = 1
STATE_CHANGE_DELAY = 1




class EntityManager:
	def __init__(self, game):
		self.game = game
		self.shootables_parent = Entity(name="shootablesparent")
		mouse.traverse_target = self.shootables_parent

		self.model_dict = {
			"wand" : load_model("assets/models/wand"),
			"wand_default" : load_model("assets/models/wand_default"),
			"wand_bolt" : load_model("assets/models/wand_bolt"),
			"wand_bolt_default" : load_model("assets/models/wand_bolt_default"),
			"wand_orb" : load_model("assets/models/wand_orb"),
			"chest": load_model("assets/models/chest_large"),
			"crate": load_model("assets/models/crate"),
			"crate_collider": load_model("assets/models/crate_collider")
		}

		self.tiki_models = {
			NORMAL : load_model("assets/models/tiki_angry"),
			FIRING_1 : load_model("assets/models/tiki_firing_1"),
			FIRING_2 : load_model("assets/models/tiki_firing_2"),
			FIRING_3 : load_model("assets/models/tiki_firing_3"),
		}
		self.active_entities = []
		self.fairies,self.enemies,self.pickups,self.projectiles,self.chests=[],[],[],[],[]

		points = np.array([Vec3(random.uniform(-10,10),random.uniform(-5,0),random.uniform(-10,10)) for i in range(160)])
		self.snow=Mesh(vertices=points, mode='point', thickness=8, render_points_in_3d=True)

	def get_snow_model(self):
		return deepcopy(self.snow)

	def spawn_tree(self, position, rotation, *args, **kwargs):
		return Tree(self.game, position, rotation, self.get_tree(), *args, **kwargs)
	def spawn_mushroom(self, position, rotation, *args, **kwargs):
		return Mushroom(self.game, position, rotation, self.get_mushroom(), *args, **kwargs)
	def spawn_fireball(self, position, target, *args, hostile = True, **kwargs):
		if hostile:
			ent = self.spawn_entity(FireBall, position, target, *args, texture="assets/textures/clouds.png", parent=self.shootables_parent, **kwargs)
		else:
			ent = self.spawn_entity(PlayerFireBall, position, target, *args, texture="assets/textures/clouds.png", parent=self.shootables_parent, **kwargs)
		return ent
	def spawn_chest(self, position, *args, **kwargs):
		ent = self.spawn_entity(Chest, position, *args, parent=self.shootables_parent, **kwargs)
		self.chests.append(ent)
		return ent
	def spawn_tiki(self, position, *args, **kwargs):
		ent = self.spawn_entity(Tiki, position, *args, parent=self.shootables_parent, **kwargs)
		ent.action_models = self.tiki_models
		self.enemies.append(ent)
		return ent
	def spawn_fairy(self, position, *args, **kwargs):
		ent = self.spawn_entity(Fairy, position, *args, parent=self.shootables_parent, **kwargs)
		self.fairies.append(ent)
		return ent
	def spawn_health(self, position, *args, **kwargs):
		print("Spawning health")
		ent = self.spawn_entity(HealthPickup, position, *args, **kwargs)
		self.pickups.append(ent)
		return ent
	def spawn_key(self, position, *args, **kwargs):
		print("Spawning key")
		ent = self.spawn_entity(KeyPickup, position, *args, **kwargs)
		self.pickups.append(ent)
		return ent
	def spawn_entity(self, clas, position, *args, **kwargs):
		ent = clas(self.game, *args, position=position, **kwargs)
		return ent

	def destroy(self, target, unload=False):
		lists = [self.active_entities, self.fairies, self.enemies, self.pickups, self.projectiles]
		for l in lists:
			if target in l:
				l.remove(target)
		pos = (int(target.position.x),int(target.position.y),int(target.position.z))
		ft = type(target)
		
		if not unload:
			if ft is Fairy:
				self.spawn_health(pos)
			if ft is Tiki:
				self.spawn_key(pos)
		target.destroy()

	def get_model(self, model_name):
		return deepcopy(self.model_dict.get(model_name))

class BaseShootable(Entity):
	def __init__(self, game, *args, max_hp = 100, **kwargs):
		Entity.__init__(self,*args,**kwargs)
		self.game = game
		self.action_models = None #Applied by entity manager
		self.health_bar = Entity(parent=self, y=3, model='cube', color=color.red)
		self.max_hp = max_hp
		self.hp = self.max_hp
		self.health_bar.scale = (self.hp / self.max_hp,.1,.1)
		self.state = 0
		self.velocity = Vec3(0,0,0)
		self.origin_y = -0.5
		self.scale = 1
		self.health_bar.enabled = False
	
	@property
	def hp(self):
		return self._hp

	@hp.setter
	def hp(self, value):
		self._hp = value
		if value <= 0:
			self.game.entity_manager.destroy(self)
			return

		self.health_bar.scale = (self.hp / self.max_hp,.1,.1)
		self.health_bar.alpha = 1

	def destroy(self): #Overwrite this
		destroy(self)

class Tiki(BaseShootable):
	def __init__(self, game, *args, **kwargs):
		BaseShootable.__init__(
			self,
			game,
			*args,
			model='assets/models/tiki_inverted',
			texture="assets/textures/tiki_texture.png",
			double_sided=False,
			color=color.rgba(120,100,100,50),
			max_hp = 40,
			**kwargs,
		)
		self.state = 0
		self.collider = Cylinder(height=2.5)
		self.next_state_change = time.time()
		self.t = 0
		self.scale *= 2

	def update(self):
		self.t += (time.dt + time.dt*random.uniform(0.0001,0.001))/3 #Random helps the tikis not move in lockstep
		# super().update()

		self.look_at(self.game.player)
		dis_to_player = distance_xz(self, self.game.player)
		if dis_to_player < TIKI_ATTACK_RANGE:
			if time.time() > self.next_state_change:
				self.state += 1
				if self.state == FIRING_3: self.attack()
				if self.state > FIRING_3:
					self.state = FIRING_1
				self.model = deepcopy(self.action_models[self.state])
				self.next_state_change = time.time() + STATE_CHANGE_DELAY + random.uniform(0,2.5)
		if dis_to_player > TIKI_NOTICE_RANGE:
			self.state = FIRING_1
		elif dis_to_player > TIKI_MIN_RANGE:
			self.position += 8*time.dt*Vec3(self.forward.x,0.5*self.forward.y,self.forward.z)

		self.velocity = self.velocity * 0.996
		self.velocity.y += math.sin(self.t*4)/200
		if random.uniform(0,1) > 0.99:
			x_ = 3.0 if random.uniform(0,1) > 0.5 else -3.0
			y_ = 8.0 if random.uniform(0,1) > 0.5 else -8.0
			z_ = 3.0 if random.uniform(0,1) > 0.5 else -3.0
			self.velocity += Vec3(x_*FAIRY_THRUST*random.uniform(0,1), y_*FAIRY_THRUST*random.uniform(0,1), z_*FAIRY_THRUST*random.uniform(0,1))*time.dt
			self.velocity[0] = max(min(self.velocity[0], FAIRY_MAX_VELOCITY),-FAIRY_MAX_VELOCITY)
			self.velocity[1] = max(min(self.velocity[1], FAIRY_MAX_VELOCITY),-FAIRY_MAX_VELOCITY)
			self.velocity[2] = max(min(self.velocity[2], FAIRY_MAX_VELOCITY),-FAIRY_MAX_VELOCITY)

		self.position += self.velocity
		# try:
		terrain_height = self.game.terrain_generator.get_heightmap(self.position[0]/self.game.map_scale,self.position[2]/self.game.map_scale)*self.game.terrain_y_scale+self.game.terrain_y_scale/10
		if self.position.y < terrain_height:
			self.position.y = terrain_height
			self.velocity.y = 1.01 * abs(self.velocity.y)
			self.position.y += FAIRY_THRUST
		elif self.position.y > terrain_height+FAIRY_MAX_HEIGHT:
			self.position.y = terrain_height+FAIRY_MAX_HEIGHT
			self.velocity.y = -0.25 * abs(self.velocity.y)
			self.position.y -= FAIRY_THRUST

		pos = min(max(self.position.y, terrain_height), terrain_height+FAIRY_MAX_HEIGHT)

		self.position.y = pos

	def attack(self):
		self.game.entity_manager.spawn_fireball(self.position,self.game.player.position+(0,0.5*self.game.player.height,0))

	def destroy(self): #Overwrite this
		destroy(self)

class Fairy(BaseShootable):
	def __init__(self, game, *args, **kwargs):
		m = load_model("assets/models/invert_orb")
		BaseShootable.__init__(
			self,
			game,
			*args,
			model=deepcopy(m),
			texture="assets/textures/clouds.png",
			double_sided=True,
			color=color.rgba(255,255,255,200),
			# ambientStrength=0.1,
			# smoothness = 120,
			# cubemapIntensity=0,
			**kwargs
		)
		self.collider = Cylinder(height=2.5)
		self.model = deepcopy(self.model)
		self.max_hp = 1
		self.hp = self.max_hp
		self.health_bar.enabled = False

		self.inner_sphere = Entity(
			model=deepcopy(m),
			texture="assets/textures/clouds2.png",
			double_sided=True,
			color=color.rgba(255,255,255,200),
		)
		
		self.center_sphere = Entity(
			model=deepcopy(load_model("assets/models/gem")),
			double_sided=True,
			color=color.rgba(200,0,0,60),
		)

		self.velocity = Vec3(0,0,0)
		self.origin_y = -0.5
		self.scale = 3.5
		self.inner_sphere.origin_y = -0.5
		self.inner_sphere.scale = 3
		self.center_sphere.scale = 3
		self.t = 0


	def update(self):
		# super().update()
		self.t += time.dt + random.uniform(0.0001,0.0003)
		self.velocity = self.velocity * 0.996
		self.velocity.y += math.sin(self.t)/2000
		if random.uniform(0,1) > 0.99:
			x_ = 3.0 if random.uniform(0,1) > 0.5 else -3.0
			y_ = 0.9 if random.uniform(0,1) > 0.7 else -3.0
			z_ = 3.0 if random.uniform(0,1) > 0.5 else -3.0
			self.velocity += Vec3(x_*FAIRY_THRUST*random.uniform(0,1), y_*FAIRY_THRUST*random.uniform(0,1), z_*FAIRY_THRUST*random.uniform(0,1))*time.dt
			self.velocity[0] = max(min(self.velocity[0], FAIRY_MAX_VELOCITY),-FAIRY_MAX_VELOCITY)
			self.velocity[1] = max(min(self.velocity[1], FAIRY_MAX_VELOCITY),-FAIRY_MAX_VELOCITY)
			self.velocity[2] = max(min(self.velocity[2], FAIRY_MAX_VELOCITY),-FAIRY_MAX_VELOCITY)

		self.position += self.velocity
		# try:
		terrain_height = self.game.terrain_generator.get_heightmap(self.position[0]/self.game.map_scale,self.position[2]/self.game.map_scale)*self.game.terrain_y_scale+self.game.terrain_y_scale/10
		if self.position.y < terrain_height:
			self.position.y = terrain_height
			self.velocity.y = 1.01 * abs(self.velocity.y)
			self.position.y += FAIRY_THRUST
		elif self.position.y > terrain_height+FAIRY_MAX_HEIGHT:
			self.position.y = terrain_height+FAIRY_MAX_HEIGHT
			self.velocity.y = -0.25 * abs(self.velocity.y)
			self.position.y -= FAIRY_THRUST

		pos = min(max(self.position.y, terrain_height), terrain_height+FAIRY_MAX_HEIGHT)
		self.rotation_y += 600*time.dt
		self.inner_sphere.rotation_y -= 720*time.dt

		self.position.y = pos
		self.inner_sphere.position = self.position
		self.center_sphere.position = self.position - (0,-0.5*self.scale_y,0)
		self.center_sphere.rotation_y = -720*self.t

	def destroy(self):
		destroy(self.inner_sphere)
		destroy(self.center_sphere)
		destroy(self)
		
class BaseLitEntity(Entity):
	def __init__(self, game, position, rotation, model, *args, color=color.rgb(180,150,120), texture='assets/textures/tree_texture.png', **kwargs):
		self.game = game
		Entity.__init__(
			self,
			*args,
			position=position,
			rotation=rotation,
			model=model,
			scale_y=1,
			texture=texture,
			color=color,
			**kwargs
		)

class BaseTerrainElement(Entity):
	def __init__(self, game, *args, **kwargs):
		self.game = game
		Entity.__init__(self, *args, texture = 'assets/textures/tree_texture.png', **kwargs)

class Tree(BaseTerrainElement):
	def __init__(self, game, *args, **kwargs):
		kwargs['model'] = game.entity_manager.get_tree()
		kwargs['color'] = color.rgb(180,150,120)
		BaseTerrainElement.__init__(self, game, *args, **kwargs)

class BigTree(BaseTerrainElement):
	def __init__(self, game, *args, **kwargs):
		kwargs['model'] = game.entity_manager.get_big_tree()
		kwargs['color'] = color.rgb(180,150,120)
		BaseTerrainElement.__init__(self, game, *args, **kwargs)
		self.scale *= 2

class Mushroom(BaseTerrainElement):
	def __init__(self, game, *args, **kwargs):
		kwargs['model'] = game.entity_manager.get_mushroom()
		kwargs['color'] = color.rgb(180,150,120)
		BaseTerrainElement.__init__(self, game, *args, **kwargs)

#This class is a trimmed version of terrain.py that takes a numpy array directly rather than an image
class HeightMesh(Mesh):
	def __init__(self, heightmap):
		heightmap = np.swapaxes(heightmap,0,1)
		self.vertices, self.triangles, self.uvs, self.normals = list(), list(), list(), list()
		lhm = len(heightmap)
		l=lhm-1
		i = 0
		for z in range(lhm):
			for x in range(lhm):
				self.vertices.append(Vec3(x/l, heightmap[x][z], z/l))
				self.uvs.append((x/l, z/l))
				if x > 0 and z > 0:
					self.triangles.append((i, i-1, i-l-2, i-l-1))
					if x < l-1 and z < l-1:
						rl = heightmap[x+1][z] - heightmap[x-1][z]
						fb = heightmap[x][z+1] - heightmap[x][z-1]
						self.normals.append(Vec3(rl, 1, fb).normalized())
					else:
						self.normals.append(Vec3(0,1,0))
				else:
					self.normals.append(Vec3(0,1,0))

				i += 1
		super().__init__(vertices=self.vertices, triangles=self.triangles, uvs=self.uvs, normals=self.normals)

#This entity is a base, when writing a game you would want to do stuff like spawning foliage etc when the chunk is initialized.
class Chunk(Entity):
	def __init__(self, game, chunk_id, heightmap, **kwargs):
		Entity.__init__(
				self,
				model=HeightMesh(heightmap),
				texture="assets/textures/grass.png",
				shader=chunk_shader,
				color=color.rgb(80,100,100),
				**kwargs,
			)
		self.game, self.chunk_id, self.heightmap = game, chunk_id, heightmap
		# self.collider = self.model
		if self.collider: del self.collider
		self.collider = None
		self.chunk_entities = []
		self.foliage_tokens = []
		lhm = len(self.heightmap)
		self.set_shader_input('mapdata', self.heightmap.copy().reshape(lhm*lhm).tolist())
		self.set_shader_input('base_position', self.position)
	# def save(self):
	# 	x,z = self.chunk_id
	# 	filename = self.game.saves_dir+f"{x}x{z}#{self.game.seed}.json"
	# 	with open(filename, "w+") as f:
	# 		json.dump({"heightmap":self.heightmap}, f)
	def update(self):
		self.set_shader_input('player_position', self.game.player.position)



class HealthPickup(Entity):
	def __init__(self, game, *args, **kwargs):
		self.game = game
		Entity.__init__(
			self,
			*args,
			model=deepcopy(load_model("assets/models/gem")),
			double_sided=True,
			color=color.rgba(255,100,100,100),
			# ambientStrength=0.1,
			# smoothness = 120,
			# cubemapIntensity=0,
			collider = 'box',
			scale=10,
			**kwargs
		)
		self.dt = 0
		self.origin_y = -0.5
		# self.light = LitPointLight(intensity=1, range = self.game.map_scale)
		# invoke(self.light.setColor, Vec3(0.5,0,0), delay=.0)

	def update(self):
		# super().update()

		if self.intersects(self.game.player).hit:
			self.game.player.hp += 10
			destroy(self)
			return

		self.dt += time.dt

		terrain_height = self.game.terrain_generator.get_heightmap(self.position[0]/self.game.map_scale,self.position[2]/self.game.map_scale)*self.game.terrain_y_scale+5
		if self.position[1] > terrain_height:
			self.position = Vec3(self.position[0],self.position[1] - time.dt*200,self.position[2])
		# self.light.setPosition(self.position)

		self.rotation_y = -220*self.dt

	def destroy(self):
		destroy(self)		

class KeyPickup(Entity):
	def __init__(self, game, *args, **kwargs):
		self.game = game
		Entity.__init__(
			self,
			*args,
			model=deepcopy(load_model("assets/models/key")),
			texture="assets/textures/key_texture",
			double_sided=True,
			color=color.rgba(255,255,255,255),
			collider = 'box',
			scale=2,
			**kwargs
		)
		self.dt = 0
		self.origin_y = -0.5

	def update(self):
		# super().update()

		if self.intersects(self.game.player).hit:
			self.game.player.keys += 1
			destroy(self)
			return

		self.dt += time.dt + random.uniform(0.00,0.04)

		terrain_height = self.game.terrain_generator.get_heightmap(self.position[0]/self.game.map_scale,self.position[2]/self.game.map_scale)*self.game.terrain_y_scale+5
		if self.position[1] > terrain_height:
			self.position = Vec3(self.position[0],self.position[1] - time.dt*200,self.position[2])

		self.rotation_y = 100*self.dt

	def destroy(self):
		destroy(self)


class FireBall(Entity):
	def __init__(self, game, target, *args, **kwargs):
		self.game = game
		Entity.__init__(
			self,
			*args,
			model='assets/models/invert_orb',
			double_sided=True,
			color=color.rgba(255,0,0,180),
			scale=0.25,
			**kwargs
		)
		self.scale *= 10
		self.collider='sphere'
		self.dt = 0
		self.look_at(target)
		self.forward_direction = self.forward
		self.origin.y = -0.5

	def update(self):
		if self.intersects(self.game.player).hit:
			self.game.player.hp -= 10
			destroy(self)
			return

		if distance(self, self.game.player) > self.game.map_scale*self.game.radius/2:
			self.game.entity_manager.destroy(self)
			return
		terrain_height = self.game.terrain_generator.get_heightmap(self.position[0]/self.game.map_scale,self.position[2]/self.game.map_scale)*self.game.terrain_y_scale-1.5
		if self.position[1] < terrain_height:
			self.game.entity_manager.destroy(self)
			return

		self.dt += time.dt
		self.position += self.forward_direction * time.dt * 60
		self.rotation_z = -1500*self.dt
		self.rotation_y = -1800*self.dt
		self.rotation_z = -1300*self.dt

	def destroy(self):
		destroy(self)


class PlayerFireBall(Entity):
	def __init__(self, game, target, *args, **kwargs):
		self.game = game
		Entity.__init__(
			self,
			*args,
			model='sphere',
			double_sided=True,
			color=color.rgba(40,40,150,255),
			scale=0.25,
			**kwargs
		)
		self.collider = 'sphere'
		self.scale *= 10
		self.dt = 0
		self.look_at(target)
		self.forward_direction = self.forward
		self.origin.y = -0.5

	def update(self):
		# super().update()
		for e in self.game.entity_manager.enemies:
			if self.intersects(e).hit:
				print("Hit")
				e.hp -= 10
				e.blink(color.red)
				e.health_bar.enabled = True
				destroy(self)
				return
		for e in self.game.entity_manager.fairies:
			if self.intersects(e).hit:
				e.hp -= 10
				destroy(self)
				return

		if distance(self, self.game.player) > self.game.map_scale*self.game.radius/2:
			self.game.entity_manager.destroy(self)
			return
		terrain_height = self.game.terrain_generator.get_heightmap(self.position[0]/self.game.map_scale,self.position[2]/self.game.map_scale)*self.game.terrain_y_scale-1.5
		if self.position[1] < terrain_height:
			self.game.entity_manager.destroy(self)
			return

		self.dt += time.dt
		self.position += self.forward_direction * time.dt * 50
		self.rotation_z = -1500*self.dt
		self.rotation_y = -1800*self.dt
		self.rotation_z = -1300*self.dt

	def destroy(self):
		# self.game.entity_manager.unassign_light(self.light)
		destroy(self)






# class Chest(Entity):
# 	def __init__(self, game, items=None, *args, **kwargs):
# 		mesh = Cube()
# 		Entity.__init__(self,*args,model=deepcopy(mesh),**kwargs)
# 		self.collider = deepcopy(mesh)
# 		self.game = game
# 		self.items = items or [LaserWand, ZapWand, ImpWand]
# 		# self.scale *= 5

# 	def destroy(self): #Overwrite this
# 		destroy(self)



class Chest(Entity):
	def __init__(self, game, items=None, *args, **kwargs):
		self.game = game
		Entity.__init__(
			self,
			*args,
			model=game.entity_manager.get_model('crate'),
			parent=game.entity_manager.shootables_parent,
			texture="assets/textures/wand_texture.png",
			color=color.rgba(24,15,0,255),
			**kwargs
		)
		self.collider = game.entity_manager.get_model('crate')
		self.scale *= 5
		self.origin.y = -0.5
		self.items = items or [LaserWand, ZapWand, ImpWand]
	def update(self):
		pass

	def destroy(self):
		destroy(self)