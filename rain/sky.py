from ursina import *


class rotating_skybox:
	def __init__(self, game):
		self.game = game
		self.sky = Sky(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/skybox.jpg",
			rotation = (0, 90, 0),
			eternal=True,
			color=color.rgb(3,3,3),
			enabled=False
		)
		self.clouds = Sky(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/clouds2.png",
			rotation = (0, 90, 0),
			eternal=True,
			color=color.rgba(150,150,150,70)
		)
		self.clouds.scale *= 0.975
		self.clouds2 = Sky(
			model="sphere",
			double_sided=True,
			texture = "assets/textures/clouds.png",
			rotation = (0, 90, 0),
			eternal=True,
			color=color.rgba(150,150,150,60)
		)
		self.clouds2.scale *= 0.95
		self.walls = Entity(
			model="cube",
			double_sided=True,
			texture = "assets/textures/fogwall.png",
			scale = self.sky.scale*1.1,
			rotation = (0, 90, 0),
			color=color.rgb(50,50,50)
		)
	def update(self):
		self.walls.position = self.game.player.position
		self.clouds.rotation_y += 0.02
		self.clouds2.rotation_y -= 0.015