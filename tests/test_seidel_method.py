import pytest
import seidel
from seidel.geometric_objects import FLOAT_EQUALITY_DELTA, Point
from seidel.seidel import ProgramStatus, SeidelMethod


@pytest.mark.parametrize(
    "id,expected_status,expected_solution,expected_target",
    [
        (0, ProgramStatus.OPTIMAL, Point(3.0, 0.0), 6.0),
        (1, ProgramStatus.OPTIMAL, Point(1.8, 0.6), 4.2),
        (2, ProgramStatus.UNBOUNDED, None, None),
        (3, ProgramStatus.INFEASIBLE, None, None),
        # (4, ProgramStatus.UNBOUNDED, None, None),
        (5, ProgramStatus.OPTIMAL, Point(0.66, 0.0), 3.33),
    ],
)
def test_seidel_solver_status(id, expected_status, expected_solution, expected_target):
    program = seidel.read_program(id, r"programs.txt")
    solver = seidel.Solver(seidel.SeidelMethod())
    solver.solve(program)
    assert program.status == expected_status
    assert program.solution == expected_solution
    if expected_target is None:
        assert program.target(program.solution) is expected_target
    else:
        assert program.target(program.solution) - expected_target < FLOAT_EQUALITY_DELTA
