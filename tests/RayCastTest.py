from WalkGen.Obstacle import Obstacle
from WalkGen.Point import Point
from WalkGen.Particle import Particle


def ray_cast_test():
    walls = []
    particle = []

    def setup():
        global particle
        global wall
        walls.append(Obstacle( point1=Point( x=0, y=0 ), point2=Point( x=0, y=200 ), description="Wall-1" ))
        walls.append(Obstacle( point1=Point( x=0, y=200 ), point2=Point( x=200, y=200 ), description="Wall-2"))
        walls.append(Obstacle( point1=Point( x=200, y=200 ), point2=Point( x=200, y=0 ), description="Wall-3"))
        walls.append(Obstacle( point1=Point( x=0, y=0 ), point2=Point( x=200, y=0 ), description="Wall-4"))
        walls.append( Obstacle( point1=Point( x=100, y=200 ), point2=Point( x=200, y=100 ), description="Wall-5") )
        particle = Particle( x=100, y=100 )

    def draw():
        global particle
        global wall
        print(particle.look( obstacles=walls ))

    setup()
    draw()


if __name__=="__main__":
    ray_cast_test()