#!/bin/bash
# show_changes.sh
#
# Compares the current commit against the last successful Jenkins build
# and prints which files changed and what commits were made since then.
#
# Expects these environment variables to be set (Jenkins sets these
# automatically when using the Git plugin):
#   GIT_COMMIT                    - current commit hash
#   GIT_PREVIOUS_SUCCESSFUL_COMMIT - commit hash of the last successful build
#
# Safe to run outside Jenkins too - falls back to comparing against
# the previous commit on the current branch.

set -e

CURRENT_COMMIT="${GIT_COMMIT:-$(git rev-parse HEAD)}"
PREVIOUS_COMMIT="${GIT_PREVIOUS_SUCCESSFUL_COMMIT:-}"

echo "=========================================="
echo "  CHANGE SUMMARY"
echo "=========================================="

if [ -z "${PREVIOUS_COMMIT}" ]; then
    # No previous successful build recorded (first build, or running standalone)
    # Fall back to comparing against the parent commit, if one exists.
    if git rev-parse HEAD~1 >/dev/null 2>&1; then
        PREVIOUS_COMMIT=$(git rev-parse HEAD~1)
        echo "No previous successful Jenkins build found."
        echo "Falling back to comparing against the previous commit."
    else
        echo "No previous commit found — this is the very first commit."
        echo ""
        echo "=== Files in this commit ==="
        git show --name-status --oneline "${CURRENT_COMMIT}"
        exit 0
    fi
fi

echo "Previous commit : ${PREVIOUS_COMMIT}"
echo "Current commit  : ${CURRENT_COMMIT}"
echo ""

echo "=== Changed files ==="
git diff --name-status "${PREVIOUS_COMMIT}" "${CURRENT_COMMIT}" || echo "(no differences found)"
echo ""

echo "=== File change stats ==="
git diff --stat "${PREVIOUS_COMMIT}" "${CURRENT_COMMIT}" || true
echo ""

echo "=== Commits since last successful build ==="
git log --oneline "${PREVIOUS_COMMIT}..${CURRENT_COMMIT}" || echo "(no new commits)"
echo ""

echo "=========================================="
