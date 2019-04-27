#!/usr/bin/env python
import sys


def main():
    namedict = {}
    for line in sys.stdin:
        name, mail = line.rstrip().split(";")
        # if first time: init list
        if name not in namedict:
            namedict[name] = set()

        namedict[name].add(mail)

    for name, mail_list in sorted(namedict.items()):
        print name, " ".join(mail_list)

if __name__ == "__main__":
    main()
