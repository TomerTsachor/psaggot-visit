import math


class Coordinate:
    """User-friendly coordinate class allowing for a broad range of operations

    Some Examples
    ----------------------------

    Creation & Basic Arithmetics
    ============================

    >>> c1 = Coordinate(2, 3)
    >>> c1 *= 2
    >>> c1
    Coordiante(x=4, y=6)

    >>> c1.x = 5
    >>> c1
    Coordinate(x=5, y=6)

    >>> c2 = Coordinate(x=-3, y=2)
    >>> c3 = c1 + c2
    >>> c3
    Coordinate(x=2, y=8)

    >>> c3 /= 2
    >>> c3
    Coordinate(x=1.0, y=4.0)

    Comparions
    ==========

    >>> c1 == Coordinate(5, 6)
    True
    >>> c1 == c3
    False

    Some Functions
    ==============

    >>> c3.distance_to(c2)
    4.47213595499958
    >>> c3.norm()
    4.123105625617661

    >>> import math
    >>> math.degrees(c3.direction_to(c1))
    26.5650511770779

    >>> str(c3), repr(c3)
    ('Coordiante(x=1.0, y=4.0)', 'Coordinate(x=1.0, y=4.0)')
    """

    def __init__(self, x: float, y: float) -> None:
        """Initializes a coordinate given its `x`, `y` values

        :param x: x value of the coordinate
        :param y: y value of the coordinate
        """
        super().__init__()

        self.x = x
        self.y = y

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Coordinate):
            return False
        return math.fabs(self.x - o.x) <= 1e-6 and math.fabs(self.y - o.y) <= 1e-6

    def __neg__(self) -> 'Coordinate':
        return Coordinate(-self.x, -self.y)

    def __add__(self, other) -> 'Coordinate':
        if not isinstance(other, Coordinate):
            raise TypeError('Addition is allowed only between two coordinates')
        return Coordinate(self.x + other.x, self.y + other.y)

    def __sub__(self, other) -> 'Coordinate':
        if not isinstance(other, Coordinate):
            raise TypeError('Subtraction is allowed only between two coordinates')
        return Coordinate(self.x - other.x, self.y - other.y)

    def __truediv__(self, other) -> 'Coordinate':
        if not isinstance(other, (float, int)):
            raise TypeError('Division on coordinate is only possible with a numerical')
        return Coordinate(self.x / other, self.y / other)

    def __mul__(self, other) -> 'Coordinate':
        if not isinstance(other, (float, int)):
            raise TypeError('Multiplication on coordinate is only possible with a numerical')
        return Coordinate(self.x * other, self.y * other)

    def distance_to(self, other: 'Coordinate') -> float:
        """Computes the euclidean distance to the other coordinate
        """
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def direction_to(self, other: 'Coordinate') -> float:
        """Computes the direction to the other coordinate
        """
        return math.atan2(other.y - self.y, other.x - self.x)

    def distance_to_squared(self, other: 'Coordinate') -> float:
        """Computes the square of the euclidean distance to the other coordinate
        """
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2

    def norm(self) -> float:
        """Computes the norm of this 2d vector
        """
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __str__(self) -> str:
        return f'Coordinate(x={self.x}, y={self.y})'

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_str(cls, s: str) -> 'Coordinate':
        """Compute coordinate from string representation

        :param s: string representing a coordinate
        :return: coordinate object
        """
        # Remove 'Coordinate' heading and parenthesis
        s = s[11:-1]

        # Split to components
        x, y = s.split(', ')

        # Remove 'x=', 'y=' headers
        x, y = x[2:], y[2:]

        # Convert to floats
        x, y = float(x), float(y)

        # Return coordinate object
        return Coordinate(x, y)

    def __hash__(self) -> int:
        return hash(self.x) ^ hash(self.y)
