from shapely.geometry import Point, Polygon


class DataAggregator:
    def __init__(self, area_config):
        self.id = area_config["id"]
        boundary = []
        for coordinate in area_config["boundary"]["coordinates"]:
            boundary.append(coordinate)
        self.polygon = Polygon(boundary)

    def is_in_radio_range(self, point):
        p1 = Point(point[0], point[1])
        return p1.within(self.polygon)


