import pytest

from seidel.seidel import ProblemStatus
import seidel

@pytest.mark.parametrize('id,expected_status', [
    (0, ProblemStatus.OPTIMAL),
    (1, ProblemStatus.OPTIMAL),
    (2, ProblemStatus.UNBOUNDED),
    (3, ProblemStatus.INFEASIBLE),
    (4, ProblemStatus.UNBOUNDED),
    (5, ProblemStatus.OPTIMAL),
])
def test_seidel_solver_status(id, expected_status):
    problem = seidel.read_problem(id, r'programs.txt')
    solver = seidel.Solver(seidel.Seidel, problem)
    program = solver.solve()
    assert problem.status == expected_status