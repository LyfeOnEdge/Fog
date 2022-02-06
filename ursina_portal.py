from ursina import *



class Game(Ursina):
	def __init__(self, *args, **kwargs):
		Ursina.__init__(self, *args, **kwargs)
		self.map = Entity(self, model="portalmap")





game = Game()

game.run()