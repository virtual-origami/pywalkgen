import random

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class CollisionDetection:
    def __init__(self,scene,particle,min_collision_distance):
        self.scene = scene
        self.particle = particle
        self.views = None
        self.min_collision_distance = min_collision_distance

    def update_particles(self,x,y):
        self.particle.update(x=x,y=y)

    def ranging(self):
        self.views = self.particle.look(self.scene.get_segments())
        return self.views

    def detect_collision(self):
        views = self.ranging()
        for view in views:
            if view["distance"] is not None:
                if view["distance"] < 70:
                    print("Collision detected")

    def get_world_view(self):
        return self.views

    def static_obstacle_avoidance(self,walk_angle):
        self.ranging()
        result=[]
        for item in self.views:
            if item['distance'] is not None:
                if item['distance'] > self.min_collision_distance:
                    result.append(item)
        return result
