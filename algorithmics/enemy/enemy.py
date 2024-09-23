from abc import ABC, abstractmethod

from algorithmics.utils.coordinate import Coordinate


class Enemy(ABC):

    @abstractmethod
    def is_legal_leg(self, start: Coordinate, end: Coordinate) -> bool:
        """Check if the movement from start to end is legal, regarding that enemy

        :param start: initial coordinate of the movement
        :param end: final coordinate of the movement
        :return: True if the leg it legal for movement, False otherwise
        """
        pass
