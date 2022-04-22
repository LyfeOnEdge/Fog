"""A module to get a lot of random numbers quickly using opensimplex"""
from opensimplex import OpenSimplex
import numpy as np
import numba

class TerrainGenerator:
#A deterministic random number generator, can generate large array of pseudo-random values quickly
	def __init__(self, seed):
		self.seed = 0
		self.counter = 1
		self.big_number_to_multiply_by = 314159 #Ensures numbers are chosen far enough apart from the simplex noise 
		self.generator = OpenSimplex(seed=(seed)).noise2 #single number generator
		self.array_generator = OpenSimplex(seed=(seed)).noise2array #number array generator
	
	def get_random_array_unsigned_scalar(self, count):

	def get_random_array_signed_scalar(self, count):

	def get_random_array_unsigned_scaled_float(self, max, count):

	def get_random_array_signed_scaled_float(self, max, count):

	def get_random_array_unsigned_scaled_int(self, max, count):

	def get_random_array_signed_scaled_int(self, max, count): 


# def get_random_number_unsigned_scalar(self):
# 	res = self.generator(self.counter,self.big_number_to_multiply_by*self.counter)
# 	self.counter+=1
# 	return abs(res)
# def get_random_number_signed_scalar(self):
# 	res = self.generator(self.counter,self.big_number_to_multiply_by*self.counter)
# 	self.counter+=1
# 	return res
# def get_random_number_unsigned_scaled_float(self, max_value):
# 	res = self.generator(self.counter,self.big_number_to_multiply_by*self.counter)
# 	self.counter+=1
# 	return abs(res*max_value)
# def get_random_number_signed_scaled_float(self, max_value):
# 	res = self.generator(self.counter,self.big_number_to_multiply_by*self.counter)
# 	res = res
# 	self.counter+=1
# 	return res*max_value
# def get_random_number_unsigned_scaled_int(self, max_value):
# 	res = self.generator(self.counter,self.big_number_to_multiply_by*self.counter)
# 	res = res
# 	self.counter+=1
# 	return int(abs(res*max_value))
# def get_random_number_signed_scaled_int(self, max_value):
# 	res = self.generator(self.counter,self.big_number_to_multiply_by*self.counter)
# 	res = res
# 	self.counter+=1
# 	return int(res*max_value)

if __name__ == "__main__":
	class dummy_world:
		def __init__(self):
			self.seed = 15
			from settings import settings
			self.settings = settings
			self.chunk_divisions = 500 
	world = dummy_world()

	indicies = np.arange(world.chunk_divisions+1)
	xs, zs = np.meshgrid(indicies, indicies)
	generator = TerrainGenerator(world)
	for i in range(300):
		generator.get_chunk_heightmap(xs.ravel(),zs.ravel())