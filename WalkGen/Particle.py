import math
from WalkGen.Point import Point
from WalkGen.Ray import Ray


class Particle:
    def __init__(self, x, y):
        self.pos = Point( x=x, y=y )
        self.rays = []
        for i in range(0,360):
            self.rays.append( Ray( origin=self.pos, angle=i ) )

    def update(self, x, y):
        self.pos.x = x
        self.pos.y = y

    def look(self, obstacles):
        result = []
        for ray in self.rays:
            closest_obstacle = None
            closest_distance = None
            closest_point_on_obstacle = None
            for obstacle in obstacles:
                pt = ray.cast( obstacle )
                if pt is not None:
                    distance = abs(math.sqrt( ((self.pos.x - pt.x) ** 2) + ((self.pos.y - pt.y) ** 2) ))
                    if closest_obstacle is None:
                        closest_obstacle = obstacle
                        closest_point_on_obstacle = pt
                        closest_distance = distance
                    else:
                        if distance < closest_distance:
                            closest_obstacle = obstacle
                            closest_point_on_obstacle = pt
                            closest_distance = distance

            result.append({
                "angle": ray.angle,
                "obstacle": closest_obstacle.description if closest_obstacle is not None else None,
                "distance": closest_distance 
            })
        return result


