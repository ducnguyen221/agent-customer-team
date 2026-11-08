#!/usr/bin/env bash
# Scan a results folder for credentials before it is kept as a workflow artifact.
# Usage: scan.sh <results dir> <file with one exact value per line, may be empty>
# Exit 0: clean. Exit 3: a value or an Anthropic-style key was found. Exit 4: the scan itself failed.
# Matching lines are never printed (grep -q), so a found value does not reach the log. Symlinks are followed (-R);
# compressed files are not unpacked, and an encoded or transformed value is not caught - the env scrub is the main fence.
set -u
dir="$1"
patterns="$2"

check() {
  # $@: grep arguments; grep exits 0 = match, 1 = no match, 2 = error
  grep -Rq "$@" "$dir"
  case $? in
    0) echo "::error::A credential was found in the results; they will not be kept."; exit 3 ;;
    1) ;;
    *) echo "::error::The credential scan could not read the results."; exit 4 ;;
  esac
}

if [ -s "$patterns" ]; then
  check -F -f "$patterns"
fi
check -E 'sk-ant-[A-Za-z0-9_-]{20,}'
echo "Credential scan: clean."
exit 0
