from ursina import *
from panda3d.core import OmniBoundingVolume, LQuaterniond, LVecBase3d
import numpy as np
if __name__ == '__main__':
	from settings import settings
else:
	from .settings import settings
snow_shader=Shader(language=Shader.GLSL, vertex='''#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 texcoords;
out vec4 world_pos;
uniform mat4 p3d_ModelMatrix;
uniform vec2 texture_scale;
uniform vec3 base_position;
uniform vec3 position_offsets[250];
uniform vec4 rotation_offsets[250];
uniform vec3 scale_multipliers[250];
uniform vec3 fallscale_multipliers[250];
uniform float snow_height;
//uniform float max_distance;
uniform float deltatime;
uniform float fog_max;
void main() {
	vec3 v = p3d_Vertex.xyz * scale_multipliers[gl_InstanceID];
	vec4 q = rotation_offsets[gl_InstanceID];
	v = v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
	float y_displacement = fallscale_multipliers[gl_InstanceID].y*deltatime*0.1;
	int false_mod = int(y_displacement) / int(snow_height) + 1;
	v.y -= y_displacement - (false_mod * snow_height);
	//vec3 displacement = vec3(1,-y_displacement,1);
	vec4 displacement = vec4(v+position_offsets[gl_InstanceID], 1.0);
	gl_Position = p3d_ModelViewProjectionMatrix * displacement;
	texcoords = (p3d_MultiTexCoord0 * texture_scale);
	world_pos = p3d_ModelMatrix * displacement;
}
''',
fragment='''
#version 140
//uniform sampler2D p3d_Texture0;
//uniform vec4 p3d_ColorScale;
uniform vec3 player_position;
uniform float max_distance;
uniform vec4 base_color;
uniform vec4 fog_color;
in vec2 texcoords;
in vec4 world_pos;
out vec4 fragColor;
void main() {
	float fog_mult = min(1,length(player_position-world_pos.xyz)/max_distance);
	//vec4 color = texture(p3d_Texture0, texcoords) * p3d_ColorScale * (1.0-fog_mult) + fog_mult*fog_color;
	vec4 color = mix(base_color, fog_color, fog_mult);
	fragColor = color.rgba;
}
''',
default_input={
	'texture_scale' : Vec2(1,1),
	'position_offsets' : [Vec3(i,0,0) for i in range(250)],
	'rotation_offsets' : [Vec4(0) for i in range(250)],
	'scale_multipliers' : [Vec3(1) for i in range(250)],
	'base_position' : 0,
	'player_position' : 0,
	'base_color': color.rgba(255,255,255,255),
	'fog_color': color.rgba(120,120,120,255),
}
)

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
	def __init__(self, *args, game = None, thickness=8, gravity=1, particle_color=color.rgba(180,180,180,100), **kwargs):
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
		self.shader = snow_shader
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
		self.set_shader_input('max_distance', self.game.map_scale*(self.game.radius-0.5)),
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
			self.set_shader_input('deltatime', t - self.start)
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