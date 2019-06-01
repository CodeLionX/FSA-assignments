#!/usr/bin/env python3
import sys
import argparse
import ast

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR - this script requires matplotlib")
    print("      - install it using pip via 'pip3 install matplotlib'")
    print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'")
    sys.exit(1)


# file encoding is ASCII only
encoding = 'ascii'
# hide outliers in boxplot
box_showfliers = False


def number_of_args(args):
    # number of parameters (more strict then definition in task)
    l = len(args.args)
    try:
        l += len(args.kwonlyargs)
    except AttributeError:
        pass
    if args.vararg:
        l += 1
    if args.kwarg:
        l += 1
    return l


def count_body_lines(filename, lineoffset, target_lineoffset):
    with open(filename, 'r', encoding=encoding) as file:
        # "seek" to function body start
        for _ in range(lineoffset - 1):
            next(file)

        # body is completed on next def start at indention level 0 or EOF
        # not counting empty lines
        count = 0
        lineno = lineoffset
        for line in file:
            if target_lineoffset and lineno >= target_lineoffset:
                return count
            if line.strip():
                count += 1
            lineno += 1

        return count


def parse_with_ast(filename):
    try:
        with open(filename, 'r', encoding=encoding) as file:
            file_content = file.read()
    except UnicodeDecodeError:
        print(filename, "is not encoded in", encoding)
        print("  Falling back to UTF-8 ...")
        try:
            with open(filename, 'r', encoding="utf-8") as file:
                file_content = file.read()
            print("  ...successful")
        except UnicodeDecodeError:
            print("  ...failed. Skipping file.")
            return

    try:
        node = ast.parse(file_content)
    except SyntaxError:
        print(filename, "contains syntax errors ( python",
                str(sys.version_info[0]) + "." + str(sys.version_info[1]),
                "). Skipping file.")
        return

    # function starts at indention level 0 with 'def',
    # can contain line breaks, comments, ..
    # ends at next top-level definition (indentation level 0)
    for i, fn in enumerate(node.body):
        if isinstance(fn, ast.FunctionDef):
            try:
                next_fn = node.body[i + 1]
                next_fn_lineno = next_fn.lineno
            except:
                next_fn_lineno = None

            n_args = number_of_args(fn.args)
            body_loc = count_body_lines(filename, fn.body[0].lineno, next_fn_lineno)
            yield (n_args, body_loc)


def plot_scatter(x, y):
    fig = plt.figure()
    plt.plot(x, y, "ko")
    plt.xticks(range(max(x)+1))
    plt.xlabel("Number of Parameters")
    plt.ylabel("Lines of Code")
    plt.close()
    return fig


def plot_boxplot(x, y):
    # transform data
    mapped = {}
    for i, noa in enumerate(x):
        if noa not in mapped:
            mapped[noa] = []
        mapped[noa].append(y[i])

    data = [(key, mapped[key]) for key in mapped]
    data = sorted(data)
    fig = plt.figure()
    plt.boxplot(
        [col for _, col in data],
        showfliers=box_showfliers,
        labels=[key for key, _ in data]
    )
    plt.xlabel("Number of Parameters")
    plt.ylabel("Lines of Code")
    plt.close()
    return fig


def main(output_filename, plot_type):
    filenames = [line for line in sys.stdin]
    noas = []
    locs = []
    for f in filenames:
        for noa, loc in parse_with_ast(f.strip()):
            noas.append(noa)
            locs.append(loc)

    if noas and locs:
        if plot_type == "dot":
            fig = plot_scatter(noas, locs)
        else:
            fig = plot_boxplot(noas, locs)
        fig.savefig(output_filename, bbox_inches="tight")
        print("Figure saved to", output_filename)
    else:
        print("No files found!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',
        type=str,
        help='output filename',
        default='output.pdf'
    )
    parser.add_argument('--type',
        type=str,
        help='depiction type',
        default='dot',
        choices=['dot', 'box']
    )

    args = parser.parse_args()
    main(args.output, args.type)
