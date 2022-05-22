from abc import abstractmethod, ABC
from typing import Tuple

from seidel.geometric_objects import Line

from .linear_program import LinearProgram

class SolvingMethod(ABC):
    @abstractmethod
    def __init__(self, program: LinearProgram) -> None:
        ...
    @abstractmethod
    def solve() -> Tuple[float, float]:
        ...

class Solver:
    def __init__(self, method: SolvingMethod) -> None:
        self.method = method

    def solve(self, program: LinearProgram) -> LinearProgram:
        self.method.solve(program)