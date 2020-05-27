"""
Checks the status of all git directories in the current directory.

Prints the output of git rev-parse
"""
import pathlib
from subprocess import check_output, call


if __name__ == "__main__":
    git_dirs = []
    for f in check_output(["find", ".", "-name", ".git"]).decode("utf-8").splitlines():
        git_dir = pathlib.Path(f).parent
        rev_parse = check_output(["git", "status", "-s"], cwd=git_dir).decode("utf-8").splitlines()
        print(f"\033[1;31m{git_dir}:")
        for r in rev_parse[0:10]:
            print(f"\t\033[1;34m{r}")
    # find . -name .git -execdir bash -c 'echo -en "\033[1;31m"repo: "\033[1;34m"; basename "`git rev-parse --show-topl>



