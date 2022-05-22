from .linear_program import LinearProgram


def read_problem(id: int, path: str) -> LinearProgram:
    problem = []
    with open(path, 'r') as f:
        for line in f:
            if line.startswith("!"+str(id)):
                break
        for line in f:
            if line.startswith("!"):
                break
            if line.startswith("#") or line.startswith("\n"):
                continue
            problem.append(line)

    problem = LinearProgram.from_strings(problem.pop(0), problem)
    return problem
