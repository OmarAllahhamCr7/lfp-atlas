#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive_sources.py — SHA-256 source snapshot archiver (port of the NMC Atlas archiver).

RUN THIS ON YOUR OWN MACHINE (it downloads the cited pages):
    pip install requests
    python build/archive_sources.py            # archive everything not yet archived
    python build/archive_sources.py --check    # re-download and compare hashes (silent-edit detection)
    python build/archive_sources.py --refresh  # force re-download of everything

Crash-safe since v0.3.1:
- canonical.json is saved every 10 sources (an interrupted run loses at most 10 records);
- on start, snapshots already ON DISK from an interrupted run are ADOPTED (hashed locally,
  no re-download) before anything is fetched;
- per-request timeout is 30 s, so a chain of blocked hosts can't stall the run for long.

For every source it downloads the cited URL into build/archive/<id>.<ext>, records
sha256 / bytes / http_status / archived_local on the source, and rewrites canonical.json.
Failures record archive_error and stay unarchived — the gaps register reports coverage
either way. Then run build/verify_archive.py: only CLEAN captures count as coverage.

Note: several filings are cited via mirror hosts (Xueqiu/10jqka/Sina/QQ/Eastmoney/dataclouds)
because www.cninfo.com.cn blocks scripted fetches; the snapshot then archives the mirror copy.
"""
import hashlib, json, mimetypes, os, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.join(ROOT, "archive")
os.makedirs(ARCH, exist_ok=True)
CHECK = "--check" in sys.argv
REFRESH = "--refresh" in sys.argv
CANON = os.path.join(ROOT, "canonical.json")

try:
    import requests
except ImportError:
    sys.exit("pip install requests   (this script runs on your machine, not in the build)")

can = json.load(open(CANON, encoding="utf-8"))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LFP-Atlas-archiver/0.3.5 (+research use; contact repo owner)"}

def save():
    json.dump(can, open(CANON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def ext_for(url, ctype):
    if url.lower().split("?")[0].endswith(".pdf"): return ".pdf"
    if ctype:
        e = mimetypes.guess_extension(ctype.split(";")[0].strip())
        if e in (".pdf", ".html", ".htm", ".txt", ".json"): return ".html" if e == ".htm" else e
    return ".html"

def adopt(s):
    """Hash an on-disk snapshot from an interrupted run instead of re-downloading."""
    for ext in (".pdf", ".html", ".json", ".txt"):
        pth = os.path.join(ARCH, s["id"] + ext)
        if os.path.exists(pth):
            body = open(pth, "rb").read()
            s["hash"] = hashlib.sha256(body).hexdigest()
            s["bytes"] = len(body)
            s["archived_local"] = "archive/" + s["id"] + ext
            s["archive_error"] = None
            return True
    return False

ok = fail = drift = skipped = adopted = 0
since_save = 0
for s in can["sources"]:
    url = s.get("url")
    if not url: continue
    have = s.get("hash") and s.get("archived_local") and os.path.exists(os.path.join(ROOT, s["archived_local"]))
    if have and not (CHECK or REFRESH):
        skipped += 1
        continue
    if not have and not (CHECK or REFRESH) and adopt(s):
        adopted += 1
        since_save += 1
        print("adopt  %s  %7d B  (from interrupted run)" % (s["id"], s["bytes"]))
        if since_save >= 10: save(); since_save = 0
        continue
    try:
        r = requests.get(url, headers=UA, timeout=30, allow_redirects=True)
        body = r.content
        h = hashlib.sha256(body).hexdigest()
        if CHECK and have:
            if h != s["hash"]:
                drift += 1
                print("DRIFT  %s  stored %s… fetched %s…  %s" % (s["id"], s["hash"][:12], h[:12], url))
            else:
                ok += 1
            continue
        name = "%s%s" % (s["id"], ext_for(url, r.headers.get("content-type", "")))
        open(os.path.join(ARCH, name), "wb").write(body)
        s["hash"] = h
        s["bytes"] = len(body)
        s["http_status"] = r.status_code
        s["archived_local"] = "archive/" + name
        s["archive_error"] = None
        ok += 1
        print("ok     %s  %7d B  %s" % (s["id"], len(body), url[:90]))
    except Exception as e:
        fail += 1
        s["archive_error"] = str(e)[:200]
        print("FAIL   %s  %s  %s" % (s["id"], url[:80], str(e)[:90]))
    since_save += 1
    if since_save >= 10 and not CHECK:
        save(); since_save = 0
    time.sleep(1.2)   # politeness

if not CHECK:
    save()
total = len(can["sources"])
snap = sum(1 for s in can["sources"] if s.get("hash"))
print("\n%s | %d ok, %d adopted, %d failed, %d skipped, %d drifted | coverage %d/%d" %
      ("CHECK" if CHECK else "ARCHIVE", ok, adopted, fail, skipped, drift, snap, total))
print("Next:  python build/verify_archive.py   then   python build/build_v1.py")
