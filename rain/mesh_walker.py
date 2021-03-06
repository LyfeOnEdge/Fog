from ursina import *
from .inventory import Inventory, HotBar, BaseBoltWand, LaserWand, ZapWand, ImpWand
from ursina.prefabs.health_bar import HealthBar
from .entities import Chest
UI_SCALE = 0.060
INVENTORY_WIDTH, INVENTORY_HEIGHT =8,1
SHOOT_ANIMATION_LENGTH = 0.19
CHEST_INTERACTION_DISTANCE = 100

class MeshWalker(Entity):
	def __init__(self, game, *args, speed = 50, height = 1, **kwargs):
		self.game = game
		Entity.__init__(self, *args, color = color.clear, **kwargs)

		self.speed = speed
		self.run_multiplier = 2.

		self.height = 50
		self.camera_pivot = Entity(parent=self, y=self.height)

		camera.parent = self.camera_pivot
		camera.position = (0,0,0)
		camera.rotation = (0,0,0)
		camera.fov = 90
		camera.lens.setFar(3*(self.game.current_world.radius)*self.game.current_world.map_scale)
		mouse.locked = True
		self.mouse_sensitivity = Vec2(40, 40)

		self.gravity = 1
		self.grounded = False
		self.running = False
		self.jump_up_duration = .3
		self.fall_after = .35 # will interrupt jump up
		self.jumping = False
		self.air_time = 0
		self.cursor = Entity(parent=camera.ui, model='quad', texture="assets/textures/crosshair", scale=.023)
		self.jump_height = 160
		self.height = height
		self.camera_pivot.y = self.height + 0.5 * self.height
		self.camera_pivot.z = self.height * 0.5
		self.gravity = 1
		self._keys = 0
		# self.collider = BoxCollider(self, Vec3(0,1,0), Vec3(1,2,1))
		self.y = self.game.current_world.terrain_generator.get_heightmap(0,0)*self.game.current_world.map_scale*self.game.current_world.terrain_y_scale #Ensure player is above map when spawned
		self.mouse_sensitivity = Vec2(80, 80)

		self.collider = BoxCollider(self, size=2*Vec3(self.height, self.height, self.height))
		
		self.hotbar = HotBar(
			self.game,
			scale =(UI_SCALE*INVENTORY_WIDTH,UI_SCALE),
			position = (-(0.5*UI_SCALE*INVENTORY_WIDTH),-0.5+UI_SCALE*(INVENTORY_HEIGHT+0.25)),
			on_selection = self.on_selection,
		)
		self.inventory = Inventory(
			self.game,
			scale =(UI_SCALE*INVENTORY_WIDTH,3*UI_SCALE),
			position = (-0.5*UI_SCALE*INVENTORY_WIDTH,- 0.5 * UI_SCALE),
			rows=3
		)
		self.chest_inventory = Inventory(
			self.game,
			scale =(UI_SCALE*INVENTORY_WIDTH,UI_SCALE*INVENTORY_HEIGHT),
			position = (-0.5*UI_SCALE*INVENTORY_WIDTH,UI_SCALE*(INVENTORY_HEIGHT+0.5)),
		)
		self.inventories = [self.hotbar, self.inventory, self.chest_inventory]
		self.hotbar.append(ZapWand)
		self.hotbar.append(LaserWand)
		self.hotbar.append(ImpWand)

		self.inventory_enabled = False
		self.in_chest = False
		self.current_chest = None
		self.exit_chest()
		self.held_item = Entity(model=self.game.entity_manager.get_model("wand_default"), parent=camera, position=(0.6,-.5,.25), scale=0.35, origin_z=-.5, color=color.rgb(200,150,150), texture="assets/textures/wand_texture.png", on_cooldown=False)
		self.held_item.gem = Entity(model=self.game.entity_manager.get_model("wand_orb"), texture="assets/textures/wand_effect.png", parent=self.held_item, z=0.5, y=0.1, world_scale=0.35, origin_y = 0.5, color=color.yellow, enabled=True)
		self.held_item.bolt = Entity(model=self.game.entity_manager.get_model("wand_bolt"), texture="assets/textures/wand_effect.png", parent=self.held_item, z=0.5, y=0.1, world_scale=0.35, origin_y = 0.5, color=color.yellow, enabled=True, visible=False)
		self.held_item.rotation_x = 90
		self.held_item.rotation_z = 12
		# self.held_item.muzzle_flash.rotation_y = 90
		# self.held_item.muzzle_flash.rotation_x = -90
		self.held_item.base_rotation = self.held_item.rotation
		self.shoot_animation_timer = 0
		self.air_time = 0
		self.origin = -0.5
		self.last_selected_item = None
		self.health_bar = HealthBar(bar_color=color.gray, roundness=.5, value=100)
		self.health_bar.position = (-0.5*self.health_bar.scale.x, .45)
		self.no_clip = False
		self.key_symbol = Entity(model='assets/models/key', parent=camera.ui, position=(-0.45*camera.aspect_ratio,.45), texture="assets/textures/key_texture_menu.png", rotation=(0,90,0), color=color.white, z=-1)
		self.key_symbol.scale=0.03

		self.key_text = Text(
			parent=camera.ui,
			text="x 0",
			color=color.white,
			origin=(-0.5,0),
		)
		self.key_text.position = self.key_symbol.position + (self.key_symbol.scale.x,0,0)


		self.input_map = {
			# 'escape' : self.exit,
			# 'tab' : self.toggle_debug,
			# 'e' : self.toggle_inventory,
		}

		self.bind_map = {
			'scroll up' : self.hotbar.bump_selection_down,
			'scroll down' : self.hotbar.bump_selection_up,
			'space' : self.jump,
			'e' : self.toggle_inventory,
			'y': self.game.transition_worlds,
			'o': self.game.toggle_screen_border,
			'p': self.toggle_no_clip,
		}

		self.keys_awaiting_release = []
		self.item_on_action = None

		self.hotbar.trigger()

	def input_task(self):
		current_keys = []
		keys_awaiting_release = self.keys_awaiting_release
		self.keys_awaiting_release = []
		for k in self.input_map.keys(): #for keys with a mapped task
			current_keys.append(k)
			if k in keys_awaiting_release:
				if held_keys[k]:
					self.keys_awaiting_release.append(k)
					continue
			if held_keys[k]: #If held
				self.input_map[k]() #Do task
				self.keys_awaiting_release.append(k)

	def input(self, key):
		if self.bind_map.get(key):
			self.bind_map.get(key)()

	def jump(self):
		if not self.grounded:
			return

		self.grounded = False
		self.animate_y(self.y+self.jump_height, self.jump_up_duration, resolution=int(1//time.dt), curve=curve.out_expo)
		invoke(self.start_fall, delay=self.fall_after)

	def start_fall(self):
		self.y_animator.pause()
		self.jumping = False

	def land(self):
		self.air_time = 0
		self.grounded = True

	def update(self): #Override to work with heightmap function instead
		self.input_task()
			
		if self.no_clip:
			self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]
			self.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
			self.rotation_x = clamp(self.rotation_x, -90, 90)

			self.direction = Vec3(
				self.forward * (held_keys['w'] - held_keys['s'])
				+ self.right * (held_keys['d'] - held_keys['a'])
				+ self.up * (held_keys['space'] - held_keys['left control'])
				).normalized()
			self.position += self.direction * self.speed * time.dt * 10
			return

		if self.movement_enabled:
			cur_time = time.time()
			rot = math.sin(cur_time*1.7)
			if held_keys['left mouse']:self.shoot()
			elif held_keys['right mouse']:self.interact()
			self.held_item.rotation = self.held_item.base_rotation + (rot,0,0)
			self.held_item.gem.rotation_y += time.dt*360
			self.held_item.gem.y = 0.65 + 0.6 * rot
			self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]

			if self.held_item.on_cooldown: 
				self.shoot_animation_timer -= time.dt
				if self.shoot_animation_timer <= 0:
					self.held_item.on_cooldown = False
					self.shoot_animation_timer = 0
				else:
					d = -12*math.sin(((SHOOT_ANIMATION_LENGTH-self.shoot_animation_timer)*(2*math.pi)))
					self.held_item.rotation += (d,0,0)

			self.held_item.bolt.rotation_y = 3.7*(self.held_item.base_rotation.x-self.held_item.rotation.x)-12

			self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
			self.camera_pivot.rotation_x= clamp(self.camera_pivot.rotation_x, -90, 90)

			self.direction = Vec3(
				self.forward * (held_keys['w'] - held_keys['s'])
				+ self.right * (held_keys['d'] - held_keys['a'])
				).normalized()
			if any((held_keys['w'],held_keys['a'],held_keys['s'],held_keys['d'])):
				if held_keys['left control'] and not self.running:
					self.running = True
			else:
				self.running = False

			if self.running:
				self.direction *= self.run_multiplier
			self.position += self.direction * self.speed * time.dt
			ms = self.game.current_world.map_scale
			if self.grounded:
				self.y = self.game.current_world.terrain_generator.get_heightmap(self.position[0]/ms,self.position[2]/ms)*self.game.current_world.y_scale
			else:
				mult = 20 if held_keys['space'] else 200
				self.air_time += time.dt
				self.y -= (self.gravity*(self.air_time+0.5))**(2)*time.dt*mult

				terrain_height = self.game.current_world.terrain_generator.get_heightmap(self.position[0]/ms,self.position[2]/ms)*self.game.current_world.y_scale

				if terrain_height > self.position.y:
					self.position = (self.position[0], terrain_height, self.position[2])
					if not self.grounded:
						self.land()

	def shoot(self):
		if not self.held_item.on_cooldown:
			self.shoot_animation_timer = SHOOT_ANIMATION_LENGTH
			self.held_item.on_cooldown = True		
			if self.item_on_action:
				self.game.audio_handler.wand_sound.play()
				self.item_on_action()

	def interact(self):
		if mouse.hovered_entity and type(mouse.hovered_entity) is Chest:
			if distance(mouse.hovered_entity, self) < CHEST_INTERACTION_DISTANCE:
				self.show_chest(mouse.hovered_entity)

	def zap(self):
		self.held_item.bolt.visible = True

		invoke(setattr, self.held_item.bolt, 'visible', False, delay=0.06)
		if mouse.hovered_entity and hasattr(mouse.hovered_entity, 'hp'):
			mouse.hovered_entity.hp -= 10
			mouse.hovered_entity.blink(color.red)

	@property
	def keys(self):
		print("Get Keys")
		return self._keys

	@keys.setter
	def keys(self, value):
		self._keys = value
		self.key_text.text = f"x {self._keys}"

	@property
	def hp(self):
		return self.health_bar.value

	@hp.setter
	def hp(self, value):
		self.health_bar.value = value
		if self.health_bar.value <= 0:
			raise "You Died"

	def show_chest(self, chest):
		self.in_chest = True
		self.current_chest = chest
		chest.disabled = True
		self.show_inventory()
		self.chest_inventory.clear()
		self.chest_inventory.visible = True
		for i in chest.items:
			self.chest_inventory.append(i)

	def exit_chest(self):
		self.in_chest = False
		if self.current_chest:
			self.current_chest.items = []
			for i in self.chest_inventory.icons:
				self.current_chest.items.append(type(i))
			self.current_chest.disabled = False
		self.chest_inventory.clear()
		self.chest_inventory.visible = False
		self.hide_inventory()
		self.current_chest = None

	def show_inventory(self):
		self.in_inventory = True
		self.set_player_locked()
		self.game.map.disable()
		self.inventory_enabled = True
		self.inventory.visible = True

	def hide_inventory(self):
		self.in_inventory = False
		self.set_player_free()
		self.game.map.enable()
		self.inventory_enabled = False
		self.inventory.visible = False

	def toggle_inventory(self):
		if self.inventory_enabled == True:
			if self.in_chest:
				self.exit_chest()
			else:
				self.hide_inventory()
		else:
			self.show_inventory()
			
	def set_player_free(self):
		self.movement_enabled = True
		mouse.locked = True

	def set_player_locked(self):
		self.movement_enabled = False
		mouse.locked = False

	def on_selection(self, item):
		self.item = item
		if item:
			print(item)
			self.held_item.visible = True
			self.held_item.gem.visible = True
			self.held_item.bolt.visible = False
			self.held_item.model = self.game.entity_manager.get_model(item.wand_model)
			self.held_item.origin_y = 0
			self.held_item.gem.model = self.game.entity_manager.get_model(item.gem_model)
			self.held_item.gem.origin_y = 0
			self.held_item.gem.color = item.item_color
			self.held_item.bolt.model = self.game.entity_manager.get_model(item.bolt_model)
			self.held_item.bolt.origin_y = 0
			self.held_item.bolt.color = item.item_color
			self.item_on_action = item.on_action
		else:
			self.item_on_action = None
			self.held_item.visible = False
			self.held_item.gem.visible = False
			self.held_item.bolt.visible = False

	def toggle_no_clip(self):
		if self.no_clip:
			self.camera_pivot.rotation_x = self.rotation_x
			self.rotation_x = 0
		else:
			self.rotation_x = self.camera_pivot.rotation_x
			self.rotation_x = 0
		self.no_clip = not self.no_clip

		