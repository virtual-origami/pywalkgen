import os
import logging
import sys
import traceback
import yaml
from Raycast.Obstacle import Obstacle
from Raycast.Point import Point


class Scene:
    def __init__(self, config_file, scene_id):
        try:
            self.obstacles = []
            if os.path.exists( config_file ):
                with open( config_file, 'r' ) as yaml_file:
                    yaml_as_dict = yaml.load( yaml_file, Loader=yaml.FullLoader )
                    scenes = yaml_as_dict["scenes"]
                    for scene in scenes:
                        if scene["id"] == scene_id:
                            obstacles = scene["obstacles"]
                            for obstacle in obstacles:
                                points = []
                                for point in obstacle["points"]:
                                    points.append( Point( x=point[0], y=point[1] ) )

                                if obstacle["type"] == "static":
                                    self.obstacles.append( Obstacle( id=obstacle["id"],
                                                                            corner_points=tuple( points ),
                                                                            obstacle_shape=obstacle["shape"],
                                                                            obstacle_type=obstacle["type"],
                                                                            description=obstacle["description"] ) )
                                else:
                                    self.obstacles.append( Obstacle( id=obstacle["id"],
                                                                             corner_points=tuple( points ),
                                                                             obstacle_shape=obstacle["shape"],
                                                                             obstacle_type=obstacle["type"],
                                                                             description=obstacle["description"] ) )
                            break;

        except FileNotFoundError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except OSError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except AssertionError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except yaml.YAMLError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except:
            logging.critical( "unhandled exception" )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()

    def update(self, obstacle_id, corner_points, shape=None):
        try:
            assert type(corner_points) == tuple, "Corner points must be tuple of Points"
            for idx, obstacle in enumerate(self.obstacles):
                if obstacle.id == obstacle_id:
                    obstacle.update(corner_points=corner_points, shape=shape)
                    break;

        except AssertionError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()

    def get_segments(self):
        segments = []
        for obstacle in self.obstacles:
            for segment in obstacle.line_segments:
                segments.append( segment )

        # for obstacle in self.dynamic_obstacles:
        #     for segment in obstacle.line_segments:
        #         segments.append( segment )
        return segments
