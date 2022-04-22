from ursina import *
from .settings import settings
from .shadergen import generate_chunk_shader
from .sky import RotatingSkybox
from .foliage import FoliageManager
from .terrain_generation import TerrainGenerator
from .chunk import Chunk

class world_defaults:
	def __init__(self):
		self.seed = 0
		self.radius = settings.render_distance
		self.terrain_scale = settings.terrain_x_z_scale
		self.terrain_y_scale = settings.terrain_y_scale
		self.map_scale = settings.map_scale
		self.fog_density = (0,self.map_scale*(self.radius-0.5))
		self.fog_color = color.rgba(120,120,120,255)
		self.color = color.rgba(200,200,200,255)
		self.foliage_color = color.rgba(40,20,20,255)
		self.generator_scale = 1
		self.second_generator_scale = 4
		self.second_generator_weight =  0.3
		self.third_generator_scale = 0.05
		self.third_generator_weight =  8
		self.fourth_generator_scale = 0.3
		self.fourth_generator_weight =  5
		self.chunk_divisions = settings.chunk_divisions
		self.overlay_alpha_vector = 1
		self.snow_height = 100
		self.sky_color = color.rgba(50,50,50,255)
		#Entity Spawning
		self.min_number_entities_per_chunk = 7
		self.max_number_entities_per_chunk = 25
		self.portal_spawn_ceil = 0.01
		self.mushroom_spawn_ceil = 0.4
		self.tree_spawn_ceil = 0.65
		self.big_tree_spawn_ceil = 1
		self.moon_enabled = False
		self.max_enemies = 20
		self.light_angle = Vec3(1.3,1.3,1.3)
		self.ambient_light_level = 0.5
		self.ground_breathes = False

class snow_world(world_defaults):
	def __init__(self):
		world_defaults.__init__(self)
		self.fog_color = color.rgba(120,120,120,255)
		self.color = color.rgba(200,200,200,255)
		self.foliage_color = color.rgba(120,120,120,255)

class dark_world(world_defaults):
	def __init__(self):
		world_defaults.__init__(self)
		self.fog_color = color.rgba(120,120,120,255)
		self.color = color.rgba(6,8,5,255)
		self.foliage_color = color.rgba(5,6,4,255)
		self.ambient_light_level = 0.3
		self.light_angle = Vec3(0,0,1.9)


class default_world(world_defaults):
	def __init__(self):
		world_defaults.__init__(self)

class amplified_world(world_defaults):
	def __init__(self):
		world_defaults.__init__(self)
		self.terrain_y_scale *= 2

class flat_world(world_defaults):
	def __init__(self):
		world_defaults.__init__(self)
		self.terrain_y_scale = 0.0001
		self.fog_density = (0,-1)
		self.fog_color = color.rgba(120,120,120,255)
		self.overlay_alpha_vector = 0
		self.sky_color = color.rgba(80,100,115,255)
		self.foliage_color = color.rgba(60,50,40,255)
		self.color = color.rgba(30,63,20,255)
		self.min_number_entities_per_chunk = 4
		self.max_number_entities_per_chunk = 12
		self.portal_spawn_ceil = 0.01
		self.mushroom_spawn_ceil = 0.9
		self.tree_spawn_ceil = 0.96
		self.big_tree_spawn_ceil = 1.

class hills_world(world_defaults):
	def __init__(self):
		world_defaults.__init__(self)
		self.terrain_y_scale = 2
		self.fog_density = (0,-1)
		self.fog_color = color.rgba(120,120,120,255)
		self.overlay_alpha_vector = 0
		self.sky_color = color.rgba(80,100,115,255)
		self.foliage_color = color.rgba(60,50,40,255)
		self.color = color.rgba(30,63,20,255)
		self.min_number_entities_per_chunk = 4
		self.max_number_entities_per_chunk = 12
		self.portal_spawn_ceil = 0.01
		self.mushroom_spawn_ceil = 0.9
		self.tree_spawn_ceil = 0.96
		self.big_tree_spawn_ceil = 1.
		self.ambient_light_level = 0.4
		
class hell_world(world_defaults):
	def __init__(self):
		world_defaults.__init__(self)
		self.fog_color = color.rgba(120,80,80,255)
		self.overlay_alpha_vector = 0
		self.sky_color = color.rgba(120,120,120,255)
		# self.color = color.rgba(80,40,40,255)
		self.color = color.rgba(40,20,20,255)
		self.foliage_color = color.rgba(40,20,20,255)
		self.min_number_entities_per_chunk = 4
		self.max_number_entities_per_chunk = 12
		self.portal_spawn_ceil = 0.01
		self.mushroom_spawn_ceil = 0.9
		self.tree_spawn_ceil = 0.96
		self.big_tree_spawn_ceil = 1.
		self.moon_enabled = True
		self.ground_breathes = True

WORLD_TYPES = [flat_world, dark_world, snow_world, hills_world, hell_world]

class WorldLoader(world_defaults):
	def __init__(self, game, worldtype=default_world, **kwargs):
		self.game = game
		worldtype.__init__(self)
		for key, value in kwargs.items():
			setattr(self, key, value)
		self.start = time.time()
		##Chunkloading
		self.chunks_to_load = []
		self.loaded = {} # loaded chunks
		self.last_chunk = None #Last place chunkload occured
		self.tick = 0
	
		#Only update chunk shaders if player has moved
		self.last_player_position = None

		#Calculate once
		self.siz = 1/self.chunk_divisions
		self.siz_map_scale = self.siz*self.map_scale
		self.div_size = 1/(self.chunk_divisions+1)
		self.inverse_div_size = 1/self.div_size
		self.y_scale = self.map_scale*self.terrain_y_scale
		self.divisions_over_map_scale = self.chunk_divisions/self.map_scale
		self.divisions_less_1 = self.chunk_divisions-1
		self.radius_less_one = self.radius-1
		self.chunk_shader = generate_chunk_shader(self)

	def load(self): #Must be called before calling update()
		self.sky = RotatingSkybox(self)
		self.foliage_manager = FoliageManager(self)
		self.terrain_generator = TerrainGenerator(self)
		
	def get_chunk_id_from_position(self,x,z):#Takes an x/z position and returns a chunk id
		return int(floor(x/self.map_scale)),int(floor(z/self.map_scale))
	def get_cell_id_from_offset(self,x,z):#Takes an offset from a tile origin and calculates what tile cell it falls into
		return int(x*self.divisions_over_map_scale),int(z*self.divisions_over_map_scale)

	def update(self): #update which chunks are loaded
		if not self.game.current_world is self: return
		self.game.entity_manager.update()
		self.update_shader_inputs()

		self.tick += 1
		self.sky.update()
		current = self.get_chunk_id_from_position(self.game.player.position.x, self.game.player.position.z)
		if current == self.last_chunk:	#Check if chunk updates are needed
			if self.chunks_to_load and not self.tick % 2: self._load_chunk(self.chunks_to_load.pop())
			return #Don't update if in same chunk as last update
		needed_chunk_ids = [] #List of chunks that should currently be loaded
		for z in range(int(current[1]-self.radius),int(current[1]+self.radius)):
			for x in range(int(current[0]-self.radius),int(current[0]+self.radius)):
				needed_chunk_ids.append((x,z))
		for cid in list(self.loaded.keys()): #Remove unneeded chunks
			if cid not in needed_chunk_ids:
				chunk = self.loaded.pop(cid)
				for f in chunk.foliage_tokens:
					self.foliage_manager.destroy_foliage(f)
				for e in chunk.chunk_entities:
					destroy(e)
				chunk.model = None
				destroy(chunk)
				print(f"Unloaded chunk {cid}")
		current_chunk_ids = list(self.loaded.keys())
		for chunk_id in self.chunks_to_load.copy():
			if not chunk_id in needed_chunk_ids:
				self.chunks_to_load.remove(chunk_id)
		for chunk_id in needed_chunk_ids: #Show the needed chunks
			if not chunk_id in current_chunk_ids:
				self.chunks_to_load.append(chunk_id)
		self.last_chunk = current #Update last rendered chunk to prevent unneeded re-draws
		self.game.map_needs_update = True

	def update_shader_inputs(self):
		# self.light_angle = Vec3(math.pi*math.sin(3*time.dt/100.),math.pi*math.sin(7*time.dt/100.),math.pi*math.sin(13*time.dt/100.))
		shadertime = time.time() - self.start
		if not self.tick % 2:
			for c in self.loaded:
				self.loaded[c].set_shader_input('player_position', self.game.player.position)
				self.loaded[c].set_shader_input('light_angle', self.light_angle)
				self.loaded[c].set_shader_input('shadertime', shadertime)
			self.foliage_manager.update_shaders()

	def _load_chunk(self, chunk_id):
		if chunk_id in self.loaded: return
		x,z=chunk_id
		heightmap = []
		self.loaded[chunk_id] = c = Chunk(self, chunk_id, self.chunk_shader)
		num_entities = int(random.uniform(self.min_number_entities_per_chunk,self.max_number_entities_per_chunk))
		
		x_map_scale = x*self.map_scale
		z_map_scale = z*self.map_scale
		
		taken_positions = []
		for i in range(num_entities): 
			while True:
				_x = int(random.uniform(0,self.divisions_less_1))
				_z =int(random.uniform(0,self.divisions_less_1))
				if not [_x, _z] in taken_positions:
					taken_positions.append([_x, _z])
					break
			
			pos = Vec3(x_map_scale+_x*self.siz_map_scale,(self.terrain_generator.get_heightmap(x+_x*self.siz,z+_z*self.siz))*self.terrain_y_scale*self.map_scale,z_map_scale+_z*self.siz_map_scale)
			rotation = -self.get_shader_angle_at_position(pos[0], pos[2])/3

			val = random.uniform(0,1)
			if val < self.portal_spawn_ceil:
				self.foliage_manager.portal_spawner.spawn_portal(pos, scale=Vec3(10))
			elif val < self.mushroom_spawn_ceil:
				pos.z -= 4*math.sin(math.radians(-rotation[1]))
				pos.x -= 4*math.sin(math.radians(-rotation[2]))
				pos.y -= 1
				c.foliage_tokens.append(self.foliage_manager.spawn_mushroom(pos, Vec3(random.uniform(.2,4)), rotation))
			elif val < self.tree_spawn_ceil:
				pos.z -= 8*math.sin(math.radians(-rotation[1]))
				pos.x -= 8*math.sin(math.radians(-rotation[2]))
				pos.y -= 3
				c.foliage_tokens.append(self.foliage_manager.spawn_tree(pos, Vec3(random.uniform(6.0,10.0)), rotation))
			elif val < self.big_tree_spawn_ceil:
				pos.z -= 10*math.sin(math.radians(-rotation[1]))
				pos.x -= 10*math.sin(math.radians(-rotation[2]))
				pos.y -= 5
				c.foliage_tokens.append(self.foliage_manager.spawn_big_tree(pos, Vec3(random.uniform(1,5)), rotation))

		# if len(self.game.entity_manager.enemies) < self.max_enemies:
		# 	if random.uniform(0,1) > 0.8:
		# 		while True:
		# 			_x = int(random.uniform(0,self.divisions_less_1))
		# 			_z = int(random.uniform(0,self.divisions_less_1))
		# 			if not [_x, _z] in taken_positions:
		# 				taken_positions.append([_x, _z])
		# 				break
		# 		pos = Vec3(x_map_scale+_x*self.siz_map_scale,(self.terrain_generator.get_heightmap(x+_x*self.siz,z+_z*self.siz))*self.terrain_y_scale*self.map_scale,z_map_scale+_z*self.siz_map_scale)
		# 		self.game.entity_manager.spawn_tiki(position=pos, scale = 12)

		print(f"Loaded chunk {chunk_id}")

	def get_shader_angle_at_position(self,x,z):
		cx, cz = int(floor(x/self.map_scale)),int(floor(z/self.map_scale))
		cell_x, cell_z = int((x-cx*self.map_scale)*self.divisions_over_map_scale),int((z-cz*self.map_scale)*self.divisions_over_map_scale)
		tile = self.get_tile_by_id((cx,cz))
		height = tile.heightmap[cell_z][cell_x]
		height_x = tile.heightmap[cell_z][cell_x+1]
		height_z = tile.heightmap[cell_z+1][cell_x]
		angle_x = math.degrees(math.atan2((height_z-height)*self.y_scale,self.inverse_div_size))
		angle_z = math.degrees(math.atan2((height_x-height)*self.y_scale,self.inverse_div_size))
		return Vec3(angle_z,0,angle_x)

	def get_tile_by_id(self, chunk_id):
		return self.loaded[chunk_id]

	def unload(self):
		self.sky.destroy()
		self.chunks_to_load = []
		for c in list(self.loaded.keys()):
			chunk = self.loaded.pop(c)
			self.foliage_manager.destroy()
			for e in chunk.chunk_entities: destroy(e)
			destroy(chunk)
			print(f"Unloaded chunk {c}")
		self.game.map_needs_update = True