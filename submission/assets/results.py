import enum


class Results(enum.Enum):
    NO_PATH = enum.auto()
    BAD_PATH = enum.auto()
    NO_SOURCE = enum.auto()
    NO_TARGET = enum.auto()
    POST = enum.auto()
    ASTROID = enum.auto()
    RADAR = enum.auto()
    SUCCESS = enum.auto()
