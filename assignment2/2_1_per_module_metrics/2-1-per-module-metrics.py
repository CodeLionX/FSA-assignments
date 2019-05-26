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
use_git_root_for_command_db_file = True


# helper functions
def run_command(command, multiline_output=True):
    command = command if isinstance(command, list) else command.split()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )
    output, _ = process.communicate()
    text = output.decode()
    return text.split("\n") if multiline_output else text.strip()


def git_root():
    return run_command("git rev-parse --show-toplevel", multiline_output=False)


def mean(l):
    return float(sum(l) / max(len(l), 1))


def ensure_ending_slash(path):
    return path if path.endswith("/") else path + "/"


def count_lines(filename):
    with open(filename, "r", encoding='latin1') as f:
        for i, _ in enumerate(f, 1):
            pass
    return i


# heavy lifting functions
def find_source_code_files():
    output = run_command('find . -type f')
    # source code file pattern
    pattern = r'.*\.h$|.*\.hpp$|.*\.c$|.*\.cpp$'

    # strip first two chars './' added by the find tool
    sourceFiles = [line[2:] for line in output]
    return list(filter(lambda f: re.fullmatch(pattern, f), sourceFiles))


def load_mapping_from_compile_command_db():
    root_folder = git_root() if use_git_root_for_command_db_file else "."
    compile_command_db_file = os.path.join(root_folder, "compile_commands.json")
    if not os.path.isfile(compile_command_db_file):
        print("no compile command db file found!!")
        return {}

    # current working dir for path rewriting
    cwd = ensure_ending_slash(os.getcwd())

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
            object_name = os.path.join(directory, args.object_name)
            input_filename = args.input_file.replace(cwd, "")

            mapping[input_filename] = object_name

    return mapping


def get_last_year_revisions(filename):
    sep = ";"
    # timestamp of last commit in HEAD
    last_commit_unix_timestamp = run_command(
        "git log --pretty=%at -1",
        multiline_output=False
    )
    last_commit_timestamp = date.fromtimestamp(int(last_commit_unix_timestamp))
    # consider commits since last commit - 365 days
    delta = timedelta(days=-365)
    since = last_commit_timestamp + delta

    git_log_command = [
        'git', 'log', '--pretty=%at' + sep + '%ae',
        '--since="{}"'.format(since.isoformat()),
        filename
    ]
    revisions = run_command(git_log_command)
    return [r.split(sep) for r in revisions if r]


def get_identifiers_from(filename):
    # identifier pattern:
    # - consists of alpha-numeric characters and underscores
    # - must start with a letter or underscore (no digit)
    # this does detect text in comments as symbols
    pattern = r'[a-zA-Z_][a-zA-Z0-9_]*'
    # filter out C++ keywords: https://en.cppreference.com/w/cpp/keyword
    keywords = [
        "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel",
        "atomic_commit", "atomic_noexcept", "auto", "bitand", "bitor", "bool",
        "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t",
        "class", "compl", "concept", "const", "consteval", "constexpr",
        "const_cast", "continue", "co_await", "co_return", "co_yield",
        "decltype", "default", "delete", "do", "double", "dynamic_cast",
        "else", "enum", "explicit", "export", "extern", "false", "float",
        "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
        "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator",
        "or", "or_eq", "private", "protected", "public", "reflexpr",
        "register", "reinterpret_cast", "requires", "return", "short",
        "signed", "sizeof", "static", "static_assert", "static_cast", "struct",
        "switch", "synchronized", "template", "this", "thread_local", "throw",
        "true", "try", "typedef", "typeid", "typename", "union", "unsigned",
        "using", "virtual", "void", "volatile", "wchar_t", "while", "xor",
        "xor_eq"
    ]
    code = ""
    print("reading file", filename)
    with open(filename, "r", encoding='latin1') as f:
        for line in f:
            code += line
    identifiers = re.findall(pattern, code)
    return [
        symbol.lower()
        for symbol in identifiers
        if symbol.lower() not in keywords
    ]


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
        osploc = None
        if f in mapping:
            object_name = mapping[f]
            object_size = os.path.getsize(object_name)
            loc = count_lines(f)
            osploc = object_size / loc

        # metric 5: SoVkC
        identifiers = get_identifiers_from(f)
        n_all = len(identifiers)
        n_vk = sum([1 for symbol in identifiers if symbol.startswith("vk")])
        sovkc = n_vk / n_all

        metrics.append([f, mtbc, noc, bf, osploc, sovkc])

    writer = csv.writer(sys.stdout, delimiter=';')
    writer.writerow(["filename", "MTBC", "NoC", "BF", "OSpLoC", "SoVkC"])
    writer.writerows(metrics)


if __name__ == "__main__":
    main()
