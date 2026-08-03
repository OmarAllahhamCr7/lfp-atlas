#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_v1.py — LFP Atlas builder. canonical.json in, every artifact out. Mirrors the
NMC Atlas build discipline: build-failing assertions, no hand-edited outputs.

  python build/build_v1.py          regenerates data.json, data.js, lfp_atlas_claims.csv
  python build/build_v1.py --check  verifies byte-identity without writing

Counting (the olivine rule, seed edition — also stated in canonical meta):
  operating bands  : plant sgroup==operating · claim kind==capacity · basis built|reported
                     · claim scale != pilot · product CAM · no bundle · no duplicate · counted!=False
                     lower    = chem stated (LFP, LMFP)
                     headline = lower + L(M)FP-unsplit
                     upper    = headline + bundles / cathode-unsplit on operating plants
  pipeline         : claim basis announced|planned|construction · plant sgroup not in
                     (dead, context, uncertain, precursor) · no duplicate · counted!=False · product CAM
                     (basis 'target' NEVER counts anywhere — expansion goals often subsume current figures)
  per-plant tonnage: per chem tag take MAX qualifying claim (several claims measure the same thing),
                     then SUM across chem tags; site-scope pipeline claims are additive.
"""
import json, os, sys, csv, io
from math import pi

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(ROOT)
CHECK = "--check" in sys.argv

can = json.load(open(os.path.join(ROOT, "canonical.json"), encoding="utf-8"))
geo = json.load(open(os.path.join(ROOT, "geo_projected.json"), encoding="utf-8"))
SRC = {s["id"]: s for s in can["sources"]}

def claim_source_ids(c):
    extra = c.get("srcs") or []
    assert isinstance(extra, list), "srcs must be a list on " + c["id"]
    ids = []
    for source_id in [c.get("src"), *extra]:
        if source_id and source_id not in ids:
            ids.append(source_id)
    return ids

def claim_sources(c):
    return [SRC[source_id] for source_id in claim_source_ids(c)]

def claim_source_roles(c):
    roles = c.get("source_roles") or {}
    assert isinstance(roles, dict), "source_roles must be an object on " + c["id"]
    assert set(roles) <= set(claim_source_ids(c)), \
        "source_roles references a source outside the claim bundle: " + c["id"]
    assert all(isinstance(role, str) and role.strip() for role in roles.values()), \
        "source_roles must contain non-empty strings on " + c["id"]
    return roles

def public_claim_source(c, source):
    out = {key: source[key] for key in
           ("id", "title", "publisher", "doc_type", "doc_date", "url", "tier")}
    role = claim_source_roles(c).get(source["id"])
    if role:
        out["role"] = role
    return out

def months_old(doc_date, dataset_date):
    def parse(value):
        value = (value or "").strip()
        if len(value) < 4 or not value[:4].isdigit():
            return None
        year = int(value[:4])
        month = 1
        if len(value) >= 7 and value[4] == "-" and value[5:7].isdigit():
            month = int(value[5:7]) or 1
        return year, month
    document = parse(doc_date)
    dataset = parse(dataset_date)
    if document is None or dataset is None:
        return None
    return max((dataset[0] - document[0]) * 12 + dataset[1] - document[1], 0)

# ---- projection: calibrated Natural Earth fit (identical approach to NMC build) --
def _ne(lon, lat):
    l = lon * pi / 180; p = lat * pi / 180; p2 = p * p; p4 = p2 * p2
    x = l * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    y = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
    return x, y
def _fit(pairs):
    n = len(pairs); sx = sum(a for a, _ in pairs); sy = sum(b for _, b in pairs)
    sxx = sum(a * a for a, _ in pairs); sxy = sum(a * b for a, b in pairs)
    k = (n * sxy - sx * sy) / (n * sxx - sx * sx); return k, (sy - k * sx) / n
_kx, _bx = _fit([(_ne(s["lon"], s["lat"])[0], s["x"]) for s in geo["sites"]])
_ky, _by = _fit([(_ne(s["lon"], s["lat"])[1], s["y"]) for s in geo["sites"]])
def project(lon, lat):
    rx, ry = _ne(lon, lat); return round(_kx * rx + _bx, 2), round(_ky * ry + _by, 2)

GEO_BASES = {"city-centroid", "region-only", "hq-city", "country-only"}
STATES = {"operating", "building", "announced", "pilot", "uncertain", "dead", "precursor", "context"}
CHEMS = {"LFP", "LMFP", "L(M)FP-unsplit", "cathode-unsplit", "FePO4", "not-LFP"}
KINDS = {"capacity", "output", "shipments", "output_cumulative", "output_rate", "share", "qualitative"}
BASES = {"built", "reported", "construction", "announced", "planned", "target", "historic", "cancelled"}
STATUS_LBL = {"operating": "Operating", "building": "Under construction", "announced": "Announced",
              "pilot": "Pilot / demo", "uncertain": "Uncertain / limited", "dead": "Exited / cancelled",
              "precursor": "Precursor only", "context": "Context row (not a CAM maker)"}

ALL_CLAIM_IDS = []
for p in can["plants"]:
    assert p["sgroup"] in STATES, "off-enum sgroup on " + p["id"]
    assert p.get("sites"), "PLANT WITHOUT A SITE: " + p["id"]
    prim = [s for s in p["sites"] if s.get("primary")]
    assert len(prim) == 1, "no single primary site on " + p["id"]
    for s in p["sites"]:
        assert s["geo_basis"] in GEO_BASES, "bad geo_basis %r on %s" % (s["geo_basis"], p["id"])
        s["x"], s["y"] = project(s["lon"], s["lat"])
    p["x"], p["y"] = prim[0]["x"], prim[0]["y"]
    p["lat"], p["lon"] = prim[0]["lat"], prim[0]["lon"]
    keys = {s["key"] for s in p["sites"]}
    for c in p["claims"]:
        ALL_CLAIM_IDS.append(c["id"])
        assert c["kind"] in KINDS, "off-enum kind %r on %s" % (c["kind"], c["id"])
        assert c["basis"] in BASES, "off-enum basis %r on %s" % (c["basis"], c["id"])
        assert c["chem"] in CHEMS, "off-enum chem %r on %s" % (c["chem"], c["id"])
        assert not c.get("site_key") or c["site_key"] in keys, "claim site_key unresolved on " + c["id"]
        if c["value_ty"] is not None:
            source_ids = claim_source_ids(c)
            assert source_ids, "figure without a source: " + c["id"]
            assert all(source_id in SRC for source_id in source_ids), \
                "figure with unresolved source: " + c["id"]
            claim_source_roles(c)
        evidence_method = c.get("evidence_method")
        assert evidence_method in (None, "component-sum", "durable-nameplate", "site-floor"), \
            "unknown evidence_method on " + c["id"]
        if evidence_method in ("component-sum", "durable-nameplate", "site-floor"):
            components = c.get("components") or []
            assert components, "component-backed claim without components: " + c["id"]
            assert sum(int(component.get("value_ty") or 0) for component in components) == c["value_ty"], \
                "components do not equal claim value: " + c["id"]
            source_ids = set(claim_source_ids(c))
            component_source_ids = set()
            for component in components:
                component_sources = component.get("srcs") or []
                assert component_sources, "component without sources: " + c["id"]
                component_source_ids.update(component_sources)
                assert set(component_sources) <= source_ids, \
                    "component source missing from claim bundle: " + c["id"]
                assert any(SRC[source_id]["tier"] in ("primary", "company")
                           for source_id in component_sources), \
                    "component lacks a direct source: " + c["id"]
            corroboration_sources = c.get("corroboration_srcs") or []
            assert isinstance(corroboration_sources, list), \
                "corroboration_srcs must be a list on " + c["id"]
            assert set(corroboration_sources) <= source_ids, \
                "corroboration source missing from claim bundle: " + c["id"]
            assert not (set(corroboration_sources) & component_source_ids), \
                "corroboration sources must be separate from component evidence: " + c["id"]
            if evidence_method == "durable-nameplate":
                assert c["kind"] == "capacity" and c["basis"] in ("built", "reported"), \
                    "durable-nameplate must describe built/reported capacity: " + c["id"]
                assert c.get("as_of"), "durable-nameplate requires an as_of date: " + c["id"]
                status_sources = c.get("status_srcs") or []
                assert isinstance(status_sources, list) and status_sources, \
                    "durable-nameplate requires status_srcs: " + c["id"]
                assert set(status_sources) <= source_ids, \
                    "status source missing from claim bundle: " + c["id"]
                assert not (set(status_sources) & component_source_ids), \
                    "status sources must be separate from exact component evidence: " + c["id"]
                assert all(SRC[source_id]["tier"] in ("primary", "trade")
                           and SRC[source_id].get("doc_date")
                           for source_id in status_sources), \
                    "status sources must be dated independent evidence: " + c["id"]
            if evidence_method == "site-floor":
                assert c["kind"] == "capacity" and c["basis"] in ("built", "reported"), \
                    "site-floor must describe built/reported capacity: " + c["id"]
                assert c.get("as_of"), "site-floor requires an as_of date: " + c["id"]
                assert c.get("scope") == "company", \
                    "site-floor must aggregate explicitly named company sites: " + c["id"]
                for component in components:
                    component_method = component.get("evidence_basis")
                    assert component_method in ("direct", "arithmetic-difference"), \
                        "site-floor component lacks a supported evidence method: " + c["id"]
                    assert component.get("site_key") in keys, \
                        "site-floor component site_key unresolved on " + c["id"]
                    if component_method == "arithmetic-difference":
                        calculation = component.get("calculation") or {}
                        assert calculation.get("operation") == "difference", \
                            "site-floor arithmetic must use explicit difference: " + c["id"]
                        minuend = calculation.get("minuend_ty")
                        subtrahend = calculation.get("subtrahend_ty")
                        assert isinstance(minuend, int) and isinstance(subtrahend, int), \
                            "site-floor difference lacks integer operands: " + c["id"]
                        assert minuend - subtrahend == component["value_ty"], \
                            "site-floor subtraction does not equal component: " + c["id"]
                status_sources = c.get("status_srcs") or []
                assert isinstance(status_sources, list) and status_sources, \
                    "site-floor requires status_srcs: " + c["id"]
                assert set(status_sources) <= source_ids, \
                    "site-floor status source missing from claim bundle: " + c["id"]
                assert not (set(status_sources) & component_source_ids), \
                    "site-floor status sources must be separate from exact evidence: " + c["id"]
                assert all(
                    SRC[source_id]["tier"] in ("primary", "company")
                    and (age := months_old(
                        SRC[source_id].get("doc_date"), can["meta"].get("dataset_date")
                    )) is not None
                    and age <= 18
                    for source_id in status_sources
                ), "site-floor status sources must be current direct evidence: " + c["id"]
                conflict_sources = c.get("conflict_srcs") or []
                assert isinstance(conflict_sources, list) and conflict_sources, \
                    "site-floor requires explicit conflict_srcs: " + c["id"]
                assert set(conflict_sources) <= source_ids, \
                    "site-floor conflict source missing from claim bundle: " + c["id"]
                assert not (set(conflict_sources) & (component_source_ids | set(status_sources))), \
                    "site-floor conflict sources must be excluded from the floor evidence: " + c["id"]
                assert all(SRC[source_id]["tier"] in ("primary", "company")
                           for source_id in conflict_sources), \
                    "site-floor conflict lacks direct evidence: " + c["id"]
                roles = claim_source_roles(c)
                assert set(status_sources + conflict_sources) <= set(roles), \
                    "site-floor status/conflict sources require explicit public roles: " + c["id"]
assert len(ALL_CLAIM_IDS) == len(set(ALL_CLAIM_IDS)), "claim ids duplicated"
_IDSET = set(ALL_CLAIM_IDS)
for p in can["plants"]:
    for c in p["claims"]:
        if c.get("duplicate_of"):
            assert c["duplicate_of"] in _IDSET, "duplicate_of points nowhere: " + c["id"]

# ---- caveat + confidence model (objective attributes only) ----------------------
def caveats(c, sources):
    cv = []
    if c.get("superseded_by"):
        cv.append("superseded by " + c["superseded_by"] + " — shown for history, counts toward no total")
    if c.get("seed_row_source") and c["value_ty"] is not None:
        cv.append("row-level seed source — figure-level re-sourcing pending")
    if c["kind"] == "capacity" and not c.get("as_of"):
        cv.append("no vintage stated in seed")
    n = (c.get("note") or "").lower()
    if "floor" in n or "'>'" in n or "'+'" in n: cv.append("stated as a floor")
    if "lower bound recorded" in n: cv.append("range — lower bound recorded")
    if "up to" in n or "ceiling" in n: cv.append("stated as a ceiling ('up to')")
    if c.get("bundle"): cv.append("bundle — non-CAM or mixed tonnage inside")
    if c.get("duplicate_of"): cv.append("same project as " + c["duplicate_of"] + " — counts once there")
    if c.get("evidence_method") == "component-sum":
        cv.append("derived component sum — all component sources listed")
    if c.get("evidence_method") == "durable-nameplate":
        cv.append("durable nameplate — exact primary components; current operation corroborated separately")
        cv.append("nameplate capacity, not actual output")
    if c.get("evidence_method") == "site-floor":
        cv.append("evidenced site floor — exact site components only; excluded sites and conflicting totals do not count")
        if any(component.get("evidence_basis") == "arithmetic-difference"
               for component in c.get("components") or []):
            cv.append("one or more site components are arithmetic differences with operands disclosed")
        cv.append("nameplate capacity, not actual output")
    if c["basis"] == "target": cv.append("company target — counts toward no total")
    if c["kind"] in ("shipments", "output"): cv.append("market observation, not nameplate")
    if c["kind"] == "output_cumulative": cv.append("cumulative, not a rate")
    if c["kind"] == "output_rate": cv.append("rate in native units — never converted")
    return cv

def pconf(c, sources):
    tiers = [(source or {}).get("tier", "weak") for source in sources] or ["weak"]
    score = max({"primary": 3, "company": 2, "trade": 1, "weak": 0}[tier]
                for tier in tiers)
    if c["kind"] == "capacity" and not c.get("as_of"): score -= 1
    if c.get("bundle"): score -= 1
    return "High" if score >= 3 else ("Medium" if score == 2 else "Low")

# ---- counting -------------------------------------------------------------------
# Superseded claims (append-only correction chains, v0.2+) count toward NOTHING.
def counted_band(p, c):
    if p["sgroup"] != "operating": return False
    if c["kind"] != "capacity" or c["basis"] not in ("built", "reported"): return False
    if c.get("scale") == "pilot" or c.get("bundle") or c.get("duplicate_of") or c.get("superseded_by"): return False
    if c.get("counted") is False or c["value_ty"] is None: return False
    return c.get("product", "CAM") == "CAM" and c["chem"] in ("LFP", "LMFP", "L(M)FP-unsplit")

def counted_upper_extra(p, c):
    if p["sgroup"] != "operating": return False
    if c["kind"] != "capacity" or c["basis"] not in ("built", "reported"): return False
    if c.get("scale") == "pilot" or c.get("duplicate_of") or c.get("superseded_by") or c.get("counted") is False: return False
    if c["value_ty"] is None or c.get("product", "CAM") != "CAM": return False
    return bool(c.get("bundle")) or c["chem"] == "cathode-unsplit"

def counted_pipeline(p, c):
    if p["sgroup"] in ("dead", "context", "uncertain", "precursor"): return False
    if c["kind"] != "capacity" or c["basis"] not in ("announced", "planned", "construction"): return False
    if c.get("duplicate_of") or c.get("superseded_by") or c.get("counted") is False or c["value_ty"] is None: return False
    return c.get("product", "CAM") == "CAM"

def plant_rollups(p):
    # operating: per chem tag take max qualifying, then sum
    per_chem = {}
    for c in p["claims"]:
        if counted_band(p, c):
            per_chem[c["chem"]] = max(per_chem.get(c["chem"], 0), c["value_ty"])
    op = sum(per_chem.values())
    op_lower = sum(v for k, v in per_chem.items() if k in ("LFP", "LMFP"))
    upper_extra = 0
    seen_bundle = {}
    for c in p["claims"]:
        if counted_upper_extra(p, c):
            seen_bundle[c["chem"] + "|" + str(c.get("bundle"))] = max(
                seen_bundle.get(c["chem"] + "|" + str(c.get("bundle")), 0), c["value_ty"])
    upper_extra = sum(seen_bundle.values())
    # pipeline: site-scope additive; company-scope max (avoid double count)
    pipe_site = sum(c["value_ty"] for c in p["claims"] if counted_pipeline(p, c) and c["scope"] == "site")
    pipe_co = max([c["value_ty"] for c in p["claims"] if counted_pipeline(p, c) and c["scope"] != "site"] or [0])
    pipe = pipe_site + pipe_co
    return op, op_lower, upper_extra, pipe, per_chem

# ---- public payload -------------------------------------------------------------
plants_pub, bands = [], {"lower": 0, "headline": 0, "upper": 0, "pipeline": 0}
pilot_built, precursor_ty, ship_ctx = 0, 0, []
for p in can["plants"]:
    op, op_lower, upx, pipe, per_chem = plant_rollups(p)
    bands["headline"] += op
    bands["lower"] += op_lower
    bands["upper"] += op + upx
    bands["pipeline"] += pipe
    for c in p["claims"]:
        if c.get("superseded_by"):
            continue                      # corrected figures: visible in the drawer, in no rollup
        if c["kind"] == "capacity" and c.get("scale") == "pilot" and c["basis"] == "built" and c["value_ty"] and p["sgroup"] in ("pilot", "building", "operating"):
            pilot_built += c["value_ty"]
        if c.get("product") == "FePO4" and c["value_ty"] and c["kind"] == "capacity" and c["basis"] in ("built", "reported"):
            precursor_ty += c["value_ty"]
        if c["kind"] == "shipments" and c["value_ty"]:
            ship_ctx.append({"company": p["company"], "value_ty": c["value_ty"], "as_of": c["as_of"], "note": c["note"]})
    q = {k: p[k] for k in ("id", "company", "country", "region", "section", "makes", "method",
                            "route_family", "stage", "chem_focus", "status_raw", "sgroup",
                            "capacity_text", "notes", "conf", "scale", "x", "y", "lat", "lon", "no_marker")}
    q["status"] = STATUS_LBL[p["sgroup"]]
    q["dead_cause"] = p.get("dead_cause")
    q["op_ty"] = op; q["op_lower"] = op_lower; q["upper_extra"] = upx; q["pipe_ty"] = pipe
    q["per_chem"] = per_chem
    q["sites"] = [{"key": s["key"], "name": s["name"], "lat": s["lat"], "lon": s["lon"],
                   "x": s["x"], "y": s["y"], "geo_basis": s["geo_basis"], "primary": bool(s.get("primary")),
                   "note": s.get("note", "")} for s in p["sites"]]
    q["links"] = p["links"]
    q["cap_claims"] = []
    for c in p["claims"]:
        sources = claim_sources(c)
        s = sources[0] if sources else None
        row = {k: c.get(k) for k in ("id", "kind", "product", "value_ty", "value_native", "as_of",
                                      "basis", "scope", "chem", "note", "bundle", "duplicate_of",
                                      "supersedes", "superseded_by", "target_date", "scale", "site_key")}
        row["counted_operating"] = counted_band(p, c)
        row["counted_pipeline"] = counted_pipeline(p, c)
        row["counted_upper_only"] = counted_upper_extra(p, c)
        row["src_title"] = s["title"] if s else ""
        row["src_pub"] = s["publisher"] if s else ""
        row["src_type"] = s["doc_type"] if s else ""
        row["src_date"] = s["doc_date"] if s else ""
        row["src_url"] = s["url"] if s else ""
        tiers = list(dict.fromkeys(source["tier"] for source in sources))
        row["src_tier"] = tiers[0] if len(tiers) == 1 else ("mixed" if tiers else "")
        row["sources"] = [public_claim_source(c, source) for source in sources]
        row["source_count"] = len(sources)
        row["components"] = c.get("components") or []
        row["evidence_method"] = c.get("evidence_method")
        row["status_sources"] = c.get("status_srcs") or []
        row["conflict_sources"] = c.get("conflict_srcs") or []
        row["corroboration_sources"] = c.get("corroboration_srcs") or []
        row["public_confidence"] = pconf(c, sources)
        row["caveats"] = caveats(c, sources)
        q["cap_claims"].append(row)
    s = SRC.get(p["src"])
    q["row_src"] = {"title": s["title"], "publisher": s["publisher"], "doc_type": s["doc_type"],
                    "url": s["url"], "tier": s["tier"]} if s else None
    plants_pub.append(q)

# ---- assertions: reproducibility + leaks ---------------------------------------
for q in plants_pub:
    for c in q["cap_claims"]:
        if c["value_ty"] is not None:
            for k in ("src_title", "src_pub", "src_url"):
                assert c[k], "DISPLAYED FIGURE WITHOUT %s: %s" % (k, c["id"])
            assert c["src_url"].startswith("http"), "malformed source url on " + c["id"]
            assert c["sources"], "displayed figure without source bundle: " + c["id"]
            assert all(source["url"].startswith("http") for source in c["sources"]), \
                "malformed source bundle url on " + c["id"]
    if q["sgroup"] in ("dead", "context", "uncertain", "precursor"):
        assert q["op_ty"] == 0 and q["pipe_ty"] == 0, "non-live plant leaks tonnage: " + q["id"]
_re_lo = sum(q["op_lower"] for q in plants_pub)
_re_hd = sum(q["op_ty"] for q in plants_pub)
_re_up = sum(q["op_ty"] + q["upper_extra"] for q in plants_pub)
_re_pp = sum(q["pipe_ty"] for q in plants_pub)
assert (_re_lo, _re_hd, _re_up, _re_pp) == (bands["lower"], bands["headline"], bands["upper"], bands["pipeline"]), \
    "bands not reproducible from public rows"
# regression pins — update ONLY deliberately, with a changelog entry (NMC discipline)
# v0.3.5 re-pin (2026-08-02): Rongtong's unsplit 300 kt company estimate is
# replaced by a primary-backed 180 kt/y LFP site floor; +100 kt/y Jiangyou
# construction is added to pipeline.
PINNED = (1845470, 3409970, 3409970, 3362250)
assert (bands["lower"], bands["headline"], bands["upper"], bands["pipeline"]) == PINNED, \
    "BANDS MOVED: %r (pinned %r)" % ((bands["lower"], bands["headline"], bands["upper"], bands["pipeline"]), PINNED)
assert precursor_ty == 890000, "precursor total moved: %d" % precursor_ty
# supersession integrity: chains resolve, and superseded claims count nothing anywhere
for p in can["plants"]:
    for c in p["claims"]:
        if c.get("supersedes"): assert c["supersedes"] in _IDSET, "supersedes points nowhere: " + c["id"]
        if c.get("superseded_by"):
            assert c["superseded_by"] in _IDSET, "superseded_by points nowhere: " + c["id"]
            assert not (counted_band(p, c) or counted_pipeline(p, c) or counted_upper_extra(p, c)), \
                "superseded claim still counted: " + c["id"]

# ---- gaps register (regenerated every build) ------------------------------------
no_figure = [{"company": q["company"], "country": q["country"], "status": q["status"]}
             for q in plants_pub if q["sgroup"] == "operating"
             and not any(c["counted_operating"] for c in q["cap_claims"])]
undated = [{"company": q["company"], "claim": c["id"], "value_ty": c["value_ty"]}
           for q in plants_pub for c in q["cap_claims"]
           if c["value_ty"] is not None and c["kind"] == "capacity" and not c["as_of"] and not c["superseded_by"]]
row_sourced = sum(1 for q in plants_pub for c in q["cap_claims"]
                  if c["value_ty"] is not None and not c["superseded_by"]
                  and "row-level seed source — figure-level re-sourcing pending" in c["caveats"])
weak_tier = [{"company": q["company"], "claim": c["id"], "value_ty": c["value_ty"],
              "tier": c["src_tier"]}
             for q in plants_pub for c in q["cap_claims"]
             if (c["counted_operating"] or c["counted_pipeline"]) and c["sources"]
             and all(source["tier"] in ("trade", "weak") for source in c["sources"])]
loc_flags = [{"company": q["company"], "basis": q["sites"][0]["geo_basis"]}
             for q in plants_pub if not q["no_marker"] and q["sites"] and
             next(s for s in q["sites"] if s["primary"])["geo_basis"] in ("country-only", "region-only")]
gaps = {
  "about": ("Regenerated from canonical at every build. The seed is one compilation workbook (19 Jul 2026): "
            "figures inherit row-level sources and mostly lack vintages. Everything listed here is a known "
            "weakness shipped openly rather than smoothed over."),
  "seed_gaps": can["gap_log"],
  "no_figure": no_figure,
  "undated_capacity_claims": undated,
  "row_sourced_figures": row_sourced,
  "counted_on_trade_or_weak_tier": weak_tier,
  "location_precision_flags": loc_flags,
  "archive": {"snapshotted": sum(1 for s in can["sources"] if s.get("hash")),
              "complete": sum(1 for s in can["sources"] if s.get("capture_quality") == "complete"),
              "proxy_partial": sum(1 for s in can["sources"] if s.get("capture_quality") == "proxy/partial"),
              "total": len(can["sources"]),
              "about": "SHA-256 snapshots via build/archive_sources.py + integrity pass via build/verify_archive.py "
                       "(both run on the maintainer's machine). Only 'complete' captures count as clean coverage; "
                       "proxy/partial marks block pages, stubs and non-PDF bodies (hash kept for drift detection). "
                       "Several filings archive via mirror hosts because CNINFO blocks scripted fetches — originals "
                       "stated in the source titles. --check re-downloads and reports silent edits."},
}

pub = {
  "meta": {**can["meta"],
    "bands": {"cam": {"lower": bands["lower"], "headline": bands["headline"], "upper": bands["upper"]},
              "pipeline": bands["pipeline"], "pilot_built": pilot_built,
              "precursor_fepo4": precursor_ty,
              "rule": can["meta"]["counting_rule"]},
    "shipments_context": sorted(ship_ctx, key=lambda x: -x["value_ty"]),
  },
  "plants": plants_pub,
  "customers": [{**c, **dict(zip(("x", "y"), project(c["lon"], c["lat"])))} for c in can["customers"]],
  "methods": can["methods"],
  "families": can["families"],
  "patent_events": can["patent_events"],
  "references": [{**r, "src_url": SRC[r["src"]]["url"] if r.get("src") in SRC else ""} for r in can["references"]],
  "sources_index": [{"id": s["id"], "publisher": s["publisher"], "doc_type": s["doc_type"],
                     "tier": s["tier"], "url": s["url"]} for s in can["sources"]],
  "gaps": gaps,
  "changelog": can["changelog"],
  "geo": {"width": geo["width"], "height": geo["height"], "sphere": geo["sphere"],
          "graticule": geo["graticule"], "borders": geo["borders"],
          "countries": [{"n": c["n"], "d": c["d"],
                         "hl": 1 if c["n"] in {"China", "Taiwan", "Japan", "South Korea",
                              "United States of America", "Canada", "Germany", "United Kingdom",
                              "Belgium", "Finland", "India", "Australia", "Morocco"} else 0}
                        for c in geo["countries"]]},
}

# links with projected endpoints
name_pos = {}
for q in plants_pub: name_pos[q["company"]] = (q["x"], q["y"], "plant", q["id"])
for c in pub["customers"]:
    if c["name"] not in name_pos: name_pos[c["name"]] = (c["x"], c["y"], "customer", c["name"])
links = []
for q in plants_pub:
    for l in q["links"]:
        # resolve target: exact name first, else a UNIQUE substring alias
        tgt = None
        if l["to"] in name_pos:
            tgt = name_pos[l["to"]]
        else:
            matches = [v for nm, v in name_pos.items() if l["to"].lower() in nm.lower()]
            assert len(matches) <= 1, \
                "ambiguous link target: %s -> %s (%d matches)" % (q["id"], l["to"], len(matches))
            if matches:
                tgt = matches[0]
        assert tgt, "link target unresolved: %s -> %s" % (q["id"], l["to"])
        links.append({"from": q["id"], "fromName": q["company"], "to": l["to"],
                      "x1": q["x"], "y1": q["y"], "x2": tgt[0], "y2": tgt[1],
                      "k": l["k"], "note": l["note"]})
pub["links"] = links

payload = json.dumps(pub, ensure_ascii=False, separators=(",", ":"))
assert "FILL IN" not in payload, "placeholder leaked"

claims_csv = io.StringIO()
w = csv.writer(claims_csv, lineterminator="\r\n")
w.writerow(["plant_id", "company", "country", "status", "claim_id", "kind", "product", "value_t_per_year",
            "value_native", "as_of", "basis", "scope", "chem", "scale", "bundle", "duplicate_of",
            "supersedes", "superseded_by", "target_date", "counted_operating", "counted_pipeline",
            "counted_upper_only", "public_confidence", "caveats", "note", "source_tier",
            "source_publisher", "source_type", "source_date", "source_url",
            "source_count", "source_ids", "source_urls", "source_roles"])
for q in plants_pub:
    for c in q["cap_claims"]:
        w.writerow([q["id"], q["company"], q["country"], q["status"], c["id"], c["kind"], c["product"],
                    c["value_ty"] if c["value_ty"] is not None else "", c["value_native"] or "",
                    c["as_of"], c["basis"], c["scope"], c["chem"], c["scale"] or "",
                    "bundle" if c["bundle"] else "", c["duplicate_of"] or "",
                    c["supersedes"] or "", c["superseded_by"] or "", c["target_date"] or "",
                    "Y" if c["counted_operating"] else "", "Y" if c["counted_pipeline"] else "",
                    "Y" if c["counted_upper_only"] else "", c["public_confidence"],
                    "; ".join(c["caveats"]), c["note"], c["src_tier"], c["src_pub"], c["src_type"],
                    c["src_date"], c["src_url"], c["source_count"],
                    "; ".join(source["id"] for source in c["sources"]),
                    "; ".join(source["url"] for source in c["sources"]),
                    "; ".join(
                        source["id"] + ": " + source["role"]
                        for source in c["sources"] if source.get("role")
                    )])

def emit(path, text):
    full = os.path.join(OUT, path)
    if CHECK:
        old = open(full, encoding="utf-8", newline="").read() if os.path.exists(full) else None
        assert old == text, "CHECK FAILED — %s differs from a fresh build" % path
    else:
        open(full, "w", encoding="utf-8", newline="").write(text)

emit("data.json", json.dumps(pub, ensure_ascii=False, indent=1))
emit("data.js", "window.DATA=" + payload + ";")
emit("lfp_atlas_claims.csv", "﻿" + claims_csv.getvalue())

print(("CHECK OK" if CHECK else "built") +
      " | plants %d | claims %d | figures %d | links %d" %
      (len(plants_pub), sum(len(q["cap_claims"]) for q in plants_pub),
       sum(1 for q in plants_pub for c in q["cap_claims"] if c["value_ty"] is not None), len(links)))
print("bands  lower %(lower)d · headline %(headline)d · upper %(upper)d | pipeline %(pipeline)d" % bands)
print("pilot built %d | FePO4 precursor %d | operating-no-figure %d | undated %d" %
      (pilot_built, precursor_ty, len(no_figure), len(undated)))
