#!/usr/bin/env python3
"""Validate v1/*.json ad configs. Stdlib only.

Usage: validate.py [file ...]   (default: all v1/*.json)
Exit 1 if any error.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(ROOT, "schema", "ad-config.schema.json")
MAX_BYTES = 10240
PACKAGE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$")
FORMATS = ("appOpen", "banner", "interstitial", "native")


def load_unit_pattern():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    return re.compile(schema["definitions"]["unitId"]["pattern"])


def reject_dupes(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("duplicate key %r" % k)
        obj[k] = v
    return obj


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def check_keys(obj, path, required, errs):
    """obj must be dict with exactly the required keys. Returns True if ok to descend."""
    if not isinstance(obj, dict):
        errs.append((path, "must be object"))
        return False
    for k in required:
        if k not in obj:
            errs.append((path, "missing required key %r" % k))
    for k in obj:
        if k not in required:
            errs.append((path + "." + k, "unexpected key"))
    return True


def check_format(obj, path, extra, unit_re, errs):
    required = ["enabled", "unitId"] + list(extra)
    if not check_keys(obj, path, required, errs):
        return
    if "enabled" in obj and not isinstance(obj["enabled"], bool):
        errs.append((path + ".enabled", "must be boolean (true/false)"))
    if "unitId" in obj:
        u = obj["unitId"]
        if not isinstance(u, str):
            errs.append((path + ".unitId", "must be string"))
        elif not unit_re.fullmatch(u):
            errs.append((path + ".unitId", "does not match %s" % unit_re.pattern))
    for name, (lo, hi) in extra.items():
        if name not in obj:
            continue
        v = obj[name]
        if not is_int(v):
            errs.append((path + "." + name, "must be integer"))
        elif not lo <= v <= hi:
            errs.append((path + "." + name, "must be %d..%d, got %d" % (lo, hi, v)))


def check_config(data, unit_re):
    errs = []
    if not check_keys(data, "$", ["schema", "ads"], errs):
        return errs
    if "schema" in data and not (is_int(data["schema"]) and data["schema"] == 1):
        errs.append(("$.schema", "must be 1"))
    ads = data.get("ads")
    if "ads" in data and check_keys(ads, "$.ads", list(FORMATS), errs):
        for fmt in FORMATS:
            if fmt not in ads:
                continue
            extra = {"everyNTaps": (3, 20), "cooldownSec": (0, 600)} if fmt == "interstitial" else {}
            check_format(ads[fmt], "$.ads." + fmt, extra, unit_re, errs)
    return errs


def check_file(path, unit_re):
    name = os.path.basename(path)
    errs = []
    if not name.endswith(".json") or not PACKAGE_RE.match(name[:-5]):
        errs.append(("$", "file name must be <android.package>.json"))
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        return errs + [("$", "cannot read: %s" % e)]
    if len(raw) > MAX_BYTES:
        errs.append(("$", "size %d bytes > %d" % (len(raw), MAX_BYTES)))
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_dupes)
    except (ValueError, UnicodeDecodeError) as e:
        return errs + [("$", "invalid JSON: %s" % e)]
    return errs + check_config(data, unit_re)


def main(argv):
    files = argv or sorted(glob.glob(os.path.join(ROOT, "v1", "*.json")))
    if not files:
        print("no files to validate")
        return 0
    unit_re = load_unit_pattern()
    bad = 0
    total = 0
    for f in files:
        errs = check_file(f, unit_re)
        for p, reason in errs:
            print("%s: %s: %s" % (f, p, reason))
        total += len(errs)
        bad += bool(errs)
    print("%d file(s) checked, %d with errors, %d error(s)" % (len(files), bad, total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
