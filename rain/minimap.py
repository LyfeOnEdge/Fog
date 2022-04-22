from ursina import *
from PIL import Image
from .jit_functions import make_rgba_from_luma

class MiniMap(Entity):
	def __init__(self, game):
		self.game = game
		self.image = None
		self.first_update = True
		self.minimap_needs_update = True
		Entity.__init__(self,
				name='minimap',
				model="quad",
				texture="white_cube",
				parent=camera.ui,
				scale=0.25,
				color=color.rgba(255,255,255,255),
				position = (0.725,0.35),
				texture_scale=(1,-1,1),
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

	def update_minimap(self, data):
		if self.first_update:
			self.first_update = False
			data = make_rgba_from_luma(data) #Convert to rgba, faster than pil when using numba
			#Set up texture, will be drawn correctly but we have texture
			#scaling reversed in the y direction so it will be drawn flipped
			self.texture = Texture(Image.fromarray(data)) 
			#Redraw texture the fast way upside-down...
			self.texture._texture.setRamImageAs(data.tobytes(),"RGBA") 
		else:
			#Subsequent draws are always upside-down but since the y texture scale is -1 it is corrected 
			self.texture._texture.setRamImageAs(make_rgba_from_luma(data).tobytes(),"RGBA")
		self.rotation_update()

	def rotation_update(self): self.minimap_cursor.rotation_z = self.game.player.rotation_y

	def disable(self):
		self.visible = False
		for c in self.children:
			c.visible = False

	def enable(self):
		self.visible = True
		for c in self.children:
			c.visible = True