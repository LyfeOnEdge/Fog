from ursina import *
from ursina.color import rgba
INVENTORY_WIDTH, INVENTORY_HEIGHT =8,1

class Inventory(Entity):
	def __init__(self, ui, items = None, rows = INVENTORY_HEIGHT, columns=INVENTORY_WIDTH, origin = (-0.5,0.5), **kwargs):
		self.ui = ui
		self.width = columns
		self.height= rows
		self.items = []
		self.start_inventory = None
		Entity.__init__(self,
			parent = camera.ui,
			model='quad',
			origin = origin,
			position = (-0.865,.4765),
			color = rgba(60,60,60,80),
		)

		self.inventory_grid = Entity(
			parent=self,
			model=Grid(self.width, self.height, thickness = 2),
			origin = origin,
			color = rgba(0,0,0,200)
			)

		for key, value in kwargs.items():
			setattr(self, key, value)

		self.z = -0.1

	def find_free_spot(self):
		for y in range(self.height):
			for x in range(self.width):
				grid_positions = [(int(e.x*self.width), int(e.y*self.height)) for e in self.items]
				if not (x,-y) in grid_positions:
					return x, y

	def append(self, item, x=0, y=0):
		print('add item:', item.name)

		if len(self.items) >= self.width*self.height:
			print('inventory full')
			error_message = Text('<red>Inventory is full!', origin=(0,-1.5), x=-.5, scale=2)
			destroy(error_message, delay=1)
			return

		x, y = self.find_free_spot()

		# icon = item(self)
		# name = icon.name
		self.items.append(item)

		# num = random.random()
		# if num < 0.33:
		# 	item.color = color.gold
		# 	name = '<orange>Rare ' + name
		# elif num < 0.66: 		
		# 	item.color = color.green
		# 	name = '<green>Uncommon ' + name
		# else:
		# 	item.color = color.white
		# 	name = ' Common ' + name		

		# item.tooltip = Tooltip(name)
		# item.tooltip.background.color = color.color(0,0,0,.8)
		item.drag = lambda:self.drag(item)
		item.drop = lambda:self.drop(item)

	def clear(self):
		for i in self.items:
			destroy(i)
		self.items = []

	def drag(self, item):
		item.org_pos = (item.x, item.y)
		item.z -= .05   # ensure the dragged item overlaps the rest
		self.start_inventory = item.parent

	def drop(self, item):
		hovered = False
		print(mouse.position)
		mouse_x, mouse_y, _ = mouse.position
		x,y = item.x, item.y
		for i in self.ui.inventories:
			inv_x, inv_y = i.x, i.y
			width, height, _ = i.bounds
			if mouse_x >= inv_x and mouse_x <= inv_x + width:
				if mouse_y <= inv_y and mouse_y >= inv_y - height:
					hovered = i
					break
		if hovered:
			if hovered == self.start_inventory:
				item.x = int((item.x + (item.scale_x/2)) * hovered.width) / hovered.width
				item.y = int((item.y - (item.scale_y/2)) * hovered.height) / hovered.height
				item.z += .05
				# if outside, return to original position
				if item.x < 0 or item.x >= 1 or item.y > 0 or item.y <= -1:
					item.position = (item.org_pos)
					return
				# if the spot is taken, swap positions
				for c in hovered.items:
					if c == item:
						continue
					if c.x == item.x and c.y == item.y:
						c.position = item.org_pos
			else:
				old_parent = item.parent
				item.world_parent = hovered
				old_parent.items.remove(item)
				hovered.items.append(item)
				item.x = int((item.x + (item.scale_x/2)) * hovered.width) / hovered.width
				item.y = int((item.y - (item.scale_y/2)) * hovered.height) / hovered.height
				item.z += .01
				# if outside, return to original position
				if item.x < 0 or item.x >= 1 or item.y > 0 or item.y <= -1:
					item.world_parent = old_parent
					item.position = item.org_pos
					return
				# if the spot is taken, swap positions
				for c in hovered.items:
					if c == item:
						continue
					if c.x == item.x and c.y == item.y:
						print('swap positions')
						c.world_parent = old_parent
						c.position = item.org_pos
						hovered.items.remove(c)
						old_parent.items.append(c)				
		else:
			item.position = item.org_pos
			return

class HotBar(Inventory):
	def __init__(self, ui, items = None, rows = 1, columns=INVENTORY_WIDTH, on_selection = None, **kwargs):
		Inventory.__init__(self, ui, items, rows, columns, **kwargs)
		self.index = 0
		self.max_selection = columns - 1
		if on_selection:
			self.on_selection = on_selection
		else:
			self.on_selection = _pass
		self.selection_frame = Entity(parent=self.inventory_grid, model='quad', texture="assets/textures/map_frame", scale=(1/self.height, 1/self.height))
		self.selection_frame.position = (self.index/self.width, self.position.y-0.1, -1)
		self.selection_frame.scale = (1/self.width,1)
		self.selection_frame.origin = (-0.5,0)
	def _pass(self,*args,**kwargs):
		pass
	def bump_selection_up(self):
		self.index += 1
		if self.index > self.max_selection:
			self.index = 0
		self.selection_frame.position = (self.index/self.width, self.position.y-0.1, -1)
		self.on_selection(self.get_selection())
	def bump_selection_down(self):
		self.index -= 1
		if self.index < 0:
			self.index = self.max_selection
		self.selection_frame.position = (self.index/self.width, self.position.y-0.1, -1)
		self.on_selection(self.get_selection())
	def get_selection(self):
		grid_positions = {int(e.x*self.width) : e for e in self.items}
		#All positions on first row
		for e in grid_positions:
			if e == self.index:
				return grid_positions[e]
	def trigger(self):
		self.selection_frame.position = (self.index/self.width, self.position.y-0.1, -1)
		self.on_selection(self.get_selection())


class Item(Draggable):
	def __init__(self,
				game,
				parent,
				origin = (-0.5,0.5),
				item_color = color.gray,
				size = (INVENTORY_WIDTH,INVENTORY_HEIGHT),
				wand_model='wand_default',
				gem_model='wand_orb',
				bolt_model="wand_bolt_default",
				on_action = None
			):
		self.game = game
		self.parent = parent
		self.item_color = item_color
		x,y = self.parent.find_free_spot()
		self.width, self.height = size
		self.name = "Item"
		Draggable.__init__(self,
			parent = parent,
			model='quad',
			color = color.white33,
			origin = origin,
			scale_x = 1/self.width,
			scale_y = 1/self.height,
			x = x * 1/self.width,
			y = -y * 1/self.height,
			z = -.5,
		)
		self.wand_model = wand_model
		self.gem_model  = gem_model
		self.bolt_model = bolt_model
		self.picture = Entity(parent=self, model=self.game.entity_manager.get_model(wand_model), texture="assets/textures/wand_texture", scale=1/9, rotation_z = 45,z=-1)
		self.picture.world_position += (1/self.width,-1/self.height-0.1)
		self.picture_gem = Entity(parent=self, model=self.game.entity_manager.get_model(gem_model), texture="", scale=1/9, rotation_z = 45,z=-1,color = self.item_color)
		self.picture_gem.world_position += (1/self.width,-1/self.height-0.1)
		if on_action: self.on_action = on_action

	# @property
	def name(self):
		return self.name

	def use(self, app):
		pass

	def on_action(self):
		print(f"Used - {self}")

SHOOT_ANIMATION_LENGTH = 0.19

class BaseWand(Item):
	def __init__(self, *args, damage = 10, **kwargs):
		self.damage = damage
		self.cooldown = SHOOT_ANIMATION_LENGTH
		Item.__init__(self, *args, **kwargs)

class BaseFireballWand(BaseWand):
	def __init__(self, *args, damage = 10, bolt_model=None, **kwargs):
		BaseWand.__init__(self, *args, on_action=self.shoot_fireball, **kwargs)

	def shoot_fireball(self):
		cam = self.game.player.position+(0,self.game.player.height,0)+self.game.player.camera_pivot.forward*5
		self.game.entity_manager.spawn_fireball(cam, cam+self.game.player.camera_pivot.forward, hostile = False)

class BaseBoltWand(BaseWand):
	def __init__(self, *args, **kwargs):
		BaseWand.__init__(self, *args, **kwargs)
		self.on_action = self.zap
	def zap(self):
		self.game.player.zap()

class LaserWand(BaseBoltWand):
	def __init__(self, *args, **kwargs):
		BaseBoltWand.__init__(
			self,
			*args,
			item_color = color.red,
			wand_model='wand_default',
			gem_model='wand_orb',
			bolt_model="wand_bolt_default",
			**kwargs
		)

class ZapWand(BaseBoltWand):
	def __init__(self, *args, **kwargs):
		BaseBoltWand.__init__(
			self,
			*args,
			item_color = color.yellow,
			wand_model='wand',
			gem_model='wand_orb',
			bolt_model="wand_bolt",
			**kwargs
		)

class ImpWand(BaseFireballWand):
	def __init__(self, *args, **kwargs):
		BaseFireballWand.__init__(
			self,
			*args,
			item_color = color.blue,
			wand_model='wand',
			gem_model='wand_orb',
			bolt_model=None,
			**kwargs
		)

# class ArmorBar(Inventory):
# 	def __init__(self, ui, items = None, rows = INVENTORY_HEIGHT + 2, columns=1, **kwargs):
# 		Inventory.__init__(self, ui, items, rows, columns, **kwargs)