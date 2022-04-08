from ursina import *
from ursina.prefabs.health_bar import HealthBar #Used for loading screen
from rain import EntityManager, rotating_skybox, \
	settings, Chunk, TerrainGenerator, Mushroom, Tree, MiniMap, \
	AudioHandler, HotBar, Inventory, MeshWalker, Chest, BigTree, \
	SnowCloud, FoliageManager, CoreEntityManager, PortalSpawner, \
	generate_chunk_shader, generate_snow_shader, generate_portal_shader
# from ursina.shaders import instancing_shader
import os, json, time, random
import numpy as np
import numba

MAX_FAIRIES = 10
MAX_GHOSTS = 25
MAX_PER_TILE = 4
GHOST_SPAWN_CHANCE = 0.1
FAIRY_SPAWN_CHANCE = 0.05


MIN_ENTITIES = 7
MAX_ENTITIES = 15

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
		self.generator_scale = settings.generator_scale
		self.second_generator_scale = settings.second_generator_scale
		self.second_generator_weight =  settings.second_generator_weight
		self.third_generator_scale = settings.third_generator_scale
		self.third_generator_weight =  settings.third_generator_weight
		self.fourth_generator_scale = settings.fourth_generator_scale
		self.fourth_generator_weight =  settings.fourth_generator_weight
		self.chunk_divisions = settings.chunk_divisions
		self.overlay_alpha_vector = 1
		self.snow_height = 100

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
		self.terrain_y_scale = 1
		self.fog_density = (0,0)
		self.fog_color = color.rgba(120,120,120,255)
		self.overlay_alpha_vector = 1
		

class WorldLoader(world_defaults):
	def __init__(self, game, worldtype=default_world, **kwargs):
		self.game = game
		worldtype.__init__(self)
		for key, value in kwargs.items():
			setattr(self, key, value)

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

	def load(self):
		self.sky = rotating_skybox(self)
		# self.foliage_manager = self.game.shared_foliage_manager
		self.foliage_manager = FoliageManager(self)
		
		self.terrain_generator = TerrainGenerator(self)
		self.entity_manager = self.game.shared_entity_manager

	def test_angle_calc(self):
		for x in range(0, 100):
			for z in range(0,100):
				self.get_shader_angle_at_position(x,z)

	def get_chunk_id_from_position(self,x,z):#Takes an x/z position and returns a chunk id
		return int(floor(x/self.map_scale)),int(floor(z/self.map_scale))
	def get_cell_id_from_offset(self,x,z):#Takes an offset from a tile origin and calculates what tile cell it falls into
		return int(x*self.divisions_over_map_scale),int(z*self.divisions_over_map_scale)

	def update(self): #update which chunks are loaded
		if not self.game.current_world is self: return

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
		#Update chunk shader inputs
		if not self.last_player_position or not self.last_player_position == self.game.player.position:
			if not self.tick % 2:
				for c in self.loaded:
					self.loaded[c].set_shader_input('player_position', self.game.player.position)
				self.foliage_manager.update_shaders()

	def _load_chunk(self, chunk_id):
		if chunk_id in self.loaded: return
		x,z=chunk_id
		heightmap = []
		c = Chunk(self, chunk_id = chunk_id, shader = generate_chunk_shader(self))
		print(c.texture)
		self.loaded[chunk_id] = c
		num_entities = random.randint(MIN_ENTITIES,MAX_ENTITIES)
		
		x_map_scale = x*self.map_scale
		z_map_scale = z*self.map_scale
		
		taken_positions = []
		for i in range(num_entities): 
			while True:
				_x = random.randint(0,self.divisions_less_1)
				_z = random.randint(0,self.divisions_less_1)
				if not [_x, _z] in taken_positions:
					taken_positions.append([_x, _z])
					break
			
			pos = Vec3(x_map_scale+_x*self.siz_map_scale,(self.terrain_generator.get_heightmap(x+_x*self.siz,z+_z*self.siz))*self.terrain_y_scale*self.map_scale,z_map_scale+_z*self.siz_map_scale)
			rotation = -self.get_shader_angle_at_position(pos[0], pos[2])/3

			val = random.uniform(0,1)
			ent = None
			if val < 0.01:
				self.foliage_manager.portal_spawner.spawn_portal(pos, scale=Vec3(10))
			elif val < 0.4:
				pos.z -= 4*math.sin(math.radians(-rotation[1]))
				pos.x -= 4*math.sin(math.radians(-rotation[2]))
				pos.y -= 1
				c.foliage_tokens.append(self.foliage_manager.spawn_mushroom(pos, Vec3(random.uniform(.2,4)), Vec3(180)+rotation))
			elif val < 0.65:
				pos.z -= 8*math.sin(math.radians(-rotation[1]))
				pos.x -= 8*math.sin(math.radians(-rotation[2]))
				pos.y -= 3
				c.foliage_tokens.append(self.foliage_manager.spawn_tree(pos, Vec3(random.uniform(6.0,10.0)), Vec3(180)+rotation))
			elif val < 1:
				pos.z -= 10*math.sin(math.radians(-rotation[1]))
				pos.x -= 10*math.sin(math.radians(-rotation[2]))
				pos.y -= 5
				c.foliage_tokens.append(self.foliage_manager.spawn_big_tree(pos, Vec3(random.uniform(1,5)), Vec3(180)+rotation/2))
			# if ent:
				# c.chunk_entities.append(ent(c.world, position=pos, rotation=Vec3(0,0,0), scale =10))

		print(f"Loaded chunk {chunk_id}")

	def get_shader_angle_at_position(self,x,z): #0.1057 - > 0.0710
		# cx,cz = self.get_chunk_id_from_position(x,z)
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
			for f in chunk.foliage_tokens:
				self.foliage_manager.destroy_foliage(f)
			for e in chunk.chunk_entities:
				destroy(e)
			destroy(chunk)
			print(f"Unloaded chunk {c}")
		self.game.map_needs_update = True

# class LoadingWheel(Entity):
#     def __init__(self, **kwargs):
#         super().__init__()
#         self.parent = camera.ui
#         self.point = Entity(parent=self, model=Circle(24, mode='point', thickness=.03), color=color.light_gray, y=.75, scale=2, texture='circle')
#         self.point2 = Entity(parent=self, model=Circle(12, mode='point', thickness=.03), color=color.light_gray, y=.75, scale=1, texture='circle')

#         self.scale = .025
#         self.text_entity = Text(world_parent=self, text='loading...', origin=(0,1.5), color=color.light_gray)
#         self.y = -.25

#         self.bg = Entity(parent=self, model='quad', scale_x=camera.aspect_ratio, color=color.black, z=1)
#         self.bg.scale *= 400

#         for key, value in kwargs.items():
#             setattr(self, key ,value)

#     def update(self):
#         self.point.rotation_y += 5
#         self.point2.rotation_y += 3


class GameWithWorldLoading(Ursina):
	def __init__(self,*args,**kwargs):
		self.game_seed = random.randint(1,9999999999)
		self.settings = settings
		self.seed = self.game_seed
		super().__init__(*args, **kwargs)
		# self.loading_screen = LoadingWheel(enabled=False)
		# self.loading_bar = HealthBar(max_value=100, value=0, position=(-.5,-.35,-2), scale_x=1, animation_duration=0.1, world_parent=self.loading_screen, bar_color=color.gray)
		self.entity_manager = CoreEntityManager(self)
		self.audio_handler = AudioHandler()
		# self.shared_foliage_manager = FoliageManager(self)
		self.shared_entity_manager = EntityManager(self)

		
		self.map = MiniMap(self)
		self.map_needs_update = False

		self.screen_border = Entity( #Overlay to add to spooky vibe
			parent=camera.ui,
			texture="assets/textures/screen_border.png",
			color=color.white,
			model="quad",
			scale=(camera.aspect_ratio, 1),
			position = (0,0,0),
		)
		self.screen_border.enabled = True

		

		self.current_world = WorldLoader(self, default_world)
		self.current_world.load()
		self.next_world = WorldLoader(self, flat_world)
		self.next_world.seed *= 2

		self.snow = SnowCloud(game=self, scale=100, thickness=1, gravity=10, particle_color=color.white, shader = generate_snow_shader(self.current_world))
		# self.portal_spawner = PortalSpawner(self, 'assets/models/tree1', generate_portal_shader(self.current_world))

		self.player = MeshWalker(self, speed=settings.player_speed, height=settings.player_height, origin_y=-.5)

		self.apply_world_settings(self.current_world)

	def toggle_screen_border(self):
		self.screen_border.enabled = not self.screen_border.enabled

	def transition_worlds(self):
		self.shared_entity_manager.clear_scene()
		self.current_world.unload()
		self.current_world = self.next_world
		self.current_world.load()
		self.apply_world_settings(self.current_world)

	def apply_world_settings(self, world):
		scene.fog_density = world.fog_density
		scene.fog_color = world.fog_color
		if self.current_world.overlay_alpha_vector:
			self.screen_border.enabled = True
			self.screen_border.alpha = self.current_world.overlay_alpha_vector
		else:
			self.screen_border.enabled = False

	# def do_update(self):
	# 	current = self.current_world.last_chunk
	# 	sz = self.current_world.chunk_divisions * (self.current_world.radius - 1)
	# 	image = np.zeros((sz,sz), dtype=float)
	# 	min_z = int(current[1]-self.radius)+1
	# 	min_x = int(current[0]-self.radius)+1
	# 	for z in reversed(range(min_z,int(current[1]+self.radius)-1)):
	# 		for x in reversed(range(min_x,int(current[0]+self.radius)-1)):
	# 			tile = self.current_world.loaded.get((x,z))
	# 			x0 = (x-min_x-2)*self.current_world.chunk_divisions/2 + self.current_world.chunk_divisions
	# 			x1 = x0 + int(self.current_world.chunk_divisions/2)
	# 			z0 = (z-min_z-2)*self.current_world.chunk_divisions/2 + self.current_world.chunk_divisions
	# 			z1 = z0 + int(self.current_world.chunk_divisions/2)
	# 			image[int(z0):int(z1),int(x0):int(x1)] = tile.heightmap[1::2,1::2]
	# 	image *= 255 #Scale heightmap to proper color
	# 	image = np.swapaxes(image,0,1)
	# 	self.map.update_minimap(image)
	# 	self.map_needs_update = False

	def do_update(self):
		current = self.current_world.last_chunk
		sz = self.current_world.chunk_divisions * (self.current_world.radius - 1)
		image = np.zeros((sz,sz), dtype=float)
		min_z = int(current[1]-self.current_world.radius)+1
		min_x = int(current[0]-self.current_world.radius)+1
		for z in reversed(range(min_z,int(current[1]+self.current_world.radius)-1)):
			for x in reversed(range(min_x,int(current[0]+self.current_world.radius)-1)):
				tile = self.current_world.loaded.get((x,z))
				x0 = (x-min_x-2)*self.current_world.chunk_divisions/2 + self.current_world.chunk_divisions
				x1 = x0 + int(self.current_world.chunk_divisions/2)
				z0 = (z-min_z-2)*self.current_world.chunk_divisions/2 + self.current_world.chunk_divisions
				z1 = z0 + int(self.current_world.chunk_divisions/2)
				copy_chunk_image(x0, x1, z0, z1, image, tile.heightmap)
				# image[int(z0):int(z1),int(x0):int(x1)] = tile.heightmap[1::2,1::2]
		self.map.update_minimap(translate_image(multiply_image(image)))
		self.map_needs_update = False

	def update(self):
		self.current_world.update()
		if self.current_world.loaded and not self.current_world.chunks_to_load and self.map_needs_update:
			self.do_update()
		else:
			self.map.rotation_update()

	def do_cutscene(self):
		pass

@numba.jit(nopython=True)
def copy_chunk_image(x0, x1, z0, z1, image, heightmap):
	image[int(z0):int(z1),int(x0):int(x1)] = heightmap[1::2,1::2]

@numba.jit(nopython=True)
def translate_image(image):
	return np.swapaxes(image,0,1)

@numba.jit(nopython=True)
def multiply_image(image):
	return image*255

if __name__ == "__main__":
	app = GameWithWorldLoading(vsync=False)
	window.exit_button.enabled = False
	window.center_on_screen()
	update = app.update
	app.run()