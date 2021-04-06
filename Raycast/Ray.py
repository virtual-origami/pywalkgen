import math
import logging
from Raycast.Point import Point

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Ray:
    def __init__(self,origin,angle):
        if type(origin) == Point:
            self.pos = origin
            self.angle = angle
            self.dir = Point(x=math.cos(math.radians(angle)),y=math.sin(math.radians(angle)))

    def cast(self,segment):
        x1 = segment.a.x
        y1 = segment.a.y
        x2 = segment.b.x
        y2 = segment.b.y

        x3 = self.pos.x
        y3 = self.pos.y
        x4 = self.pos.x + self.dir.x
        y4 = self.pos.y + self.dir.y
        den1 = (x1 - x2) * (y3 - y4)
        den2 = (y1 - y2) * (x3 - x4)
        den = (den1 - den2)
        if den == 0:
            return None
        t1 = (x1 - x3) * (y3 - y4)
        t2 = (y1 - y3) * (x3 - x4)
        t = (t1 - t2) / den
        u1 = (x1 - x2) * (y1 - y3)
        u2 = (y1 - y2) * (x1 - x3)
        u = -(u1 - u2) / den

        if 0 < t < 1 and u > 0:
            ptx = x1 + (t * (x2 - x1))
            pty = y1 + (t * (y2 - y1))
            pt = Point(ptx,pty)
            return pt
        return None
