#!/usr/bin/env python3
import argparse
import subprocess
import sys
import re
from operator import itemgetter

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
except ImportError:
    print("ERROR - this script requires matplotlib")
    print("      - install it using pip via 'pip3 install matplotlib'")
    print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'")
    sys.exit(1)

try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import PCA, TruncatedSVD
except ImportError:
    print("ERROR - this script requires sklearn")
    print("      - install it using pip via 'pip3 install scikit-learn'")
    sys.exit(1)


token_pattern = r'\w\w+'
random_seed = 89715348


def run_command(command, multiline_output=True, separator="\n"):
    command = command if isinstance(command, list) else command.split()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )
    output, _ = process.communicate()
    text = output.decode()
    return text.split(separator) if multiline_output else text.strip()


def startswith_none_of(exclude_patterns, text):
    return not any(
        text.strip().startswith(pattern) for pattern in exclude_patterns
    )


def load():
    commit_sep = "~~==~~"
    command = [
        "git", "log", "--no-merges", "--no-color", "--cc", "-U0",
        "--pretty=format:" + commit_sep + "%ae"
    ]
    result = run_command(command, multiline_output=True, separator=commit_sep)

    git_exclude_prefixes = [
        "diff",
        "index", "mode", "new", "old", "deleted", "copy",
        "rename", "similarity", "dissimilarity",
        "---", "+++",
        "@@", "@@@"
    ]

    commits = []
    for commit in result:
        if not commit:
            continue
        lines = commit.split("\n")
        author = lines[0]
        lines = filter(
            lambda x: x and startswith_none_of(git_exclude_prefixes, x),
            map(
                lambda x: x.strip(),
                lines[1:]
            )
        )
        commits.append((author, "\n".join(lines)))
    return list(commits)


def build_vocabulary(commits):
    terms = [
        term
        for _, lines in commits
        for line in lines
        for term in re.findall(token_pattern, line)
    ]
    term_tf = {}
    for term in terms:
        if term not in term_tf:
            term_tf[term] = 0
        term_tf[term] += 1
    term_tf = [(term, term_tf[term]) for term in term_tf]
    top_256_terms = list(sorted(term_tf, key=itemgetter(1), reverse=True))[:256]
    return map(itemgetter(0), top_256_terms)


def plot_scatter(points, authors):
    x = list(map(itemgetter(0), points))
    y = list(map(itemgetter(1), points))

    color_mapping = list(set(authors))
    c = [float(color_mapping.index(author)) for author in authors]
    print(color_mapping)

    fig = plt.figure()
    norm = Normalize(vmin=0, vmax=len(color_mapping)-1, clip=False)
    plt.scatter(
        x,
        y,
        s=2,
        c=c,
        marker=".",
        cmap=plt.cm.Set1,
        norm=norm
    )
    #plt.xticks(range(max(x)+1))

    cb = plt.colorbar()
    cb.set_label("authors")
    cb.set_ticks(range(len(color_mapping)))
    cb.set_ticklabels(color_mapping)
    plt.show()
    #plt.close()
    return fig


def main(output):
    commits = load()
    corpus = [text for _, text in commits]
    cv = CountVectorizer(
        analyzer="word",
        token_pattern=token_pattern,
        max_features=256
    )
    X = cv.fit_transform(corpus)
    vocabulary = cv.get_feature_names()


    svd = TruncatedSVD(n_components=2, random_state=random_seed, n_iter=10)
    Y = svd.fit_transform(X)

    fig = plot_scatter(Y, [author for author, _ in commits])
    fig.savefig(output, bbox_inches="tight")
    print("Figure saved to", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('output',
        type=str,
        nargs='?',
        help='output filename',
        default='result.pdf'
    )

    args = parser.parse_args()
    main(args.output)
