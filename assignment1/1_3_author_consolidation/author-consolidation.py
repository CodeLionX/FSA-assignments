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
    
    for name, mailList in sorted(namedict.items()):
        print name, " ".join(mailList)

if __name__ == "__main__":
    main()