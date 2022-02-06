from ursina import *
from PIL import Image
from numpy import uint8, asarray

class MiniMap(Entity):
	def __init__(self, game):
		self.game = game
		self.image = None
		Entity.__init__(self,
				name='minimap',
				model="quad",
				texture="white_cube",
				parent=camera.ui,
				scale=0.25,
				color=color.rgba(255,255,255,255),
				position = (0.725,0.35),
			)
		self.z -=0.1

		self.minimap_frame = Entity(
				name='minimap_frame',
				model="quad",
				texture="assets/textures/map_frame.png",
				parent=self,
				scale=1,
				color=color.white,
				position = (0,0)
			)
		self.minimap_frame.z -=0.1

		self.minimap_cursor = Entity(
				name='minimap_cursor',
				model="quad",
				texture="assets/textures/minimap_cursor.png",
				parent=self,
				scale=0.4,
				origin = (0,0),
				color=color.white,
				position = (0,0)
			)
		self.minimap_cursor.z -=0.1

		self.minimap_needs_update = True

	def update_minimap(self, data):
		self.texture = Texture(Image.fromarray(data).convert("RGBA"))
		self.minimap_cursor.rotation_z = self.game.player.rotation_y

	def rotation_update(self):
		self.minimap_cursor.rotation_z = self.game.player.rotation_y

	def disable(self):
		self.visible = False
		for c in self.children:
			c.visible = False

	def enable(self):
		self.visible = True
		for c in self.children:
			c.visible = True