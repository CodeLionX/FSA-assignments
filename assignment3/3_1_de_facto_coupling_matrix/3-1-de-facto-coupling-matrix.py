#!/usr/bin/env python3
import argparse
import subprocess
from datetime import timedelta
from datetime import date

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR - this script requires matplotlib")
    print("      - install it using pip via 'pip3 install matplotlib'")
    print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'")
    sys.exit(1)

deltaDays = 3


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


def load_all_commits():
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
    return commits, files, commits_per_day, commits_per_hash


def init_cooccurrence_matrix(files, value=0):
    matrix = {}
    for f1 in files:
        matrix[f1] = {}
        for f2 in files:
            matrix[f1][f2] = value
    return matrix


def plot():
    # use plt.pcolormesh(X, Y, C)
    pass


def plot_scatter(c):
    data = [
        [c[name1][name2] for name2 in c[name1]]
        for name1 in c
    ]
    fig = plt.figure()
    plt.pcolormesh(data)
    #plt.xticks(range(max(x)+1))
    #plt.xlabel("Number of Parameters")
    #plt.ylabel("Lines of Code")
    #plt.close()
    plt.show()
    return fig


def main(output):
    commits, files, day_index, hash_index = load_all_commits()
    matrix = init_cooccurrence_matrix(files)

    for index, commithash in enumerate(hash_index):
        current = commits[hash_index[commithash]]
        current_author = current.author
        current_timestamp = current.timestamp
        current_files = current.filenames

        # iterate over time window [-deltaDays; +deltaDays]
        other_files = []
        for x in range(-deltaDays, + deltaDays + 1):
            date = current_timestamp + timedelta(days=x)
            try:
                others = day_index[date]
                for i in others:
                    other_commit = commits[i]
                    if other_commit.author == current_author:
                        for filename in other_commit.filenames:
                            other_files.append(filename)
            except KeyError:
                continue

        for file1 in current_files:
            for file2 in other_files:
                matrix[file1][file2] += 1

    plot_scatter(matrix)


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
