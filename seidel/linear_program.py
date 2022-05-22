from __future__ import annotations

import random
from typing import List, Tuple
from enum import Enum

from .geometric_objects import Line, Point, Side, Intersection

class ProgramStatus(Enum):
    NOT_SOLVED = "Program is not solved yet"
    OPTIMAL = "Program has optimal solution"
    INFEASIBLE = "Program is infeasible"
    UNBOUNDED = "Program is unbounded"

class Target(Line):
    def f(self, point: Point) -> float:
        return point.x*self.x + point.y*self.y

    def __call__(self, point: Point) -> float:
        return self.f(point)

    def find_x(self, cmax, y):
        return (cmax + self.y*y) / self.x

    def find_y(self, cmax, x):
        return (cmax - self.x*x) / self.y


class Constraint(Line):
    """ All constraints are 'less than or equal' inequalities. """

    def __init__(self, s: str):
        super().__init__(s)
        coefficients = s.split(' ')
        self.b = float(coefficients[2])

    def __repr__(self):
        return str(self.x) + "x + " + str(self.y) + "y <= " + str(self.b)

    def xside(self):
        return Side.PLUS if self.x < 0 else Side.NEITHER if self.x == 0 else Side.MINUS

    def yside(self):
        return Side.PLUS if self.y < 0 else Side.NEITHER if self.y == 0 else Side.MINUS

    def side(self):
        return self.xside(), self.yside()

    def fx(self, x):
        return x * self.slope() + self.b / self.y

    def fy(self, y):
        return -1 * y * self.y / self.x + self.b / self.x

    # is the point on the left side of the line
    def contains(self, point):
        return point.x * self.x + point.y * self.y <= self.b

    def intersect(self, other) -> Tuple[Point, Intersection]:
        l1 = self
        l2 = other

        # if l2 is horizontal or vertical, swap them to remove redundant checks
        if l2.x == 0 or l2.y == 0:
            l1, l2 = l2, l1

        # if the lines are parallel
        # this doesnt cover Ax + By <= C1 and -Ax -By <= C2
        if l1.x == l2.x and l1.y == l2.y:
            # and if the lines overlay
            if l1.b == l2.b:
                return Point(0, l1.fx(0)), Intersection.OVERLAY
            else:
                # lines are parallel and dont overlay
                return Point(0, l1.fx(0)), Intersection.NONE
        else:
            # resolving case where Ax + By <= C1 and -Ax -By <= C2
            if l1.x == -1*l2.x and l1.y == -1*l2.y:
                # lines are parallel, but regions have inverse sides
                if l1.b == -1*l2.b:
                    # they share only line
                    return Point(0, l1.fx(0)), Intersection.OVERLAY
                else:
                    # they either have common stripe or dont overlap
                    if l1.x < 0:
                        # set the one with positive x as first
                        l1, l2 = l2, l1
                    if l1.b < -1*l2.b:
                        return Point(0, 0), Intersection.NONE
                        # they dont overlap
                    else:
                        return Point(0, 0), Intersection.NONE
                        # they have common stripe

        # if self is horizontal (x==0 && y!=0)
        if l1.x == 0:
            y = l1.b / l1.y
            # and other is perpendicular (x!=0 && y==0)
            if l2.y == 0:
                x = l2.b / l2.x
            else:
                x = l2.fy(y)
            return Point(x, y), Intersection.POINT

        # if self is vertical
        if l1.y == 0:
            x = l1.b / l1.x
            # and other is perpendicular
            if l2.x == 0:
                y = l2.b / l2.y
            else:
                y = l2.fx(x)
            return Point(x, y), Intersection.POINT

        # if none above happened,
        # the intersection must be a point shared between 'generic' lines

        # x = (B1*C2 - B2*C1) / (A2*B1 - A1*B2)
        # where A = x, B = y, C=b
        x = (l1.y * l2.b - l2.y * l1.b) / (l2.x * l1.y - l1.x * l2.y)
        y = l1.fx(x)
        return Point(x, y), Intersection.POINT

AXIS_X = Constraint('-1 0 0')
AXIS_Y = Constraint('0 -1 0')

class LinearProgram:
    def __init__(
        self,
        target: Target,
        constraints: List[Constraint],
        positive_x: bool=True,
        positive_y: bool=True) -> None:

        self.status = ProgramStatus.NOT_SOLVED
        self.solution = None
        self.target = target
        self.constraints = constraints
        if positive_x:
            self.constraints.append(Constraint("-1 0 0"))
        if positive_y:
            self.constraints.append(Constraint("0 -1 0"))
        random.shuffle(self.constraints)

    @classmethod
    def from_strings(cls, target_str: str, constraints_strs: List[str]) -> LinearProgram:
        return cls(Target(target_str), [Constraint(c) for c in constraints_strs])