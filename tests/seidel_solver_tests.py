import pytest

from seidel.seidel import ProgramStatus
import seidel

@pytest.mark.parametrize('id,expected_status', [
    (0, ProgramStatus.OPTIMAL),
    (1, ProgramStatus.OPTIMAL),
    (2, ProgramStatus.UNBOUNDED),
    (3, ProgramStatus.INFEASIBLE),
    (4, ProgramStatus.UNBOUNDED),
    (5, ProgramStatus.OPTIMAL),
])
def test_seidel_solver_status(id, expected_status):
    program = seidel.read_program(id, r'programs.txt')
    solver = seidel.Solver(seidel.Seidel())
    solver.solve(program)
    assert program.status == expected_status