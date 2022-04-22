from opensimplex import OpenSimplex
import numpy as np
import numba
import math
import random
from PIL import Image, ImageOps

@numba.jit(nopython=True)
def scale_all(arr1, arr2, m_2, m_3, m_4):
	return arr1 * m_2, arr2 * m_2, arr1 * m_3, arr2 * m_3, arr1 * m_4, arr2 * m_4,

@numba.jit(nopython=True)
def s_all(arr_1, arr_2, arr_2_w, arr_3, arr_3_w, arr_4, arr_4_w, cw):
	return (((arr_1 + (arr_2 * arr_2_w) + (arr_3 * arr_3_w) + (arr_4 * arr_4_w)) / cw) + 1.5) * 96.

class TextureGenerator:
	def __init__(
		self,
		width,
		height,
		second_generator_scale = 10,
		second_generator_weight = 3,
		third_generator_scale = 0.6,
		third_generator_weight = 0.3,
		fourth_generator_scale = 0.7,
		fourth_generator_weight = 0.3,
		):
		self.width = width
		self.height = height
		self.second_generator_scale = second_generator_scale
		self.second_generator_weight = second_generator_weight
		self.third_generator_scale = third_generator_scale
		self.third_generator_weight = third_generator_weight
		self.fourth_generator_scale = fourth_generator_scale
		self.fourth_generator_weight = fourth_generator_weight
		self.combined_weight = 1+self.second_generator_weight+self.third_generator_weight+self.fourth_generator_weight

	def get_texture(self,seed,scale = 40.,x_scale=1,y_scale=1):
		xs, ys = np.meshgrid(
			np.arange(self.height)/scale,
			np.arange(self.width)/scale
		)
		xs = xs.ravel() * x_scale
		ys = ys.ravel() * y_scale
		x2, y2, x3, y3, x4, y4 = scale_all(
			xs,
			ys,
			self.second_generator_scale,
			self.third_generator_scale,
			self.fourth_generator_scale
		)
		array_generator = OpenSimplex(seed=(seed)).noise2array
		array_generator2 = OpenSimplex(seed=(seed+7)).noise2array
		array_generator3 = OpenSimplex(seed=(seed+13)).noise2array
		array_generator4 = OpenSimplex(seed=(seed+19)).noise2array
		out = array_generator(xs,ys)
		out2 = array_generator2(x2,y2)
		out3 = array_generator3(x3,y3)
		out4 = array_generator4(x4,y4)
		out = s_all(
			out,
			out2,
			self.second_generator_weight,
			out3,
			self.third_generator_weight, 
			out4,
			self.fourth_generator_weight,
			self.combined_weight
		)
		return np.swapaxes(np.uint8(out.reshape(self.width,self.height)),0,1)

class BackgroundGenerator:
	def __init__(self):
		seed = random.randint(0,9999999)
		print(f"Using seed {seed}")
		print("Using Open Simplex")
		self.array_generator = OpenSimplex(seed=(seed)).noise2array

	def get_terrain_heightmap(self,x_values,depth=0):
		return (self.array_generator(np.full(x_values.shape,depth*0.1,dtype=np.float32),- x_values)+1.)/4.+0.4

if __name__ == "__main__":
	from PIL import Image, ImageFilter
	IMAGE_HEIGHT = 2000
	IMAGE_WIDTH = 2000
	SCALE = 0.005 #X scale of background curve
	BACKGROUND = (100,128,200,255)
	# FILL = (100,100,0,255)
	# FILL2 = (80,80,60,255)
	# FILL3 = (50,90,90,255)
	tex = TextureGenerator(IMAGE_WIDTH, IMAGE_HEIGHT)
	SKY_TEX = tex.get_texture(-1, x_scale=10)
	
	FILL = tex.get_texture(0)
	FILL_COLOR = np.asarray([255,255,255],dtype=np.float32)

	FILL2 = tex.get_texture(1)
	FILL_COLOR2 = np.asarray([127,127,127],dtype=np.float32)

	FILL3 = tex.get_texture(2)
	FILL_COLOR3 = np.asarray([63,63,63],dtype=np.float32)


	SUN_COLOR = (255,255,128,255)
	SUN_EDGE_COLOR = (230,97,35,255)
	ADD_SUN = True
	x_values = np.arange(IMAGE_WIDTH) * SCALE
	generator = BackgroundGenerator()
	heights = generator.get_terrain_heightmap(x_values)
	heights2 = generator.get_terrain_heightmap(x_values, 1)
	heights3 = generator.get_terrain_heightmap(x_values, 2)
	im = np.full((IMAGE_HEIGHT, IMAGE_WIDTH, 4),BACKGROUND,dtype=np.uint8)
	im[:,:,1] = SKY_TEX[:,:]
	im[:,:,3] = SKY_TEX[:,:]
	for x in range(IMAGE_WIDTH):
		height = int(heights[x]*IMAGE_HEIGHT*math.sin((x*math.pi)/IMAGE_WIDTH))
		if height:
			chunk = FILL[:height, x]
			chunk = chunk.repeat(3).reshape((chunk.shape[0],3))
			color_array = np.full(chunk.shape, FILL_COLOR, dtype=np.uint8)
			# print(color_array)
			# print(chunk)
			# print(chunk*color_array)
			im[:height, x, :3] = chunk * color_array

		shifted_x = (x+int(IMAGE_WIDTH/2))%IMAGE_WIDTH
		height2 = int(heights2[shifted_x]*IMAGE_HEIGHT*math.sin((shifted_x*math.pi)/IMAGE_WIDTH))
		if height2:
			chunk = FILL2[:height2, x]
			chunk = chunk.repeat(3).reshape((chunk.shape[0],3))
			color_array = np.full(chunk.shape, FILL_COLOR2, dtype=np.uint8)
			im[:height2, x, :3] = chunk * color_array
		
		shifted_x = (x+int(IMAGE_WIDTH/3))%IMAGE_WIDTH
		height3 = int(heights3[shifted_x]*IMAGE_HEIGHT*math.sin((shifted_x*math.pi)/IMAGE_WIDTH))
		if height3:
			chunk = FILL3[:height3, x]
			chunk = chunk.repeat(3).reshape((chunk.shape[0],3))
			color_array = np.full(chunk.shape, FILL_COLOR3, dtype=np.uint8)
			im[:height3, x, :3] = chunk * color_array
	if ADD_SUN:
		im[-22:,:]=SUN_COLOR
		im[-26:-22,:]=SUN_EDGE_COLOR

	im = Image.fromarray(np.flip(im, 0), mode="RGBA").filter(ImageFilter.GaussianBlur(radius=1))
	# im = Image.fromarray(np.flip(im, 0), mode="RGBA").resize()
	im.save('test.png')

	from ursina import *
	from ursina.prefabs.first_person_controller import FirstPersonController
	app = Ursina()
	# editor_camera = EditorCamera(enabled=True, ignore_paused=True, rotation=(60,0,0))
	player = FirstPersonController(y=10, collider = 'cube')
	ground = Entity(model='plane', collider='box', scale=64, texture='grass', texture_scale=(4,4))
	ent = Sky(model='sphere', texture=Texture(im), double_sided=True)
	app.run()

	ursina.Texture(self.game.screen_image().convert("RGBA"))
	tex._texture.setRamImageAs(im.tobytes(), "RGBA")
