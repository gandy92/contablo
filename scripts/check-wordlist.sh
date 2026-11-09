#!/bin/bash
# Block commits and pushes that contain words from a private, optional wordlist.
#
# The wordlist lives outside the repository so it never becomes part of the history:
#   ${XDG_CONFIG_HOME:-$HOME/.config}/gitpurge/wordlist
# One entry per line, matched case-insensitively as whole words (fixed strings, no regex).
# Empty lines and lines starting with '#' are ignored.
# A missing wordlist is not an error: the check is skipped with a notice.
#
# Usage (called by pre-commit, see .pre-commit-config.yaml):
#   check-wordlist.sh files FILE...   staged file names and contents; binary files via
#                                     strings, images must not carry text metadata
#   check-wordlist.sh msg FILE        commit message
#   check-wordlist.sh ident           author and committer identity of the new commit
#   check-wordlist.sh push            all local ref names, plus identities, messages and
#                                     diffs of all unpushed commits (catches --no-verify)

# Run the last command of a pipeline in this shell, so match() can set $status.
shopt -s lastpipe

WORDLIST="${XDG_CONFIG_HOME:-$HOME/.config}/gitpurge/wordlist"
MODE=$1
shift

PATTERNS=$(mktemp)
trap 'rm -f "$PATTERNS"' EXIT

status=0

# Read stdin, report matches prefixed with a label.
match() {
    local label=$1 out
    out=$(grep -n -i -w -F -f "$PATTERNS")
    if [ -n "$out" ]; then
        printf '%s\n' "$out" | awk -v label="$label" '{ print label ":" $0 }'
        status=1
    fi
}

# Report image files that carry text metadata (e.g. generator prompts, EXIF, XMP).
check_image_metadata() {
    python3 - "$@" <<'EOF' || status=1
import struct
import sys

found = False
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        data = f.read()
    hits = []
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        pos = 8
        while pos + 8 <= len(data):
            length, ctype = struct.unpack(">I4s", data[pos : pos + 8])
            if ctype in (b"tEXt", b"iTXt", b"zTXt", b"eXIf"):
                hits.append(ctype.decode())
            pos += 12 + length
    elif data.startswith(b"\xff\xd8"):
        pos = 2
        while pos + 4 <= len(data) and data[pos] == 0xFF:
            marker = data[pos + 1]
            if marker == 0xDA:  # start of scan, no more metadata segments
                break
            length = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
            if marker in (0xE1, 0xED, 0xFE):  # EXIF/XMP, IPTC, comment
                hits.append(f"segment 0x{marker:02X}")
            pos += 2 + length
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        pos = 12
        while pos + 8 <= len(data):
            ctype, length = struct.unpack("<4sI", data[pos : pos + 8])
            if ctype in (b"EXIF", b"XMP "):
                hits.append(ctype.decode().strip())
            pos += 8 + length + (length & 1)
    if hits:
        found = True
        print(f"{path}: image metadata ({', '.join(sorted(set(hits)))})")
if found:
    print("check-wordlist: strip image metadata first, e.g. 'mogrify -strip FILE'.")
sys.exit(1 if found else 0)
EOF
}

# The image check does not depend on the wordlist.
if [ "$MODE" = files ] && [ $# -gt 0 ]; then
    check_image_metadata "$@"
fi

if [ ! -r "$WORDLIST" ]; then
    echo "check-wordlist: no wordlist at $WORDLIST, skipping word check."
    exit $status
fi

grep -v -e '^[[:space:]]*$' -e '^[[:space:]]*#' "$WORDLIST" > "$PATTERNS"
[ -s "$PATTERNS" ] || exit $status

case "$MODE" in
    files)
        printf '%s\n' "$@" | match "file name"
        for f in "$@"; do
            if grep -q -I '' -- "$f" 2>/dev/null || [ ! -s "$f" ]; then
                match "$f" < "$f"
            else
                strings -n 3 -- "$f" | match "$f (binary)"
            fi
        done
        ;;
    msg)
        match "commit message" < "$1"
        ;;
    ident)
        git var GIT_AUTHOR_IDENT | match "author"
        git var GIT_COMMITTER_IDENT | match "committer"
        ;;
    push)
        # pre-commit passes only the first pushed ref (and no range at all when the root
        # commit is pushed), so check a superset instead: all local branch and tag names
        # with tag annotations, and every commit not yet on the remote.
        printf '%s\n' "$PRE_COMMIT_REMOTE_BRANCH" | match "remote ref name"
        git for-each-ref --format='%(refname)%0a%(taggername) %(taggeremail)%0a%(contents)' \
            refs/heads refs/tags | match "local refs"
        git log -p --format='commit %h %an <%ae> / %cn <%ce>%n%B' \
            --branches --tags --not --remotes${PRE_COMMIT_REMOTE_NAME:+=$PRE_COMMIT_REMOTE_NAME} |
            match "unpushed commits"
        ;;
    *)
        echo "check-wordlist: unknown mode '$MODE'"
        exit 2
        ;;
esac

[ $status -ne 0 ] && echo "check-wordlist: forbidden word(s) found above."
exit $status
