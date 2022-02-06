class TerrainGenerator:
	def __init__(self, game):
		self.game = game
		self.settings = game.settings

		print(f"Using seed {self.game.seed}")
		if self.settings.use_perlin:
			print("Using Perlin Noise")
			from perlin_noise import PerlinNoise
			self.generators = [PerlinNoise(seed=self.game.seed,octaves=self.settings.num_generators)]
		else:
			print("Using Open Simplex")
			from opensimplex import OpenSimplex
			self.generators = [OpenSimplex(seed=(self.game.seed + i)*(i+1)).noise2 for i in range(self.settings.num_generators)]

	def get_heightmap(self,x,z):#Get terrain y at a given unscaled x/z position
		pos = (x*self.settings.terrain_x_z_scale,z*self.settings.terrain_x_z_scale) #Get adjusted position in heightmap
		#Get the sum of the heights for all generators at a given position
		#If using perlin noise this is handled internally using 'octaves' option
		height = sum(g(pos) if self.settings.use_perlin else g(*pos) for g in self.generators)
		# if len(self.generators)>1: height /= len(self.generators) #scale output back to range of [-1...1]
		return height