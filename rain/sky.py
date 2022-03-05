from ursina import *
import time

class rotating_skybox:
	def __init__(self, game):
		self.game = game
		# self.sky = Sky(
		# 	model="sphere",
		# 	double_sided=True,
		# 	texture = "assets/textures/skybox.jpg",
		# 	rotation = (0, 90, 0),
		# 	eternal=True,
		# 	color=color.rgb(3,3,3),
		# 	enabled=False
		# )
		# self.clouds = Sky(
		# 	model="sphere",
		# 	double_sided=True,
		# 	texture = "assets/textures/clouds2.png",
		# 	rotation = (0, 90, 0),
		# 	eternal=True,
		# 	color=color.rgba(150,150,150,70),
		# 	scale = self.sky.scale * 0.675
		# )

		self.walls = Entity(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/fogwall.png",
			scale = self.game.map_scale*(self.game.radius)*2,
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
			scale= self.walls.scale * 0.6
		)
		self.clouds4.scale *= 0.75
		
	def update(self):
		self.walls.position = self.game.player.position
		# self.clouds.rotation_y = self.game.player.position
		# self.clouds2.rotation_y = self.game.player.position
		self.clouds3.rotation_y = self.game.player.position
		self.clouds4.rotation_y = self.game.player.position

		# self.clouds.rotation_y += 1.2 * time.dt
		# self.clouds2.rotation_y -= 2.4 * time.dt
		# self.clouds2.rotation_x -= 0.1 * time.dt
		self.clouds3.rotation_y += 3 * time.dt
		self.clouds3.rotation_x -= 0.25 * time.dt
		self.clouds4.rotation_y -= 2 * time.dt

		