#!/usr/bin/env python3
import sys
import os
import subprocess

try:
    import numpy as np
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.manifold import TSNE
    from joblib import dump, load
except ImportError:
    print("ERROR - this script requires sklearn", file=sys.stderr)
    print("      - install it using pip via 'pip3 install scikit-learn'", file=sys.stderr)
    exit(1)

try:
    from scipy.spatial import Voronoi, Delaunay, voronoi_plot_2d
    from scipy.spatial.distance import euclidean
except ImportError:
    print("ERROR - this script requires scipy", file=sys.stderr)
    print("      - install it using pip via 'pip3 install numpy scipy'", file=sys.stderr)
    print("      - you can also use your preferred package manager, " +
          "e.g. 'sudo apt install python3-numpy python3-scipy'", file=sys.stderr)
    exit(1)


# debug settings
show_embedding_plot = False
show_voronoi_plot = False
# testing_filter = "--since='100 days'"
testing_filter = None
# configuration
vectorizer_filename = "CountVectorizer.joblib"
author_embeddings_filename = "AuthorEmbeddings.joblib"
encoding = 'ascii'
token_pattern = r'\w\w+'
random_seed = 89715348


def plot_embeddings(author_embeddings, authors, file_embeddings, filenames):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR - this script requires matplotlib", file=sys.stderr)
        print("      - install it using pip via 'pip3 install matplotlib'", file=sys.stderr)
        print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'", file=sys.stderr)
        exit(1)

    data = np.concatenate(
        (author_embeddings, file_embeddings),
        axis=0
    )
    colors = np.concatenate(
        (
            np.full((len(author_embeddings),), 0),
            np.full((len(file_embeddings),), 1)
        ),
        axis=0
    )
    x = list(map(lambda x: x[0], data))
    y = list(map(lambda x: x[1], data))
    fig = plt.figure()
    plt.scatter(
        x,
        y,
        c=colors,
        cmap='Set1',
        marker="."
    )

    # labels = np.concatenate((authors, filenames), axis=0)
    # for point, label in zip(data, labels):
    #     plt.annotate(
    #         xy=point,
    #         s=label
    #     )
    plt.show()


def plot_voronoi_neighbors(voro, query_points, neighbors):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR - this script requires matplotlib", file=sys.stderr)
        print("      - install it using pip via 'pip3 install matplotlib'", file=sys.stderr)
        print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'", file=sys.stderr)
        exit(1)

    # plot voronoi diagram
    _ = voronoi_plot_2d(voro)
    # plot query points
    plt.scatter(query_points[:, 0], query_points[:, 1], c='r', marker='x')
    # plot found neighbors
    plt.scatter(neighbors[:, 0], neighbors[:, 1], c='g', marker='o')
    plt.legend([
        "Authors",
        "Voro Vertices",
        "Voro Finite Ridges",
        "Voro Infinite Ridges",
        "Query Points (Source Files)",
        "Neighbor Points"
    ])
    plt.show()


def run_command(command, multiline_output=True, separator="\n"):
    command = command if isinstance(command, list) else command.split()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )
    output, _ = process.communicate()
    text = output.decode('latin1')
    return text.split(separator) if multiline_output else text.strip()


def read_file(filename):
    try:
        with open(filename, 'r', encoding=encoding) as file:
            return file.read()
    except UnicodeDecodeError:
        print(filename, "is not encoded in", encoding, file=sys.stderr)
        print("  Falling back to UTF-8 ...", file=sys.stderr)
        try:
            with open(filename, 'r', encoding="utf-8") as file:
                return file.read()
            print("  ...successful", file=sys.stderr)
        except UnicodeDecodeError:
            print("  ...failed. Skipping file.", file=sys.stderr)
            return


def startswith_none_of(exclude_patterns, text):
    return not any(
        text.strip().startswith(pattern) for pattern in exclude_patterns
    )


def load_changes():
    commit_sep = "~~==~~"
    command = [
        "git", "log", "--no-merges", "--no-color", "--cc", "-U0",
        "--pretty=format:" + commit_sep + "%ae"
    ]
    if testing_filter:
        command.append(testing_filter)

    print("Running command:", " ".join(command), file=sys.stderr)
    result = run_command(command, multiline_output=True, separator=commit_sep)

    git_exclude_prefixes = [
        "diff",
        "index", "mode", "new", "old", "deleted", "copy",
        "rename", "similarity", "dissimilarity",
        "---", "+++",
        "@@", "@@@"
    ]

    print("Received results, building dict", file=sys.stderr)
    changes_per_author = {}
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
        if author not in changes_per_author:
            changes_per_author[author] = []
        for line in lines:
            changes_per_author[author].append(line)
    print("Dictionary created, authors:", len(changes_per_author), file=sys.stderr)
    return changes_per_author


def init():
    if (
        os.path.exists(vectorizer_filename) and
        os.path.exists(author_embeddings_filename)
    ):
        # load vectorizer and author embeddings from dump
        print("Loading vectorizer and embeddings", file=sys.stderr)
        vectorizer = load(vectorizer_filename)
        authors, author_embeddings = load(author_embeddings_filename)
    else:
        # build corpus
        print("No existing vectorizer and embeddings found, creating new...", file=sys.stderr)
        changes_per_author = load_changes()
        print("Creating vectorizer and bag of words repr. for authors", file=sys.stderr)
        authors = sorted(changes_per_author.keys())
        corpus = [
            "\n".join(changes_per_author[author])
            for author in authors
        ]
        # create new vectorizer and fit it
        vectorizer = CountVectorizer(  # CountVectorizer, TfidfVectorizer
            analyzer="word",
            token_pattern=token_pattern,
            max_features=256
        )
        author_embeddings = vectorizer.fit_transform(corpus).toarray()
        # dump vectorizer and author embeddings to file
        print(
            "Saving vectorizer and author vector representation to disk:",
            vectorizer_filename, author_embeddings_filename,
            file=sys.stderr
        )
        dump(vectorizer, vectorizer_filename)
        dump((authors, author_embeddings), author_embeddings_filename)
    return vectorizer, authors, author_embeddings


def embed_with_tsne(author_vecs, file_vecs):
    tsne = TSNE(
        n_components=2,
        n_iter=2000,
        init='pca',
        random_state=random_seed
    )
    split_point = len(author_vecs)
    embeddings = tsne.fit_transform(
        np.concatenate((author_vecs, file_vecs), axis=0)
    )
    author_embeddings = embeddings[:split_point]
    file_embeddings = embeddings[split_point:]

    print(
        "Using t-SNE to reduce dims of authors:",
        author_vecs.shape, "-->", author_embeddings.shape,
        file=sys.stderr
    )
    print(
        "Using t-SNE to reduce dims of files:",
        file_vecs.shape, "-->", file_embeddings.shape,
        file=sys.stderr
    )
    return author_embeddings, file_embeddings


def find_nearest_neighbors(voro, query_points):
    # triangulate voronoi (dual of voronoi)
    delauney = Delaunay(voro.points, incremental=False)

    # find simplices which include the query points
    simplex_indices = delauney.find_simplex(query_points)
    simplex_indices = simplex_indices[simplex_indices != -1]
    simplices = delauney.simplices[simplex_indices]

    # simplices consist of three of the original points --> take nearest
    neighbors = []
    for query_point, simplex in zip(query_points, simplices):
        # get points of simplex
        points = delauney.points[simplex]

        # find nearest point using euclidean distance
        min_dist = np.inf
        nearest_point = None
        for point in points:
            dist = euclidean(query_point, point)
            if dist < min_dist:
                min_dist = dist
                nearest_point = point
        neighbors.append(nearest_point)

    return np.array(neighbors)


def main():
    filenames = [line.strip() for line in sys.stdin]

    # init phase
    cv, authors, author_vecs = init()

    # query phase
    file_contents = [read_file(f) for f in filenames]
    file_vecs = cv.transform(file_contents).toarray()
    author_embeddings, file_embeddings = embed_with_tsne(
        author_vecs,
        file_vecs
    )
    if show_embedding_plot:
        plot_embeddings(author_embeddings, authors, file_embeddings, filenames)

    print("Building voronoi diagram", file=sys.stderr)
    voro = Voronoi(
        author_embeddings,
        incremental=False
    )
    print("Finding nearest neighbors", file=sys.stderr)
    neighbors = find_nearest_neighbors(voro, file_embeddings)

    if show_voronoi_plot:
        plot_voronoi_neighbors(voro, file_embeddings, neighbors)

    print("Finished. Printing result to stdout", file=sys.stderr)
    for filename, neighbor in zip(filenames, neighbors):
        index = np.where(author_embeddings == neighbor)[0][0]
        author = authors[index]
        print("{};{}".format(filename, author))


if __name__ == "__main__":
    main()
