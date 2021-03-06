from asyncio import constants
from typing import List, Union

from .geometric_objects import IntersectionType, Point, Side
from .linear_program import AXIS_X, AXIS_Y, Constraint, LinearProgram, ProgramStatus
from .solver import SolvingMethod


class SeidelMethod(SolvingMethod):
    """Seidel method of solving linear programs"""

    def __init__(self, initial_solution: Union[Point, None] = None):
        """Settings of this method.

        Keyword arguments:
        starting_solution --
        """
        self.initial_solution = initial_solution

    def find_basic_solution(self, program: LinearProgram):
        """To find the basic solution:
            1. Find constraints that are enclosing the space.
            2. Use them to calculate intersection points between themselves and between them and axes.
        Best legal point will be the basic solution.

        The constraints should accept (-inf; y) and (x; -inf) 'points' to enclose the space.
        It can be a single constraint with positive coefficients or two constraints covering the 'points' separately.
        """
        xyminus = None
        xminus = None
        yminus = None
        for constraint in program.constraints:
            match constraint.sides():
                case (Side.MINUS, Side.MINUS):
                    xyminus = constraint
                    # if there is a single constraint enclosing the program,
                    # we dont need to search for a pair
                    break
                case (Side.MINUS, _):
                    if yminus is None:
                        xminus = constraint
                    else:
                        if yminus.intersect(constraint).type != IntersectionType.NONE:
                            xminus = constraint
                            break
                case (_, Side.MINUS):
                    if xminus is None:
                        yminus = constraint
                    else:
                        if xminus.intersect(constraint).type != IntersectionType.NONE:
                            yminus = constraint
                            break
        possible_solutions = []
        # if we found single enclosing constraint, use it to calculate the two possible solutions
        if xyminus is not None:
            # intersect the constraint with the X and Y axes
            # no need to check intersection type
            self.applied.append(xyminus)
            possible_solutions.append(xyminus.intersect(AXIS_X).point)
            possible_solutions.append(xyminus.intersect(AXIS_Y).point)

            program.constraints.remove(xyminus)
        else:
            # there was no constraint that encloses the program by itself
            # we use xminus and yminus (if both exist) to cover the
            # (-inf; y) and (x; -inf) 'points'

            if xminus is None or yminus is None:
                # the program is unbounded or infeasible, there were no two constraints that
                # can enclose the program together,
                # nor there was a single constraint doing this
                # OR there the constraint pair made program infeasible

                # hypothesis
                program.status = ProgramStatus.UNBOUNDED
                # if all below fails, this should be true

                if xminus is None:
                    # check if any constraint covers xminus
                    # if it there is one, it was parallel to the yminus without any overlap
                    for constraint in program.constraints:
                        if constraint.sides()[0] == Side.MINUS:
                            program.status = ProgramStatus.INFEASIBLE
                            break
                elif yminus is None:
                    # same for yminus
                    for constraint in program.constraints:
                        if constraint.sides()[1] == Side.MINUS:
                            program.status = ProgramStatus.INFEASIBLE
                            break
                elif xminus is None and yminus is None:
                    # there are no constraints maybe ?
                    pass

            else:
                # xminus and yminus exist so the program can be enclosed

                # the constraints cant be parallel to the axes in first two solutions because
                # we only check them against one axis where we assured
                # that they arent straight in the same way
                # ( the zero coefficient of the axis is not a zero in the constraint)

                # we only care about the xminus intersection with the X axis
                # because the Y axis intersection must be illegal
                self.applied.append(xminus)
                self.applied.append(yminus)
                possible_solutions.append(xminus.intersect(self.applied[0]).point)
                # likewise, we only care about the Y axis for yminus
                possible_solutions.append(yminus.intersect(self.applied[1]).point)

                """the third solution is the intersection of the xminus and yminus
                this solution can have parallel lines so we cant always get intersection point
                if this happens, there are three cases
                    1) constraints overlap by a line (unbounded)
                    2) constraints overlap by a stripe (unbounded)
                    3) constraints dont overlap (infeasible)
                cases 1) 2) are unbounded
                case 3) is infeasible
                constraints cant be 'almost the same' (differ only by C coefficient) in this case"""
                intersection = yminus.intersect(xminus)
                if intersection.type == IntersectionType.POINT:
                    possible_solutions.append(intersection.point)
                elif intersection.type == IntersectionType.OVERLAY:
                    # Solution space is a line
                    pass
                elif intersection.type == IntersectionType.NONE:
                    # constraints were parallel and dont overlap
                    pass

        # proceed only when there are possible solutions
        # (the only case when there are none is when program is unbounded)
        if len(possible_solutions) > 0:
            # need to check if the solutions are legal
            # ( if point.x >= 0 and point.y >= 0 )
            legal_solutions = [sol for sol in possible_solutions if sol.is_legal()]

            if len(legal_solutions) == 0:
                # if there are no legal solutions, the program is infeasible
                program.status = ProgramStatus.INFEASIBLE

            else:
                # we now have all the legal solutions, given the current constraints
                # now we find  the basic solution with the greatest value of target function
                # to compare against in the iterations
                program.solution = max(legal_solutions, key=program.target)

    def solve(self, program: LinearProgram) -> LinearProgram:
        self.program = program
        self.applied: List[Constraint] = []
        program.solution = self.initial_solution if not None else Point(0, 0)
        # other starting point
        # C = 10**10
        # program.solution = Point (C/(program.target.x*2), C/(program.target.y*2))

        self.find_basic_solution(program)
        assert program.solution is not None or program.status in [
            ProgramStatus.INFEASIBLE,
            ProgramStatus.UNBOUNDED,
        ]
        while (
            len(program.constraints) > 0 and program.status == ProgramStatus.NOT_SOLVED
        ):
            constraint = program.constraints.pop()
            self.apply_constraint(program, constraint)

        if len(program.constraints) == 0 and program.status == ProgramStatus.NOT_SOLVED:
            program.status = ProgramStatus.OPTIMAL

        if program.status != ProgramStatus.OPTIMAL:
            program.solution = None
        return program

    def apply_constraint(self, program, constraint):

        if constraint.contains(program.solution):
            # the constraint doesnt change optimal solution
            self.applied.append(constraint)
            return

        # the constraint changes optimal solution

        # list of all intersections that satisfy all applied constraints
        intersections: List[Point] = []
        for applied in self.applied:
            intersection = constraint.intersect(applied)

            if intersection.type == IntersectionType.OVERLAY:
                # if the constraints overlay, there is no need
                continue
            elif intersection.type == IntersectionType.NONE:
                # constraints are parallel and dont have common region
                program.status = ProgramStatus.INFEASIBLE
                intersections = []
                break

            for constr in self.applied:
                if constr.contains(intersection.point):
                    continue
                else:
                    # the point didnt belong to one of applied constraints
                    break
            else:
                # the point belongs to all applied constraints
                intersections.append(intersection.point)

        if len(intersections) == 0:
            program.status = ProgramStatus.INFEASIBLE
        else:
            program.solution = intersections[0]
            for solution in intersections:
                if program.target(solution) > program.target(program.solution):
                    program.solution = solution
            self.applied.append(constraint)

    def __str__(self):
        if self.program.status == ProgramStatus.OPTIMAL:
            return (
                "There is optimal solution\n"
                + str(self.program.solution)
                + f"\nThe value of target function at optimum is: {self.program.target(self.program.solution)}"
            )

        else:
            return str(self.program.status)
