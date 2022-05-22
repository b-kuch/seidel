from typing import List

from .solver import SolvingMethod
from .geometric_objects import Point, Intersection, Side
from .linear_program import LinearProgram, ProblemStatus, AXIS_X, AXIS_Y

class Seidel(SolvingMethod):
    def __init__(self, program: LinearProgram):
        self.program = program
        self.status = ProblemStatus.NOT_SOLVED

        # self.target = program.target
        self.constraints = program.constraints
        self.applied = []

        self.solution = Point(0, 0)
        # other starting point
        # C = 10**10
        # self.solution = Point (C/(self.program.target.x*2), C/(self.program.target.y*2))
        
        self.find_basic_solution()

    def find_basic_solution(self):
        """To find the basic solution:
            1. Find constraints that are enclosing the space.
            2. Use them to calculate intersection points between themselves and between them and axes.
        Best legal point will be the basic solution.

        The constraints should accept (-inf; y) and (x; -inf) 'points' to enclose the space.
        It can be a single constraint with positive coefficients or two constraints covering the 'points' separately."""
        xyminus = None
        xminus = None
        yminus = None
        for constr in self.program.constraints:
            if constr.side() == (Side.MINUS, Side.MINUS):
                xyminus = constr
                # if there is a single constraint enclosing the problem,
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
            possible_solutions.append(
                xyminus.intersect(AXIS_X)[0])
            possible_solutions.append(
                xyminus.intersect(AXIS_Y)[0])

            self.program.constraints.remove(xyminus)
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
                self.status = ProblemStatus.UNBOUNDED
                # if all below fails, this should be true

                if xminus is None:
                    # check if any constraint covers xminus
                    # if it there is one, it was parallel to the yminus without any overlap
                    for constr in self.program.constraints:
                        if constr.side()[0] == Side.MINUS:
                            self.status = ProblemStatus.INFEASIBLE
                            break
                elif yminus is None:
                    # same for yminus
                    for constr in self.program.constraints:
                        if constr.side()[1] == Side.MINUS:
                            self.status = ProblemStatus.INFEASIBLE
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
                if intersection[1] == Intersection.POINT:
                    possible_solutions.append(
                        intersection[0])
                elif intersection[1] == Intersection.OVERLAY:
                    # Solution space is a line
                    pass
                elif intersection[1] == Intersection.NONE:
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
                self.status = ProblemStatus.INFEASIBLE

            else:
                # we now have all the legal solutions, given the current constraints
                # now we find  the basic solution with the greatest value of target function
                # to compare against in the iterations
                self.solution = legal_solutions[0]
                for solution in legal_solutions:
                    if self.program.target.f(solution) > self.program.target.f(self.solution):
                        self.solution = solution

    def solve(self) -> LinearProgram:
        while len(self.program.constraints) > 0 and self.status == ProblemStatus.NOT_SOLVED:
            constraint = self.program.constraints.pop()
            self.apply_constraint(constraint)

        if len(self.program.constraints) == 0 and self.status == ProblemStatus.NOT_SOLVED:
            self.status = ProblemStatus.OPTIMAL

        self.program.solution = self.solution
        self.program.status = self.status
        return self.program

    def apply_constraint(self, constraint):

        if constraint.contains(self.solution):
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
                self.status = ProblemStatus.INFEASIBLE
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
            self.status = ProblemStatus.INFEASIBLE
        else:
            self.solution = intersections[0]
            for solution in intersections:
                if self.program.target.f(solution) > self.program.target.f(self.solution):
                    self.solution = solution
            self.applied.append(constraint)

    def __str__(self):
        if self.status == ProblemStatus.OPTIMAL:
            return (
                "There is optimal solution\n" + 
                str(self.solution) + 
                f"\nThe value of target function at optimum is: {self.program.target.f(self.solution)}"
                )
                
        elif self.status == ProblemStatus.UNBOUNDED:
            return "Problem is unbounded"
        elif self.status == ProblemStatus.INFEASIBLE:
            return "Problem is infeasible"
        elif self.status == ProblemStatus.NOT_SOLVED:
            return "Problem is not solved yet"
