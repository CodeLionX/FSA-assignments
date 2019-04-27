#!/usr/bin/env python3
import re
import sys
from operator import itemgetter

word_black_list = set(["a", "an", "at", "for", "from", "in", "is", "of", "on", "the", "to", "use", "with", "when"])
tokenizer_pattern = r"[#\w]+(?:[-'#]\w+)*"


def main():
    msgs = ''.join([line for line in sys.stdin])
    words = {}
    for word in re.findall(tokenizer_pattern, msgs):
        lower_word = word.lower()
        if lower_word not in word_black_list:
            if lower_word not in words:
                words[lower_word] = 0
            words[lower_word] += 1
    most_used = sorted(words.items(), key=itemgetter(1), reverse=True)
    print(", ".join([word for word, _ in most_used[:10]]))


if __name__ == "__main__":
    main()
