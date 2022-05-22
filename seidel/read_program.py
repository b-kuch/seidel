from .linear_program import LinearProgram


def read_program(id: int, path: str) -> LinearProgram:
    program = []
    with open(path, 'r') as f:
        for line in f:
            if line.startswith("!"+str(id)):
                break
        for line in f:
            if line.startswith("!"):
                break
            if line.startswith("#") or line.startswith("\n"):
                continue
            program.append(line)

    program = LinearProgram.from_strings(program.pop(0), program)
    return program
