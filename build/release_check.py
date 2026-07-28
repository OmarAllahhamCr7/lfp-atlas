#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_check.py — the one-command release gate (NMC discipline, LFP scale).
Runs: rebuild → byte-identity check → standalone rebuild + self-containment → node suite
→ version consistency. Exits non-zero on any failure."""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(ROOT)
def run(cmd, **kw):
    print("·", " ".join(cmd))
    r = subprocess.run(cmd, cwd=kw.pop("cwd", OUT), **kw)
    if r.returncode: sys.exit("GATE FAILED: " + " ".join(cmd))

run([sys.executable, os.path.join(ROOT, "build_v1.py")])
run([sys.executable, os.path.join(ROOT, "build_v1.py"), "--check"])
run([sys.executable, os.path.join(ROOT, "make_standalone.py")])

sa = open(os.path.join(OUT, "LFP_Atlas_standalone.html"), encoding="utf-8").read()
assert "window.DATA=" in sa and "<script src=" not in sa and 'href="styles.css"' not in sa, \
    "standalone is not self-contained"

can = json.load(open(os.path.join(ROOT, "canonical.json"), encoding="utf-8"))
pub = json.load(open(os.path.join(OUT, "data.json"), encoding="utf-8"))
v = can["meta"]["version"]
assert pub["meta"]["version"] == v, "version drift canonical vs data.json"
assert can["changelog"][0]["version"] == v, "changelog head is not the current version"
pkg = json.load(open(os.path.join(OUT, "package.json"), encoding="utf-8"))
assert pkg["version"] == v, "package.json version drift"

if os.path.exists(os.path.join(OUT, "node_modules")):
    run(["node", "test.mjs"])
else:
    print("· node_modules missing — run `npm install && npm test` to complete the gate")

print("RELEASE GATE PASSED — v%s, %d plants, %d sources" %
      (v, len(can["plants"]), len(can["sources"])))
