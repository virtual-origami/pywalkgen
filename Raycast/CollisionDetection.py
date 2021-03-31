
class CollisionDetection:
    def __init__(self, scene):
        self.scene = scene
        self.particles = []

    def add_particle(self, particle):
        self.particles.append (particle)

    def remove_particle(self ,id):
        for particle in self.particles:
            if particle.id == id:
                self.particles.remove (particle)

    def update_dynamic_obstacles(self ,id ,corner_points):
        self.scene.update( obstacle_id=id, corner_points=corner_points )

    def update_particles(self, id ,x ,y):
        for particle in self.particles:
            if particle.id == id:
                particle.update( x=x, y=y )

    def detect_collision(self):
        for particle in self.particles:
            views = particle.look(self.scene.get_segments())
            for view in views:
                if view["distance"] is not None:
                    if view["distance"] < 10:
                        print("Collision detected")
                    else:
                        print(f'Distance: {view["distance"]}')



