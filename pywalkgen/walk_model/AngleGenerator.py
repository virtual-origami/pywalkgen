import numpy
from .Sigmoid import Sigmoid
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class WalkAngleGenerator:
    """Walk Angle Generator. This use Sigmoid function
    """

    def __init__(self, mid_point=0, steepness=0.5, max_value=1, level_shift=0, walk_direction_factor=0.341,
                 walk_angle_deviation_factor=1):
        """Initializes Walk Angle generator

        Args:
            mid_point (int, optional): Midpoint of the sigmoid (point of inflection). Defaults to 0.
            steepness (float, optional): Steepness of the the function. Defaults to 0.5.
            max_value (int, optional): Maximum value of the Sigmoid function. Defaults to 1.
            level_shift (int, optional): Minimum value of the Sigmoid function. Defaults to 0.
        """
        self.sigmoid = Sigmoid(mid_point=mid_point,
                               steepness=steepness,
                               max_value=max_value,
                               level_shift=level_shift)
        self.walk_direction_factor = walk_direction_factor
        self.walk_angle = 0.0
        self.max_angle_deviation = 0.0
        self.walk_angle_deviation_factor = walk_angle_deviation_factor

    def _get_max_angle_deviation(self, velocity):
        """Get max angle of deviation given velocity

        Args:
            velocity (float): Velocity in meter per second

        Returns:
            float: Maximum angle of deviation
        """
        self.max_angle_deviation = self.sigmoid.generate(-1.0 * velocity)
        return self.max_angle_deviation

    def get_walk_angle(self, angle, ranging, velocity):
        """Generates angle value for given velocity

        Args:
            angle (float): maximum angle of deviation in radians
            ranging
            velocity (float): velocity in meter per second

        Returns:
            [type]: [description]
        """

        # get maximum deviation angle
        max_angle_dev = self._get_max_angle_deviation(velocity=velocity)
        max_angle_scale = max_angle_dev * self.walk_angle_deviation_factor
        is_in_collision_course = True

        # ranging
        for item in ranging:
            if item['angle'] == self.walk_angle:
                new_angle = int(numpy.random.normal(loc=angle, scale=max_angle_scale))
                new_angle = (new_angle * self.walk_direction_factor) + (
                            self.walk_angle * (1 - self.walk_direction_factor))
                self.walk_angle = int(new_angle)
                is_in_collision_course = False
                break

        # collision detection
        if is_in_collision_course:
            max_dist = 0
            max_angle = 0
            for item in ranging:
                if item['distance'] > max_dist:
                    max_angle = item['angle']
                    max_dist = item['distance']
            self.walk_angle = max_angle

        return self.walk_angle, is_in_collision_course
