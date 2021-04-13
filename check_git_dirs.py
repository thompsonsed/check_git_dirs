"""
Checks the status of all git directories in the current directory.

Prints the output of git rev-parse
"""
from typing import Tuple
import pathlib
import argparse
from subprocess import check_output, call
import logging


def scan_all_git_repos(directory: pathlib.Path) -> Tuple[int, int, int]:
    """
    Checks all git repositories in the path for those requiring an action.

    :return: a tuple of the number of repositories with no changes, push required or unstaged changes
    """
    if not directory.exists():
        raise IOError(f"Directory does not exist at {directory}")
    git_dirs = check_output(["find", str(directory), "-name", ".git"]).decode("utf-8").splitlines()
    logging.info(f"Found {len(git_dirs)} directories containing git repos.")
    total_push = 0
    total_okay = 0
    total_unstaged = 0
    for f in git_dirs:
        git_dir = pathlib.Path(f).parent
        rev_parse = check_output(["git", "status", "-s"], cwd=git_dir).decode("utf-8").splitlines()
        output_message = f"\033[1;34m{git_dir}: "
        if len(rev_parse) == 0:
            git_status = check_output(["git", "status"], cwd=git_dir).decode("utf-8")
            if "Your branch is ahead" in git_status:
                output_message += "\033[1;33m - Requires push"
                total_push += 1
            else:
                output_message += "\033[1;32m \u2713"
                total_okay += 1
            logging.info(output_message)
        else:
            output_message += "\033[1;31m \u2717 Unstaged changes"
            logging.warning(output_message)
            total_unstaged += 1
        for r in rev_parse[0:10]:
            logging.warning(f"\t\033[1;31m{r}")
        if len(rev_parse) > 10:
            logging.warning("\t\033[1;31m....")
    return total_unstaged, total_push, total_okay


def dir_path(p: str):
    path = pathlib.Path(p)
    if path.is_dir():
        return p
    else:
        raise NotADirectoryError(p)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check the status of git repos in all subdirectories of the given folder."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Print out information on all repositories (not just those with unstaged commits",
    )
    parser.add_argument(
        "dir",
        nargs="?",
        default=".",
        help="Path to directory to parse in (defaults to current working directory",
        type=dir_path,
    )
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s")
    if args.verbose:
        logging.getLogger().setLevel(20)
    else:
        logging.getLogger().setLevel(30)
    total_unstaged, total_push, total_okay = scan_all_git_repos(pathlib.Path(args.dir))
    grand_total = total_unstaged + total_push + total_okay
    logging.warning("\033[1;32mChecks completed")
    if total_unstaged != 0:
        logging.warning(f"\033[1;31mUnstaged changes: {total_unstaged}")
    if total_push != 0:
        logging.warning(f"\033[1;33mRequires push: {total_push}")
    if grand_total == total_okay:
        logging.warning(f"\033[1;32mAll {total_okay} repositories okay.")
    else:
        logging.warning(f"\033[1;33m{total_okay}/{grand_total} okay")
    

