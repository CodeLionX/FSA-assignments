#!/usr/bin/env python3
import argparse
import subprocess
import sys
import re
from operator import itemgetter

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR - this script requires matplotlib")
    print("      - install it using pip via 'pip3 install matplotlib'")
    print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'")
    sys.exit(1)

try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.manifold import MDS
except ImportError:
    print("ERROR - this script requires sklearn")
    print("      - install it using pip via 'pip3 install scikit-learn'")
    sys.exit(1)


sourcecode_pattern = r'.*\.ts$|.*\.tsx$|.*\.js$|.*\.jsx$'
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


def find_source_code_files():
    output = run_command('find . -type f')

    # strip first two chars './' added by the find tool
    sourceFiles = [line[2:] for line in output]
    return list(filter(lambda f: re.fullmatch(sourcecode_pattern, f), sourceFiles))


def load():
    files = find_source_code_files()
    documents = []
    for filename in files:
        with open(filename, "r", encoding='utf-8') as f:
            documents.append("\n".join(f))

    return files, documents


def plot_scatter(points, filenames):
    x = list(map(itemgetter(0), points))
    y = list(map(itemgetter(1), points))

    fig = plt.figure()
    plt.rcParams["font.size"] = "6"
    plt.scatter(
        x,
        y,
        s=2,
        marker="."
    )

    for point, filename in zip(points, filenames):
        plt.annotate(
            xy=point,
            s=filename
        )
    #plt.show()
    plt.close()
    return fig


def main(output):
    filenames, documents = load()
    cv = CountVectorizer(
        analyzer="word",
        token_pattern=token_pattern,
        max_features=256
    )
    X = cv.fit_transform(documents)

    mds = MDS(n_components=2, random_state=random_seed, n_jobs=-1)
    Y = mds.fit_transform(X.toarray())

    fig = plot_scatter(Y, filenames)
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
