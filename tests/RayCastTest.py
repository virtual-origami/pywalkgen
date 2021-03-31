from Raycast.Obstacle import Obstacle
from Raycast.Point import Point
from Raycast.Particle import Particle
from Raycast.Scene import Scene
from Raycast.CollisionDetection import CollisionDetection

def ray_cast_test():

    def look(particle, segments):
        print( particle.look( segments=segments ) )

    scene = Scene( config_file="../scene.yaml", scene_id=1 )
    particle1 = Particle( particle_id=1, x=100, y=100 )
    particle2 = Particle( particle_id=1, x=100, y=130 )
    particle3 = Particle( particle_id=1, x=100, y=150 )
    collision_detector = CollisionDetection(scene)
    collision_detector.add_particle(particle=particle1)
    collision_detector.add_particle( particle=particle2 )
    collision_detector.add_particle( particle=particle3 )
    collision_detector.detect_collision()
    scene.update( obstacle_id=5, corner_points=(Point( x=0, y=160), Point( x=200, y=160 )) )
    collision_detector.detect_collision()


if __name__ == "__main__":
    ray_cast_test()
