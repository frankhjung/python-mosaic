#!/bin/bash

# Check if a directory is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

SEARCH_DIR="$1"

# Check if directory exists
if [ ! -d "${SEARCH_DIR}" ]; then
    echo "Error: Directory '${SEARCH_DIR}' not found."
    exit 1
fi

# Find files, calculate md5 checksums, sort by checksum,
# and use uniq to print only duplicates (based on the first 32 chars - the hash)
# --all-repeated=separate prints all duplicate lines, separated by newlines
# We use -print0 and xargs -0 to handle filenames with spaces correctly
find "${SEARCH_DIR}" -type f -print0 | xargs -0 md5sum | sort | uniq -w32 --all-repeated=separate
