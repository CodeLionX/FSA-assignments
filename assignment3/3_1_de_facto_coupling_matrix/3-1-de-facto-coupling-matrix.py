#!/usr/bin/env python3
import argparse
import subprocess

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR - this script requires matplotlib")
    print("      - install it using pip via 'pip3 install matplotlib'")
    print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'")
    sys.exit(1)


def run_command(command, multiline_output=True, separator="\n"):
    command = command if isinstance(command, list) else command.split()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )
    output, _ = process.communicate()
    text = output.decode()
    return text.split(separator) if multiline_output else text.strip()


def load_all_commits():
    commit_sep = "==="
    value_sep = ";"
    command = [
        "git", "log", "--name-only",
        "--pretty=format:" + commit_sep + "%H" + value_sep + "%ae" + value_sep + "%at",
        "--no-merges"
    ]
    result = run_command(command, multiline_output=True, separator=commit_sep)
    commits = {}
    for commit in result:
        if not commit:
            continue
        lines = commit.split("\n")
        hashcode, author, timestamp = lines[0].split(value_sep)
        filenames = [lines[i] for i in range(1, len(lines)) if lines[i]]
        commits[hashcode] = {
            "hashcode": hashcode,
            "author": author,
            "timestamp": timestamp,
            "filenames": filenames
        }
    for c in commits:
        print(c, commits[c], "\n")
    return commits


def main(output):
    commits = load_all_commits()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('output',
        type=str,
        nargs='?',
        help='output filename',
        default='output.pdf'
    )

    args = parser.parse_args()
    main(args.output)
