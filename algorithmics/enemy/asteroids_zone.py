from typing import List

from shapely.geometry import Polygon, LineString

from algorithmics.enemy.enemy import Enemy
from algorithmics.utils.coordinate import Coordinate


class AsteroidsZone(Enemy):

    def __init__(self, boundary: List[Coordinate]):
        """Initializes a new asteroids zone area

        :param boundary: list of coordiantes representing the boundary of the asteroids zone
        """
        self.boundary = boundary
        self._polygon = Polygon([[c.x, c.y] for c in self.boundary]).buffer(-1e-6)

    def is_legal_leg(self, start: Coordinate, end: Coordinate) -> bool:
        leg = LineString([[start.x, start.y], [end.x, end.y]])
        return not self._polygon.intersects(leg)
