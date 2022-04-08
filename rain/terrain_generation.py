from opensimplex import OpenSimplex
import numpy as np
import numba

@numba.jit(nopython=True)
def s_arr(arr_1, arr_2, weight):
	return arr_1 + (arr_2 * weight)

@numba.jit(nopython=True)
def s_all(arr_1, arr_2, arr_2_w, arr_3, arr_3_w, arr_4, arr_4_w, cw):
	return (((arr_1 + (arr_2 * arr_2_w) + (arr_3 * arr_3_w) + (arr_4 * arr_4_w)) / cw) + 1.) / 2.

@numba.jit(nopython=True)
def scale_all(arr1, arr2, m_1, m_2, m_3, m_4):
	return arr1 * m_1, arr2 * m_1, arr1 * m_2, arr2 * m_2, arr1 * m_3, arr2 * m_3, arr1 * m_4, arr2 * m_4,

class TerrainGenerator:
	def __init__(self, world):
		self.world = world
		seed = self.world.seed
		print(f"Using seed {seed}")
		print("Using Open Simplex")
		self.generator = OpenSimplex(seed=(seed)).noise2
		self.generator2 = OpenSimplex(seed=(seed+7)).noise2
		self.generator3 = OpenSimplex(seed=(seed+13)).noise2
		self.generator4 = OpenSimplex(seed=(seed+19)).noise2
		self.array_generator = OpenSimplex(seed=(seed)).noise2array
		self.array_generator2 = OpenSimplex(seed=(seed+7)).noise2array
		self.array_generator3 = OpenSimplex(seed=(seed+13)).noise2array
		self.array_generator4 = OpenSimplex(seed=(seed+19)).noise2array
		self.combined_weight = 1+self.world.second_generator_weight+self.world.third_generator_weight+self.world.fourth_generator_weight
		self.divisions = self.world.chunk_divisions+1
	def get_heightmap(self,x,z):
		height = self.generator(x*self.world.generator_scale,z*self.world.generator_scale)
		height = height + self.generator2(x*self.world.second_generator_scale,z*self.world.second_generator_scale) * self.world.second_generator_weight
		height = height + self.generator3(x*self.world.third_generator_scale,z*self.world.third_generator_scale) * self.world.third_generator_weight
		height = height + self.generator4(x*self.world.fourth_generator_scale,z*self.world.fourth_generator_scale) * self.world.fourth_generator_weight
		return ((height / self.combined_weight)+1)/2.

	def get_chunk_heightmap(self,x_values,z_values):
		x1, z1, x2, z2, x3, z3, x4, z4 = scale_all(x_values, z_values, self.world.generator_scale, self.world.second_generator_scale, self.world.third_generator_scale, self.world.fourth_generator_scale)
		out = self.array_generator(x1,z1).reshape(self.divisions,self.divisions)
		out2 = self.array_generator2(x2,z2).reshape(self.divisions,self.divisions)
		out3 = self.array_generator3(x3,z3).reshape(self.divisions,self.divisions)
		out4 = self.array_generator4(x4,z4).reshape(self.divisions,self.divisions)
		return s_all(out, out2, self.world.second_generator_weight, out3, self.world.third_generator_weight, out4, self.world.fourth_generator_weight, self.combined_weight)

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