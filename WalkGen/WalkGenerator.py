# Python code for 2D random walk.
import json
import os
import sys
import traceback
import yaml
import random
import time
import math
import logging, asyncio
from .AngleGenerator import WalkAngleGenerator
from .AMQPubSub import AMQ_Pub_Sub

CONFIG_DIR = os.path.dirname( os.path.abspath( __file__ ) + "/configuration/" )
CONFIG_FILES = dict( personnel="personnel.yaml" )

logging.basicConfig( level=logging.WARNING, format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s' )


# ========================================= WALK PATTERN GENERATOR ==================================================================
class WalkPatternGenerator:

    def __init__(self, eventloop, config_file, personnel_id):
        try:
            if os.path.exists( config_file ):
                with open( config_file, 'r' ) as yaml_file:
                    yaml_as_dict = yaml.load( yaml_file, Loader=yaml.FullLoader )

                    # extract data from yaml config file
                    personnel_info = yaml_as_dict["walk_generator"]["personnel"]
                    walk_property_info = yaml_as_dict["walk_generator"]["property"]

                    # The personnel id of instance must be specified in yaml config file. If not raise Assertion error
                    person_info = None
                    for personnel in personnel_info:
                        if personnel["id"] == personnel_id:
                            person_info = personnel
                            break;
                    assert (person_info is not None), f"personnel_id: {personnel_id} does not exists in configuration file"

                    self.x_pos = person_info["start_coordinates"]["x"]
                    self.y_pos = person_info["start_coordinates"]["y"]
                    self.z_pos = person_info["start_coordinates"]["z"]
                    self.boundary = person_info["walk_boundary"]
                    self.max_walk_speed = walk_property_info["walk"]["max_walk_speed"]
                    self.walk_dimension = walk_property_info["walk"]["walk_dimension"]

                    self.walk_angle_gen = WalkAngleGenerator( mid_point=walk_property_info["walk"]["sigmoid_attributes"]["mid_point"],
                                                              steepness=walk_property_info["walk"]["sigmoid_attributes"]["steepness"],
                                                              max_value=math.radians( walk_property_info["walk"]["sigmoid_attributes"]["min_angle"] ),
                                                              level_shift=math.radians( walk_property_info["walk"]["sigmoid_attributes"]["max_angle"] ) )

                    self.eventloop = eventloop
                    self.publisher = AMQ_Pub_Sub( eventloop=self.eventloop, config_file=config_file, pub_sub_name=person_info["pub_sub_mapping"]["publisher"], mode="pub" )

                    self.x_pos_prev = self.x_pos
                    self.y_pos_prev = self.y_pos
                    self.z_pos_prev = self.z_pos

                    self.net_step_size = 0
                    self.x_step_length = 0
                    self.y_step_length = 0
                    self.z_step_length = 0

                    self.time_now = 0
                    self.time_past = 0

                    self.walk_angle = 0
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

    async def _publish(self, binding_key, msg):
        await self.publisher.publish( binding_key=binding_key, message_content=msg )

    def _update3d(self, tdelta=-1):
        try:
            # calculate loop time
            if tdelta > 0:
                timedelta = tdelta
            elif self.time_now == 0 and self.time_past == 0:
                self.time_now = time.time()
                timedelta = 0.01
            else:
                self.time_now = time.time()
                timedelta = self.time_now - self.time_past
            assert (timedelta >= 0), f"Time delta: {timedelta},  can't be negative"

            # calculate instantaneous velocity, based on step size calculated in previous iteration and take direction decision
            self.walk_angle = self.walk_angle_gen.generate( self.walk_angle, self.net_step_size / timedelta )
            # assert ((self.walk_angle >= 0) and (self.walk_angle <= 180)), f"Walk angle: {self.walk_angle} , out of range, range 0 to 180 (both inclusive)"

            # step size decision
            distance_in_sample_time = self.max_walk_speed * timedelta

            self.net_step_size = random.uniform( self.net_step_size, distance_in_sample_time * 0.682 )

            # step length in each of the axis
            if self.walk_dimension == 1:
                self.x_step_length = self.net_step_size * math.cos( self.walk_angle )
                self.y_step_length = 0
                self.z_step_length = 0
            elif self.walk_dimension == 2:
                self.x_step_length = self.net_step_size * math.cos( self.walk_angle )
                self.y_step_length = self.net_step_size * math.sin( self.walk_angle )
                self.z_step_length = 0
            else:
                self.x_step_length = self.net_step_size * math.cos( self.walk_angle )
                self.y_step_length = self.net_step_size * math.sin( self.walk_angle )
                self.z_step_length = math.sin( math.sqrt( (math.pow( self.x_step_length, 2 ) + math.pow( self.y_step_length, 2 )) ) )  # todo write logic for z_step_length based on angle

            # walk based on step size calculated in each direction
            self.x_pos = self.x_pos_prev + self.x_step_length
            self.y_pos = self.y_pos_prev + self.y_step_length
            self.z_pos = self.z_pos_prev + self.z_step_length

            # prepare for next iteration
            self.x_pos_prev = self.x_pos
            self.y_pos_prev = self.y_pos
            self.z_pos_prev = self.z_pos

            self.time_past = self.time_now

            return {"x_ref_pos": self.x_pos, "y_ref_pos": self.y_pos, "z_ref_pos": self.z_pos}
        except AssertionError as e:
            logging.critical( e )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()
        except:
            logging.critical( "unhandled exception" )
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.critical( repr( traceback.format_exception( exc_type, exc_value, exc_traceback ) ) )
            sys.exit()

    async def connect(self):
        await self.publisher.connect()

    async def run_once(self, tdelta=-1, binding_key=None):
        result = dict()
        result.update( self._update3d( tdelta=tdelta ) )

        # Publish
        if binding_key is not None:
            await self._publish( binding_key=binding_key, msg=json.dumps( result ).encode() )

        # sleep until its time for next sample
        if tdelta >= 0:
            await asyncio.sleep( delay=tdelta )
        else:
            await asyncio.sleep( delay=0 )

    def update_once(self, tdelta=-1):
        result = dict()
        result.update( self._update3d( tdelta ) )
        return result

    def get_states(self):
        return {"x_ref_pos": self.x_pos, "y_ref_pos": self.y_pos, "z_ref_pos": self.z_pos}

    def __get_all_states__(self):
        print( vars( self ) )




