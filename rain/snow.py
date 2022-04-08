from ursina import *
from panda3d.core import OmniBoundingVolume, LQuaterniond, LVecBase3d
import numpy as np
if __name__ == '__main__':
	from settings import settings
else:
	from .settings import settings

class snow_entity:
	__slots__ = ['position', 'rotation', 'scale', 'q', 'fallscale']
	def __init__(self, position, rotation, scale):
		self.position = position
		self.rotation = rotation
		self.scale = scale
		self.q = LQuaterniond()
		self.q.setHpr(LVecBase3d(self.rotation.x,self.rotation.y,self.rotation.z))
		self.fallscale = random.uniform(0.8,1.2)
	@property
	def quaternion(self):
		return self.q


DELAY = 1.0/60.0

class SnowCloud(Entity):
	def __init__(self, *args, game = None, thickness=8, gravity=1, particle_color=color.rgba(180,180,180,100), shader=None, **kwargs):
		if hasattr(game, 'entity_manager'):
			model = game.entity_manager.get_snow_model()
		else:
			points = np.array([Vec3(random.uniform(-10,10),random.uniform(-5,0),random.uniform(-10,10)) for i in range(2000)])
			model = deepcopy(Mesh(vertices=points, mode='point', thickness=thickness, render_points_in_3d=True))

		Entity.__init__(self, *args, model=model, color=particle_color, **kwargs)
		self.game = game
		self.setRenderModePerspective(True)
		self.instances = []
		self.model.uvs = [(v[0],v[1]) for v in self.model.vertices]
		self.shader = shader
		self.setInstanceCount(250)
 
		self.positions = []
		self.quaternions = []
		self.scales = [Vec3(1) for i in range(250)]
		self.fallscales = [Vec3(0,random.uniform(0.7,1.3)*gravity,0) for i in range(250)]
		self.start = time.time()

		for z in range(16):
			for x in range(16):
				self.positions.append( Vec3(x/16+random.uniform(0,1), random.uniform(-40,40), z/16+random.uniform(0,1)) )
				q = LQuaterniond()
				q.setHpr(LVecBase3d(random.uniform(0,360),0,0))
				self.quaternions.append(q)
				self.scales.append(Vec3(1))

		self.node().setBounds(OmniBoundingVolume())
		self.node().setFinal(True)
		self.last_update = time.time()

		self.set_shader_input('snow_height', 40)
		self.set_shader_input('max_distance', self.game.current_world.map_scale*(self.game.current_world.radius-0.5)),
		self.set_shader_input('base_position', self.position)
		self.set_shader_input('deltatime', 0)
		self.set_shader_input('fallscale_multipliers', self.fallscales)
		self.set_shader_input('position_offsets', self.positions)
		self.set_shader_input('rotation_offsets', self.quaternions)
		self.set_shader_input('scale_multipliers',self.scales)

	def update(self):
		if time.time() > self.last_update + DELAY:
			t = time.time()
			self.set_shader_input('player_position', self.game.player.position)
			self.set_shader_input('shadertime', t - self.start)
			self.last_update = t


class dummy_player(Entity):
	def __init__(self):
		Entity.__init__(self)
		self.position = Vec3(0,0,0)

if __name__ == '__main__':
	from ursina.prefabs.first_person_controller import FirstPersonController
	app = Ursina(vsync=False)
	app.map_scale = 100
	app.player = FirstPersonController(game=app, y=2)
	app.player.cursor.color = color.clear
	app.radius = 1
	SnowCloud(game=app, scale=10, thickness=2, gravity=10, particle_color=color.white)
	ground = Entity(model='plane', texture='grass', scale=2*app.map_scale)
	ground.collider = ground.model
	app.run()