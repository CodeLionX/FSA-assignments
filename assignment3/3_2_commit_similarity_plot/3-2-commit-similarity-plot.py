#!/usr/bin/env python3
import argparse
import sys

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR - this script requires matplotlib")
    print("      - install it using pip via 'pip3 install matplotlib'")
    print("      - you can also use your preferred package manager, e.g. 'apt install python3-matplotlib'")
    sys.exit(1)

try:
    import sklearn
except ImportError:
    print("ERROR - this script requires sklearn")
    print("      - install it using pip via 'pip3 install scikit-learn'")
    sys.exit(1)


def main(output):
    pass


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
