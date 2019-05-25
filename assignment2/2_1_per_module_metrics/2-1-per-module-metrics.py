#!/usr/bin/env python3
import sys
import csv
import json
import subprocess
import re
import argparse
import os
from datetime import timedelta
from datetime import date

# configuration
include_files_from_submodules = True


def find_source_code_files():
    working_dir = "."
    git_lsfiles_command = 'git ls-files' + (
        ' --recurse-submodules' if include_files_from_submodules else ''
    )
    # source code file pattern
    pattern = r'.*\.h$|.*\.hpp$|.*\.c$|.*\.cpp$'

    git_process = subprocess.Popen(
        git_lsfiles_command.split(),
        stdout=subprocess.PIPE,
        cwd=working_dir
    )
    output, _ = git_process.communicate()
    sourceFiles = output.decode().split("\n")
    return list(filter(lambda f: re.fullmatch(pattern, f), sourceFiles))


def load_mapping_from_compile_command_db():
    compile_command_db_file = "compile_commands.json"
    if not os.path.isfile(compile_command_db_file):
        print("no compile command db file found!!")
        return {}

    # current working dir for path rewriting
    cwd = os.getcwd()
    cwd = cwd if cwd.endswith("/") else cwd + "/"

    # configure argument parser for compile commands
    parser = argparse.ArgumentParser()
    parser.add_argument('-o',
        type=str,
        required=True,
        dest='object_name'
    )
    parser.add_argument('-c',
        type=str,
        required=True,
        dest='input_file'
    )

    # result dict
    mapping = {}

    with open(compile_command_db_file, 'r') as inputfile:
        compiler_info = json.load(inputfile)
        commands = [(obj['command'], obj['directory']) for obj in compiler_info]
        for command, directory in commands:
            args, _ = parser.parse_known_args(command.split())
            directory = directory if directory.endswith("/") else directory + "/"
            object_name = directory + args.object_name
            input_filename = args.input_file.replace(cwd, "")

            mapping[input_filename] = object_name

    return mapping


def get_last_year_revisions(filename):
    working_dir = "."
    git_log_command = [
        'git', 'log', '--pretty=%at;%ae', '--since="365 days"', filename
    ]

    git_process = subprocess.Popen(
        git_log_command,
        stdout=subprocess.PIPE,
        cwd=working_dir
    )
    output, _ = git_process.communicate()
    revisions = output.decode().split("\n")
    return [r.split(';') for r in revisions if r]


def mean(l):
    return float(sum(l) / max(len(l), 1))


def main():
    # find all files in repo
    filenames = find_source_code_files()
    # load compile mapping
    mapping = load_mapping_from_compile_command_db()

    # create metric list
    metrics = []

    for f in filenames:
        revisions = get_last_year_revisions(f)

        # metric 1: MTBC
        mtbc = None
        if len(revisions) >= 2:
            timestamps = [
                date.fromtimestamp(int(timestamp)) for timestamp, _ in revisions
            ]
            deltas = []
            for i in range(1, len(timestamps)):
                deltas.append((timestamps[i-1] - timestamps[i]).days)
            mtbc = mean(deltas)

        # metric 2: NoC
        authors = set([author for _, author in revisions])
        noc = len(authors) if len(authors) else None

        # metric 3: BF
        if(mtbc and noc):
            bf = noc**2 / mtbc
        else:
            bf = None

        # metric 4: OSpLoC
        if f in mapping:
            object_name = mapping[f]
            object_size = os.path.getsize(object_name)
            loc = count_lines(f)
            osploc = object_size / loc
        else:
            osploc = None

        # metric 5: SoVkC
        sovkc = None

        metrics.append([f, mtbc, noc, bf, osploc, sovkc])

    writer = csv.writer(sys.stdout, delimiter=';')
    writer.writerow(["filename", "MTBC", "NoC", "BF", "OSpLoC", "SoVkC"])
    writer.writerows(metrics)


def count_lines(filename):
    with open(filename, "r") as f:
        for i, _ in enumerate(f, 1):
            pass
    return i


if __name__ == "__main__":
    main()
