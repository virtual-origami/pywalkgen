# Python code for 2D random walk.
import json
import sys
import random
import time
import math
import logging
import asyncio
from .AngleGenerator import WalkAngleGenerator
from .AMQPubSub import AMQ_Pub_Sub

logging.basicConfig(stream=sys.stdout,level=logging.INFO)
logger = logging.getLogger(__name__)

handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# ========================================= WALK PATTERN GENERATOR ==================================================================
class WalkPatternGenerator:

    def __init__(self,eventloop,config_file):
        try:
            self.x_pos = config_file["start_coordinates"]["x"]
            self.y_pos = config_file["start_coordinates"]["y"]
            self.z_pos = config_file["start_coordinates"]["z"]
            self.boundary = config_file["walk_boundary"]
            self.max_walk_speed = config_file["attribute"]["walk"]["max_walk_speed"]
            self.walk_dimension = config_file["attribute"]["walk"]["walk_dimension"]
            self.protocol_type = config_file['protocol']["type"]
            self.walk_angle_gen = WalkAngleGenerator(mid_point=config_file["attribute"]["walk"]["sigmoid_attributes"]["mid_point"],
                                                     steepness=config_file["attribute"]["walk"]["sigmoid_attributes"]["steepness"],
                                                     max_value=math.radians(config_file["attribute"]["walk"]["sigmoid_attributes"]["min_angle"]),
                                                     level_shift=math.radians(config_file["attribute"]["walk"]["sigmoid_attributes"]["max_angle"]))

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
            self.interval = config_file['attribute']['interval']
            self.eventloop = eventloop

            if self.protocol_type == "amq":
                self.publisher = AMQ_Pub_Sub(
                    eventloop=self.eventloop,
                    config_file=config_file['protocol'],
                    binding_suffix=".walk." + config_file['id']
                )
            else:
                raise AssertionError("Provide protocol (amq/mqtt) config")
        except Exception as e:
            logger.critical("unhandled exception",e)
            sys.exit(-1)

    async def _publish(self,binding_key,msg):
        await self.publisher.publish(binding_key=binding_key,message_content=msg)

    def _update3d(self,tdelta=-1):
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
            assert (timedelta >= 0),f"Time delta: {timedelta},  can't be negative"

            # calculate instantaneous velocity, based on step size calculated in previous iteration and take direction decision
            self.walk_angle = self.walk_angle_gen.generate(self.walk_angle,self.net_step_size / timedelta)
            # assert ((self.walk_angle >= 0) and (self.walk_angle <= 180)), f"Walk angle: {self.walk_angle} , out of range, range 0 to 180 (both inclusive)"

            # step size decision
            distance_in_sample_time = self.max_walk_speed * timedelta

            self.net_step_size = random.uniform(self.net_step_size,distance_in_sample_time * 0.682)

            # step length in each of the axis
            if self.walk_dimension == 1:
                self.x_step_length = self.net_step_size * math.cos(self.walk_angle)
                self.y_step_length = 0
                self.z_step_length = 0
            elif self.walk_dimension == 2:
                self.x_step_length = self.net_step_size * math.cos(self.walk_angle)
                self.y_step_length = self.net_step_size * math.sin(self.walk_angle)
                self.z_step_length = 0
            else:
                self.x_step_length = self.net_step_size * math.cos(self.walk_angle)
                self.y_step_length = self.net_step_size * math.sin(self.walk_angle)
                self.z_step_length = math.sin(math.sqrt((math.pow(self.x_step_length,2) + math.pow(self.y_step_length,2))))  # todo write logic for z_step_length based on angle

            # walk based on step size calculated in each direction
            self.x_pos = self.x_pos_prev + self.x_step_length
            self.y_pos = self.y_pos_prev + self.y_step_length
            self.z_pos = self.z_pos_prev + self.z_step_length

            # prepare for next iteration
            self.x_pos_prev = self.x_pos
            self.y_pos_prev = self.y_pos
            self.z_pos_prev = self.z_pos

            self.time_past = self.time_now

            return {"x_ref_pos":self.x_pos,"y_ref_pos":self.y_pos,"z_ref_pos":self.z_pos}
        except Exception as e:
            logger.critical("unhandled exception", e)
            sys.exit(-1)

    async def connect(self):
        await self.publisher.connect()

    async def run_once(self,binding_key=None):
        result = dict()
        if self.interval >= 0:
            result.update(self._update3d(tdelta=self.interval))
        else:
            result.update(self._update3d())

        # Publish
        if binding_key is not None:
            await self._publish(binding_key=binding_key,msg=json.dumps(result).encode())

        # sleep until its time for next sample
        if self.interval >= 0:
            await asyncio.sleep(delay=self.interval)
        else:
            await asyncio.sleep(delay=0)

    def get_states(self):
        return {"x_ref_pos":self.x_pos,"y_ref_pos":self.y_pos,"z_ref_pos":self.z_pos}

    def __get_all_states__(self):
        print(vars(self))
