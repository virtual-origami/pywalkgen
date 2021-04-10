# Python code for 2D random walk.
import json
import sys
import random
import time
import math
import logging
import asyncio
from .AngleGenerator import WalkAngleGenerator
from .AMQPubSub import PubSubAMQP
from .OutlierGenerator import OutlierGenerator
from .IMU import IMU
from Raycast.Particle import Particle
from Raycast.StaticMap import StaticMap
from Raycast.CollisionDetection import CollisionDetection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# ========================================= WALK PATTERN GENERATOR ===================================================

class WalkPatternGenerator:

    def __init__(self,eventloop,config_file):
        try:
            self.id = config_file["id"]
            self.x_pos = config_file["start_coordinates"]["x"]
            self.y_pos = config_file["start_coordinates"]["y"]
            self.z_pos = config_file["start_coordinates"]["z"]
            self.boundary = config_file["walk_boundary"]
            self.max_walk_speed = config_file["attribute"]["walk"]["max_walk_speed"]
            self.walk_dimension = config_file["attribute"]["walk"]["walk_dimension"]

            walk_attribute = config_file["attribute"]["walk"]
            self.walk_angle_gen = WalkAngleGenerator(mid_point=walk_attribute["sigmoid_attributes"]["mid_point"],
                                                     steepness=walk_attribute["sigmoid_attributes"]["steepness"],
                                                     max_value=math.radians(walk_attribute["sigmoid_attributes"]["min_angle"]),
                                                     level_shift=math.radians(walk_attribute["sigmoid_attributes"]["max_angle"]),
                                                     walk_direction_factor=walk_attribute["direction_factor"],
                                                     walk_angle_deviation_factor=walk_attribute["angle_deviation_factor"])

            self.imu = IMU(config_file=config_file)

            self.collision = CollisionDetection(scene=StaticMap(config_file=config_file["workspace"]),
                                                particle=Particle(particle_id=config_file["id"],
                                                                  x=config_file["start_coordinates"]["x"],
                                                                  y=config_file["start_coordinates"]["y"]),
                                                min_collision_distance=config_file["attribute"]["collision"]["distance"])

            outlier_config = config_file["attribute"]["positioning"]["outliers"]
            self.outlier_gen = []
            self.outlier_gen.append(OutlierGenerator(mean=outlier_config["x"]["mean"],
                                                     standard_deviation=outlier_config["x"]["standard_deviation"],
                                                     number_of_outliers=outlier_config["x"]["number_of_outlier"],
                                                     sample_size=outlier_config["x"]["sample_size"]))

            self.outlier_gen.append(OutlierGenerator(mean=outlier_config["y"]["mean"],
                                                     standard_deviation=outlier_config["y"]["standard_deviation"],
                                                     number_of_outliers=outlier_config["y"]["number_of_outlier"],
                                                     sample_size=outlier_config["y"]["sample_size"]))

            self.outlier_gen.append(OutlierGenerator(mean=outlier_config["z"]["mean"],
                                                     standard_deviation=outlier_config["z"]["standard_deviation"],
                                                     number_of_outliers=outlier_config["z"]["number_of_outlier"],
                                                     sample_size=outlier_config["z"]["sample_size"]))

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

            self.distance_factor = config_file["attribute"]["walk"]["distance_factor"]

            self.distance_in_sample_time = 0

            protocol = config_file["protocol"]

            self.subscribers = []
            self.publishers = []

            if protocol["publishers"] is not None:
                for publisher in protocol["publishers"]:
                    if publisher["type"] == "amq":
                        logger.debug('Setting Up AMQP Publisher for Robot')
                        self.publishers.append(
                            PubSubAMQP(
                                eventloop=self.eventloop,
                                config_file=publisher,
                                binding_suffix=self.id
                            )
                        )
                    else:
                        logger.error("Provide protocol amq config")
                        raise AssertionError("Provide protocol amq config")

            if protocol["subscribers"] is not None:
                for subscriber in protocol["subscribers"]:
                    if subscriber["type"] == "amq":
                        logger.debug('Setting Up AMQP Subcriber for Robot')
                        self.subscribers.append(
                            PubSubAMQP(
                                eventloop=self.eventloop,
                                config_file=subscriber,
                                binding_suffix=self.id,
                                app_callback=self._consume_telemetry_msg
                            )
                        )
                    else:
                        logger.error("Provide protocol amq config")
                        raise AssertionError("Provide protocol amq config")

        except Exception as e:
            logger.critical("unhandled exception",e)
            sys.exit(-1)

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

            # calculate instantaneous velocity, based on step size calculated in previous iteration and take
            # direction decision
            ranging = self.collision.static_obstacle_avoidance(walk_angle=self.walk_angle)
            self.walk_angle,is_in_collision_course = self.walk_angle_gen.get_walk_angle(angle=self.walk_angle,
                                                                                        ranging=ranging,
                                                                                        velocity=self.net_step_size / timedelta)

            if is_in_collision_course:
                self.x_step_length = 0
                self.y_step_length = 0
                self.z_step_length = 0
                self.net_step_size = 0
            else:
                # step size decision
                new_distance_in_sample_time = random.uniform(self.distance_in_sample_time,
                                                             self.max_walk_speed * timedelta * 0.6134)

                self.distance_in_sample_time = (self.distance_in_sample_time * (1 - self.distance_factor)) \
                                               + (new_distance_in_sample_time * self.distance_factor)

                self.net_step_size = random.uniform(self.net_step_size,self.distance_in_sample_time)

                # step length in each of the axis
                if self.walk_dimension == 1:
                    self.x_step_length = self.net_step_size * math.cos(self.walk_angle)
                    self.y_step_length = 0
                    self.z_step_length = 0
                elif self.walk_dimension == 2:
                    self.x_step_length = self.net_step_size * math.cos(math.radians(self.walk_angle))
                    self.y_step_length = self.net_step_size * math.sin(math.radians(self.walk_angle))
                    self.z_step_length = 0
                else:
                    self.x_step_length = self.net_step_size * math.cos(self.walk_angle)
                    self.y_step_length = self.net_step_size * math.sin(self.walk_angle)
                    self.z_step_length = math.sin(math.sqrt((math.pow(self.x_step_length,2) + math.pow(self.y_step_length,2))))  # todo write logic for z_step_length based on angle

            # walk based on step size calculated in each direction
            self.x_pos = self.x_pos_prev + self.x_step_length
            self.y_pos = self.y_pos_prev + self.y_step_length
            self.z_pos = self.z_pos_prev + self.z_step_length

            # update particle's position
            self.collision.update_particles(x=self.x_pos,y=self.y_pos)

            heading = {'ref_heading':{'end':(self.x_pos,self.y_pos),'start':(self.x_pos_prev,self.y_pos_prev)}}

            # prepare for next iteration
            self.x_pos_prev = self.x_pos
            self.y_pos_prev = self.y_pos
            self.z_pos_prev = self.z_pos

            self.time_past = self.time_now

            x_uwb_pos = self.x_pos + self.outlier_gen[0].generate()
            y_uwb_pos = self.y_pos + self.outlier_gen[1].generate()
            z_uwb_pos = self.z_pos + self.outlier_gen[2].generate()

            result = {"id":self.id,"x_ref_pos":self.x_pos,"y_ref_pos":self.y_pos,"z_ref_pos":self.z_pos,
                      "x_uwb_pos":x_uwb_pos,"y_uwb_pos":y_uwb_pos,"z_uwb_pos":z_uwb_pos,
                      'view':ranging}
            result.update(heading)

            imu_result = self.imu.update(cur_position=result,tdelta=tdelta)
            result.update(imu_result)

            timestamp_ms = round(time.time() * 1000)
            result.update({"timestamp":timestamp_ms})

            return result
        except Exception as e:
            logger.critical("unhandled exception",e)
            sys.exit(-1)

    def get_states(self):
        return {"x_ref_pos":self.x_pos,"y_ref_pos":self.y_pos,"z_ref_pos":self.z_pos}

    async def publish(self, exchange_name, msg):
        for publisher in self.publishers:
            if exchange_name == publisher.exchange_name:
                await publisher.publish(message_content=msg)
                logger.debug(msg)

    async def connect(self):
        for publisher in self.publishers:
            await publisher.connect()

        for subscriber in self.subscribers:
            await subscriber.connect(mode="subscriber")

    async def update(self,binding_key=None):
        result = dict()
        if self.interval >= 0:
            result.update(self._update3d(tdelta=self.interval))
        else:
            result.update(self._update3d())

        # Publish
        if binding_key is not None:
            await self.publish(exchange_name='telemetry_exchange',msg=json.dumps(result).encode())
            await self.publish(exchange_name='db_exchange', msg=json.dumps(result).encode())

        # sleep until its time for next sample
        if self.interval >= 0:
            await asyncio.sleep(delay=self.interval)
        else:
            await asyncio.sleep(delay=0)



