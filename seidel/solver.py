from abc import abstractmethod, ABC
from typing import Tuple

from .linear_program import LinearProgram

class SolvingMethod(ABC):
    @abstractmethod
    def __init__(self, program: LinearProgram) -> None:
        ...
    @abstractmethod
    def solve() -> Tuple[float, float]:
        ...

class Solver:
    def __init__(self, method: SolvingMethod, program: LinearProgram) -> None:
        self.method = method
        self.program = program

    def solve(self) -> LinearProgram:
        self.method(self.program).solve()