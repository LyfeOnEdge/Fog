from ursina import Audio

class AudioHandler:
	def __init__(self): #Currently just loops the background track, sfx planned
		self.background = Audio('assets/audio/background', volume=0.2, loop=True,loops=99999)