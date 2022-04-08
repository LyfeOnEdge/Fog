from ursina import *
import time

class RotatingSkybox:
	def __init__(self, world):
		self.world = world

		self.walls = Entity(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/fogwall.png",
			scale = self.world.map_scale*(self.world.radius)*4,
			rotation = (0, 90, 0),
			color=color.rgb(50,50,50,255)
		)

		self.clouds2 = Sky(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/clouds.png",
			rotation = (0, 90, 0),
			eternal=True,
			color=color.rgba(150,150,150,30),
			scale = self.walls.scale * 0.8
		)
		self.clouds3 = Sky(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/clouds.png",
			rotation = (0, 90, 0),
			eternal=True,
			color=color.rgba(150,150,150,30),
			scale= self.walls.scale * 0.7
		)
		self.clouds4 = Sky(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/clouds.png",
			rotation = (0, 90, 0),
			eternal=True,
			color=color.rgba(150,150,150,30),
			scale= self.walls.scale * 0.45
		)
		self.clouds4.scale *= 0.75
		
	def update(self):
		self.walls.position = self.world.game.player.position
		# self.clouds.rotation_y = self.game.player.position
		# self.clouds2.rotation_y = self.game.player.position
		self.clouds3.rotation_y = self.world.game.player.position
		self.clouds4.rotation_y = self.world.game.player.position

		# self.clouds.rotation_y += 1.2 * time.dt
		# self.clouds2.rotation_y -= 2.4 * time.dt
		# self.clouds2.rotation_x -= 0.1 * time.dt
		self.clouds3.rotation_y += 3 * time.dt
		self.clouds3.rotation_x -= 0.25 * time.dt
		self.clouds4.rotation_y -= 2 * time.dt

	def destroy(self):
		destroy(self.walls)
		destroy(self.clouds2)
		destroy(self.clouds3)
		destroy(self.clouds4)
		del self
		