import typer
import seidel

def main(id: int, problem_file_path: str) -> seidel.Seidel:
    problem = seidel.read_problem(id, problem_file_path)
    program = seidel.Seidel(problem)
    program.solve()
    typer.echo(program)
    return program


if __name__ == "__main__":
    typer.run(main)