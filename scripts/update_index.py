#!/usr/bin/env python3
"""Maintain meta/index.json: v1/*.json names + last-updated time. Stdlib only.

Usage: update_index.py [--staged | --rebuild]
  --staged   (default) staged v1 files get now; new files from git log; drop missing.
  --rebuild  all entries from git log (fallback now for untracked).
"""
import datetime
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "meta", "index.json")


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    if r.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def last_commit_time(rel):
    return git("log", "-1", "--format=%cI", "--", rel) or None


def load_existing():
    try:
        with open(INDEX, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def main(argv):
    if len(argv) > 1 or (argv and argv[0] not in ("--staged", "--rebuild")):
        print("usage: update_index.py [--staged | --rebuild]", file=sys.stderr)
        return 2
    rebuild = bool(argv) and argv[0] == "--rebuild"

    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "v1", "*.json")))
    old = load_existing()
    old_files = old.get("files", {}) if isinstance(old, dict) else {}
    t = now()
    files = {}

    if rebuild:
        for n in names:
            files[n] = {"updated": last_commit_time("v1/" + n) or t}
    else:
        staged = set(git("diff", "--cached", "--name-only", "--diff-filter=ACMR",
                         "--", "v1/*.json").splitlines())
        for n in names:
            prev = old_files.get(n)
            if "v1/" + n in staged:
                files[n] = {"updated": t}
            elif isinstance(prev, dict) and prev.get("updated"):
                files[n] = {"updated": prev["updated"]}
            else:
                files[n] = {"updated": last_commit_time("v1/" + n) or t}

    if isinstance(old, dict) and old.get("schema") == 1 and old_files == files:
        changed = False
    else:
        changed = True
        out = {"schema": 1, "generated": t, "files": files}
        os.makedirs(os.path.dirname(INDEX), exist_ok=True)
        with open(INDEX, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, sort_keys=True)
            f.write("\n")

    print("meta/index.json: %s (%d file(s))" % ("updated" if changed else "unchanged", len(files)))
    if not rebuild and os.path.exists(INDEX):
        git("add", "meta/index.json")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except RuntimeError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        sys.exit(1)
