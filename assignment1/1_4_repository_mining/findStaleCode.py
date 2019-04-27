#!/usr/bin/env python3
import argparse
import subprocess


def main(from_ref, working_dir):
    # find all files in repo
    allFilesCommand = 'find . -path "./.git" -prune -o -type f'
    process1 = subprocess.Popen(
        allFilesCommand.split(),
        stdout=subprocess.PIPE,
        cwd=working_dir
    )
    output, _ = process1.communicate()
    # strip first two chars './' added by the find tool
    allFiles = [filename[2:] for filename in output.decode().split("\n")]

    # find all files that changed from the provided git ref (commit-sha, branch, ...)
    # use -l to increase threshold of file candidates for rename detection
    changedFilesCommand = 'git diff --name-only -l20000 ' + from_ref + ' HEAD'
    process2 = subprocess.Popen(
        changedFilesCommand.split(),
        stdout=subprocess.PIPE,
        cwd=working_dir
    )
    output2, _ = process2.communicate()
    nameset = set(output2.decode().split("\n"))

    # collect only those files, that have not changed (are not in the diff)
    stales = [name for name in allFiles if name not in nameset]

    # calculate and output percentage
    print("%2.1f%%" % (len(stales) / float(len(allFiles)) * 100))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--from-ref',
        type=str,
        required=True,
        dest='from_ref',
        help='git ref to the first commit that should be considered'
    )
    parser.add_argument('--wd',
        type=str,
        help='working directory',
        default='.'
    )

    args = parser.parse_args()
    main(args.from_ref, args.wd)
