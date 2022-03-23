from ursina import *
from rain import combine_targets, EntityManager, rotating_skybox, \
	settings, chunk, TerrainGenerator, Mushroom, Tree, MiniMap, \
	AudioHandler, HotBar, Inventory, MeshWalker, Chest, BigTree, \
	SnowCloud, FoliageManager
# from ursina.shaders import instancing_shader
import os, json, time, random
import numpy as np
import numba


MAX_FAIRIES = 10
MAX_GHOSTS = 25
MAX_PER_TILE = 4
GHOST_SPAWN_CHANCE = 0.1
FAIRY_SPAWN_CHANCE = 0.05


MIN_ENTITIES = 25
MAX_ENTITIES = 40

class GameWithChunkloading(Ursina):
	def __init__(self,*args,**kwargs):
		self.game_seed = random.randint(1,9999999999)
		self.settings = settings
		self.radius = settings.render_distance
		self.radius_less_one = self.radius-1
		self.use_perlin = settings.use_perlin
		self.terrain_scale = settings.terrain_x_z_scale
		self.terrain_y_scale = settings.terrain_y_scale
		self.map_scale = settings.map_scale
		self.half_map_scale = self.map_scale/2 #Calc once
		self.seed = self.game_seed
		super().__init__(*args, **kwargs)
		
		#Handles mobs and drops
		self.entity_manager = EntityManager(self)
		self.sky = rotating_skybox(self)
		
		#Handles Foliage
		self.foliage = FoliageManager(self)

		#UI/UX
		self.map = MiniMap(self)
		self.map_needs_update = False
		self.audio_handler = AudioHandler()
		self.screen_border = Entity( #Overlay to add to spooky vibe
			parent=camera.ui,
			texture="assets/textures/screen_border.png",
			color=color.white,
			model="quad",
			scale=(camera.aspect_ratio, 1),
			position = (0,0,0),
		)

		##Chunkloading
		self.load_tick = 0
		self.terrain_generator = TerrainGenerator(self)
		self.chunks_to_load = []
		self.chunk_entities_to_load = {}
		self.loaded = {} # loaded chunks
		self.last_chunk = None #Last place chunkload occured
		
		self.player = MeshWalker(self, speed=settings.player_speed, height=settings.player_height, origin_y=-.5)
		scene.fog_density = (0,self.map_scale*(self.radius-0.5))
		scene.fog_color = color.rgba(120,120,120,255)

	def get_chunk_id_from_position(self,x,z):#Takes an x/z position and returns a chunk id
		return int(floor(x/self.map_scale)),int(floor(z/self.map_scale))
	def get_cell_id_from_offset(self,x,z):#Takes an offset from a tile origin and calculates what tile cell it falls into
		return int((x*self.settings.chunk_divisions)/self.map_scale),int((z*self.settings.chunk_divisions)/self.map_scale)

	def update(self): #update which chunks are loaded
		self.update_heightmap_image()
		self.sky.update()
		current = self.get_chunk_id_from_position(self.player.position.x, self.player.position.z)
		if current == self.last_chunk:	#Check if chunk updates are needed
			if self.chunks_to_load:
				self._load_chunk(self.chunks_to_load.pop())

			return #Don't update if in same chunk as last update
		needed_chunk_ids = [] #List of chunks that should currently be loaded
		for z in range(int(current[1]-self.radius),int(current[1]+self.radius)):
			for x in range(int(current[0]-self.radius),int(current[0]+self.radius)):
				needed_chunk_ids.append((x,z))
		for cid in list(self.loaded.keys()): #Remove unneeded chunks
			if cid not in needed_chunk_ids:
				chunk = self.loaded.pop(cid)
				for f in chunk.foliage_tokens:
					# print("Removing foliage")
					self.foliage.destroy_foliage(f)
				for e in chunk.chunk_entities:
					destroy(e)
				destroy(chunk)
				print(f"Unloaded chunk {cid}")
		current_chunk_ids = list(self.loaded.keys())
		for chunk_id in needed_chunk_ids: #Show the needed chunks
			if not chunk_id in current_chunk_ids:
				self.chunks_to_load.append(chunk_id)
		self.last_chunk = current #Update last rendered chunk to prevent unneeded re-draws
		self.map_needs_update = True

	def _load_chunk(self, chunk_id):
		x,z=chunk_id
		heightmap = []
		heightmap = self.terrain_generator.get_chunk_heightmap(x,z)
		c = chunk(
			self,
			chunk_id = chunk_id,
			heightmap=heightmap,
			scale=self.map_scale,
			scale_y=self.terrain_y_scale,
			position=(x*self.map_scale,0,z*self.map_scale)
			)
		self.loaded[chunk_id] = c
		num_entities = random.randint(MIN_ENTITIES,MAX_ENTITIES)
		siz = 1/self.settings.chunk_divisions
		siz_map_scale = siz*self.map_scale
		x_map_scale = x*self.map_scale
		z_map_scale = z*self.map_scale
		half_map_scale = 0.5*self.map_scale
		divisions_less_1 = self.settings.chunk_divisions-4
		taken_positions = []
		for i in range(num_entities): 
			while True:
				_x = random.randint(0,divisions_less_1)
				_z = random.randint(0,divisions_less_1)
				if not [_x, _z] in taken_positions:
					taken_positions.append([_x, _z])
					break
			
			pos = Vec3(x_map_scale+_x*siz_map_scale,(self.terrain_generator.get_heightmap(x+_x*siz,z+_z*siz))*self.terrain_y_scale,z_map_scale+_z*siz_map_scale)
			rotation = -self.get_shader_angle_at_position(pos[0], pos[2])/3
			pos.z -= 16*math.sin(math.radians(-rotation[1]))
			pos.x -= 16*math.sin(math.radians(-rotation[2]))
			pos.y -= 5

			val = random.uniform(0,1)
			# ent = None
			if val < 0.05:
				continue
				ent = Chest
			elif val < 0.4:
				c.foliage_tokens.append(self.foliage.spawn_mushroom(pos, Vec3(random.uniform(10,25)), Vec3(180)+rotation))
			elif val < 0.8:
				c.foliage_tokens.append(self.foliage.spawn_tree(pos, Vec3(random.uniform(30,60)), Vec3(180)+rotation))
			elif val < 1:
				c.foliage_tokens.append(self.foliage.spawn_big_tree(pos, Vec3(random.uniform(3,15)), Vec3(180)))
				pass
			# if ent:
			# 	terrain_elements.append((ent, {'position':pos, 'rotation':rotation}))
		print(f"Loaded chunk {chunk_id}")

	def generate_chunk_heightmap(self,x,z):
		return self.terrain_generator.get_chunk_heightmap(x,z)

	# @numba.jit()
	def update_heightmap_image(self): #Pulls from loaded chunks to make one heightmap | Fast version with 1/4th resolution
		if self.loaded and not self.chunks_to_load and self.map_needs_update:
			current = self.last_chunk
			image = np.zeros((self.settings.chunk_divisions * self.radius_less_one,self.settings.chunk_divisions * self.radius_less_one), dtype=float)
			min_z = int(current[1]-self.radius)+1
			min_x = int(current[0]-self.radius)+1
			for z in reversed(range(min_z,int(current[1]+self.radius)-1)):
				for x in reversed(range(min_x,int(current[0]+self.radius)-1)):
					tile = self.loaded.get((x,z))
					x0 = (x-min_x-2)*self.settings.chunk_divisions/2 + self.settings.chunk_divisions
					x1 = x0 + int(self.settings.chunk_divisions/2)
					z0 = (z-min_z-2)*self.settings.chunk_divisions/2 + self.settings.chunk_divisions
					z1 = z0 + int(self.settings.chunk_divisions/2)
					image[int(z0):int(z1),int(x0):int(x1)] = tile.heightmap[1::2,1::2]
			self.map_needs_update = False
			image += 10
			image *= (255/30) #Scale heightmap to proper color
			image = np.swapaxes(image,0,1)
			self.map.update_minimap(image)
		else:
			self.map.rotation_update()

	def get_shader_angle_at_position(self,x,z):
		cx,cz = self.get_chunk_id_from_position(x,z)
		cell_x, cell_z = self.get_cell_id_from_offset(x-cx*self.map_scale,z-cz*self.map_scale)
		tile = self.get_tile_by_id((cx,cz))
		height = tile.heightmap[cell_z][cell_x]
		height_x = tile.heightmap[cell_z][cell_x+1]
		height_z = tile.heightmap[cell_z+1][cell_x]
		angle_x = math.degrees(math.atan2(height-height_z,1/(self.settings.chunk_divisions+1)))
		angle_z = math.degrees(math.atan2(height-height_x,1/(self.settings.chunk_divisions+1)))
		return Vec3(-angle_z,0,-angle_x)

	def get_terrain_angle_at_position(self,x,z):
		cx,cz = self.get_chunk_id_from_position(x,z)
		cell_x, cell_z = self.get_cell_id_from_offset(x-cx*self.map_scale,z-cz*self.map_scale)
		tile = self.get_tile_by_id((cx,cz))
		height = tile.heightmap[cell_z][cell_x]
		height_x = tile.heightmap[cell_z][cell_x+1]
		height_z = tile.heightmap[cell_z+1][cell_x]
		angle_x = math.degrees(math.atan2(height-height_z,1/(self.settings.chunk_divisions+1)))
		angle_z = math.degrees(math.atan2(height-height_x,1/(self.settings.chunk_divisions+1)))
		return Vec3(angle_x,0,angle_z)

	def get_terrain_height_at_position(self,x,z): #Fast get height method from already generated data, chunk must be loaded though
		cx,cz = self.get_chunk_id_from_position(x,z)
		cell_x, cell_z = self.get_cell_id_from_offset(x-cx*self.map_scale,z-cz*self.map_scale)
		tile = self.get_tile_by_id((cx,cz))
		return tile.heightmap[cell_z][cell_x]

	def get_tile_by_id(self, chunk_id):
		return self.loaded[chunk_id]

if __name__ == "__main__":
	app = GameWithChunkloading(vsync=False)
	window.exit_button.enabled = False
	window.center_on_screen()
	update = app.update
	app.run()