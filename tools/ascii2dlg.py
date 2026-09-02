#!/usr/bin/env python3
"""ascii2dlg.py -- convert ASCII art to Dialog output statements.

Emits Dialog source using the built-in predicates:

    (space N)   prints N spaces (built-in `(space $)`)
    (space)     prints one space  (only with --single-space)
    (line)      line break

Rules:
  * Every run of spaces in the art becomes a single (space N).
  * Every art line ends with (line); blank lines become just (line).
  * Characters that are special in Dialog program text are escaped
    with a leading backslash:  \\ ( ) { } [ ] " ; $ @ # | *
    (matches the style used in src/rooms/volcano.dg)
  * Generated source lines are wrapped on token boundaries so the
    .dg file stays readable (volcano.dg does the same).

Usage:
    python3 ascii2dlg.py art.txt > art.dg
    python3 ascii2dlg.py --single-space --wrap 0 art.txt
    echo '  /\\' | python3 ascii2dlg.py
"""

import argparse
import sys

# Characters with syntactic meaning in Dialog program text; escaping an
# ordinary character with a backslash is harmless, but we only escape
# these to keep the output tidy.
SPECIAL = set('\\(){}[]";$@#|*')


def escape(text):
    return ''.join('\\' + c if c in SPECIAL else c for c in text)


def tokenize(line):
    """Split one line of art into ('space', n) / ('text', s) tokens."""
    tokens = []
    i, n = 0, len(line)
    while i < n:
        if line[i] == ' ':
            j = i
            while j < n and line[j] == ' ':
                j += 1
            tokens.append(('space', j - i))
            i = j
        else:
            j = i
            while j < n and line[j] != ' ':
                j += 1
            tokens.append(('text', escape(line[i:j])))
            i = j
    return tokens


def render(tokens, single_space=False, wrap=76, indent='\t'):
    """Render tokens as one or more wrapped Dialog source lines."""
    out = []
    cur = indent

    def emit(s):
        nonlocal cur
        if wrap and len(cur) + len(s) > wrap and cur.strip():
            out.append(cur)
            cur = indent
        cur += s

    for kind, val in tokens:
        if kind == 'line':
            emit('(line)')
        elif kind == 'space':
            if val == 1 and single_space:
                emit('(space)')
            else:
                emit('(space %d)' % val)
        else:
            emit(val)
    if cur.strip():
        out.append(cur)
    return out


def convert(text, **opts):
    result = []
    for line in text.splitlines():
        line = line.rstrip()          # trailing spaces are invisible anyway
        tokens = tokenize(line)
        tokens.append(('line', None))
        result.extend(render(tokens, **opts))
    return '\n'.join(result) + '\n'


def main():
    ap = argparse.ArgumentParser(
        description='Convert ASCII art to Dialog (space N)/(line) statements.')
    ap.add_argument('infile', nargs='?', default='-',
                    help="input file ('-' or omitted = stdin)")
    ap.add_argument('-o', '--outfile', default='-',
                    help="output file ('-' = stdout)")
    ap.add_argument('-w', '--wrap', type=int, default=76,
                    help='max columns of generated source (0 = no wrap)')
    ap.add_argument('-i', '--indent', default='\t',
                    help='prefix for each generated source line')
    ap.add_argument('--single-space', action='store_true',
                    help='use (space) instead of (space 1)')
    args = ap.parse_args()

    if args.infile == '-':
        text = sys.stdin.read()
    else:
        with open(args.infile, 'r', encoding='utf-8') as f:
            text = f.read()

    output = convert(text, single_space=args.single_space,
                     wrap=args.wrap, indent=args.indent)

    if args.outfile == '-':
        sys.stdout.write(output)
    else:
        with open(args.outfile, 'w', encoding='utf-8') as f:
            f.write(output)


if __name__ == '__main__':
    main()
