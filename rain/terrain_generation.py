from opensimplex import OpenSimplex
import numpy as np
import numba

class TerrainGenerator:
	def __init__(self, game):
		self.game = game
		print(f"Using seed {self.game.seed}")
		print("Using Open Simplex")
		self.generator = OpenSimplex(seed=(self.game.seed)).noise2
		self.generator2 = OpenSimplex(seed=(self.game.seed+7)).noise2
		self.generator3 = OpenSimplex(seed=(self.game.seed+13)).noise2
		self.generator4 = OpenSimplex(seed=(self.game.seed+19)).noise2
		self.array_generator = OpenSimplex(seed=(self.game.seed)).noise2array
		self.array_generator2 = OpenSimplex(seed=(self.game.seed+7)).noise2array
		self.array_generator3 = OpenSimplex(seed=(self.game.seed+13)).noise2array
		self.array_generator4 = OpenSimplex(seed=(self.game.seed+19)).noise2array

	def get_heightmap(self,x,z):
		height = self.generator(x,z) 
		height = height + self.generator2(x*self.game.settings.second_generator_scale,z*self.game.settings.second_generator_scale) * self.game.settings.second_generator_weight
		height = height + self.generator3(x*self.game.settings.third_generator_scale,z*self.game.settings.third_generator_scale) * self.game.settings.third_generator_weight
		height = height + self.generator4(x*self.game.settings.fourth_generator_scale,z*self.game.settings.fourth_generator_scale) * self.game.settings.fourth_generator_weight
		return height

	def get_chunk_heightmap(self,x,z):
		z_values = np.linspace(z, z+1, self.game.settings.chunk_divisions+1, endpoint=True)
		z_values = np.repeat(z_values,self.game.settings.chunk_divisions+1,axis=0)
		x_values = np.linspace(x, x+1, self.game.settings.chunk_divisions+1, endpoint=True)
		x_values = np.hstack((x_values, ) * (self.game.settings.chunk_divisions+1))
		out = self.array_generator(x_values,z_values).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
		out2 = self.array_generator2(x_values*self.game.settings.second_generator_scale,z_values*self.game.settings.second_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
		out3 = self.array_generator3(x_values*self.game.settings.third_generator_scale,z_values*self.game.settings.third_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
		out4 = self.array_generator4(x_values*self.game.settings.fourth_generator_scale,z_values*self.game.settings.fourth_generator_scale).reshape(self.game.settings.chunk_divisions+1,self.game.settings.chunk_divisions+1)
		return out + (out2 * self.game.settings.second_generator_weight) + (out3 * self.game.settings.third_generator_weight) + (out4 * self.game.settings.fourth_generator_weight)

if __name__ == "__main__":
	# from time import perf_counter
	from settings import settings
	class dummy_game:
		def __init__(self):
			self.seed = 15
			self.settings = settings

	game = dummy_game()
	CHUNKS = 10
	chunk_divisions = game.settings.chunk_divisions

	generator = TerrainGenerator(game)
	image = np.zeros((chunk_divisions*(CHUNKS+1),chunk_divisions*(CHUNKS+1)), dtype=float)
	for z in range(0,CHUNKS):
		for x in range(0,CHUNKS):
			image[z*chunk_divisions:(z+1)*chunk_divisions,x*chunk_divisions:(x+1)*chunk_divisions] = generator.get_chunk_heightmap(x,z)[:-1,:-1]
			
	import json
	with open("minimap_test_data.json", 'w+') as f:
		json.dump(image.tolist(), f)
