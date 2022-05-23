from typing import List

from .geometric_objects import Intersection, Point, Side
from .linear_program import AXIS_X, AXIS_Y, LinearProgram, ProgramStatus
from .solver import SolvingMethod


class Seidel(SolvingMethod):
    def __init__(self):
        ...

    def find_basic_solution(self, program: LinearProgram):
        """To find the basic solution:
            1. Find constraints that are enclosing the space.
            2. Use them to calculate intersection points between themselves and between them and axes.
        Best legal point will be the basic solution.

        The constraints should accept (-inf; y) and (x; -inf) 'points' to enclose the space.
        It can be a single constraint with positive coefficients or two constraints covering the 'points' separately."""
        xyminus = None
        xminus = None
        yminus = None
        for constr in program.constraints:
            if constr.side() == (Side.MINUS, Side.MINUS):
                xyminus = constr
                # if there is a single constraint enclosing the program,
                # we dont need to search for a pair
                break
            elif constr.side()[0] == Side.MINUS:
                if yminus is None:
                    xminus = constr
                else:
                    if yminus.intersect(constr)[1] != Intersection.NONE:
                        xminus = constr
                        break
            elif constr.side()[1] == Side.MINUS:
                if xminus is None:
                    yminus = constr
                else:
                    if xminus.intersect(constr)[1] != Intersection.NONE:
                        yminus = constr
                        break
        possible_solutions = []
        # if we found single enclosing constraint, use it to calculate the two possible solutions
        if xyminus is not None:
            # intersect the constraint with the X and Y axes
            # no need to check intersection type
            self.applied.append(xyminus)
            possible_solutions.append(xyminus.intersect(AXIS_X)[0])
            possible_solutions.append(xyminus.intersect(AXIS_Y)[0])

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
                    for constr in program.constraints:
                        if constr.side()[0] == Side.MINUS:
                            program.status = ProgramStatus.INFEASIBLE
                            break
                elif yminus is None:
                    # same for yminus
                    for constr in program.constraints:
                        if constr.side()[1] == Side.MINUS:
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
                possible_solutions.append(xminus.intersect(self.applied[0])[0])
                # likewise, we only care about the Y axis for yminus
                possible_solutions.append(yminus.intersect(self.applied[1])[0])

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
                if intersection[1] == Intersection.POINT:
                    possible_solutions.append(intersection[0])
                elif intersection[1] == Intersection.OVERLAY:
                    # Solution space is a line
                    pass
                elif intersection[1] == Intersection.NONE:
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
        self.applied = []
        program.solution = Point(0, 0)
        # other starting point
        # C = 10**10
        # program.solution = Point (C/(program.target.x*2), C/(program.target.y*2))

        self.find_basic_solution(program)

        while (
            len(program.constraints) > 0 and program.status == ProgramStatus.NOT_SOLVED
        ):
            constraint = program.constraints.pop()
            self.apply_constraint(program, constraint)

        if len(program.constraints) == 0 and program.status == ProgramStatus.NOT_SOLVED:
            program.status = ProgramStatus.OPTIMAL

        return program

    def apply_constraint(self, program, constraint):

        if constraint.contains(program.solution):
            # the constraint doesnt change optimal solution
            self.applied.append(constraint)
            return

        # the constraint changes optimal solution

        # list of all intersections that satisfy all applied constraints
        intersections: List[Point] = []
        for con in self.applied:
            point, status = constraint.intersect(con)

            if status == Intersection.OVERLAY:
                # if the constraints overlay, there is no need
                continue
            elif status == Intersection.NONE:
                # constraints are parallel and dont have common region
                program.status = ProgramStatus.INFEASIBLE
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
