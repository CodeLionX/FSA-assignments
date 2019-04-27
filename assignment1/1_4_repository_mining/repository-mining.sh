#!/usr/bin/env bash

function formatDays() {
    local devRestDays=$1
    local devYears=$(( devRestDays / 365 ))
    local devRestDays=$(( devRestDays - (devYears * 365) ))

    local devMonths=$(( devRestDays / 30 ))
    local devRestDays=$(( devRestDays - (devMonths * 30) ))

    [[ ${devYears} != 0 ]]    && {
        unit="years"
        [[ ${devMonths} == 1 ]] && unit="year"
        yearInfo="${devYears} ${unit}"
    }
    [[ ${devMonths} != 0 ]]   && {
        unit="months"
        [[ ${devMonths} == 1 ]] && unit="month"
        monthInfo="${devMonths} ${unit}"
        [[ ${devYears} != 0 ]] && monthInfo=", ${monthInfo}"
    }
    [[ ${devRestDays} != 0 ]] && {
        unit="days"
        [[ ${devRestDays} == 1 ]] && unit="day"
        dayInfo="${devRestDays} ${unit}"
        [[ ${devYears} != 0 ]] || [[ ${devMonths} != 0 ]] && dayInfo=", ${dayInfo}"
    }
    echo "started ${yearInfo}${monthInfo}${dayInfo} ago"
}

## main script
###############################################################################

# number of authors
n_authors=$(git log --format="%ae" | sort | uniq | wc -l)
echo "Number of authors: ${n_authors}"

# most active author
aYearAgo=$(date --date="365 days ago" "+%Y-%m-%d")
mostActive=$(git log --format="%an <%ae>" --after=$aYearAgo | sort | uniq -c | sort -n | tail -n 1 | sed 's/^ *[0-9]* //')
echo "Most active author within last year: ${mostActive}"

# development time
firstCommitDate=$(git log --format="%at" --topo-order --reverse | head -n 1)
now=$(date +%s)
devDays=$(( (now - firstCommitDate) /3600/24 ))
humanFormat=$(formatDays ${devDays})
echo "Time range of development: ${devDays} days ($humanFormat)"

# share of maintenance
log=$(git log --cherry-pick --no-merges --format="%s")
commits=$(wc -l <<<${log})
maintenanceCommits=$(grep -wi 'fix\|rewrite\|doc\|test\|improve' <<<${log} | wc -l)
maintenancePercentage=$(awk -vn=${commits} -vm=${maintenanceCommits} 'BEGIN{printf("%.1f%%", (m/n)*100)}')
echo "Share of maintenance: ${maintenancePercentage}"

# share of stale code
echo "Share of stale code: "

# top 10 commit keywords
echo "Top 10 commit message keywords last month: "