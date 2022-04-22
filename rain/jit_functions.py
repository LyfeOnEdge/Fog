import numpy as np
import numba

@numba.jit(nopython=True)
def s_arr(arr_1, arr_2, weight):
	return arr_1 + (arr_2 * weight)

@numba.jit(nopython=True)
def make_rgba_from_luma(arr):
	out = np.full((arr.shape[0], arr.shape[1], 4), 255, dtype=np.uint8)
	out[:, :, 0] = arr
	out[:, :, 1] = arr
	out[:, :, 2] = arr
	return out

@numba.jit(nopython=True)
def translate_image(image):
	return np.swapaxes(image,0,1)

@numba.jit(nopython=True)
def multiply_image(image):
	return image*255

@numba.jit(nopython=True)
def sample_chunk(x0, x1, z0, z1, dest, src):
	dest[int(z0):int(z1),int(x0):int(x1)] = src[1::2,1::2]