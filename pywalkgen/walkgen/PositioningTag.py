from pywalkgen.outliergen.OutlierGenerator import OutlierGenerator


class PositioningTag:
    def __init__(self, config):
        """
        Initializes Positioning Tag
        :param config: configuration file
        """
        outlier_config = config
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

    def get_measurement(self, ref):
        """
        Get UWB measurements
        :param ref: reference true position input in all 3 axes (x,y,z) in list format
        :return: uwb measurement in all 3 axes (x,y,z) in list format
        """
        uwb_result = [ref[0] + self.outlier_gen[0].generate(), ref[1] + self.outlier_gen[1].generate(),
                      ref[2] + self.outlier_gen[2].generate()]
        return uwb_result
