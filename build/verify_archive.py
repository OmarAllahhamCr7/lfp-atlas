#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_archive.py — snapshot-integrity pass. Run AFTER archive_sources.py, on your machine:

    python build/verify_archive.py

Coverage honesty (the NMC lesson: a block page with a hash is not an archived source).
Classifies every snapshot and writes capture_quality onto the source in canonical.json:

  complete       looks like the real document
  proxy/partial  suspicious capture — one of:
                   - byte-identical body shared by DIFFERENT URLs (mirror serving one
                     block/consent page for everything)
                   - file smaller than 1,500 bytes (stub / error body)
                   - .pdf snapshot that does not start with %PDF magic bytes
                   - HTML whose first 4 KB contains a known block marker
  missing        no snapshot on disk (archive failed or never ran)

Then rerun `python build/build_v1.py` — the gaps register reports complete vs
proxy/partial separately. Suspect captures keep their hash (drift detection still
works); they just stop counting as clean coverage.
"""
import collections, json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
can = json.load(open(os.path.join(ROOT, "canonical.json"), encoding="utf-8"))

BLOCK_MARKERS = [b"Access Denied", b"access denied", b"Just a moment", b"cf-browser-verification",
                 b"captcha", b"CAPTCHA", b"Please enable JavaScript", b"Request unsuccessful"]
BLOCK_MARKERS += [m.encode("utf-8") for m in
                  ("人机验证",        # 人机验证 (human verification)
                   "安全验证",        # 安全验证 (security check)
                   "访问过于频繁",  # 访问过于频繁 (too many requests)
                   "请开启JavaScript")]   # 请开启JavaScript

# first pass: hash frequency across DIFFERENT urls
by_hash = collections.Counter()
for s in can["sources"]:
    if s.get("hash"):
        by_hash[s["hash"]] += 1

complete = suspect = missing = 0
for s in can["sources"]:
    if not s.get("hash") or not s.get("archived_local"):
        s["capture_quality"] = "missing"
        missing += 1
        continue
    path = os.path.join(ROOT, s["archived_local"])
    reasons = []
    if not os.path.exists(path):
        s["capture_quality"] = "missing"
        missing += 1
        continue
    body = open(path, "rb").read()
    if by_hash[s["hash"]] > 1:
        reasons.append("byte-identical to %d other snapshot(s) — same page served for different URLs" % (by_hash[s["hash"]] - 1))
    if len(body) < 1500:
        reasons.append("only %d bytes — stub/error body" % len(body))
    if path.lower().endswith(".pdf") and not body.startswith(b"%PDF"):
        reasons.append("no %PDF magic — not a real PDF")
    head = body[:4096]
    for m in BLOCK_MARKERS:
        if m in head:
            reasons.append("block marker in page head")
            break
    if reasons:
        s["capture_quality"] = "proxy/partial"
        s["capture_note"] = "; ".join(reasons)
        suspect += 1
        print("SUSPECT  %s  %s" % (s["id"], "; ".join(reasons)))
    else:
        s["capture_quality"] = "complete"
        s.pop("capture_note", None)
        complete += 1

json.dump(can, open(os.path.join(ROOT, "canonical.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\ncomplete %d | proxy/partial %d | missing %d | total %d" %
      (complete, suspect, missing, len(can["sources"])))
print("Now rerun:  python build/build_v1.py")
