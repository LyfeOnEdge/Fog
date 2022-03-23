from ursina import *
ripple_shader = Shader(language=Shader.GLSL,
vertex='''
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
out vec2 texcoords;
out vec4 draw_color;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoords = p3d_MultiTexCoord0.xy;
    draw_color = vec4(0.5,0.5,1.,1.);
}
''',
# fragment='''
# #version 140
# in vec2 texcoords;
# in vec4 draw_color;
# out vec4 fragColor;
# uniform float shadertime;

fragment='''
#version 140
in vec2 texcoords;
in vec4 draw_color;
out vec4 fragColor;
uniform float shadertime;
//	Simplex 3D Noise 
//	by Ian McEwan, Ashima Arts
//
vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

float rand(vec2 co){
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

float snoise(vec3 v){ 
  const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
  const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);

// First corner
  vec3 i  = floor(v + dot(v, C.yyy) );
  vec3 x0 =   v - i + dot(i, C.xxx) ;

// Other corners
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min( g.xyz, l.zxy );
  vec3 i2 = max( g.xyz, l.zxy );

  //  x0 = x0 - 0. + 0.0 * C 
  vec3 x1 = x0 - i1 + 1.0 * C.xxx;
  vec3 x2 = x0 - i2 + 2.0 * C.xxx;
  vec3 x3 = x0 - 1. + 3.0 * C.xxx;

// Permutations
  i = mod(i, 289.0 ); 
  vec4 p = permute( permute( permute( 
             i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0 )) 
           + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));

// Gradients
// ( N*N points uniformly over a square, mapped onto an octahedron.)
  float n_ = 1.0/7.0; // N=7
  vec3  ns = n_ * D.wyz - D.xzx;

  vec4 j = p - 49.0 * floor(p * ns.z *ns.z);  //  mod(p,N*N)

  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_ );    // mod(j,N)

  vec4 x = x_ *ns.x + ns.yyyy;
  vec4 y = y_ *ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);

  vec4 b0 = vec4( x.xy, y.xy );
  vec4 b1 = vec4( x.zw, y.zw );

  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));

  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;

  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);

//Normalise gradients
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;

// Mix final noise value
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), 
                                dot(p2,x2), dot(p3,x3) ) );
}

void main() {
	float x = (texcoords.x - 0.5);
	float y = (texcoords.y - 0.5);
	float len = sqrt(x*x + y*y);
	vec3 out_color = draw_color.xyz * vec3((sin(len*3.14*20-8*shadertime)+1)/2)*sin(asin(sin(len+shadertime)));
	//vec3 out_color = vec3(snoise((texcoords.xy+vec2(0.1*shadertime, -0.3*shadertime))*15.));
	vec3 out_color_2 = (vec3(snoise(vec3(texcoords.xy/0.01, shadertime)))+1)/2.;

	//fragColor = vec4(out_color, 1.);
	fragColor = vec4(mix(mix(out_color, vec3(rand(texcoords.xy*shadertime)), 0.3), out_color_2, 0.3), 1.).rgba;
}
'''
)
class simplex_shaded_entity(Entity):
	def __init__(self, *args, **kwargs):
		Entity.__init__(self, *args, shader=ripple_shader, **kwargs)
if __name__ == '__main__':
	from ursina.prefabs.first_person_controller import FirstPersonController
	app = Ursina(vsync=True)
	editor_camera = EditorCamera(enabled=True, ignore_paused=True, rotation=(60,0,0))
	# ground = simplex_shaded_entity(model='plane', parent=camera.ui, rotation=(90,90,90), scale=(camera.aspect_ratio, 1, camera.aspect_ratio))
	# ground = simplex_shaded_entity(model='plane', scale=10)
	ground = simplex_shaded_entity(model='cube', scale=10)
	start = time.time()
	def update(): ground.set_shader_input('shadertime', time.time()-start)
	ground.collider = ground.model
	app.run()