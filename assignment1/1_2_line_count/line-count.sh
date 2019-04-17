#!/usr/bin/env bash

# check if argument was passed, otherwise use current working directory
working_dir=${1:-.}

## count folder-nesting
cut_number=$( awk -F'/' '{print NF-1}' <<< "${working_dir}" )
# cut is 1-indexed and we want one folder more
cut_number=$(( cut_number + 2 ))

# (1) find all files in the current directory excluding the `.git`-folder
# (2) pass those relative file names to `wc` to count the lines in the file
# (3) ignore the last line (which is the line total)
# (4) format output to "filepath;loc"
# (5) find adds the name of the directory to all paths, we don't need this, so we remove the first path entry
find "${working_dir}" -path "${working_dir}/.git" -prune -o -type f \
        -exec wc -l '{}' '+' \
    | head -n -1 \
    | awk -F ' ' '{print $2 ";" $1};' \
    | cut -d'/' -f${cut_number}-
