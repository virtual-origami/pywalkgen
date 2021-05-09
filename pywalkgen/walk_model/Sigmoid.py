import math
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('/tmp/walkgen.log')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(levelname)-8s-[%(filename)s:%(lineno)d]-%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Sigmoid:
    """Sigmoid function generator
    """

    def __init__(self,mid_point=0,steepness=0.5,max_value=1,level_shift=0):
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

    def generate(self,x):
        """Generates output(y-axis) value for given input(X-axis) value

        Args:
            x (float): input(X-axis) value

        Returns:
            float: output(y-axis)
        """
        denom = 1 + math.exp(-1.0 * self.steepness * (x - self.mid_point))
        return (self.max_value / denom) + self.level_shift
