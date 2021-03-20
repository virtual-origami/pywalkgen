import math
import matplotlib.pyplot as plt
import numpy
import logging

logging.basicConfig(level=logging.WARNING, format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')


class Sigmoid:
    """Sigmoid function generator
    """

    def __init__(self, mid_point=0, steepness=0.5, max_value=1, level_shift=0):
        """Initializes Sigmoid function

        Args:
            mid_point (int, optional): Midpoint of the sigmoid (point of inflection). Defaults to 0.
            steepness (float, optional): Steepness of the the function. Defaults to 0.5.
            max_value (int, optional): Maximum value of the Sigmoid function. Defaults to 1.
            level_shift (int, optional): Minimum value of the Sigmoid function. Defaults to 0.
        """
        self.mid_point = mid_point
        self.steepness = steepness
        self.max_value = max_value
        self.level_shift = level_shift

    def generate(self, x):
        """Generates output(y-axis) value for given input(X-axis) value

        Args:
            x (float): input(X-axis) value

        Returns:
            float: output(y-axis)
        """
        denom = 1 + math.exp( -1.0 * self.steepness * (x - self.mid_point) )
        return (self.max_value / denom) + self.level_shift


if __name__ == '__main__':
    def sigmoid_wave_test():
        number_of_samples = 100

        sigmoid_1 = Sigmoid( steepness=0.1 )
        sigmoid_1_out = numpy.zeros( number_of_samples )
        sigmoid_1_in = numpy.zeros( number_of_samples )

        start_val = int( number_of_samples / 2 )
        stop_val = int( (-1 * start_val) - 1 )
        for i in range( start_val, stop_val, -1 ):
            sigmoid_1_out[i - start_val] = sigmoid_1.generate( i )
            sigmoid_1_in[i - start_val] = i

        plt.title( "Sigmoid-1 ($n = " + str( number_of_samples ) + "$ steps)" )
        plt.xlabel( "Input samples" )
        plt.ylabel( "Output values" )
        plt.plot( sigmoid_1_in, sigmoid_1_out )
        plt.show()


    sigmoid_wave_test()