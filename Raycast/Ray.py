import math
from Raycast.Point import Point


class Ray:
    def __init__(self, origin, angle):
        if type( origin ) == Point:
            self.pos = origin
            self.angle = angle
            self.dir = Point( x=math.cos( math.radians( angle ) ), y=math.sin( math.radians( angle ) ) )

    def cast(self, segment):
        x1 = segment.a.x
        y1 = segment.a.y
        x2 = segment.b.x
        y2 = segment.b.y

        x3 = self.pos.x
        y3 = self.pos.y
        x4 = self.pos.x + self.dir.x
        y4 = self.pos.y + self.dir.y

        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if den == 0:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if 0 < t < 1 and u > 0:
            pt = Point( x1 + t * (x2 - x1), y1 + t * (y2 - y1) )
            return pt
        return None
