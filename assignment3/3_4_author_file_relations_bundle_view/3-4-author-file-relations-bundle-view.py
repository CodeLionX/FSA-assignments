#!/usr/bin/env python3
import argparse
import subprocess
import re
import sys
from datetime import timedelta
from datetime import date


sourcecode_pattern = r'.*\.ts$|.*\.tsx$|.*\.js$|.*\.jsx$'


class Commit:
    def __init__(self, author, timestamp, files):
        self.author = author
        self.timestamp = timestamp
        self.filenames = files

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Commit(author={},timestamp={},filenames=List(n={}))".format(
            self.author,
            self.timestamp.isoformat(),
            len(self.filenames)
        )


class Node():
    def __init__(self, node_type, identifier, noc, mtbc):
        self.node_type = node_type
        self.identifier = identifier
        self.noc = noc
        self.mtbc = mtbc

    def __str__(self):
        return self.serialize()

    def __repr__(self):
        return self.serialize()

    def serialize(self):
        return "node;{};{};{};{}".format(
            self.node_type,
            self.identifier,
            self.noc,
            self.mtbc
        )


class Module(Node):
    def __init__(self, identifier, noc, mtbc):
        super().__init__("module", identifier, noc, mtbc)


class Author(Node):
    def __init__(self, identifier, noc, mtbc):
        super().__init__("author", identifier, noc, mtbc)


class Edge():
    def __init__(self, author_id, module_id):
        self.edge_type = "edit"
        self.author_id = author_id
        self.module_id = module_id

    def __str__(self):
        return self.serialize()

    def __repr__(self):
        return self.serialize()

    def __eq__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return ((self.author_id, self.module_id) ==
                (other.author_id, other.module_id))

    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return ((self.author_id, self.module_id) <
                (other.author_id, other.module_id))

    def _is_valid_operand(self, other):
        return (hasattr(other, "author_id") and
                hasattr(other, "module_id"))

    def serialize(self):
        return "edge;{};{};{}".format(
            self.edge_type,
            self.author_id,
            self.module_id
        )


def run_command(command, multiline_output=True, separator="\n"):
    command = command if isinstance(command, list) else command.split()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )
    output, _ = process.communicate()
    text = output.decode()
    return text.split(separator) if multiline_output else text.strip()


def flatMap(f, items):
    for item in items:
        for inner_item in f(item):
            yield inner_item


def partialMap(f, items):
    for item in items:
        newItem = f(item)
        if newItem is not None:
            yield newItem


def mean(l):
    return float(sum(l) / max(len(l), 1))


def parse_raw_commit(raw_commit, value_sep, filter_files):
    if not raw_commit:
        return None
    lines = raw_commit.split("\n")
    author, timestamp = lines[0].split(value_sep)
    timestamp = date.fromtimestamp(int(timestamp))
    filenames = [lines[j] for j in range(1, len(lines)) if lines[j]]
    if filter_files:
        filenames = list(filter(
            lambda f: re.fullmatch(sourcecode_pattern, f),
            filenames
        ))
    if not filenames:
        print(
            "WARN: ignoring commit from author",
            author,
            "on",
            timestamp.isoformat(),
            "- no source files changed by commit",
            file=sys.stderr
        )
        return None
    return Commit(
        author,
        timestamp,
        filenames
    )


def load_all_commits(filter_files):
    commit_sep = "==="
    value_sep = ";"
    command = [
        "git", "log", "--name-only",
        "--pretty=format:" + commit_sep + "%ae" + value_sep + "%at",
        "--no-merges"
    ]
    results = run_command(command, multiline_output=True, separator=commit_sep)
    return list(partialMap(
        lambda result: parse_raw_commit(result, value_sep, filter_files),
        results
    ))


def collect_edges(commits):
    return list(flatMap(
        lambda c: (Edge(c.author, filename) for filename in c.filenames),
        commits
    ))


def collect_nodes(commits):
    authors = set(commit.author for commit in commits)
    modules = set(flatMap(
        lambda c: (filename for filename in c.filenames),
        commits
    ))
    return authors, modules


def calc_noc_for_module(module_id, edges):
    return len(list(
        filter(
            lambda e: e.module_id == module_id,
            edges
        )
    ))


def calc_noc_for_author(author_id, edges):
    return len(list(
        filter(
            lambda e: e.author_id == author_id,
            edges
        )
    ))


def calc_mtbc(commits):
    commits = list(commits)
    mtbc = 0
    if len(commits) > 2:
        deltas = []
        # git log returns logs ordered descending, so they are already sorted
        for i in range(1, len(commits)):
            deltas.append(
                (commits[i-1].timestamp - commits[i].timestamp).days
            )
        mtbc = mean(deltas)
    return mtbc


def serialize_all(items):
    return list(map(lambda i: i.serialize(), items))


def output_graph(authors, modules, edges, unique_edges=False):
    # author nodes
    authors = sorted(serialize_all(authors))
    print("hierarchy;authors;{}".format(len(authors)))
    for author in authors:
        print(author)

    # modules
    modules = sorted(serialize_all(modules))
    print("hierarchy;modules;{}".format(len(modules)))
    for module in modules:
        print(module)

    # edges
    edges = sorted(serialize_all(edges))
    # the viz doesn't change if we have duplicated edges,
    # so there is no need to filter them for uniqueness?
    if(unique_edges):
        edges = sorted(set(edges))

    print("edges;edits;{}".format(len(edges)))
    for edge in edges:
        print(edge)


def main(filter_files, unique_edges):
    commits = load_all_commits(filter_files)
    edges = collect_edges(commits)
    author_names, module_names = collect_nodes(commits)

    modules = []
    for module in module_names:
        noc = calc_noc_for_module(module, edges)

        module_commits = filter(lambda c: module in c.filenames, commits)
        mtbc = calc_mtbc(module_commits)

        modules.append(Module(
            module,
            noc,
            mtbc
        ))

    authors = []
    for author in author_names:
        noc = calc_noc_for_author(author, edges)

        author_commits = filter(lambda c: c.author == author, commits)
        mtbc = calc_mtbc(author_commits)

        authors.append(Author(
            author,
            noc,
            mtbc
        ))

    output_graph(authors, modules, edges, unique_edges=unique_edges)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--filter-files', '-f',
        help='filter files to only contain source code files, according to '
            +'the following regex: r/' + sourcecode_pattern + '/',
        action='store_true',
        dest='filter_files'
    )
    parser.add_argument('--unique-edges', '-e',
        help='output only unique edges, duplicates are removed',
        action='store_true',
        dest='unique_edges'
    )

    args = parser.parse_args()
    main(args.filter_files, args.unique_edges)
