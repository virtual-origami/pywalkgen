import sys
import math
import logging
from pywalkgen.outliergen import OutlierGenerator

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class IMU:
    def __init__(self, config_file):
        """
        Initializes IMU
        :param config_file: configuration file
        """
        try:
            attribute = config_file["attribute"]['motion']
            initial_acc = attribute["acceleration"]["initial"]
            initial_vel = attribute["velocity"]["initial"]
            initial_ori = attribute["orientation"]["initial"]

            self.prev_position = {'x': config_file["start_coordinates"]["x"],
                                  'y': config_file["start_coordinates"]["y"],
                                  'z': config_file["start_coordinates"]["z"]}

            self.acceleration = {'x': initial_acc['x'], 'y': initial_acc['y'], 'z': initial_acc['z']}
            self.velocity = {'x': initial_vel['x'], 'y': initial_vel['y'], 'z': initial_vel['z']}
            self.orientation = {'roll': initial_ori['roll'], 'pitch': initial_ori['pitch'], 'yaw': initial_ori['yaw']}
            self.time_now = 0
            self.time_past = 0
            self.outlier_gen = dict()
            self.outlier_gen.update({'x': OutlierGenerator(mean=attribute["acceleration"]["outliers"]["x"]["mean"],
                                                           standard_deviation=
                                                           attribute["acceleration"]["outliers"]["x"][
                                                               "standard_deviation"],
                                                           number_of_outliers=
                                                           attribute["acceleration"]["outliers"]["x"][
                                                               "number_of_outlier"],
                                                           sample_size=attribute["acceleration"]["outliers"]["x"][
                                                               "sample_size"])})

            self.outlier_gen.update({'y': OutlierGenerator(mean=attribute["acceleration"]["outliers"]["y"]["mean"],
                                                           standard_deviation=
                                                           attribute["acceleration"]["outliers"]["y"][
                                                               "standard_deviation"],
                                                           number_of_outliers=
                                                           attribute["acceleration"]["outliers"]["y"][
                                                               "number_of_outlier"],
                                                           sample_size=attribute["acceleration"]["outliers"]["y"][
                                                               "sample_size"])})

            self.outlier_gen.update({'z': OutlierGenerator(mean=attribute["acceleration"]["outliers"]["z"]["mean"],
                                                           standard_deviation=
                                                           attribute["acceleration"]["outliers"]["z"][
                                                               "standard_deviation"],
                                                           number_of_outliers=
                                                           attribute["acceleration"]["outliers"]["z"][
                                                               "number_of_outlier"],
                                                           sample_size=attribute["acceleration"]["outliers"]["z"][
                                                               "sample_size"])})

        except Exception as e:
            logger.critical("unhandled exception", e)
            sys.exit(-1)

    def update(self, cur_position, tdelta=-1):
        """
        update IMU generator.
        Note This function need to be called in a loop every update cycle
        :param cur_position: current position
        :param tdelta: time delta
        :return:
        """
        try:
            # calculate loop time
            if tdelta < 0:
                raise RuntimeError("timedelta cannot be negative value")
            timedelta = tdelta

            noisy_velocity = {'x': 0, 'y': 0, 'z': 0}
            noisy_acceleration = {'x': 0, 'y': 0, 'z': 0}
            noisy_orientation = {'roll': 0, 'pitch': 0, 'yaw': 0}

            self.acceleration['x'] = (cur_position['x_ref_pos'] - self.prev_position['x']) / (timedelta**2)
            self.acceleration['y'] = (cur_position['y_ref_pos'] - self.prev_position['y']) / (timedelta**2)
            self.acceleration['z'] = (cur_position['y_ref_pos'] - self.prev_position['y']) / (timedelta**2)

            self.velocity['x'] = (cur_position['x_ref_pos'] - self.prev_position['x']) / timedelta
            self.velocity['y'] = (cur_position['y_ref_pos'] - self.prev_position['y']) / timedelta
            self.velocity['z'] = (cur_position['y_ref_pos'] - self.prev_position['y']) / timedelta

            self.prev_position['x'] = cur_position['x_ref_pos']
            self.prev_position['y'] = cur_position['y_ref_pos']
            self.prev_position['z'] = cur_position['z_ref_pos']

            self.orientation['roll'] = math.atan2(self.acceleration['y'],
                                                  math.sqrt((self.acceleration['x'] ** 2) +
                                                            (self.acceleration['z'] ** 2)))

            self.orientation['pitch'] = math.atan2(self.acceleration['x'],
                                                   math.sqrt((self.acceleration['y'] ** 2) +
                                                             (self.acceleration['z'] ** 2)))

            self.orientation['yaw'] = math.atan2(math.sqrt((self.acceleration['x'] ** 2) +
                                                           (self.acceleration['y'] ** 2)),
                                                 self.acceleration['z'])

            for i in ['x', 'y', 'z']:
                noisy_acceleration[i] = self.acceleration[i]
                noisy_velocity[i] = self.velocity[i] + self.outlier_gen[i].generate()

            noisy_orientation['roll'] = math.atan2(noisy_acceleration['y'], math.sqrt(
                (noisy_acceleration['x'] ** 2) + (noisy_acceleration['z'] ** 2)))
            noisy_orientation['pitch'] = math.atan2(noisy_acceleration['x'], math.sqrt(
                (noisy_acceleration['y'] ** 2) + (noisy_acceleration['z'] ** 2)))
            noisy_orientation['yaw'] = math.atan2(
                math.sqrt((noisy_acceleration['x'] ** 2) + (noisy_acceleration['y'] ** 2)), noisy_acceleration['z'])

            return {
                'x_ref_vel': self.velocity['x'],
                'y_ref_vel': self.velocity['y'],
                'z_ref_vel': self.velocity['z'],
                'x_ref_acc': self.acceleration['x'],
                'y_ref_acc': self.acceleration['y'],
                'z_ref_acc': self.acceleration['z'],
                'ref_roll': self.orientation['roll'],
                'ref_pitch': self.orientation['pitch'],
                'ref_yaw': self.orientation['yaw'],
                'x_imu_vel': noisy_velocity['x'],
                'y_imu_vel': noisy_velocity['y'],
                'z_imu_vel': noisy_velocity['z'],
                'x_imu_acc': noisy_acceleration['x'],
                'y_imu_acc': noisy_acceleration['y'],
                'z_imu_acc': noisy_acceleration['z'],
                'imu_roll': self.orientation['roll'],
                'imu_pitch': self.orientation['pitch'],
                'imu_yaw': self.orientation['yaw']
            }
        except Exception as e:
            logger.critical("unhandled exception", e)
            sys.exit(-1)

