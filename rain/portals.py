from ursina import *
from panda3d.core import Camera as Camera
from panda3d.core import ColorWriteAttrib

class SimpleUrsinaPortals(Entity):
    def __init__(self,iterations=2):
        super().__init__()

        self.linkDumy = Entity()
        self.controllers=[]
        self.cameras=[]
        self.cameraNodes=[]
        self.regions=[]
        self.windows=[]

        self.originEnt = None
        self.target = None
        dr = application.base.camNode.getDisplayRegion(0)
        dr.setActive(0)

        w = dr.getWindow()
        for i in range(iterations):
            cameraController = Entity(origin_y=camera.aspect_ratio)
            c = Camera("cam"+str(i))
            cam = application.base.render.attachNewNode(c)
            cam.setName("camera"+str(i))
            cam.setPos(0,0,0)
            cam.reparentTo(cameraController)

            dr1 = w.makeDisplayRegion(0, 1, 0, 1)
            dr1.setSort(iterations-i)
            dr1.setClearDepthActive(True)
            dr1.setCamera(cam)
            
            self.regions.append(dr1)
            self.controllers.append(cameraController)
            self.cameraNodes.append(cam)
            self.cameras.append(c)
        self.prepareEntities()

        
    def prepareEntities(self):
        for i in scene.entities:
            i.setBin("fixed", 1)


    def link(self,origin,target):
        #origin.double_sided = True
        if self.originEnt != None:
            self.originEnt.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.C_on))
            self.originEnt.setBin("fixed",1)
        origin.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.C_off))
        origin.setBin("fixed", 0)

        self.originEnt = origin
        self.target = target

    def update(self):
        if self.originEnt != None and self.target != None:
            self.linkDumy.world_position = self.originEnt.world_position 
            self.linkDumy.rotation = self.originEnt.rotation

            self.parent = self.linkDumy

            self.world_position = self.controllers[0].world_position
            self.rotation = self.controllers[0].world_rotation

            self.linkDumy.world_position = self.target.world_position
            self.linkDumy.rotation = self.target.rotation

            self.controllers[1].world_position= self.world_position
            self.controllers[1].rotation = self.world_rotation