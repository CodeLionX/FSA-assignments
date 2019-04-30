#!/usr/bin/env python3
import argparse
import sys
import csv
from operator import itemgetter

delimiter = ' | '
artSymbol = '+'  # preferrably just one char


def main(width, attribute, sort_order, limit, flat):
    reader = csv.reader(sys.stdin, delimiter=';')
    header = next(reader)
    keyIndex = 0
    attrIndex = 1

    # find key index based on supplied attribute name
    if attribute:
        for i, attr in enumerate(header):
            if attr == attribute:
                attrIndex = i
                break

    # read and parse dataset
    dataset = []
    for line in reader:
        key = line[keyIndex].split('/')[-1] if flat else line[keyIndex]
        try:
            value = int(line[attrIndex])
        except:
            value = 0
        dataset.append((key, value))

    # handle sorting
    if sort_order == 'asc':
        dataset = sorted(dataset, key=itemgetter(1))
    elif sort_order == 'desc':
        dataset = sorted(dataset, key=itemgetter(1), reverse=True)

    # handle limiting
    if limit:
        dataset = dataset[:limit-1]

    # get maxima
    keyLength = len(max(dataset, key=lambda x: len(x[0]))[0])
    valueMax = max(dataset, key=itemgetter(1))[1]

    # get remaining width
    maxWidth = width - keyLength - len(delimiter)
    maxWidth = maxWidth if maxWidth > 0 else 0

    for key, value in dataset:
        # calc bar chars
        times = int((value / float(valueMax)) * maxWidth)
        bar = (artSymbol * (times//len(artSymbol)+1))[:times]
        # print result
        print(key.rjust(keyLength) + delimiter + bar)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--attribute',
        type=str,
        help='select attribute of dataset to display. Default: first attribute'
    )
    parser.add_argument('--sort', '-s',
        type=str,
        choices=['asc', 'desc'],
        help='sort by attribute'
    )
    parser.add_argument('--limit', '-n',
        type=int,
        help='limit the number of lines of the output'
    )
    parser.add_argument('--hierarchical', '-k',
        action='store_false',
        dest='flat',
        default=True,
        help='print the full file path'
    )
    parser.add_argument('--flat', '-f',
        action='store_true',
        dest='flat',
        default=True,
        help='print only the file name'
    )
    parser.add_argument('--columns', '-c',
        type=int,
        default=80,
        help='Set the number of characters used to create the viz.'
    )
    args = parser.parse_args()
    main(args.columns, args.attribute, args.sort, args.limit, args.flat)
