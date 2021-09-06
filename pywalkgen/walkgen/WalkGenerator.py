# Python code for 2D random walk.
import json
import sys
import random
import time
import math
import logging
import asyncio

from .DataAggregator import DataAggregator
from .PositioningTag import PositioningTag
from pywalkgen.walk_model.AngleGenerator import WalkAngleGenerator
from pywalkgen.pub_sub.AMQP import PubSubAMQP
from pywalkgen.imu.IMU import IMU
from pywalkgen.raycast.Particle import Particle
from pywalkgen.raycast.StaticMap import StaticMap
from pywalkgen.collision_detection.CollisionDetection import CollisionDetection

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# ========================================= WALK PATTERN GENERATOR ===================================================

class WalkPatternGenerator:

    def __init__(self, eventloop, config_file):
        """
        Initialize walk pattern generator
        Walk pattern generator consists of
        :param eventloop: event loop for amqp pub sub
        :param config_file: config file
        """
        try:
            # id assigned to the personnel.
            self.walker_id = config_file["id"]

            # initialize the start coordinates of the personnel
            self.pos = {'x': config_file["start_coordinates"]["x"],
                        'y': config_file["start_coordinates"]["y"],
                        'z': config_file["start_coordinates"]["z"]}

            walk_attribute = config_file["attribute"]["walk"]

            # Walk angle generator for the personnel walk
            self.walk_angle_gen = WalkAngleGenerator(mid_point=walk_attribute["sigmoid_attributes"]["mid_point"],
                                                     steepness=walk_attribute["sigmoid_attributes"]["steepness"],
                                                     max_value=math.radians(
                                                         walk_attribute["sigmoid_attributes"]["min_angle"]),
                                                     level_shift=math.radians(
                                                         walk_attribute["sigmoid_attributes"]["max_angle"]),
                                                     walk_direction_factor=walk_attribute["direction_factor"],
                                                     walk_angle_deviation_factor=walk_attribute[
                                                         "angle_deviation_factor"])
            # IMU tag
            self.imu_tag = IMU(config_file=config_file)

            # Collision detection for static and dynamic obstacles
            self.collision = CollisionDetection(scene=StaticMap(config_file=config_file["map"]),
                                                particle=Particle(particle_id=config_file["id"],
                                                                  x=config_file["start_coordinates"]["x"],
                                                                  y=config_file["start_coordinates"]["y"]),
                                                env_collision_distance=config_file["attribute"]["collision"][
                                                    "distance"]["environment"],
                                                robot_collision_distance=config_file["attribute"]["collision"][
                                                    "distance"]["robot"])

            # UWB tag
            self.uwb_tag = PositioningTag(config=config_file["attribute"]["positioning"]["outliers"])

            self.data_aggregators = []
            for area in config_file["map"]["area_division"]:
                self.data_aggregators.append(DataAggregator(area_config=area))

            # set Walk attributes and angle generators
            self.max_walk_speed = walk_attribute["max_walk_speed"]
            self.walk_dimension = walk_attribute["walk_dimension"]
            self.walk_angle = 0

            # position related states
            self.pos_prev = {'x': self.pos['x'], 'y': self.pos['y'], 'z': self.pos['z']}
            self.net_step_size = 0

            # time stamp information
            self.time_now = 0
            self.time_past = 0

            # sample time information
            self.interval = config_file['attribute']['other']['interval']

            self.distance_factor = config_file["attribute"]["walk"]["distance_factor"]
            self.distance_in_sample_time = 0

            # Publisher
            protocol = config_file["protocol"]
            self.publishers = []
            if protocol["publishers"] is not None:
                for publisher in protocol["publishers"]:
                    if publisher["type"] == "amq":
                        logger.debug('Setting Up AMQP Publisher for Robot')
                        self.publishers.append(
                            PubSubAMQP(
                                eventloop=eventloop,
                                config_file=publisher,
                                binding_suffix=self.walker_id
                            )
                        )
                    else:
                        logger.error("Provide protocol amq config")
                        raise AssertionError("Provide protocol amq config")

            # Subscriber
            self.subscribers = []
            if protocol["subscribers"] is not None:
                for subscriber in protocol["subscribers"]:
                    if subscriber["type"] == "amq":
                        logger.debug('Setting Up AMQP Subcriber for Robot')
                        if subscriber["exchange"] == "control_exchange":
                            self.subscribers.append(
                                PubSubAMQP(
                                    eventloop=eventloop,
                                    config_file=subscriber,
                                    binding_suffix="",
                                    app_callback=self._consume_telemetry_msg
                                )
                            )
                        else:
                            self.subscribers.append(
                                PubSubAMQP(
                                    eventloop=eventloop,
                                    config_file=subscriber,
                                    binding_suffix=self.walker_id,
                                    app_callback=self._consume_telemetry_msg
                                )
                            )
                    else:
                        logger.error("Provide protocol amq config")
                        raise AssertionError("Provide protocol amq config")

        except Exception as e:
            logger.critical("unhandled exception", e)
            sys.exit(-1)

    def _consume_telemetry_msg(self, **kwargs):
        """
        consume telemetry messages
        :param kwargs: must contain following information
                       1.   exchange_name
                       2.   binding_name
                       3.   message_body
        :return: none
        """
        # extract message attributes from message
        exchange_name = kwargs["exchange_name"]
        binding_name = kwargs["binding_name"]
        message_body = json.loads(kwargs["message_body"])

        # check for matching subscriber with exchange and binding name in all subscribers
        for subscriber in self.subscribers:
            if subscriber.exchange_name == exchange_name:
                if "visual.generator.robot" in binding_name:
                    # extract robot id from binding name
                    binding_delimited_array = binding_name.split(".")
                    robot_id = binding_delimited_array[len(binding_delimited_array) - 1]
                    msg_attributes = message_body.keys()

                    # check for must fields in the message attributes
                    if ("id" in msg_attributes) and ("base" in msg_attributes) \
                            and ("shoulder" in msg_attributes) and ("elbow" in msg_attributes):

                        # check if robot id matches with 'id' field in the message
                        if robot_id == message_body["id"]:
                            logger.debug(f'Sub: exchange: {exchange_name} msg {message_body}')

                            # extract information from message body
                            base_shoulder = [message_body["base"], message_body["shoulder"]]
                            shoulder_elbow = [message_body["shoulder"], message_body["elbow"]]
                            elbow_wrist = [message_body["elbow"], message_body["wrist"]]
                            prefix = "robot_" + message_body["id"]

                            # update robot in scene for collision detection
                            self.collision.update_scene(obstacle_id=prefix + "_base_shoulder",
                                                        points=base_shoulder,
                                                        shape="line")
                            self.collision.update_scene(obstacle_id=prefix + "_shoulder_elbow",
                                                        points=shoulder_elbow,
                                                        shape="line")
                            self.collision.update_scene(obstacle_id=prefix + "_elbow_wrist",
                                                        points=elbow_wrist,
                                                        shape="line")
                            return

    async def _update3d(self, tdelta=-1):
        """
        update walker position in 3D
        :param tdelta: time duration between successive updates
        :return:
        """
        try:
            # calculate loop time
            if tdelta > 0:
                # valid time delta received as input paramter
                timedelta = tdelta
            elif self.time_now == 0 and self.time_past == 0:
                # time delta calculation for first update cycle
                self.time_now = time.time()
                self.time_past = self.time_now
                timedelta = 0.01
            else:
                # time delta calculation based on run time
                self.time_now = time.time()
                timedelta = self.time_now - self.time_past
                self.time_past = self.time_now

            assert (timedelta >= 0), f"Time delta: {timedelta},  can't be negative"

            # Calculate Walk angle for next step, and also check if walker is in collision course
            ranging, collision_avoidance_msg = self.collision.ranging()
            self.walk_angle, collision_decision = \
                self.walk_angle_gen.get_walk_angle(angle=self.walk_angle,
                                                   ranging=ranging,
                                                   velocity=self.net_step_size / timedelta)

            step_length = {'x': 0, 'y': 0, 'z': 0}

            if collision_decision:
                # self.net_step_size = self.net_step_size * 0.2
                self.net_step_size = random.uniform(self.net_step_size, self.distance_in_sample_time * 0.6134)
            else:
                # step size decision
                new_distance_in_sample_time = random.uniform(self.distance_in_sample_time,
                                                             self.max_walk_speed * timedelta * 0.6134)

                self.distance_in_sample_time = (self.distance_in_sample_time * (1 - self.distance_factor)) \
                                               + (new_distance_in_sample_time * self.distance_factor)

                self.net_step_size = random.uniform(self.net_step_size, self.distance_in_sample_time * 0.6134)

                # step length in each of the axis
                if self.walk_dimension == 1:
                    step_length['x'] = self.net_step_size * math.cos(self.walk_angle)
                    step_length['y'] = 0
                    step_length['z'] = 0
                elif self.walk_dimension == 2:
                    step_length['x'] = self.net_step_size * math.cos(math.radians(self.walk_angle))
                    step_length['y'] = self.net_step_size * math.sin(math.radians(self.walk_angle))
                    step_length['z'] = 0
                else:
                    step_length['x'] = self.net_step_size * math.cos(self.walk_angle)
                    step_length['y'] = self.net_step_size * math.sin(self.walk_angle)
                    step_length['z'] = math.sin(math.sqrt((math.pow(self.x_step_length, 2) + math.pow(
                        self.y_step_length, 2))))  # todo write logic for z_step_length based on angle

            # walk based on step size calculated in each direction
            self.pos['x'] = self.pos_prev['x'] + step_length['x']
            self.pos['y'] = self.pos_prev['y'] + step_length['y']
            self.pos['z'] = self.pos_prev['z'] + step_length['z']

            # update particle's position
            self.collision.update_particles(x=self.pos['x'], y=self.pos['y'])

            heading = {'ref_heading': {'end': (self.pos['x'], self.pos['y']),
                                       'start': (self.pos_prev['x'], self.pos_prev['y'])}}

            # prepare for next iteration
            self.pos_prev['x'] = self.pos['x']
            self.pos_prev['y'] = self.pos['y']
            self.pos_prev['z'] = self.pos['z']

            uwb_measurement = self.uwb_tag.get_measurement(ref=[self.pos['x'], self.pos['y'], self.pos['z']])
            data_aggregator_id = self.get_area_information(ref=[self.pos['x'], self.pos['y']])
            result = {
                "measurement": "walk",
                "time": time.time_ns(),
                "id": self.walker_id,
                "data_aggregator_id": data_aggregator_id,
                "walk_angle": self.walk_angle,
                "x_step_length": step_length['x'],
                "y_step_length": step_length['y'],
                "z_step_length": step_length['z'],
                "x_ref_pos": self.pos['x'],
                "y_ref_pos": self.pos['y'],
                "z_ref_pos": self.pos['z'],
                "x_uwb_pos": uwb_measurement[0],
                "y_uwb_pos": uwb_measurement[1],
                "z_uwb_pos": uwb_measurement[2],
                "view": ranging
            }
            result.update(heading)

            imu_result = self.imu_tag.update(cur_position=result, tdelta=timedelta)
            result.update(imu_result)

            result.update({"timestamp": round(time.time() * 1000)})

            plm_result = {
                "id": result["id"],
                "data_aggregator_id": result["data_aggregator_id"],
                "x_uwb_pos": result["x_uwb_pos"],
                "y_uwb_pos": result["y_uwb_pos"],
                "z_uwb_pos": result["z_uwb_pos"],
                'x_imu_vel': result['x_imu_vel'],
                'y_imu_vel': result['y_imu_vel'],
                'z_imu_vel': result['z_imu_vel'],
                "timestamp": result['timestamp']
            }

            return result, plm_result
        except Exception as e:
            logger.critical("unhandled exception", e)
            sys.exit(-1)

    async def publish(self, exchange_name, msg, external_binding_suffix=None):
        '''
        publishes amqp message
        :param exchange_name: name of amqp exchange
        :param msg: message to be published
        :param external_binding_suffix: binding suffix. suffix is appended to the end of binding namedd
        :return:
        '''
        for publisher in self.publishers:
            if exchange_name == publisher.exchange_name:
                await publisher.publish(message_content=msg, external_binding_suffix=external_binding_suffix)
                logger.debug(f'Pub: exchange: {exchange_name} msg {msg}')

    async def connect(self):
        """
        connects amqp publishers and subscribers
        :return:
        """
        for publisher in self.publishers:
            await publisher.connect()

        for subscriber in self.subscribers:
            await subscriber.connect(mode="subscriber")

    async def update(self):
        """
        update walk generator.
        Note This function need to be called in a loop every update cycle
        :param binding_key: binding key name (optional) used when other than default binding key
        :return:
        """

        result = dict()
        if self.interval >= 0:
            all_result, plm_result = await self._update3d()
            result.update(all_result)

        await self.publish(exchange_name='generator_personnel', msg=json.dumps(result).encode())

        # sleep until its time for next sample
        if self.interval >= 0:
            await asyncio.sleep(delay=self.interval)
        else:
            await asyncio.sleep(delay=0)

    def get_states(self):
        return {"x_ref_pos": self.pos['x'], "y_ref_pos ": self.pos['y'], "z_ref_pos": self.pos['z']}

    def get_area_information(self, ref):
        for data_aggregator in self.data_aggregators:
            if data_aggregator.locate(point=[ref[0], ref[1]]):
                return data_aggregator.id
        return None
