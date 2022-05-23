import typer

import seidel


def main(id: int, program_file_path: str = "programs.txt") -> seidel.SeidelMethod:
    program = seidel.read_program(id, program_file_path)
    solver = seidel.Solver(seidel.SeidelMethod())
    solver.solve(program)
    typer.echo(program)
    return program


if __name__ == "__main__":
    typer.run(main)
