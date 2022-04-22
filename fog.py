from ursina import *
from ursina.prefabs.health_bar import HealthBar #Used for loading screen
from rain import settings, EntityManager, MiniMap, \
	AudioHandler, MeshWalker, SnowCloud, \
	generate_snow_shader, WorldLoader, generate_deformation_shader, \
	WORLD_TYPES, translate_image, multiply_image, sample_chunk
import os, json, time, random
import numpy as np
import numba

class GameWithWorldLoading(Ursina):
	def __init__(self,*args,**kwargs):
		self.start = time.time()
		self.current_world_number = 0
		self.game_seed = random.randint(1,9999999999)
		self.settings = settings
		self.seed = self.game_seed
		super().__init__(*args, **kwargs)
		self.entity_manager = EntityManager(self)
		
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

		self.current_world = WorldLoader(self, WORLD_TYPES[0])
		self.current_world.load()
		self.player = MeshWalker(self, speed=settings.player_speed, height=settings.player_height, origin_y=-.5)
		self.apply_world_settings(self.current_world)
		self.audio_handler = AudioHandler()
		
		self.test_entity = Entity(model='assets/models/monkae', shader=generate_deformation_shader(self.current_world, 2, 0.01), position=(400,30,400), scale=1, color=color.rgb(20,13,0))

	def toggle_screen_border(self):
		self.screen_border.enabled = not self.screen_border.enabled

	def transition_worlds(self):
		self.current_world_number += 1
		self.entity_manager.clear_scene()
		self.current_world.unload()
		choice = WORLD_TYPES[self.current_world_number % len(WORLD_TYPES)]
		self.current_world = WorldLoader(self, choice)
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
				sample_chunk(x0, x1, z0, z1, image, tile.heightmap)
		self.map.update_minimap(translate_image(multiply_image(image)))
		self.map_needs_update = False

	def update(self):
		self.test_entity.set_shader_input('shadertime', time.time()-self.start)
		self.current_world.update()
		if self.current_world.loaded and not self.current_world.chunks_to_load and self.map_needs_update:
			self.do_update()
		else:
			self.map.rotation_update()

	def do_cutscene(self):
		pass

if __name__ == "__main__":
	app = GameWithWorldLoading(vsync=False)
	window.exit_button.enabled = False
	window.center_on_screen()
	update = app.update
	app.run()