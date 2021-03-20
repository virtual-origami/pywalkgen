import math
import numpy
import matplotlib.pyplot as plt
from .Sigmoid import Sigmoid
import logging

logging.basicConfig(level=logging.WARNING, format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')


class WalkAngleGenerator:
    """Walk Angle Generator. This use Sigmoid function
    """

    def __init__(self, mid_point=0, steepness=0.5, max_value=1, level_shift=0):
        """Initializes Walk Angle generator

        Args:
            mid_point (int, optional): Midpoint of the sigmoid (point of inflection). Defaults to 0.
            steepness (float, optional): Steepness of the the function. Defaults to 0.5.
            max_value (int, optional): Maximum value of the Sigmoid function. Defaults to 1.
            level_shift (int, optional): Minimum value of the Sigmoid function. Defaults to 0.
        """
        self.sigmoid = Sigmoid( mid_point=mid_point, steepness=steepness,
                                max_value=max_value, level_shift=level_shift )

    def get_angle_deviation(self, velocity):
        """Get max angle of deviation given velocity

        Args:
            velocity (float): Velocity in meter per second

        Returns:
            float: Maximum angle of deviation
        """
        return self.sigmoid.generate( -1.0 * velocity )

    def generate(self, angle, velocity):
        """Generates angle value for given velocity

        Args:
            angle (float): maximum angle of deviation in radians
            velocity (float): velocity in meter per second

        Returns:
            [type]: [description]
        """
        one_standard_deviation = 0.341
        return numpy.random.normal( loc=angle, scale=self.get_angle_deviation( velocity=velocity ) * one_standard_deviation )


if __name__ == '__main__':
    def walk_angle_test():
        mid_point = -2
        steepness = 0.5
        # angle_deviation_degrees = 10.0
        # max_speed_mps = 40.0

        walk_angle_gen = WalkAngleGenerator(
            mid_point=mid_point, steepness=steepness, max_value=math.radians( 135 ), level_shift=math.radians( 45 ) )

        walk_angle_result = numpy.zeros( 40 )
        velocity_in = numpy.zeros( 40 )

        prev_angle = 0.0
        for i in range( 0, 40 ):
            walk_angle_result[i] = math.degrees(
                walk_angle_gen.generate( prev_angle, i * 1.0 ) )
            prev_angle = 0  # math.radians(walk_angle_result[i])
            velocity_in[i] = i

        plt.title( "Walk angle" )
        plt.xlabel( "Velocity" )
        plt.ylabel( "Angle in degrees" )
        plt.plot( velocity_in, walk_angle_result )
        plt.show()