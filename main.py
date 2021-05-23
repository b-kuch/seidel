from seidel import Seidel

if __name__ == '__main__':
    i = 2
    problem = []
    with open('A.txt', 'r') as f:
        for line in f:
            if line.startswith("!"+str(i)):
                break
        for line in f:
            if line.startswith("!"):
                break
            if line.startswith("#") or line.startswith("\n"):
                continue
            problem.append(line)

    program = Seidel(problem)
    program.solve()
    print(program)
