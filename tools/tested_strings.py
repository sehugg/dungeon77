#!/usr/bin/env python3
"""Find mdl-all-strings.txt entries marked "NOT FOUND in any .dg file"
whose text appears verbatim in some recorded skein transcript, and mark
them "TESTED in <skein file>" instead.

Usage:
    tools/tested_strings.py                # search and update in place
    tools/tested_strings.py --dry-run      # report matches, write nothing
    tools/tested_strings.py --min-len 10   # ignore shorter strings
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRINGS_FILE = ROOT / "mdl-all-strings.txt"
SKEIN_DIR = ROOT / "skeins"

# A status block starts with one of these (leading two spaces).
STATUS_RE = re.compile(r"^  (ADDED (?:in|to) |FOUND in |NOT FOUND in any)")
NOT_FOUND_RE = re.compile(r"^  NOT FOUND in any \.dg file$")
TESTED_HEADER_RE = re.compile(r"^  TESTED in ")

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def normalize(text):
    """Collapse whitespace and strip ANSI colors so game prose matches
    transcripts regardless of wrapping or colorization."""
    return re.sub(r"\s+", " ", ANSI_RE.sub("", text)).strip()


def parse_entries(lines):
    """Split the strings file into (start, end, status_start) runs.
    Returns a list of dicts: header line index, content lines, and the
    index range of the status block."""
    entries = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].startswith('STRING: "'):
            start = i
            i += 1
            # content runs until the first status line
            while i < n and not STATUS_RE.match(lines[i]):
                i += 1
            status_start = i
            # status block runs until the next entry header (or EOF),
            # skipping the blank separators between entries
            while i < n and not lines[i].startswith('STRING: "'):
                i += 1
            # don't swallow the blank separator line before the next entry
            end = i
            while end > status_start and not lines[end - 1].strip():
                end -= 1
            entries.append({
                "start": start,
                "status_start": status_start,
                "end": end,
            })
        else:
            i += 1
    return entries


def entry_text(lines, entry):
    """The raw string content of an entry: everything after the opening
    quote of the STRING: header through the closing quote."""
    header = lines[entry["start"]]
    body = header[len('STRING: '):].lstrip()
    if body.startswith('"'):
        body = body[1:]
    body += "\n" + "\n".join(lines[entry["start"] + 1:entry["status_start"]])
    # drop everything from the final closing quote onwards
    last_quote = body.rfind('"')
    if last_quote >= 0:
        body = body[:last_quote]
    return body


def load_skein_texts():
    """normalized text per skein file (backups ending in ~ skipped)."""
    texts = []
    for path in sorted(SKEIN_DIR.rglob("*.skein")):
        if path.name.endswith("~"):
            continue
        texts.append((path.relative_to(ROOT).as_posix(),
                      normalize(path.read_text(errors="replace"))))
    return texts


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="report matches but do not rewrite the file")
    ap.add_argument("--min-len", type=int, default=6,
                    help="ignore normalized strings shorter than this "
                         "(avoids bogus substring hits)")
    args = ap.parse_args()

    lines = STRINGS_FILE.read_text().splitlines()
    entries = parse_entries(lines)
    skeins = load_skein_texts()

    # pass 1: find matches and collect edits (status_start, end, replacement)
    edits = []
    for entry in entries:
        # only touch NOT FOUND entries; skip ones already TESTED
        status = lines[entry["status_start"]:entry["end"]]
        if status and not NOT_FOUND_RE.match(status[0]):
            continue

        needle = normalize(entry_text(lines, entry))
        if len(needle) < args.min_len:
            continue

        hits = [name for name, hay in skeins if needle in hay]
        if not hits:
            continue

        if len(hits) == 1:
            replacement = [f"  TESTED in {hits[0]}"]
        else:
            replacement = [f"  TESTED in {len(hits)} file(s):"]
            replacement += [f"    - {h}" for h in hits]

        rel = STRINGS_FILE.relative_to(ROOT)
        print(f"{rel}:{entry['start'] + 1}: {needle[:60]!r}...")
        for h in hits:
            print(f"    found in {h}")

        edits.append((entry["status_start"], entry["end"], replacement))

    # pass 2: apply edits bottom-up so earlier indices stay valid
    if not args.dry_run:
        for status_start, end, replacement in reversed(edits):
            lines[status_start:end] = replacement
        STRINGS_FILE.write_text("\n".join(lines) + "\n")

    print(f"\n{len(edits)} entr"
          f"{'y' if len(edits) == 1 else 'ies'} "
          f"{'would be' if args.dry_run else ''} marked TESTED"
          f"{'' if args.dry_run else ''}.")
    if not args.dry_run and edits:
        print(f"{STRINGS_FILE} updated.")


if __name__ == "__main__":
    sys.exit(main())
