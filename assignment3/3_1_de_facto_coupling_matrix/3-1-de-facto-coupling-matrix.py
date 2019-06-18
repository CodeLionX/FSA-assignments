#!/usr/bin/env python3
import argparse
import subprocess
import math
import sys
import re
from datetime import timedelta
from datetime import date

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize, LogNorm
except ImportError:
    print("ERROR - this script requires matplotlib")
    print("      - install it using pip via 'pip3 install matplotlib'")
    print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'")
    sys.exit(1)

deltaDays = 3
sourcecode_pattern = r'.*\.ts$|.*\.tsx$|.*\.js$|.*\.jsx$'


class Commit:
    def __init__(self, hash, author, timestamp, files):
        self.hash = hash
        self.author = author
        self.timestamp = timestamp
        self.filenames = files


def run_command(command, multiline_output=True, separator="\n"):
    command = command if isinstance(command, list) else command.split()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )
    output, _ = process.communicate()
    text = output.decode()
    return text.split(separator) if multiline_output else text.strip()


def load_all_commits(filter_files):
    commit_sep = "==="
    value_sep = ";"
    command = [
        "git", "log", "--name-only",
        "--pretty=format:" + commit_sep + "%H" + value_sep + "%ae" + value_sep + "%at",
        "--no-merges"
    ]
    result = run_command(command, multiline_output=True, separator=commit_sep)

    commits = []
    commits_per_hash = {}
    commits_per_day = {}
    files = set()
    i = 0
    for commit in result:
        if not commit:
            continue
        lines = commit.split("\n")
        hexhash, author, timestamp = lines[0].split(value_sep)
        timestamp = date.fromtimestamp(int(timestamp))
        filenames = [lines[j] for j in range(1, len(lines)) if lines[j]]
        if filter_files:
            filenames = list(filter(
                lambda f: re.fullmatch(sourcecode_pattern, f),
                filenames
            ))
        commits.append(Commit(
            hexhash,
            author,
            timestamp,
            filenames
        ))
        files.update(filenames)

        # update indices
        commits_per_hash[hexhash] = i
        if timestamp not in commits_per_day:
            commits_per_day[timestamp] = []
        commits_per_day[timestamp].append(i)

        i += 1
    return commits, sorted(list(files)), commits_per_day, commits_per_hash


def init_cooccurrence_matrix(files, value=0):
    matrix = {}
    for f1 in files:
        matrix[f1] = {}
        for f2 in files:
            matrix[f1][f2] = value
    return matrix


def plot(c, clip):
    # clip to max 30 occurrences as highest value (for color mapping)
    if clip:
        v_max = 30
        v_min = 0
        data = [
            [c[name1][name2] for name2 in c[name1]]
            for name1 in c
        ]
    else:
        v_max = 0
        v_min = math.inf
        data = []
        for name1 in c:
            row = []
            for name2 in c[name1]:
                value = c[name1][name2]
                if value > v_max:
                    v_max = value
                if value < v_min:
                    v_min = value
                row.append(value)
            data.append(row)

    norm = Normalize(vmin=v_min, vmax=v_max, clip=clip)
    #norm = LogNorm(vmin=v_min + 1, vmax=v_max, clip=False)

    fig = plt.figure()
    plt.imshow(data, cmap=plt.cm.YlGn, norm=norm)

    labels = [name for name in c]
    ticks = range(len(labels))
    plt.xticks(ticks, labels, ma="center", rotation="vertical")
    plt.yticks(ticks, labels, ma="center", va="center")

    cb = plt.colorbar()
    cb.set_label("Number of conjunct changes")
    plt.close()
    #plt.show()

    return fig


def main(output, clip, filter_files):
    commits, files, day_index, hash_index = load_all_commits(filter_files)
    matrix = init_cooccurrence_matrix(files)

    for index, commithash in enumerate(hash_index):
        current = commits[hash_index[commithash]]
        current_author = current.author
        current_timestamp = current.timestamp
        current_files = current.filenames

        # iterate over time window [-deltaDays; +deltaDays]
        other_files = []
        for x in range(- deltaDays, + deltaDays + 1):
            date = current_timestamp + timedelta(days=x)
            try:
                others = day_index[date]
                for i in others:
                    other_commit = commits[i]
                    if other_commit.hash != current.hash and other_commit.author == current_author:
                        for filename in other_commit.filenames:
                            other_files.append(filename)
            except KeyError:
                pass

        for file1 in current_files:
            for file2 in other_files + current_files:
                if file1 != file2:
                    matrix[file1][file2] += 1

    fig = plot(matrix, clip)
    fig.savefig(output, bbox_inches="tight")
    print("Figure saved to", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('output',
        type=str,
        nargs='?',
        help='output filename',
        default='output.pdf'
    )

    parser.add_argument('--no-clip', '-c',
        help='disable color mapping clipping',
        action='store_true',
        dest='noclip'
    )

    parser.add_argument('--no-filter-files', '-f',
        help='disable color mapping clipping',
        action='store_true',
        dest='no_filter_files'
    )

    args = parser.parse_args()
    main(args.output, not args.noclip, not args.no_filter_files)
