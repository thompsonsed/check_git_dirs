"""
Checks the status of all git directories in the current directory.

Prints the output of git rev-parse
"""

import pathlib
import argparse
from subprocess import check_output
import logging


def add_branch_label(record_branches: bool, git_status: str, output_message: str) -> str:
    """
    Adds the branch label to the output message if record_branches is True.

    :param record_branches: Whether to record branch names.
    :param git_status: The status of the git repository.
    :param output_message: The current output message.
    :return: The updated output message with the branch label if applicable.
    """
    if record_branches:
        branch_name = git_status.splitlines()[0].replace("On branch ", "")
        return f"{output_message} - {branch_name}"
    return output_message


def read_check_ignore(cur_dir: pathlib.Path) -> list[str]:
    """
    Reads the .check_ignore file in the current directory if it exists.

    :param cur_dir: The current directory path.
    :return: A list of ignored directory names.
    """
    check_ignore_file = cur_dir / ".check_ignore"
    if check_ignore_file.exists() and check_ignore_file.is_file():
        with check_ignore_file.open("rt") as f:
            return [x.strip() for x in f.readlines()]
    return []


def find_git_dirs(directory: pathlib.Path) -> list[pathlib.Path]:
    """
    Finds all git directories in the given directory recursively.

    :param directory: The directory to search in.
    :return: A list of paths to git directories.
    """
    return [x.parent for x in directory.rglob(".git") if x.is_dir()]


def filter_ignored_dirs(
    git_dirs: list[pathlib.Path], ignore_names: list[str]
) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    """
    Filters out ignored directories from the list of git directories.

    :param git_dirs: The list of git directories.
    :param ignore_names: The list of directory names to ignore.
    :return: A tuple containing the filtered git directories and the ignored directories.
    """
    ignore_dirs = [x for x in git_dirs if x.name in ignore_names]
    git_dirs = [x for x in git_dirs if x.name not in ignore_names]
    return git_dirs, ignore_dirs


def process_git_dir(git_dir: pathlib.Path, record_branches: bool) -> tuple[str, bool, bool]:
    """
    Processes a single git directory to determine its status.

    :param git_dir: The git directory to process.
    :param record_branches: Whether to record branch names.
    :return: A tuple containing the output message, a boolean indicating if the repository is okay, and a boolean indicating if it requires a push.
    """
    rev_parse = check_output(["git", "status", "-s"], cwd=git_dir).decode("utf-8").splitlines()
    git_status = check_output(["git", "status"], cwd=git_dir).decode("utf-8")
    output_message = f"\033[1;34m{git_dir}: "
    if len(rev_parse) == 0:
        if "Your branch is ahead" in git_status:
            output_message += "\033[1;33m - Requires push"
            return add_branch_label(record_branches, git_status, output_message), False, True
        else:
            output_message += "\033[1;32m \u2713"
            return add_branch_label(record_branches, git_status, output_message), True, False
    else:
        output_message += "\033[1;31m \u2717 Unstaged changes"
        return add_branch_label(record_branches, git_status, output_message), False, False


def scan_all_git_repos(
    directory: pathlib.Path, record_branches: bool = False
) -> tuple[int, int, int, list[str], list[str]]:
    """
    Scans all git repositories in the given directory and checks their status.

    :param directory: The directory to scan.
    :param record_branches: Whether to record branch names.
    :return: A tuple containing the total number of unstaged changes, the total number of repositories requiring a push, the total number of okay repositories, a list of directories with unstaged changes, and a list of directories requiring a push.
    """
    if not directory.exists():
        raise IOError(f"Directory does not exist at {directory}")

    git_dirs = find_git_dirs(directory)
    ignore_names = read_check_ignore(directory)
    git_dirs, ignore_dirs = filter_ignored_dirs(git_dirs, ignore_names)

    logging.info(f"Found {len(git_dirs)} directories containing git repos.")
    if ignore_dirs:
        logging.info(f"Ignoring {len(ignore_dirs)} directories containing git repos.")

    total_push, total_okay, total_unstaged = 0, 0, 0
    unstaged_list, push_list = [], []

    for git_dir in git_dirs:
        output_message, is_okay, requires_push = process_git_dir(git_dir, record_branches)
        if requires_push:
            total_push += 1
            push_list.append(git_dir)
        elif is_okay:
            total_okay += 1
        else:
            total_unstaged += 1
            unstaged_list.append(git_dir)
        logging.info(output_message)

    return total_unstaged, total_push, total_okay, unstaged_list, push_list


def dir_path(p: str) -> str:
    """
    Validates if the given path is a directory.

    :param p: The path to validate.
    :return: The path if it is a directory.
    :raises NotADirectoryError: If the path is not a directory.
    """
    path = pathlib.Path(p)
    if path.is_dir():
        return p
    else:
        raise NotADirectoryError(p)


def main():
    """
    The main function that parses arguments and initiates the git repository scan.
    """
    parser = argparse.ArgumentParser(
        description="Check the status of git repos in all subdirectories of the given folder.",
        usage="python check_git_dirs.py -v -b",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Print out information on all repositories (not just those with unstaged commits)",
    )
    parser.add_argument(
        "dir",
        nargs="?",
        default=".",
        help="Path to directory to parse in (defaults to current working directory)",
        type=dir_path,
    )
    parser.add_argument(
        "-b", "--branch", action="store_true", default=False, help="Output the branch that each folder is currently on"
    )
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s")
    if args.verbose:
        logging.getLogger().setLevel(20)
    else:
        logging.getLogger().setLevel(30)
    total_unstaged, total_push, total_okay, unstaged_list, push_list = scan_all_git_repos(
        pathlib.Path(args.dir), args.branch
    )
    grand_total = total_unstaged + total_push + total_okay
    logging.warning("\033[1;32mChecks completed")
    if total_unstaged != 0:
        logging.warning(f"\033[1;31mUnstaged changes: {total_unstaged}")
        logging.info(f"\033[1;31m{', '.join([str(x) for x in unstaged_list])}")
    if total_push != 0:
        logging.warning(f"\033[1;33mRequires push: {total_push}")
        logging.info(f"\033[1;33m{', '.join([str(x) for x in push_list])}")
    if grand_total == total_okay:
        logging.warning(f"\033[1;32mAll {total_okay} repositories okay.")
    else:
        logging.warning(f"\033[1;33m{total_okay}/{grand_total} okay")


if __name__ == "__main__":
    main()
