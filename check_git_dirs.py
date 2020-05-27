"""
Checks the status of all git directories in the current directory.

Prints the output of git rev-parse
"""
import pathlib
from subprocess import check_output, call

if __name__ == "__main__":
    for f in check_output(["find", ".", "-name", ".git"]).decode("utf-8").splitlines():
        git_dir = pathlib.Path(f).parent
        rev_parse = check_output(["git", "status", "-s"], cwd=git_dir).decode("utf-8").splitlines()
        output_message = f"\033[1;34m{git_dir}: "
        if len(rev_parse) == 0:
            git_status = check_output(["git", "status", "-s"], cwd=git_dir).decode("utf-8")
            if "Your branch is ahead" in git_status:
                output_message += "\033[1;33m - Requires push"
            else:
                output_message += "\033[1;32m \u2713 All up to date"
        else:
            output_message += "\033[1;31m \u2717 Unstaged changes"
        print(output_message)
        for r in rev_parse[0:10]:
            print(f"\t\033[1;31m{r}")
        if len(rev_parse) > 10:
            print("\t\033[1;31m....")



