from __future__ import annotations

from enum import Enum

FLOAT_EQUALITY_DELTA = 0.01


class Side(Enum):
    """Which side of the axis satisfies the constraint at almost entire length"""

    PLUS = -1
    MINUS = 1
    NEITHER = 0


class Intersection(Enum):
    NONE = 0
    POINT = 1
    OVERLAY = 2


class Region(Enum):
    NONE = 0
    LINE = 1
    STRIPE = 2


class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        self.x += 0.0
        self.y += 0.0
        return f"({self.x}, {self.y})"

    def __eq__(self, other: Point) -> bool:
        return (
            self.x - other.x < FLOAT_EQUALITY_DELTA
            and self.y - other.y < FLOAT_EQUALITY_DELTA
        )

    def is_legal(self):
        return self.x >= 0 and self.y >= 0


class Line:
    def __init__(self, s: str):
        coefficients = s.split(" ")
        self.x = float(coefficients[0])
        self.y = float(coefficients[1])

    def slope(self):
        return -1 * self.x / self.y

    def __repr__(self):
        return f"{self.x}x + {self.y}y"
