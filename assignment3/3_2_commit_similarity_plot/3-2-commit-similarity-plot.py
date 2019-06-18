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
    return commits


def plot_scatter(points, authors):
    x = list(map(itemgetter(0), points))
    y = list(map(itemgetter(1), points))

    color_mapping = sorted(set(authors), reverse=True)
    c = [float(color_mapping.index(author)) for author in authors]
    norm = Normalize(vmin=0, vmax=len(color_mapping)-1, clip=False)

    fig = plt.figure()
    plt.scatter(
        x,
        y,
        s=2,
        c=c,
        marker=".",
        cmap=plt.cm.Set1,
        norm=norm
    )

    cb = plt.colorbar()
    cb.set_label("authors")
    cb.set_ticks(range(len(color_mapping)))
    cb.set_ticklabels(color_mapping)
    #plt.show()
    plt.close()
    return fig


def main(output, sparse):
    commits = load()
    corpus = (text for _, text in commits)
    authors = [author for author, _ in commits]
    cv = CountVectorizer(
        analyzer="word",
        token_pattern=token_pattern,
        max_features=256
    )
    X = cv.fit_transform(corpus)

    if sparse:
        # PCA does not support sparse input, so use the alternative:
        svd = TruncatedSVD(n_components=2, random_state=random_seed, n_iter=10)
        Y = svd.fit_transform(X)
    else:
        pca = PCA(n_components=2, random_state=random_seed)
        Y = pca.fit_transform(X.toarray())

    fig = plot_scatter(Y, authors)
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

    parser.add_argument('--sparse', '-s',
        help='use sparse data and TruncatedSVD',
        action='store_true',
        dest='sparse'
    )

    args = parser.parse_args()
    main(args.output, args.sparse)
