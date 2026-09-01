#!/usr/bin/env python3
"""skein.py -- drive dgdebug and compare against a recorded skein.

Designed to be easy for an LLM (or a human) to call and read:

    tools/skein.py play n e "open window" w        # ad-hoc transcript
    tools/skein.py diff                            # check every branch
    tools/skein.py diff 1785098749839              # ...just the path to one node
    tools/skein.py bless --dry-run                 # preview what blessing changes
    tools/skein.py bless                           # accept live output as the recording
    tools/skein.py bless 1785098749839             # ...just the path to one node
    tools/skein.py replay --json                   # transcript as JSON
    tools/skein.py list                            # node ids + commands
    tools/skein.py list --tree                     # branch structure
    tools/skein.py show 1785098749839              # recorded output
    tools/skein.py find "getting dimmer"           # nodes matching a regex
    tools/skein.py path 1785098749839              # "n,e,open window" selector
    tools/skein.py --skein skeins/ diff            # merged directory of skeins

A skein is a tree: nodes carry a parent-id, and a node with several children
is a branch point.  `diff` with no argument replays one path per branch tip,
which together visit every node exactly once (shared prefixes are compared
on the first branch that reaches them, not re-run per branch).

dgdebug is launched fresh for every invocation and fed commands on stdin,
so there is no interactive state to manage.  `--tag-lines` makes the
segmentation exact: the debugger prefixes its own output with two spaces
and echoes input with "> " (or ") " at a query prompt).

Exit status of `diff` is 1 when any node's output differs, 0 when clean.

--skein also accepts a DIRECTORY, which is loaded as one merged tree:

    skeins/root.skein               the trunk (has `seed:`, no parent-*)
    skeins/puzzles/kitchen.skein    a fragment, attached by its header

A fragment names its attach point with parent-* constraints, all of which
must hold, and which together must match exactly one node:

    parent-id:       node id, file-local ("3") or qualified ("root.skein#3")
    parent-label:    the node's label:
    parent-command:  the node's own command
    parent-after:    the command before it (its parent's command)
    parent-output:   regex over the node's output, e.g. /peppers/
    parent-path:     the whole command chain from the root, "n,e,open window"

Zero matches, or more than one, is a fatal error naming the candidates, so a
selector never silently drifts onto the wrong node.  Fragments may attach to
nodes supplied by other fragments; placement iterates to a fixpoint and then
re-checks every selector against the finished tree, so file order can never
change the result.  Inside a fragment `id:` and `parent-id:` are optional --
a node chains onto the previous node in the same file, so a linear sub-skein
is just a header plus a run of command blocks.

`bless` is the other half of `diff`: once you have reviewed a diff and decided
the live behavior is the correct one, `bless` replays the same paths and
rewrites each mismatched node's transcript in place -- in whichever fragment
file supplies that node.  The written transcript is the normalized live text
(colors and volatile lines such as warnings and the version banner removed,
trailing whitespace trimmed), which is exactly what `diff` compares against,
so a bless followed by a diff is always clean.  Afterwards the merged tree is
re-loaded; if a changed transcript breaks a fragment's `parent-output:`
selector, bless reports it instead of letting the skein silently drift.

    tools/skein.py bless                # bless every branch
    tools/skein.py bless <node-id>      # bless only the path to one node
    tools/skein.py bless --dry-run      # list what would change, write nothing

`record` writes such a fragment for you: it resolves the parent, replays the
path down to it, runs your new commands, and saves the result with the
selector already in the header.  Turns recorded after a game over (the
UNDO/RESTORE menu and anything typed past it) are dropped automatically;
pass `--keep-junk` to keep them:

    tools/skein.py --skein skeins/ record --parent-command "open window" \\
        --into puzzles/kitchen.skein "take sack" "open sack"

Two lookup helpers make attach points easy to pick:

    tools/skein.py find "maintenance room"    # nodes whose command or
                                              # output matches a regex
    tools/skein.py path <node-id>             # the command chain, in exactly
                                              # the parent-path: syntax
"""

import argparse
import difflib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEPARATOR = "-" * 80

# Lines that legitimately vary between runs / tool versions and must not
# count as a regression.  Applied to both the live and recorded sides.
VOLATILE = [
    re.compile(r"^Warning:"),
    re.compile(r"^Error:"),
    re.compile(r"^Dialog Interactive Debugger\b"),
    re.compile(r"^Release \d+\. Serial number\b"),
]

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


# ---------------------------------------------------------------- skein file

class Node:
    def __init__(self, nid, parent, command, label, output,
                 origin=None, local_id=None):
        self.id = nid              # unique within the merged tree
        self.parent = parent
        self.command = command
        self.label = label
        self.output = output
        self.origin = origin       # file the node was read from
        self.local_id = local_id   # id as written in that file

    def __repr__(self):
        return "<Node %s %r>" % (self.id, self.command)


def parse_skein(path, origin=None, qualify=False):
    """Return (header, [Node...]) for a dgt .skein file.

    The file is a header, then alternating metadata / transcript chunks
    delimited by 80-dash separator lines.

    With `qualify`, node ids become "<origin>#<id>" so fragments from
    different files cannot collide.  A fragment may omit `id:` (ids are then
    assigned positionally) and `parent-id:` (a node then chains onto the
    previous node in the same file), which makes a linear sub-skein trivial
    to hand-write: a header plus a run of command blocks.
    """
    with open(path, encoding="utf-8", errors="replace") as fp:
        text = fp.read()

    chunks = re.split(r"^-{10,}$\n?", text, flags=re.M)
    header = {}
    for line in chunks[0].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            header[k.strip()] = v.strip()

    def qual(x):
        # An id that already names a file is a cross-file reference.
        if x is None or not qualify or "#" in x:
            return x
        return "%s#%s" % (origin, x)

    nodes = []
    prev = None
    for i in range(1, len(chunks) - 1, 2):
        meta = {}
        for line in chunks[i].splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()

        local = meta.get("id")
        if local is None:
            local = "n%d" % (len(nodes) + 1)
        parent_local = meta.get("parent-id")
        if parent_local is None and prev is not None:
            parent_local = prev.local_id

        body = chunks[i + 1]
        # A node's transcript opens with the "> command" echo; drop it so
        # `output` is purely what the game said.
        lines = body.split("\n")
        if lines and (lines[0].startswith("> ") or lines[0].startswith(") ")):
            lines = lines[1:]

        prev = Node(
            nid=qual(local),
            parent=qual(parent_local),
            command=meta.get("command"),
            label=meta.get("label"),
            output="\n".join(lines),
            origin=origin,
            local_id=local,
        )
        nodes.append(prev)
    return header, nodes


# ------------------------------------------------------- sub-skein selectors

SELECTOR_KEYS = ("parent-id", "parent-label", "parent-command",
                 "parent-after", "parent-output", "parent-path")


def selector_of(header):
    """The parent-* constraints in a fragment header, all of which must hold."""
    return {k: v for k, v in header.items() if k in SELECTOR_KEYS}


def describe_selector(sel):
    return ", ".join("%s: %s" % (k, v) for k, v in sorted(sel.items()))


def path_commands(node, by_id):
    """Commands from the root down to `node`."""
    out = []
    seen = set()
    while node is not None and node.id not in seen:
        seen.add(node.id)
        if node.command:
            out.append(node.command)
        node = by_id.get(node.parent) if node.parent else None
    out.reverse()
    return out


def _fold(text):
    return (text or "").strip().lower()


def match_selector(nodes, sel):
    """Every node satisfying all of `sel`."""
    by_id = {n.id: n for n in nodes}
    found = []
    for n in nodes:
        ok = True
        for key, want in sel.items():
            if key == "parent-id":
                ok = n.id == want or n.local_id == want
            elif key == "parent-label":
                ok = n.label == want
            elif key == "parent-command":
                ok = _fold(n.command) == _fold(want)
            elif key == "parent-after":
                gp = by_id.get(n.parent) if n.parent else None
                ok = gp is not None and _fold(gp.command) == _fold(want)
            elif key == "parent-output":
                pat = want.strip()
                if len(pat) > 1 and pat.startswith("/") and pat.endswith("/"):
                    pat = pat[1:-1]
                try:
                    ok = re.search(pat, normalize(n.output), re.I | re.S) is not None
                except re.error as exc:
                    sys.exit("bad regex in parent-output %r: %s" % (want, exc))
            elif key == "parent-path":
                want_path = [_fold(c) for c in want.split(",") if c.strip()]
                ok = want_path == [_fold(c) for c in path_commands(n, by_id)]
            if not ok:
                break
        if ok:
            found.append(n)
    return found


def resolve_selector(nodes, sel, where):
    """Exactly one node, or a fatal error naming the alternatives."""
    found = match_selector(nodes, sel)
    if len(found) == 1:
        return found[0]
    by_id = {n.id: n for n in nodes}
    if not found:
        sys.exit("%s: no node matches (%s)" % (where, describe_selector(sel)))
    lines = ["%s: parent selector matches %d nodes; add a constraint to "
             "disambiguate" % (where, len(found))]
    for n in found[:10]:
        lines.append("    %-28s %s" % (n.id, " > ".join(path_commands(n, by_id)) or "(start)"))
    if len(found) > 10:
        lines.append("    ... and %d more" % (len(found) - 10))
    sys.exit("\n".join(lines))


# ------------------------------------------------------------ loading a tree

class Fragment:
    def __init__(self, rel, header, nodes):
        self.rel = rel
        self.header = header
        self.nodes = nodes
        self.selector = selector_of(header)
        self.attached_to = None


def load_skein(path):
    """Load a single .skein file, or a directory tree of them, as one tree."""
    if not os.path.isdir(path):
        return parse_skein(path)

    rels = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()
        for name in sorted(filenames):
            if name.endswith(".skein"):
                full = os.path.join(dirpath, name)
                rels.append(os.path.relpath(full, path))
    if not rels:
        sys.exit("no .skein files under %s" % path)

    frags = []
    for rel in sorted(rels):
        header, nodes = parse_skein(os.path.join(path, rel), origin=rel, qualify=True)
        frags.append(Fragment(rel, header, nodes))

    roots = [f for f in frags if not f.selector]
    if len(roots) != 1:
        names = ", ".join(f.rel for f in roots) or "(none)"
        sys.exit("expected exactly one root skein (a file with no parent-* "
                 "header); found %d: %s" % (len(roots), names))
    root = roots[0]

    merged = list(root.nodes)
    pending = [f for f in frags if f is not root and f.nodes]

    # Fixpoint: a fragment may attach to a node another fragment supplies, so
    # keep sweeping while anything resolves.  More than one match is fatal at
    # once (the candidate set only ever grows); zero is fatal only at the end.
    while pending:
        progress = False
        for frag in list(pending):
            found = match_selector(merged, frag.selector)
            if len(found) > 1:
                resolve_selector(merged, frag.selector, frag.rel)
            if len(found) == 1:
                frag.attached_to = found[0].id
                frag.nodes[0].parent = found[0].id
                merged += frag.nodes
                pending.remove(frag)
                progress = True
        if not progress:
            break
    if pending:
        sys.exit("\n".join(
            ["could not place %d sub-skein(s):" % len(pending)] +
            ["    %s: no node matches (%s)" % (f.rel, describe_selector(f.selector))
             for f in pending]))

    # Re-validate against the finished tree: a fragment added later can make
    # an earlier selector ambiguous, and that must fail loudly rather than
    # depend on file order.
    for frag in frags:
        if frag is root or not frag.nodes:
            continue
        node = resolve_selector(merged, frag.selector, frag.rel)
        if node.id != frag.attached_to:
            sys.exit("%s: parent selector became ambiguous after merging "
                     "(now resolves to %s, attached to %s)"
                     % (frag.rel, node.id, frag.attached_to))

    return root.header, merged


def children_map(nodes):
    kids = {n.id: [] for n in nodes}
    roots = []
    for n in nodes:
        if n.parent and n.parent in kids:
            kids[n.parent].append(n)
        else:
            roots.append(n)
    return roots, kids


def find_leaves(nodes):
    """Every node with no children, in file order.  One per branch tip."""
    parents = {n.parent for n in nodes}
    return [n for n in nodes if n.id not in parents]


def resolve(nodes, target):
    """A node by qualified id, file-local id, or label."""
    by_id = {n.id: n for n in nodes}
    if target in by_id:
        return by_id[target]
    for attr in ("local_id", "label"):
        matches = [n for n in nodes if getattr(n, attr) == target]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            sys.exit("%r is ambiguous (%s); use a full id"
                     % (target, ", ".join(n.id for n in matches)))
    sys.exit("no node with id or label %r" % target)


def all_paths(nodes, target=None):
    """The set of root-to-leaf paths needed to cover the skein.

    A named target gives one path; otherwise every branch tip gets one, which
    together visit every node in the tree exactly once.
    """
    if target is not None:
        return [path_to(nodes, target)]
    return [path_to(nodes, leaf.id) for leaf in find_leaves(nodes)] or [[]]


def path_to(nodes, target=None):
    """Root-to-target chain.  target may be an id, a label, or None (= leaf)."""
    by_id = {n.id: n for n in nodes}
    if target is None:
        leaves = find_leaves(nodes)
        node = leaves[-1] if leaves else nodes[-1]
    else:
        node = resolve(nodes, target)

    chain = []
    seen = set()
    while node is not None:
        if node.id in seen:
            sys.exit("cycle in skein at node %s" % node.id)
        seen.add(node.id)
        chain.append(node)
        node = by_id.get(node.parent) if node.parent else None
    chain.reverse()
    return chain


# ------------------------------------------------------------------ sources

def sources_from_edn(path):
    """Pull :main / :debug / :library source paths out of dialog.edn."""
    try:
        with open(path, encoding="utf-8") as fp:
            edn = fp.read()
    except OSError:
        return None
    out = []
    for key in (":main", ":debug", ":library"):
        m = re.search(re.escape(key) + r"\s*\[([^\]]*)\]", edn)
        if m:
            out += re.findall(r'"([^"]+)"', m.group(1))
    return out or None


def expand_sources(entries):
    """Directories expand to their sorted *.dg files; files pass through."""
    files = []
    for entry in entries:
        full = entry if os.path.isabs(entry) else os.path.join(ROOT, entry)
        if os.path.isdir(full):
            files += sorted(
                os.path.join(full, f)
                for f in os.listdir(full)
                if f.endswith(".dg")
            )
        else:
            files.append(full)
    return files


# ------------------------------------------------------------------- dgdebug

def run_dgdebug(commands, seed, sources, dgdebug="dgdebug"):
    """Feed `commands` to a fresh dgdebug.  Returns (preamble, [(cmd, out)]).

    `preamble` is everything printed before the first command echo: compiler
    warnings, the banner and the opening room description.
    """
    argv = [dgdebug, "--unit-test", "--width", "-1", "--formatting", "none",
            "--no-links", "--tag-lines", "--seed", str(seed)] + sources
    proc = subprocess.run(
        argv,
        input="".join(c + "\n" for c in commands),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace", cwd=ROOT,
    )

    segments = []          # [(command, [line, ...])]
    preamble = []
    current = preamble
    for line in proc.stdout.split("\n"):
        if line.startswith("> ") or line.startswith(") "):
            current = []
            segments.append((line[2:], current))
        elif line.startswith("  "):
            current.append(line[2:])
        else:
            current.append(line)

    def clean(lines):
        # The prompt itself arrives as an output line ("  > "); it trails
        # every segment and is not game text.
        while lines and lines[-1].rstrip() in (">", ")", ""):
            lines.pop()
        return "\n".join(lines)

    # dgdebug echoes a final empty prompt at EOF.
    if segments and segments[-1][0].strip() == "" and not clean(list(segments[-1][1])):
        segments.pop()

    return clean(preamble), [(cmd, clean(lines)) for cmd, lines in segments]


# ---------------------------------------------------------------- comparison

def normalize(text):
    """Canonical form for comparison: no ANSI, no volatile lines, no trailing
    whitespace, no trailing blank lines."""
    lines = []
    for line in ANSI.sub("", text).split("\n"):
        if any(pat.match(line) for pat in VOLATILE):
            continue
        lines.append(line.rstrip())
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return "\n".join(lines)


def unified(recorded, live, label):
    return list(difflib.unified_diff(
        recorded.split("\n"), live.split("\n"),
        fromfile="recorded/" + label, tofile="live/" + label,
        lineterm="",
    ))


def rewrite_skein(path, updates):
    """Rewrite recorded outputs in a .skein file, preserving everything else.

    `updates` maps file-local node id -> (command, new_output).  Returns the
    number of nodes changed.  The file is split on the same separator regex
    the parser uses and joined back with the identical separator, so node
    order, headers, labels and every untouched byte survive unchanged.
    """
    with open(path, encoding="utf-8", errors="replace") as fp:
        text = fp.read()
    chunks = re.split(r"^-{10,}$\n?", text, flags=re.M)
    changed = 0
    for i in range(1, len(chunks) - 1, 2):
        meta = {}
        for line in chunks[i].splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        local = meta.get("id") or "n%d" % ((i - 1) // 2 + 1)
        if local in updates:
            cmd, out = updates[local]
            # A node with no command (the start node) has no "> " echo line;
            # its body is pure preamble, exactly as parse_skein expects.
            chunks[i + 1] = (("> " + cmd + "\n") if cmd else "") + out + "\n"
            changed += 1
    if changed:
        new_text = ("-" * 80 + "\n").join(chunks)
        if not new_text.endswith("\n"):
            new_text += "\n"
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(new_text)
    return changed


# -------------------------------------------------------------------- output

def print_transcript(preamble, segments):
    if preamble.strip():
        print(preamble)
    for cmd, out in segments:
        print()
        print("> " + cmd)
        if out.strip():
            print(out)


# -------------------------------------------------------------------- verbs

def cmd_play(args, sources):
    preamble, segments = run_dgdebug(args.commands, args.seed, sources, args.dgdebug)
    if args.json:
        json.dump({
            "seed": args.seed,
            "preamble": normalize(preamble),
            "turns": [{"command": c, "output": normalize(o)} for c, o in segments],
        }, sys.stdout, indent=2)
        print()
    else:
        print_transcript(preamble, segments)
    return 0


def cmd_replay(args, sources):
    _, nodes = load_skein(args.skein)
    if args.node is None:
        leaves = find_leaves(nodes)
        if len(leaves) > 1:
            print("skein has %d branches; replaying the last (%s). "
                  "Name a node id or label to pick another."
                  % (len(leaves), leaves[-1].id), file=sys.stderr)
    chain = path_to(nodes, args.node)
    args.commands = [n.command for n in chain if n.command]
    return cmd_play(args, sources)


def compare_path(chain, seed, sources, args, seen):
    """Run one root-to-leaf path and compare each node not already checked."""
    commands = [n.command for n in chain if n.command]
    preamble, segments = run_dgdebug(commands, seed, sources, args.dgdebug)
    # chain[0] is the start node, whose recorded output is the preamble.
    live_by_index = [preamble] + [out for _, out in segments]

    results = []
    for i, node in enumerate(chain):
        if node.id in seen:
            continue
        seen.add(node.id)
        recorded = normalize(node.output)
        label = "%s (%s)" % (node.id, node.command or node.label or "START")
        if i >= len(live_by_index):
            results.append({
                "id": node.id, "command": node.command, "match": False,
                "branch": chain[-1].id, "origin": node.origin,
                "diff": ["live run ended before this node (dgdebug quit early?)"],
            })
            continue
        live = normalize(live_by_index[i])
        entry = {"id": node.id, "command": node.command,
                 "match": live == recorded, "branch": chain[-1].id,
                 "origin": node.origin}
        if not entry["match"]:
            entry["diff"] = unified(recorded, live, label)
            entry["recorded"] = recorded
            entry["live"] = live
        results.append(entry)
    return results


def cmd_diff(args, sources):
    header, nodes = load_skein(args.skein)
    seed = args.seed if args.seed is not None else int(header.get("seed", 0))
    paths = all_paths(nodes, args.node)

    seen = set()
    results = []
    for chain in paths:
        results += compare_path(chain, seed, sources, args, seen)

    bad = [r for r in results if not r["match"]]
    branched = len(paths) > 1

    if args.json:
        json.dump({
            "seed": seed,
            "branches": len(paths),
            "nodes": len(results),
            "mismatched": len(bad),
            "diffs": [
                {k: v for k, v in r.items()
                 if (k != "live" or args.full) and (k != "branch" or branched)}
                for r in bad
            ],
        }, sys.stdout, indent=2)
        print()
    else:
        for r in bad:
            print("=" * 80)
            print("node %s  command: %s%s%s" % (
                r["id"], r["command"] or "(start)",
                "  [branch %s]" % r["branch"] if branched else "",
                "  [from %s]" % r["origin"] if r.get("origin") else ""))
            print("=" * 80)
            for line in r["diff"]:
                print(line)
            print()
        print("%d/%d nodes match, %d differ%s" % (
            len(results) - len(bad), len(results), len(bad),
            " (%d branches)" % len(paths) if branched else ""))
    return 1 if bad else 0


def render_tree(node, kids, prefix="", is_last=True, only=True, out=None):
    """Box-drawing view of a skein.

    Only-children render flush with their parent, so a long linear run stays
    readable; indentation appears only where the skein actually forks.
    """
    if out is None:
        out = []
    if only:
        stem, child_prefix = "", prefix
    else:
        stem = "`- " if is_last else "|- "
        child_prefix = prefix + ("   " if is_last else "|  ")
    text = node.command or "(start)"
    if node.label:
        text += "   [%s]" % node.label
    out.append("%s%s%s  %s" % (prefix, stem, text, node.id))
    children = kids.get(node.id, [])
    for i, child in enumerate(children):
        render_tree(child, kids, child_prefix,
                    i == len(children) - 1, len(children) == 1, out)
    return out


def cmd_bless(args, sources):
    header, nodes = load_skein(args.skein)
    seed = args.seed if args.seed is not None else int(header.get("seed", 0))
    paths = all_paths(nodes, args.node)

    seen = set()
    results = []
    for chain in paths:
        results += compare_path(chain, seed, sources, args, seen)
    bad = [r for r in results if not r["match"]]

    by_file = {}    # origin file -> {file-local id: (command, normalized output)}
    skipped = []
    by_id = {n.id: n for n in nodes}
    for r in bad:
        node = by_id[r["id"]]
        if "live" not in r:
            skipped.append(r)      # dgdebug quit early; nothing to bless
            continue
        if node.origin:
            # origin is relative to the --skein directory (which may itself
            # be a single file's directory when --skein names a file).
            target = node.origin if os.path.isabs(node.origin) else \
                os.path.join(args.skein, node.origin)
        else:
            target = args.skein      # single-file skein: nodes have no origin
        by_file.setdefault(target, {})[node.local_id] = (
            node.command, normalize(r["live"]))

    if args.json:
        json.dump({
            "seed": seed,
            "branches": len(paths),
            "nodes": len(results),
            "mismatched": len(bad),
            "blessed": [r["id"] for r in bad if "live" in r],
            "skipped": [r["id"] for r in skipped],
            "files": sorted(by_file),
        }, sys.stdout, indent=2)
        print()
        return 0

    for r in skipped:
        print("cannot bless %s (%s): %s" % (r["id"], r["command"], r["diff"][0]),
              file=sys.stderr)
    if not by_file:
        print("nothing to bless: %d/%d nodes match" % (len(results), len(results)))
        return 0

    if args.dry_run:
        for path in sorted(by_file):
            for local, (cmd, _) in sorted(by_file[path].items(),
                                          key=lambda kv: kv[1][0] or ""):
                print("would bless %s in %s (%s)"
                      % (local, path, cmd or "(start)"))
        print("%d node(s) would change (dry run; use without --dry-run to write)"
              % sum(len(u) for u in by_file.values()))
        return 0

    total = 0
    for path in sorted(by_file):
        n = rewrite_skein(path, by_file[path])
        total += n
        print("blessed %d node(s) in %s" % (n, path))

    # Re-validate: a changed transcript can break a fragment's parent-output
    # selector.  load_skein exits with a message when that happens; surface it
    # as a warning rather than a failure, since the bless itself succeeded.
    try:
        load_skein(args.skein)
    except SystemExit as exc:
        print("\nwarning: skein no longer loads after blessing -- a parent-* "
              "selector may no longer match:\n%s" % exc, file=sys.stderr)

    print("%d node(s) blessed; re-run `tools/skein.py diff` to confirm clean"
          % total)
    return 0


def cmd_list(args, sources):
    _, nodes = load_skein(args.skein)
    roots, kids = children_map(nodes)
    branched = any(len(v) > 1 for v in kids.values())

    if args.tree or (branched and args.node is None and not args.json):
        start = [resolve(nodes, args.node)] if args.node else roots
        for root in start:
            for line in render_tree(root, kids):
                print(line)
        return 0

    chain = path_to(nodes, args.node)
    if args.json:
        json.dump([{"id": n.id, "parent": n.parent, "command": n.command,
                    "label": n.label, "children": [c.id for c in kids.get(n.id, [])]}
                   for n in chain], sys.stdout, indent=2)
        print()
    else:
        for i, n in enumerate(chain):
            fork = len(kids.get(n.id, []))
            print("%4d  %-16s %s%s%s" % (
                i, n.id, n.command or "(start)",
                "   [%s]" % n.label if n.label else "",
                "   (+%d branches)" % (fork - 1) if fork > 1 else ""))
    return 0


def cmd_show(args, sources):
    _, nodes = load_skein(args.skein)
    node = resolve(nodes, args.node)
    if args.json:
        json.dump({"id": node.id, "command": node.command,
                   "output": normalize(node.output)}, sys.stdout, indent=2)
        print()
    else:
        print("> " + (node.command or "(start)"))
        print(normalize(node.output))
    return 0


# Matches the end of a game (death or any other (game over)): the death
# banner, the UNDO/RESTORE menu, or the post-death parse-error prompt.
GAME_OVER = re.compile(r"\*\*\* You have died \*\*\*"
                       r"|Would you like to:"
                       r"|Please type one of the given words")


def cmd_find(args, sources):
    """List every node whose command or output matches a regex."""
    _, nodes = load_skein(args.skein)
    rx = re.compile(args.pattern, 0 if args.case else re.IGNORECASE)
    hits = []
    for n in nodes:
        where = None
        if n.command and rx.search(n.command):
            where = n.command
        if where is None:
            for line in normalize(n.output).splitlines():
                if rx.search(line):
                    where = line.strip()
                    break
        if where is not None:
            hits.append((n, where))

    if args.json:
        json.dump([{"id": n.id, "command": n.command, "label": n.label,
                    "origin": n.origin, "match": where}
                   for n, where in hits], sys.stdout, indent=2)
        print()
        return 0
    for n, where in hits:
        print("%s  %s" % (n.id, n.command or "(start)"))
        print("    %s" % where)
        if n.origin:
            print("    from %s" % n.origin)
    print("%d node(s) match /%s/" % (len(hits), args.pattern))
    return 0 if hits else 1


def cmd_path(args, sources):
    """Print a node's command chain in parent-path: selector syntax."""
    _, nodes = load_skein(args.skein)
    node = resolve(nodes, args.node)
    chain = path_to(nodes, node.id)
    commands = [n.command for n in chain if n.command]
    if args.json:
        json.dump({"id": node.id, "origin": node.origin,
                   "path": ",".join(commands), "commands": commands},
                  sys.stdout, indent=2)
        print()
    else:
        print(",".join(commands))
    return 0


def selector_from_args(args):
    pairs = (
        ("parent-id", args.parent_id),
        ("parent-label", args.parent_label),
        ("parent-command", args.parent_command),
        ("parent-after", args.parent_after),
        ("parent-output", args.parent_output),
        ("parent-path", args.parent_path),
    )
    return {k: v for k, v in pairs if v is not None}


def write_fragment(path, selector, turns):
    """Emit a sub-skein: the parent selector, then one block per new turn."""
    parts = ["\n".join("%s: %s" % (k, v) for k, v in sorted(selector.items()))]
    for cmd, out in turns:
        parts.append(SEPARATOR)
        parts.append("command: " + cmd)
        parts.append(SEPARATOR)
        parts.append("> " + cmd + "\n" + out + "\n")
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(parts) + "\n")


def cmd_record(args, sources):
    header, nodes = load_skein(args.skein)
    seed = args.seed if args.seed is not None else int(header.get("seed", 0))

    selector = selector_from_args(args)
    if not selector:
        sys.exit("record needs a parent selector: one or more of "
                 + ", ".join("--" + k.replace("parent-", "parent-")
                             for k in SELECTOR_KEYS))
    parent = resolve_selector(nodes, selector, "record")

    # Where the fragment lands: relative paths go beside the skein.
    base = args.skein if os.path.isdir(args.skein) else os.path.dirname(
        os.path.abspath(args.skein))
    out_path = args.into if os.path.isabs(args.into) else os.path.join(base, args.into)
    if os.path.exists(out_path) and not args.force:
        sys.exit("%s already exists (use --force to overwrite)" % out_path)

    prefix = [n.command for n in path_to(nodes, parent.id) if n.command]
    _, segments = run_dgdebug(prefix + args.commands, seed, sources, args.dgdebug)
    if len(segments) < len(prefix) + len(args.commands):
        sys.exit("dgdebug produced %d turns for %d commands; the game may have "
                 "ended early" % (len(segments), len(prefix) + len(args.commands)))
    turns = [(cmd, out) for cmd, out in segments[len(prefix):]]

    # Death transcripts record the post-death UNDO/RESTORE menu and any
    # commands typed past it turn into junk nodes.  Keep the turn that ends
    # the game, drop the rest, unless asked not to.
    if not args.keep_junk:
        for i, (cmd, out) in enumerate(turns):
            if GAME_OVER.search(normalize(out)):
                dropped = len(turns) - i - 1
                turns = turns[:i + 1]
                if dropped:
                    print("dropped %d turn(s) after game over (--keep-junk keeps them)"
                          % dropped, file=sys.stderr)
                break

    parent_dir = os.path.dirname(out_path)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    write_fragment(out_path, selector, turns)

    if args.json:
        json.dump({"file": out_path, "parent": parent.id,
                   "selector": selector,
                   "turns": [{"command": c, "output": normalize(o)} for c, o in turns]},
                  sys.stdout, indent=2)
        print()
    else:
        print("wrote %s (%d turns) under %s"
              % (out_path, len(turns), parent.id))
        print_transcript("", turns)
        if not os.path.isdir(args.skein):
            print("\nnote: --skein points at a file, so this fragment will not "
                  "be loaded until you pass the containing directory instead.",
                  file=sys.stderr)
    return 0


def main():
    def common(parser, sub=False):
        """Shared flags, accepted either before or after the subcommand.

        On the subparsers the defaults are SUPPRESSed, so an unused flag
        there does not clobber a value given before the subcommand.
        """
        d = (lambda v: argparse.SUPPRESS) if sub else (lambda v: v)
        parser.add_argument("--skein", default=d(os.path.join(ROOT, "skeins/")),
                            help="a .skein file, or a directory tree of them")
        parser.add_argument("--seed", type=int, default=d(None))
        parser.add_argument("--dgdebug", default=d("dgdebug"))
        parser.add_argument("--source", action="append", default=d([]),
                            help="source file or directory (repeatable); "
                                 "defaults to the :sources in dialog.edn")
        parser.add_argument("--json", action="store_true", default=d(False),
                            help="machine-readable output")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    common(ap)
    sub = ap.add_subparsers(dest="verb", required=True)

    p = sub.add_parser("diff", help="replay and diff against the recording")
    p.add_argument("node", nargs="?",
                   help="node id or label (default: every branch of the tree)")
    p.add_argument("--full", action="store_true",
                   help="include full live text in --json output")
    common(p, sub=True)
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("play", help="run commands from a fresh start")
    p.add_argument("commands", nargs="+")
    common(p, sub=True)
    p.set_defaults(func=cmd_play)

    p = sub.add_parser("replay", help="replay a recorded path")
    p.add_argument("node", nargs="?", help="node id or label (default: leaf)")
    common(p, sub=True)
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("bless",
                       help="accept live output as the new recording")
    p.add_argument("node", nargs="?",
                   help="node id or label (default: every branch of the tree)")
    p.add_argument("--dry-run", action="store_true",
                   help="list what would change without writing any file")
    common(p, sub=True)
    p.set_defaults(func=cmd_bless)

    p = sub.add_parser("list", help="list nodes along a path, or the whole tree")
    p.add_argument("node", nargs="?")
    p.add_argument("--tree", action="store_true",
                   help="always render as a tree, even for a linear skein")
    common(p, sub=True)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("record",
                       help="run new commands under a parent and save a sub-skein")
    p.add_argument("commands", nargs="+")
    p.add_argument("--into", required=True,
                   help="fragment file to write (relative to the skein directory)")
    p.add_argument("--force", action="store_true", help="overwrite an existing file")
    p.add_argument("--keep-junk", action="store_true",
                   help="keep turns recorded after a game over (default: drop them)")
    for flag in SELECTOR_KEYS:
        p.add_argument("--" + flag, default=None,
                       help="parent constraint: %s" % flag)
    common(p, sub=True)
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("show", help="show one node's recorded output")
    p.add_argument("node")
    common(p, sub=True)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("find",
                       help="list nodes whose command or output matches a regex")
    p.add_argument("pattern", help="regular expression over commands and output")
    p.add_argument("--case", action="store_true",
                   help="case-sensitive matching (default: insensitive)")
    common(p, sub=True)
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("path",
                       help="print a node's command chain as a parent-path: selector")
    p.add_argument("node", help="node id or label")
    common(p, sub=True)
    p.set_defaults(func=cmd_path)

    args = ap.parse_args()

    entries = args.source or sources_from_edn(os.path.join(ROOT, "dialog.edn")) \
        or ["src/rooms", "src/core", "lib/dialog/debug", "lib/dialog/stdlib.dg"]
    sources = expand_sources(entries)

    if args.verb in ("play", "replay") and args.seed is None:
        header = load_skein(args.skein)[0] if os.path.exists(args.skein) else {}
        args.seed = int(header.get("seed", 0))

    sys.exit(args.func(args, sources))


if __name__ == "__main__":
    main()
