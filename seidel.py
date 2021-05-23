import random
from enum import Enum


class Side(Enum):
    """ Which side of the axis satisfies the constraint at almost entire length """
    plus = -1
    minus = 1
    none = 0


class Intersection(Enum):
    none = 0
    point = 1
    overlay = 2


class Region(Enum):
    none = 0
    line = 1
    stripe = 2


class Problem(Enum):
    not_solved = 0
    optimal = 1
    infeasible = 2
    unbounded = 3


class Point(object):
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        self.x += 0.0
        self.y += 0.0
        return "(" + str(self.x) + "; " + str(self.y) + ")"

    def is_legal(self):
        return self.x >= 0 and self.y >= 0


class Line(object):
    def __init__(self, s: str):
        coefficients = s.split(' ')
        self.x = float(coefficients[0])
        self.y = float(coefficients[1])

    def slope(self):
        return -1 * self.x / self.y

    def __repr__(self):
        return str(self.x) + "x + " + str(self.y) + "y"


class Target(Line):

    def f(self, point: Point):
        return point.x*self.x + point.y*self.y

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
        return Side.plus if self.x < 0 else Side.none if self.x == 0 else Side.minus

    def yside(self):
        return Side.plus if self.y < 0 else Side.none if self.y == 0 else Side.minus

    def side(self):
        return self.xside(), self.yside()

    def fx(self, x):
        return x * self.slope() + self.b / self.y

    def fy(self, y):
        return -1 * y * self.y / self.x + self.b / self.x

    # is the point on the left side of the line
    def contains(self, point):
        return point.x * self.x + point.y * self.y <= self.b

    def intersect(self, other) -> (Point, Intersection):
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
                return Point(0, l1.fx(0)), Intersection.overlay
            else:
                # lines are parallel and dont overlay
                return Point(0, l1.fx(0)), Intersection.none
        else:
            # resolving case where Ax + By <= C1 and -Ax -By <= C2
            if l1.x == -1*l2.x and l1.y == -1*l2.y:
                # lines are parallel, but regions have inverse sides
                if l1.b == -1*l2.b:
                    # they share only line
                    return Point(0, l1.fx(0)), Intersection.overlay
                else:
                    # they either have common stripe or dont overlap
                    if l1.x < 0:
                        # set the one with positive x as first
                        l1, l2 = l2, l1
                    if l1.b < -1*l2.b:
                        return Point(0, 0), Intersection.none
                        # they dont overlap
                    else:
                        return Point(0, 0), Intersection.none
                        # they have common stripe

        # if self is horizontal (x==0 && y!=0)
        if l1.x == 0:
            y = l1.b / l1.y
            # and other is perpendicular (x!=0 && y==0)
            if l2.y == 0:
                x = l2.b / l2.x
            else:
                x = l2.fy(y)
            return Point(x, y), Intersection.point

        # if self is vertical
        if l1.y == 0:
            x = l1.b / l1.x
            # and other is perpendicular
            if l2.x == 0:
                y = l2.b / l2.y
            else:
                y = l2.fx(x)
            return Point(x, y), Intersection.point

        # if none above happened,
        # the intersection must be a point shared between 'generic' lines

        # x = (B1*C2 - B2*C1) / (A2*B1 - A1*B2)
        # where A = x, B = y, C=b
        x = (l1.y * l2.b - l2.y * l1.b) / (l2.x * l1.y - l1.x * l2.y)
        y = l1.fx(x)
        return Point(x, y), Intersection.point


class Seidel(object):
    def __init__(self, array: []):
        self.status = Problem.not_solved
        # first string in the array is the target function
        self.target = Target(array.pop(0))
        self.constraints = [Constraint(s) for s in array]
        random.shuffle(self.constraints)
        # the non negativity constraints are applied in the code, no need to add them manually
        self.applied: [Constraint] = [Constraint("-1 0 0"), Constraint("0 -1 0")]
        # self.solution = Point(0, 0)  # dummy value
        # self.find_basic_solution()
        C = 10**10
        self.solution = Point (C/(self.target.x*2), C/(self.target.y*2))

    def find_basic_solution(self):
        # to find the basic solution
        # find constraints that are enclosing the space
        # use them to calculate intersection points between themselves and between them and axes
        # best legal point will be the basic solution
        # the constraints should accept (-inf; y) and (x; -inf) 'points' to enclose the space
        # it can be a single constraint with positive coefficients
        # or two constraints covering the 'points' separately
        xyminus = None
        xminus = None
        yminus = None
        for constr in self.constraints:
            if constr.side() == (Side.minus, Side.minus):
                xyminus = constr
                # if there is a single constraint enclosing the problem,
                # we dont need to search for a pair
                break
            elif constr.side()[0] == Side.minus:
                if yminus is None:
                    xminus = constr
                else:
                    if yminus.intersect(constr)[1] != Intersection.none:
                        xminus = constr
                        break
            elif constr.side()[1] == Side.minus:
                if xminus is None:
                    yminus = constr
                else:
                    if xminus.intersect(constr)[1] != Intersection.none:
                        yminus = constr
                        break
        possible_solutions = []
        # if we found single enclosing constraint, use it to calculate the two possible solutions
        if xyminus is not None:
            # intersect the constraint with the X and Y axes
            # no need to check intersection type
            self.applied.append(xyminus)
            possible_solutions.append(
                xyminus.intersect(self.applied[0])[0])
            possible_solutions.append(
                xyminus.intersect(self.applied[1])[0])

            self.constraints.remove(xyminus)
        else:
            # there was no constraint that encloses the problem by itself
            # we use xminus and yminus (if both exist) to cover the
            # (-inf; y) and (x; -inf) 'points'

            if xminus is None or yminus is None:
                # the problem is unbounded or infeasible, there were no two constraints that
                # can enclose the problem together,
                # nor there was a single constraint doing this
                # OR there the constraint pair made problem infeasible

                # hypothesis
                self.status = Problem.unbounded
                # if all below fails, this should be true

                if xminus is None:
                    # check if any constraint covers xminus
                    # if it there is one, it was parallel to the yminus without any overlap
                    for constr in self.constraints:
                        if constr.side()[0] == Side.minus:
                            self.status = Problem.infeasible
                            break
                elif yminus is None:
                    # same for yminus
                    for constr in self.constraints:
                        if constr.side()[1] == Side.minus:
                            self.status = Problem.infeasible
                            break
                elif xminus is None and yminus is None:
                    # there are no constraints maybe ?
                    pass

            else:
                # xminus and yminus exist so the problem can be enclosed

                # the constraints cant be parallel to the axes in first two solutions because
                # we only check them against one axis where we assured
                # that they arent straight in the same way
                # ( the zero coefficient of the axis is not a zero in the constraint)

                # we only care about the xminus intersection with the X axis
                # because the Y axis intersection must be illegal
                self.applied.append(xminus)
                self.applied.append(yminus)
                possible_solutions.append(
                    xminus.intersect(self.applied[0])[0])
                # likewise, we only care about the Y axis for yminus
                possible_solutions.append(
                    yminus.intersect(self.applied[1])[0])

                # the third solution is the intersection of the xminus and yminus
                # this solution can have parallel lines so we cant always get intersection point
                # if this happens, there are three cases
                # 1) constraints overlap by a line (unbounded)
                # 2) constraints overlap by a stripe (unbounded)
                # 3) constraints dont overlap (infeasible)
                # cases 1) 2) are unbounded
                # case 3) is infeasible
                # constraints cant be 'almost the same' (differ only by C coefficient) in this case
                intersection = yminus.intersect(xminus)
                if intersection[1] == Intersection.point:
                    possible_solutions.append(
                        intersection[0])
                elif intersection[1] == Intersection.overlay:
                    # Solution space is a line
                    pass
                elif intersection[1] == Intersection.none:
                    # constraints were parallel and dont overlap
                    pass

        # proceed only when there are possible solutions
        # (the only case when there are none is when problem is unbounded)
        if len(possible_solutions) > 0:
            # need to check if the solutions are legal
            # ( if point.x >= 0 and point.y >= 0 )
            legal_solutions = []
            for sol in possible_solutions:
                if sol.is_legal():
                    legal_solutions.append(sol)

            if len(legal_solutions) == 0:
                # if there are no legal solutions, the problem is infeasible
                self.status = Problem.infeasible

            else:
                # we now have all the legal solutions, given the current constraints
                # now we find  the basic solution with the greatest value of target function
                # to compare against in the iterations
                self.solution = legal_solutions[0]
                for solution in legal_solutions:
                    if self.target.f(solution) > self.target.f(self.solution):
                        self.solution = solution

    def solve(self):
        while len(self.constraints) > 0 and self.status == Problem.not_solved:
            constraint = self.constraints.pop()
            self.apply_constraint(constraint)

        if len(self.constraints) == 0 and self.status == Problem.not_solved:
            self.status = Problem.optimal

    def apply_constraint(self, constraint):

        if constraint.contains(self.solution):
            # the constraint doesnt change optimal solution
            self.applied.append(constraint)
            return

        # the constraint changes optimal solution

        # list of all intersections that satisfy all applied constraints
        intersections: [Point] = []
        for con in self.applied:
            point, status = constraint.intersect(con)

            if status == Intersection.overlay:
                # if the constraints overlay, there is no need
                continue
            elif status == Intersection.none:
                # constraints are parallel and dont have common region
                self.status = Problem.infeasible
                intersections = []
                break
            for constr in self.applied:
                if constr.contains(point):
                    continue
                else:
                    # the point didnt belong to one of applied constraints
                    break
            else:
                # the point belongs to all applied constraints
                intersections.append(point)

        if len(intersections) == 0:
            print("There are no possible solutions")
            self.status = Problem.infeasible
        else:
            self.solution = intersections[0]
            for solution in intersections:
                if self.target.f(solution) > self.target.f(self.solution):
                    self.solution = solution
            self.applied.append(constraint)

    def __str__(self):
        if self.status == Problem.optimal:
            return "There is optimal solution\n" + \
                str(self.solution) + \
                "\nThe value of target function at optimum is: " + str(self.target.f(self.solution))
        elif self.status == Problem.unbounded:
            return "Problem is unbounded"
        elif self.status == Problem.infeasible:
            return "Problem is infeasible"
        elif self.status == Problem.not_solved:
            return "Problem is not solved yet"
