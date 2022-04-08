import os, sys, json
from types import SimpleNamespace

TERRAIN_Y_SCALE = 6
def remake_settings():
	# setting_dict = {
	# 	"devMode" : True,
	# 	"keep_topmost" : False,
	# 	"borderless" : True,
	# 	"fullscreen" : False,
	# 	"terrain_y_scale" : TERRAIN_Y_SCALE,
	# 	"fairy_max_height" : TERRAIN_Y_SCALE/3,
	# 	"use_perlin" : False,
	# 	"num_generators": 4,
	# 	"render_distance":8,
	# 	"map_scale": 300,
	# 	"chunk_divisions":7,
	# 	"terrain_x_z_scale":0.4,
	# }
	setting_dict = {
		"devMode" : True,
		"keep_topmost" : False,
		"borderless" : True,
		"fullscreen" : False,
		"terrain_y_scale" : TERRAIN_Y_SCALE,
		"fairy_max_height" : TERRAIN_Y_SCALE/3,
		"use_perlin" : False,
		"render_distance":5,
		"map_scale": 500,
		"generator_scale" : 1,
		"second_generator_scale": 4, #Fine details
		"second_generator_weight" : 0.3, #Fine details
		"third_generator_scale": 0.05, #Big details
		"third_generator_weight" : 8, #Big details
		"fourth_generator_scale": 0.3, #Big details
		"fourth_generator_weight" : 5, #Big details
		"chunk_divisions":10,
		"terrain_x_z_scale":3.2,
		"player_speed" : 150,
		"player_height" : 12,
	}
	with open("settings.json", "w+") as s:
		json.dump(setting_dict, s, indent=4)

def load_settings():
	with open("settings.json") as data:
		return json.load(data, object_hook=lambda d: SimpleNamespace(**d))

if not os.path.isfile("settings.json"):remake_settings()
settings=load_settings()
if settings.devMode:remake_settings()
settings=load_settings()