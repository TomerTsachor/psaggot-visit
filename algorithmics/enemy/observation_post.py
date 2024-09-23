import math
from typing import List

from shapely.geometry import Point, LineString

from algorithmics.enemy.enemy import Enemy
from algorithmics.utils.coordinate import Coordinate


class ObservationPost(Enemy):

    def __init__(self, center: Coordinate, radius: float):
        """Initializes a new observation post object anchored at the given point

        :param center: the location of the observation post
        :param radius: observation distance of the post
        """
        self.center = center
        self.radius = radius

        self._circle = Point(self.center.x, self.center.y).buffer(self.radius - 1e-6)

    def approximate_boundary(self, n: int = 20) -> List[Coordinate]:
        """Compute polygon approximating the boundary of the post

        The returned polygon will out-bound the circle

        :param n: number of vertices in the approximation polygon
        :return: polygon approximating the circle
        """

        angle_step = math.radians(360 / n)
        buffed_radius = self.radius / math.cos(angle_step / 2)
        return [Coordinate(self.center.x + buffed_radius * math.sin(i * angle_step),
                           self.center.y + buffed_radius * math.cos(i * angle_step))
                for i in range(n)]

    def is_legal_leg(self, start: Coordinate, end: Coordinate) -> bool:
        leg = LineString([[start.x, start.y], [end.x, end.y]])
        return not self._circle.intersects(leg)
