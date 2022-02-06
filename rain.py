from ursina import *
from rain import combine_targets, EntityManager, rotating_skybox, \
	settings, Chunk, TerrainGenerator, Mushroom, Tree, MiniMap, \
	AudioHandler, HotBar, Inventory, MeshWalker

import os, json, time, random
import numpy as np


MAX_FAIRIES = 10
MAX_GHOSTS = 25
MAX_PER_TILE = 2
GHOST_SPAWN_CHANCE = 0.1
FAIRY_SPAWN_CHANCE = 0.05

class GameWithChunkloading(Ursina):
	def __init__(self,*args,**kwargs):
		self.game_seed = random.randint(1,9999999999) #Random overwritten by kwargs
		self.settings = settings
		self.radius = settings.render_distance
		self.use_perlin = settings.use_perlin
		self.terrain_scale = settings.terrain_x_z_scale
		self.terrain_y_scale = settings.terrain_y_scale
		self.map_scale = settings.map_scale
		self.seed = self.game_seed
		super().__init__(*args, **kwargs)
		
		#Handles mobs and drops
		self.entity_manager = EntityManager(self)
		self.sky = rotating_skybox(self)
		
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
		self.terrain_generator = TerrainGenerator(self)
		self.chunks_to_load = []
		self.chunk_entities_to_load = {}
		self.loaded = {} # loaded chunks
		self.last_chunk = None #Last place chunkload occured
		

		self.player = MeshWalker(self, speed=200, origin_y=-.5)

		self.init_map()

		# for i in range(20):
		# 	x = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	z = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	y = self.terrain_generator.get_heightmap(x/self.map_scale,z/self.map_scale)*self.terrain_y_scale+1
		# 	self.entity_manager.spawn_fairy((x,y,z))

		# for i in range(20):
		# 	x = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	z = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	y = self.terrain_generator.get_heightmap(x/self.map_scale,z/self.map_scale)*self.terrain_y_scale+1
		# 	self.entity_manager.spawn_tiki((x,y,z))

		scene.fog_density = (150,self.map_scale*(self.radius-0.5))
		scene.fog_color = color.rgba(120,120,120,255)

	def init_map(self):
		self.update_chunks_rendered()
		while self.chunks_to_load: #Only load in one terrain chunk or terrain entity per frame
			self._load_new_chunk(self.chunks_to_load.pop(0))
		while self.chunk_entities_to_load:
			chunk_id = list(self.chunk_entities_to_load.keys())[0]
			if len(self.chunk_entities_to_load[chunk_id]) > 1:
				ent, kwargs = self.chunk_entities_to_load[chunk_id].pop()
				self._load_entity(chunk_id, ent, *[], **kwargs)
			else:
				c = self.chunk_entities_to_load.pop(chunk_id)
				if c:
					ent, kwargs = c[0]
					self._load_entity(chunk_id, ent, *[], **kwargs)
		self.update()
		
	def get_chunk_id_from_position(self,x,z):#Takes an x/z position and returns a chunk id
		return int(floor(x/self.map_scale)),int(floor(z/self.map_scale))
	def get_cell_id_from_offset(self,x,z):#Takes an offset from a tile origin and calculates what tile cell it falls into
		return int((x*self.settings.chunk_divisions)/self.map_scale),int((z*self.settings.chunk_divisions)/self.map_scale)

	def update(self): #update which chunks are loaded
		self.update_heightmap_image()
		self.sky.update()

		self.update_chunks_rendered()
		if self.chunks_to_load: #Only load in one terrain chunk or terrain entity per frame
			self._load_new_chunk(self.chunks_to_load.pop(0))
		elif self.chunk_entities_to_load:
			chunk_id = list(self.chunk_entities_to_load.keys())[0]
			if len(self.chunk_entities_to_load[chunk_id]) > 1:
				ent, kwargs = self.chunk_entities_to_load[chunk_id].pop()
				self._load_entity(chunk_id, ent, *[], **kwargs)
			else:
				c = self.chunk_entities_to_load.pop(chunk_id)
				if c:
					ent, kwargs = c[0]
					self._load_entity(chunk_id, ent, *[], **kwargs)

	def load_chunk_entities(self, chunk_id, chunk_entities_data):
		self.chunk_entities_to_load[chunk_id] = chunk_entities_data

	def _load_entity(self, chunk_id, ent, *args, **kwargs):
		position = kwargs.pop('position')
		rotation = kwargs.get('rotation')
		e = self.entity_manager.spawn_entity(ent, position, *args, **kwargs)
		e.z -= 16*math.sin(math.radians(rotation[0]))
		e.x -= 16*math.sin(math.radians(rotation[2]))
		e.scale_y = e.scale_y*random.uniform(0.8,1.5)
		e.scale = e.scale * random.uniform(0.8,5) * 5
		self.loaded[chunk_id].chunk_entities.append(e)

	def load_new_chunk(self, chunk_id):
		self.chunks_to_load.append(chunk_id)
	
	def _load_new_chunk(self, chunk_id):
		x,z=chunk_id
		heightmap = self.generate_chunk_heightmap(x,z)
		c = Chunk(
			self,
			chunk_id = chunk_id,
			heightmap=heightmap,
			scale=self.map_scale,
			scale_y=self.terrain_y_scale,
			position=(x*self.map_scale,0,z*self.map_scale)
		)
		self.loaded[chunk_id] = c
		siz = 1/self.settings.chunk_divisions
		
		terrain_elements = []
		for _x in range(self.settings.chunk_divisions):
			for _z in range(self.settings.chunk_divisions):
				if random.uniform(0,1) < 0.02:
					pos = (x*self.map_scale+_x*siz*self.map_scale,self.terrain_generator.get_heightmap(x+_x*siz,z+_z*siz)*self.terrain_y_scale,z*self.map_scale+_z*siz*self.map_scale)
					rotation = self.get_terrain_angle_at_position(pos[0],pos[2])/2
					if random.uniform(0,1) < 0.1:
						ent = Mushroom
					else:
						ent = Tree
					terrain_elements.append((ent, {'position':pos, 'rotation':rotation}))
		# c.chunk_entities.extend(terrain_elements)
		self.load_chunk_entities(chunk_id, terrain_elements)

		if len(self.entity_manager.enemies) < MAX_GHOSTS:
			if random.uniform(0,1) < GHOST_SPAWN_CHANCE:
				_x = random.uniform(0,self.settings.chunk_divisions)
				_z = random.uniform(0,self.settings.chunk_divisions)
				y = self.terrain_generator.get_heightmap(x/self.map_scale,z/self.map_scale)*self.terrain_y_scale+1
				self.entity_manager.spawn_tiki(((x+_x*siz)*self.map_scale,y,(z+_z*siz)*self.map_scale))

		if len(self.entity_manager.fairies) < MAX_FAIRIES:
			if random.uniform(0,1) < FAIRY_SPAWN_CHANCE:
				_x = random.uniform(0,self.settings.chunk_divisions)
				_z = random.uniform(0,self.settings.chunk_divisions)
				y = self.terrain_generator.get_heightmap(x/self.map_scale,z/self.map_scale)*self.terrain_y_scale+1
				self.entity_manager.spawn_fairy(((x+_x*siz)*self.map_scale,y,(z+_z*siz)*self.map_scale))

		# for i in range(20):
		# 	x = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	z = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	y = self.terrain_generator.get_heightmap(x/self.map_scale,z/self.map_scale)*self.terrain_y_scale+1
		# 	self.entity_manager.spawn_fairy((x,y,z))

		# for i in range(20):
		# 	x = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	z = random.uniform(self.map_scale*-0.5*self.radius,self.map_scale*0.5*self.radius)
		# 	y = self.terrain_generator.get_heightmap(x/self.map_scale,z/self.map_scale)*self.terrain_y_scale+1
		# 	self.entity_manager.spawn_tiki((x,y,z))

		print(f"Loaded chunk {chunk_id}")

	def update_chunks_rendered(self, force_load = False):
		current = self.get_chunk_id_from_position(self.player.position.x, self.player.position.z)
		if current == self.last_chunk:
			return False#Don't update if in same chunk as last update

		for e in self.entity_manager.enemies:
			if abs(distance_xz(e, self.player)) > self.map_scale * self.radius:
				self.entity_manager.destroy(e, unload = True)
		for e in self.entity_manager.fairies:
			if abs(distance_xz(e, self.player)) > self.map_scale * self.radius:
				self.entity_manager.destroy(e, unload = True)
		for e in self.entity_manager.pickups:
			if e:
				if abs(distance_xz(e, self.player)) > self.map_scale * self.radius:	
					self.entity_manager.destroy(e, unload = True)

		self.map_needs_update = True

		needed_chunk_ids = [] #List of chunks that should currently be loaded
		for z in range(int(current[1]-self.radius),int(current[1]+self.radius)):
			for x in range(int(current[0]-self.radius),int(current[0]+self.radius)):
				needed_chunk_ids.append((x,z))

		for c in list(self.loaded.keys()): #Remove unneeded chunks
			if c not in needed_chunk_ids:
				chunk = self.loaded.pop(c)
				for e in chunk.chunk_entities:
					destroy(e)
				destroy(chunk)
				print(f"Unloaded chunk {c}")

		current_chunk_ids = list(self.loaded.keys())
		for c in self.chunks_to_load: #Remove pending chunks that aren't needed
			if not c in needed_chunk_ids:
				self.chunks_to_load.remove(c)

		for c in list(self.chunk_entities_to_load.keys()): #Remove pending chunk entity loads that aren't needed
			if not c in needed_chunk_ids:
				self.chunk_entities_to_load.pop(c)

		for chunk_id in needed_chunk_ids: #Show the needed chunks
			if not chunk_id in current_chunk_ids and not chunk_id in self.chunks_to_load:
				self.load_new_chunk(chunk_id)
	
		self.last_chunk = current #Update last rendered chunk to prevent unneeded re-draws

	def generate_chunk_heightmap(self,x,z):
		heightmap = np.zeros((self.settings.chunk_divisions+1,self.settings.chunk_divisions+1), dtype=float)
		for _z in range(self.settings.chunk_divisions+1):
			for _x in range(self.settings.chunk_divisions+1):
				heightmap[_z][_x] = self.terrain_generator.get_heightmap(x+_x/self.settings.chunk_divisions,z+_z/self.settings.chunk_divisions)
		return heightmap

	def update_heightmap_image(self): #Pulls from loaded chunks to make one heightmap
		if self.loaded and not self.chunks_to_load and self.map_needs_update:
			current = self.last_chunk
			image = np.zeros((self.settings.chunk_divisions * self.radius * 2,self.settings.chunk_divisions * self.radius * 2+1), dtype=float)
			min_z = int(current[1]-self.radius)
			min_x = int(current[0]-self.radius)
			for z in range(min_z,int(current[1]+self.radius)):
				for x in range(min_x,int(current[0]+self.radius)):
					tile = self.loaded.get((x,z))
					x0 = (x-min_x-1)*self.settings.chunk_divisions + self.settings.chunk_divisions
					x1 = x0 + self.settings.chunk_divisions	
					z0 = (z-min_z-1)*self.settings.chunk_divisions + self.settings.chunk_divisions
					z1 = z0 + self.settings.chunk_divisions
					image[z0:z1,x0:x1] = tile.heightmap[1:,1:] + self.settings.num_generators
			self.map_needs_update = False
			image *= (255/(2*self.settings.num_generators)/1.5) #Scale heightmap to proper color
			image = np.swapaxes(image,0,1)
			self.map.update_minimap(image)
		else:
			self.map.rotation_update()

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
		for c in self.loaded:
			if c == chunk_id:
				return self.loaded[chunk_id]

if __name__ == "__main__":
	app = GameWithChunkloading(vsync=True)
	update = app.update
	app.run()