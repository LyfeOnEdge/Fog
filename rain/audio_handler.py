from ursina import Audio

class AudioHandler:
	def __init__(self): #Currently just loops the background track, sfx planned
		self.background = Audio('assets/audio/background', volume=0.2, loop=True,loops=99999)
		self.wand_sound = Audio('assets/audio/wand_distorted', volume=1, loop=False,autoplay=False,pitch=1)