#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_from_excel.py — one-time provenance script: LFP_LMFP_Synthesis_Methods_and_Producers.xlsx
-> canonical.json (schema-compatible with NMC Atlas canonical, LFP extensions added).

After this runs once, build/canonical.json is THE source of truth (hand-edit it, never the outputs).
This script is kept for provenance: it shows exactly how the Excel seed became claims.

Discipline (inherited from NMC Atlas):
  - No figure is invented, interpolated or unit-converted. value_ty is set ONLY where the seed
    states a t/y figure. Rates in other units (kg/day) stay in value_native and never enter totals.
  - Every claim cites a source. The seed carries ROW-level sources; claims inherit them and are
    flagged seed_row_source=True until figure-level re-sourcing upgrades them (gaps register).
  - Bands count ONLY: operating plants, commercial scale, kind=capacity, basis built/reported,
    no bundles, no duplicates. Everything else ships visible but counts nothing.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
EX = json.load(open(os.path.join(ROOT, "seed", "excel_extract.json"), encoding="utf-8"))

VERSION = "0.1.0"
DATASET_DATE = "2026-07-27"
SEED_COMPILED = "2026-07-19"   # "Compiled 19 Jul 2026" — Read Me sheet

def cells(sheet):
    return EX[sheet]

def cval(row, col):
    for k, v in row.items():
        if "".join(ch for ch in k if ch.isalpha()) == col:
            return v
    return None

def txt(row, col, d=""):
    c = cval(row, col)
    return str(c["v"]).strip() if c and c.get("v") is not None else d

def link(row, col):
    c = cval(row, col)
    return (c or {}).get("link", "")

def fill(row, col):
    c = cval(row, col)
    return (c or {}).get("fill", "")

# ---------------- sources: dedup by URL ----------------------------------------
# publisher/doc_type/tier assigned per domain; explicit and conservative.
# tier: primary = regulator/government/peer-reviewed/patent/SEC · company = issuer's own site/PR
#       trade = trade press/analyst · weak = encyclopedic/aggregator
DOMAIN_META = {
    "www.sec.gov":              ("US SEC (EDGAR)", "regulatory filing", "primary"),
    "iopscience.iop.org":       ("IOP / J. Electrochem. Soc.", "peer-reviewed paper", "primary"),
    "link.springer.com":        ("Springer / MRS Communications", "peer-reviewed review", "primary"),
    "patents.google.com":       ("Google Patents", "patent", "primary"),
    "arena.gov.au":             ("ARENA (Australian Government)", "government project page", "primary"),
    "natural-resources.canada.ca": ("Natural Resources Canada", "government project page", "primary"),
    "www.airitilibrary.com":    ("Airiti Library", "academic article", "primary"),
    "doi.org":                  ("DOI", "peer-reviewed paper", "primary"),
    "www.sciencedirect.com":    ("Elsevier / ScienceDirect", "peer-reviewed paper", "primary"),
    "www.mitsui.com":           ("Mitsui & Co. Global Strategic Studies Institute", "industry report", "trade"),
    "cen.acs.org":              ("C&EN (American Chemical Society)", "trade press", "trade"),
    "www.adamasintel.com":      ("Adamas Intelligence", "analyst note", "trade"),
    "news.metal.com":           ("SMM (Shanghai Metals Market)", "trade press", "trade"),
    "www.energytrend.com":      ("EnergyTrend (TrendForce)", "trade press", "trade"),
    "www.yicaiglobal.com":      ("Yicai Global", "trade press", "trade"),
    "eu.36kr.com":              ("36Kr", "trade press", "trade"),
    "www.electrive.com":        ("electrive", "trade press", "trade"),
    "www.greencarcongress.com": ("Green Car Congress", "trade press", "trade"),
    "www.koreatimes.co.kr":     ("The Korea Times", "news article", "trade"),
    "www.marklines.com":        ("MarkLines", "trade press", "trade"),
    "www.chemeurope.com":       ("chemeurope.com", "trade press", "trade"),
    "battery-news.de":          ("Battery-News.de", "trade press", "trade"),
    "www.pv-magazine-india.com":("pv magazine India", "trade press", "trade"),
    "evreporter.com":           ("EVreporter", "trade press", "trade"),
    "batterytechassociation.org":("Battery Tech Association", "industry association", "trade"),
    "www.shoosmiths.com":       ("Shoosmiths LLP", "legal analysis", "trade"),
    "chemanager-online.com":    ("CHEManager", "trade press", "trade"),
    "faxiangongchang.com":      ("faxiangongchang.com", "industry report", "trade"),
    "www.prnewswire.com":       ("PR Newswire", "company press release", "company"),
    "www.businesswire.com":     ("Business Wire", "company press release", "company"),
    "en.wikipedia.org":         ("Wikipedia", "encyclopedia", "weak"),
    "www.cbinsights.com":       ("CB Insights", "company profile", "weak"),
}
COMPANY_SITE = ("company website", "company")   # fallback for issuer domains

def domain_of(url):
    m = re.match(r"https?://([^/]+)/?", url or "")
    return m.group(1).lower() if m else ""

def date_from_url(url):
    # only what the URL itself states — never guessed
    m = re.search(r"/(20\d{2})[/-]?(\d{2})?[/-]?(\d{2})?", url or "")
    if not m:
        m = re.search(r"(20\d{6})", url or "")
        if m:
            s = m.group(1); return f"{s[:4]}-{s[4:6]}-{s[6:]}"
        return ""
    y, mo, d = m.group(1), m.group(2), m.group(3)
    if mo and d: return f"{y}-{mo}-{d}"
    if mo: return f"{y}-{mo}"
    return y

SOURCES = {}          # url -> source dict
def src_id(url, title, override_meta=None):
    if not url: return None
    if url in SOURCES: return SOURCES[url]["id"]
    dom = domain_of(url)
    pub, dt, tier = (override_meta or DOMAIN_META.get(dom) or (dom, *COMPANY_SITE))
    if len((override_meta or DOMAIN_META.get(dom) or (dom,))) == 1:
        pub, (dt, tier) = dom, COMPANY_SITE
    sid = "s%03d" % (len(SOURCES) + 1)
    SOURCES[url] = {"id": sid, "url": url, "publisher": pub, "doc_type": dt, "tier": tier,
                    "title": title or dom, "doc_date": date_from_url(url), "accessed": SEED_COMPILED,
                    "archived_local": None, "hash": None,
                    "note": "Seed source carried from the compilation workbook (19 Jul 2026); not yet snapshot-archived."}
    return sid

# ---------------- geography (city/province centroids; flagged approximate) ------
# geo_basis: city-centroid | region-only | hq-city | country-only    geo sources: standard
# public-domain geography (Natural Earth base map); coordinates are centroids, NOT plant addresses.
GEO = {
 "Changsha":        (28.228, 112.939), "Wuhan":       (30.593, 114.305),
 "Shenzhen":        (22.543, 114.058), "Changzhou":   (31.811, 119.974),
 "Guiyang":         (26.647, 106.630), "Nanchang":    (28.682, 115.858),
 "Beijing":         (39.904, 116.407), "Ningbo":      (29.878, 121.549),
 "Chungju":         (36.970, 127.932), "Ya'an":       (29.987, 103.001),
 "Hefei":           (31.821, 117.227), "Chongqing":   (29.563, 106.551),
 "Jinan":           (36.668, 116.997), "Chengdu":     (30.651, 104.076),
 "Yinchuan":        (38.487, 106.231), "Kunming":     (25.043, 102.706),
 "Yantai":          (37.464, 121.448), "Ningde":      (26.662, 119.523),
 "ChinaCentroid":   (34.500, 108.900), "TaiwanCentroid": (23.700, 121.000),
 "JapanCentroid":   (36.200, 138.250), "Tokyo":       (35.676, 139.650),
 "Daegu":           (35.871, 128.601), "Pohang":      (36.019, 129.343),
 "Seoul":           (37.566, 126.978), "KoreaCentroid": (36.500, 127.800),
 "Candiac":         (45.383, -73.518), "MountainView": (37.386, -122.084),
 "Muskegon":        (43.234, -86.248), "JacksonTN":   (35.615, -88.814),
 "Saguenay":        (48.428, -71.068), "SanDiego":    (32.716, -117.161),
 "HooksTX":         (33.466, -94.288), "StLouis":     (38.627, -90.199),
 "Clarksville":     (36.530, -87.359), "USACentroid": (39.800, -98.600),
 "Weimar":          (50.979, 11.329),  "Bitterfeld":  (51.620, 12.320),
 "MiltonKeynes":    (52.041, -0.759),  "Moosburg":    (48.470, 11.935),
 "Engis":           (50.578, 5.398),   "UKCentroid":  (52.500, -1.500),
 "Bengaluru":       (12.972, 77.594),  "Hyderabad":   (17.385, 78.487),
 "Jamnagar":        (22.470, 70.057),  "Brisbane":    (-27.470, 153.026),
 "Darwin":          (-12.464, 130.846),"Vaasa":       (63.096, 21.616),
 "MoroccoCentroid": (31.800, -7.100),  "Salzgitter":  (52.150, 10.330),
 "Yongin":          (37.240, 127.180),
}

def site(key, name, basis, primary=True, note=""):
    lat, lon = GEO[key]
    return {"key": key.lower(), "name": name, "lat": lat, "lon": lon,
            "geo_basis": basis, "primary": primary, "note": note}

# ---------------- per-row overlay ----------------------------------------------
# Keyed by the Excel row number in 'CAM Producers'. Verbatim text fields come from
# the sheet programmatically; this overlay adds ONLY structure: status enum, stage,
# chemistry tags, discrete claims, geography, links. Claim values are transcribed
# from the row's 'Capacity / market position' text — nothing added.
# claim fields: kind capacity|output|shipments|output_cumulative|output_rate|share|qualitative
#               basis built|reported|construction|announced|planned|target|historic|cancelled
#               chem  LFP|LMFP|L(M)FP-unsplit|cathode-unsplit|FePO4|not-LFP
C = lambda **kw: dict(**kw)

OVERLAY = {
 1: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Changsha", "Hunan (province from company name; site not stated)", "region-only")],
    claims=[
      C(kind="shipments", value_ty=700000, as_of="2024", basis="reported", scope="company", chem="LFP",
        note="~700 kt shipped 2024; 28.8% global share; rank #1"),
      C(kind="shipments", value_ty=1000000, as_of="2025", basis="reported", scope="company", chem="LFP",
        note=">1 Mt shipped 2025 — stated as a floor ('>'); not a nameplate figure"),
      C(kind="capacity", value_ty=50000, as_of="", basis="announced", scope="site", chem="LFP",
        site_key="", note="Spain plant, 50 ktpa, from the cited source's own title; Malaysia plant also announced (no figure)"),
    ],
    links=[("CATL","q","chief supplier; CATL held ~7% stake"), ("BYD","q","chief supplier")]),
 2: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Wuhan", "Hubei (province from company name; site not stated)", "region-only")],
    claims=[C(kind="shipments", value_ty=375000, as_of="2025", basis="reported", scope="company", chem="LFP",
        note="~375 kt 2025 rank #2 (rank #3 in 2024); ranking figure, seed source is the company site")]),
 3: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Shenzhen", "Shenzhen (city from company name)", "city-centroid")],
    claims=[
      C(kind="capacity", value_ty=345000, as_of="2025", basis="reported", scope="company", chem="LFP",
        note="LFP ~345 kt by 2025 (SELPS liquid-phase route)"),
      C(kind="capacity", value_ty=110000, as_of="2022", basis="built", scope="site", chem="LMFP",
        note="Qujing plant — world-first >100 kt LMFP plant (2022)"),
    ],
    links=[("CATL","n","2021 JV with CATL for captive LFP (stated on CATL row)")]),
 4: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Changzhou", "Changzhou (city from subsidiary name Changzhou Liyuan)", "city-centroid")],
    claims=[
      C(kind="capacity", value_ty=310000, as_of="", basis="reported", scope="company", chem="LFP", note="~310 kt; Top-5; acquired BTR's LFP business"),
      C(kind="capacity", value_ty=600000, as_of="", basis="target", scope="company", chem="LFP", note="company target; supersedes nothing — expansion goal"),
      C(kind="qualitative", value_ty=None, as_of="", basis="announced", scope="site", chem="LFP", note="Indonesia plant — first Chinese LFP-CAM maker to build overseas; no figure in seed"),
    ]),
 5: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Guiyang", "Guizhou (province from company name)", "region-only")],
    claims=[C(kind="capacity", value_ty=150000, as_of="", basis="reported", scope="company", chem="LFP", bundle=True,
        note="~150 kt LFP + iron-phosphate — BUNDLE (precursor lines inside); upper band only")],
    links=[("BYD","q","client"), ("CATL","q","client"), ("CALB","q","client")]),
 6: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Nanchang", "Jiangxi (province from subsidiary name Jiangxi Shenghua)", "region-only")],
    claims=[
      C(kind="capacity", value_ty=300000, as_of="", basis="reported", scope="company", chem="LFP", note="~300 kt (high-tap-density LFP); seed source is a build announcement"),
      C(kind="output", value_ty=128000, as_of="2024", basis="reported", scope="company", chem="LFP", note="128 kt produced 2024"),
    ],
    links=[("CATL","q","CATL-backed — raising stake toward 51%")]),
 7: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[C(kind="capacity", value_ty=100000, as_of="", basis="reported", scope="company", chem="LFP",
        note="~100–145 kt — range; LOWER bound recorded; rank 10th 2024")],
    links=[("Reliance New Energy","n","Reliance-India JV")]),
 8: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Beijing", "Beijing (from Peking University origin, stated est. 1999)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2024", basis="reported", scope="company", chem="LFP",
        note="Entered top-10 in 2024; early LFP maker (est. 1999); no figure in seed")],
    links=[("CATL","q","client"), ("ATL","q","client"), ("Prayon","lic","Prayon JV; Nano One JDA")]),
 9: dict(sg="announced", stage="CAM", region="China", chem="L(M)FP-unsplit",
    sites=[site("Beijing", "Beijing (city from company name)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=300000, as_of="", basis="announced", scope="company", chem="L(M)FP-unsplit",
        note="300 kt L(M)FP JV with Sichuan Shudao — announced; a 'first-four' LMFP investor")]),
 10: dict(sg="operating", stage="CAM", region="China", chem="LMFP",
    sites=[site("Chungju", "Korea plant (city geocode carried from NMC Atlas: Chungju)", "city-centroid"),
           site("Ningbo", "Ningbo HQ (geocode carried from NMC Atlas)", "hq-city", primary=False)],
    claims=[
      C(kind="capacity", value_ty=20000, as_of="", basis="reported", scope="site", chem="LMFP", note="Korea plant, 20 kt LMFP"),
      C(kind="share", value_ty=None, as_of="2025-H1", basis="reported", scope="company", chem="LMFP",
        note="LMFP co-leader — ~80% of H1-2025 LMFP shipments jointly with Hengchuang; no absolute base disclosed"),
    ]),
 11: dict(sg="announced", stage="CAM", region="China", chem="L(M)FP-unsplit",
    sites=[site("Ya'an", "Ya'an (stated project site)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=80000, as_of="", basis="planned", scope="site", chem="L(M)FP-unsplit",
        note="Ya'an LFP/LMFP project ~80 kt planned")]),
 12: dict(sg="operating", stage="cell-maker CAM", region="China", chem="LFP",
    sites=[site("Hefei", "Hefei / Lujiang (stated)", "city-centroid")],
    claims=[
      C(kind="capacity", value_ty=50000, as_of="", basis="built", scope="company", chem="LFP", note="own CAM 50 kt (Hefei/Lujiang); in-house since 2007"),
      C(kind="capacity", value_ty=200000, as_of="", basis="target", scope="company", chem="LFP", note="expansion target 200 kt; LMFP in Astroinno L600"),
    ]),
 13: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Chongqing", "Chongqing (city from company name)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=60000, as_of="", basis="reported", scope="company", chem="LFP", note="~60 kt (48 lines); top-10")],
    links=[("CATL","q","supplier since 2021")]),
 14: dict(sg="announced", stage="CAM", region="China", chem="LFP",
    sites=[site("Jinan", "Shandong (stated; 100 kt project)", "region-only"),
           site("Chengdu", "Sichuan (stated; +120 kt project)", "region-only", primary=False)],
    claims=[
      C(kind="capacity", value_ty=120000, as_of="", basis="announced", scope="site", chem="LFP", site_key="chengdu", note="Sichuan +120 kt"),
      C(kind="capacity", value_ty=100000, as_of="", basis="announced", scope="site", chem="LFP", site_key="jinan", target_date="2026", note="Shandong 100 kt (~2026); IBU-tec Europe JV"),
    ]),
 15: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[C(kind="capacity", value_ty=200000, as_of="2022", basis="built", scope="company", chem="LFP",
        note="~200 kt added 2022; TiO2 by-product (ferrous sulfate) integrated")]),
 16: dict(sg="announced", stage="CAM", region="China", chem="LFP",
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[C(kind="capacity", value_ty=500000, as_of="", basis="planned", scope="company", chem="LFP",
        note="500 kt planned in 3 phases (~$1.9 B); acquired Zhaoqing Helin Liye")]),
 17: dict(sg="announced", stage="CAM", region="China", chem="LMFP",
    sites=[site("Yinchuan", "Ningxia (stated planned site)", "region-only")],
    claims=[
      C(kind="capacity", value_ty=130000, as_of="", basis="planned", scope="site", chem="LMFP", note="130 kt planned (Ningxia); bought Dow's LMFP patents"),
      C(kind="share", value_ty=None, as_of="2025-H1", basis="reported", scope="company", chem="LMFP",
        note="LMFP co-leader ~80% H1-2025 jointly with Ronbay; new entrant 2022"),
    ]),
 18: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("ChinaCentroid", "China (Huayou Cobalt subsidiary; site not stated)", "country-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2024", basis="reported", scope="company", chem="LFP",
        note="EVTank 2024 top-10; no figure in seed")],
    links=[("LG Chem","q","supplies LG Chem's Morocco LFP JV")]),
 19: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Changsha", "Hunan (province from company name)", "region-only")],
    claims=[C(kind="capacity", value_ty=20000, as_of="2023", basis="built", scope="company", chem="LFP",
        note="LFP line since 2023, ~20–30 kt initial — LOWER bound recorded; ternary 120 kt excluded (not LFP)")]),
 20: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Kunming", "Yunnan (province from company name)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="LFP",
        note="Lists LiFePO4 CAM (CAS 15365-14-7) as a product; phosphate-rock integrated; no figure")]),
 21: dict(sg="operating", stage="CAM", region="China", chem="LFP",
    sites=[site("Yantai", "Yantai (city from company name)", "city-centroid")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="LFP",
        note="Cost-focused ESS/grid LFP; cited in peer-reviewed review; no figure")]),
 22: dict(sg="dead", stage="CAM", region="China", chem="LFP", dead_cause="exit",
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2022", basis="historic", scope="company", chem="LFP",
        note="Sold Tianjin & Jiangsu LFP business to Lopal (2022); now #1 anode maker")]),
 23: dict(sg="context", stage="not-LFP", region="China", chem="not-LFP",
    sites=[site("Ningbo", "Ningbo (city from company name)", "city-centroid")],
    claims=[]),
 24: dict(sg="precursor", stage="precursor-only", region="China", chem="FePO4",
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[C(kind="capacity", value_ty=200000, as_of="", basis="reported", scope="company", chem="FePO4",
        note="iron-phosphate precursor ~200 kt; finished LFP CAM only in customer qualification")]),
 25: dict(sg="precursor", stage="precursor-only", region="China", chem="FePO4",
    sites=[site("Guiyang", "Guizhou (province from company name)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="FePO4",
        note="iron-phosphate precursor (CATL JV); no figure")]),
 26: dict(sg="precursor", stage="precursor-only", region="China", chem="FePO4",
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="FePO4",
        note="iron-phosphate precursor (EVE, Gotion, SVOLT deals); no figure")]),
 27: dict(sg="context", stage="cell-maker (buys)", region="China", chem="LFP", no_marker=True,
    sites=[site("Ningde", "Ningde (city from company name)", "city-centroid")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2021", basis="reported", scope="company", chem="LFP",
        note="World's largest LFP cell maker; buys chiefly from Yuneng & Dynanonic; 2021 captive-LFP JV with Dynanonic")]),
 28: dict(sg="operating", stage="cell-maker CAM", region="China", chem="LFP",
    sites=[site("Shenzhen", "Shenzhen (HQ; widely documented, not stated in seed)", "hq-city")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="LFP",
        note="FinDreams units make LFP in-house for Blade batteries; no figure disclosed")]),
 29: dict(sg="context", stage="cell-maker (JV)", region="China", chem="cathode-unsplit", no_marker=True,
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[C(kind="capacity", value_ty=100000, as_of="", basis="reported", scope="company", chem="cathode-unsplit", bundle=True,
        counted=False, count_reason="JV attribution (Hunan Zhongke) and chemistry unsplit — reference only",
        note="JV w/ Hunan Zhongke for cathode ~100 kt; largely buys")]),
 30: dict(sg="context", stage="cell-maker (buys)", region="China", chem="not-LFP", no_marker=True,
    sites=[site("ChinaCentroid", "China (site not stated in seed)", "country-only")],
    claims=[]),
 31: dict(sg="operating", stage="CAM + licensor", region="Taiwan", chem="LFP",
    sites=[site("TaiwanCentroid", "Taiwan (site not stated in seed)", "region-only")],
    claims=[C(kind="output_cumulative", value_ty=None, value_native="~30 kt cumulative", as_of="", basis="reported",
        scope="company", chem="LFP", note="~30 kt CUMULATIVE shipped — not a t/y rate; never enters totals")],
    links=[("ICL Group","x","license discontinued Nov 2025"), ("FREYR / T1 Energy","lic","process licensee"),
           ("Avenira","lic","process licensee")]),
 32: dict(sg="operating", stage="CAM", region="Taiwan", chem="LFP",
    sites=[site("TaiwanCentroid", "Taiwan (site not stated in seed)", "region-only")],
    claims=[C(kind="capacity", value_ty=4800, as_of="", basis="reported", scope="company", chem="LFP",
        note="~4,800 t/y; JV of Formosa Plastics + Changs Ascending")],
    links=[("Gotion High-tech","q","customer incl. Gotion")]),
 33: dict(sg="operating", stage="CAM + licensor", region="Taiwan", chem="LFP",
    sites=[site("TaiwanCentroid", "Taiwan (site not stated in seed)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2001", basis="reported", scope="company", chem="LFP",
        note="First LFP maker in Taiwan (2001); niche ESS/UPS; licenses tech to FEMTC")],
    links=[("Formosa Lithium Iron Oxide (FEMTC)","lic","licenses tech to FEMTC")]),
 34: dict(sg="uncertain", stage="CAM", region="Taiwan", chem="LFP",
    sites=[site("TaiwanCentroid", "Taiwan (site not stated in seed)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2012", basis="historic", scope="company", chem="LFP",
        note="Entered Japan ESS market 2012; LiFePO4+C license terminated 2017; low-profile since")]),
 35: dict(sg="dead", stage="CAM", region="Japan", chem="LFP", dead_cause="exit",
    sites=[site("JapanCentroid", "Japan (site not stated in seed)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2022", basis="historic", scope="company", chem="LFP",
        note="EXITED — LFP business + Vietnam plant transferred to SMM (Feb/May 2022); carbon-coating pioneer")]),
 36: dict(sg="uncertain", stage="CAM", region="Japan", chem="LFP",
    sites=[site("Tokyo", "Tokyo (HQ; plant not stated)", "hq-city")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2022", basis="reported", scope="company", chem="LFP",
        note="Holds ex-SOC LFP business; large-scale commercial production not confirmed; R&D with Nano One")],
    links=[("Nano One Materials","n","R&D partnership")]),
 37: dict(sg="operating", stage="CAM", region="Japan", chem="LFP",
    sites=[site("JapanCentroid", "Japan (site not stated in seed)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="LFP",
        note="LiFePO4 is a listed catalog cathode ('original synthetic process'); scale small")]),
 38: dict(sg="precursor", stage="precursor-only", region="Japan", chem="FePO4",
    sites=[site("JapanCentroid", "Japan (site not stated in seed)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="FePO4",
        note="Sells iron-oxide precursor for LFP, not finished CAM")]),
 39: dict(sg="announced", stage="CAM", region="Japan", chem="LMFP",
    sites=[site("JapanCentroid", "Japan (site not stated in seed)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2025", basis="announced", scope="company", chem="LMFP",
        note="Proprietary hydrothermal 'Nanolitia' LMFP; targeted mass production 2025 — start not confirmed; no figure")]),
 40: dict(sg="dead", stage="CAM", region="Japan", chem="LFP", dead_cause="exit",
    sites=[site("JapanCentroid", "Japan (site not stated in seed)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="historic", scope="company", chem="LFP",
        note="Historical LiFePO4+C license holder; not a current producer")]),
 41: dict(sg="building", stage="CAM", region="South Korea", chem="LFP",
    sites=[site("Daegu", "Daegu (stated)", "city-centroid")],
    claims=[
      C(kind="capacity", value_ty=30000, as_of="", basis="construction", scope="site", chem="LFP",
        target_date="2026-Q4", note="Daegu 30 kt; mass production ~Q4 2026 (Korea's first/only mass producer)"),
      C(kind="capacity", value_ty=60000, as_of="", basis="target", scope="site", chem="LFP",
        target_date="2027", note="Daegu expansion 30 → 60 kt (2027)"),
      C(kind="qualitative", value_ty=None, as_of="", basis="announced", scope="company", chem="LFP",
        note="US plant with Mitra Chem — MP 2028; no figure in seed"),
    ],
    links=[("Samsung SDI","q","1.6T KRW LFP deal"), ("SK On","q","supply MOU"), ("Mitra Chem","n","US plant partnership")]),
 42: dict(sg="announced", stage="CAM", region="South Korea", chem="LFP",
    sites=[site("Pohang", "Pohang (stated)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=50000, as_of="", basis="announced", scope="site", chem="LFP",
        target_date="2027", note="JV w/ CNGR + FINO — Pohang UP TO 50 kt, MP 2027 (ceiling, not committed nameplate)")]),
 43: dict(sg="announced", stage="CAM", region="South Korea", chem="LFP",
    sites=[site("Seoul", "Seoul (HQ; LFP project site is Morocco — see Morocco cluster row)", "hq-city")],
    claims=[C(kind="capacity", value_ty=50000, as_of="", basis="announced", scope="site", chem="LFP",
        duplicate_of="p065.c1", target_date="2026",
        note="Morocco 50 kt with Youshan/Huayou, MP target 2026 — SAME project as the Morocco-cluster row; counts once there")]),
 44: dict(sg="pilot", stage="CAM", region="South Korea", chem="LFP", scale="pilot",
    sites=[site("KoreaCentroid", "South Korea (site not stated in seed)", "region-only")],
    claims=[C(kind="capacity", value_ty=3000, as_of="2025", basis="built", scope="site", chem="LFP",
        note="pilot line ~3 kt; samples from Q2 2025; precursor-free direct-synthesis R&D (with Hyundai/Kia/Hyundai Steel)")]),
 45: dict(sg="pilot", stage="CAM", region="North America", chem="LFP", scale="pilot",
    sites=[site("Candiac", "Candiac, QC (stated; ex-Johnson Matthey plant)", "city-centroid")],
    claims=[
      C(kind="capacity", value_ty=2400, as_of="", basis="built", scope="site", chem="LFP",
        note="site nameplate ~2,400 tpa (ex-JM Candiac); operated by Nano One"),
      C(kind="output_rate", value_ty=None, value_native="~200 tpa current pilot", as_of="", basis="reported", scope="site", chem="LFP",
        note="current pilot production ~200 tpa"),
      C(kind="capacity", value_ty=800, as_of="", basis="target", scope="site", chem="LFP",
        target_date="2027-H1", note="demo target ~800 tpa H1-2027"),
    ]),
 46: dict(sg="announced", stage="CAM", region="North America", chem="LFP",
    sites=[site("MountainView", "Mountain View, CA (stated)", "city-centroid"),
           site("Muskegon", "Muskegon, MI (stated planned plant)", "city-centroid", primary=False)],
    claims=[C(kind="capacity", value_ty=15000, as_of="", basis="planned", scope="site", chem="LFP", site_key="muskegon",
        note="planned MI plant ~15,000 → 30,000 tpa ($125M DOE+Michigan); multi-ton samples produced; LMFP too")]),
 47: dict(sg="building", stage="CAM", region="North America", chem="LFP",
    sites=[site("JacksonTN", "Jackson, TN (stated)", "city-centroid")],
    claims=[
      C(kind="capacity", value_ty=400, as_of="", basis="built", scope="site", chem="LFP", scale="pilot",
        note="R&D line ~400 tpa (pilot producing)"),
      C(kind="capacity", value_ty=13000, as_of="", basis="construction", scope="site", chem="LFP",
        note="'PlusCAM' 13,000 tpa under construction ($50M DOE); UniMelt microwave-plasma — also NMC"),
    ]),
 48: dict(sg="pilot", stage="CAM", region="North America", chem="LFP", scale="pilot",
    sites=[site("Saguenay", "Saguenay, QC (stated)", "city-centroid")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2025", basis="reported", scope="company", chem="LFP",
        note="pilot; produced LFP CAM & cells from North American minerals (2025); commercial ~2027; integrated from igneous phosphate")]),
 49: dict(sg="announced", stage="CAM", region="North America", chem="LFP",
    sites=[site("SanDiego", "San Diego (stated)", "city-centroid"),
           site("HooksTX", "Hooks, TX (stated planned JV plant)", "city-centroid", primary=False)],
    claims=[
      C(kind="output_cumulative", value_ty=None, value_native="1 metric ton produced w/ offtakes", as_of="", basis="reported", scope="company", chem="LFP",
        note="produced 1 MT (metric ton) LFP with offtakes — cumulative, not t/y"),
      C(kind="capacity", value_ty=15000, as_of="2026-06", basis="announced", scope="site", chem="LFP", site_key="hookstx",
        note="15,000 tpa TX plant (JV w/ EnergyX) announced Jun 2026"),
    ]),
 50: dict(sg="dead", stage="CAM", region="North America", chem="LFP", dead_cause="cancellation",
    sites=[site("StLouis", "St. Louis, MO (stated)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=30000, as_of="", basis="cancelled", scope="site", chem="LFP",
        note="was $400M / 30,000 tpa (licensed Aleees process); DISCONTINUED Nov 2025 after DOE pulled $197M; Spain JV w/ Dynanonic also killed")]),
 51: dict(sg="context", stage="not-LFP", region="North America", chem="not-LFP", no_marker=True,
    sites=[site("Clarksville", "Clarksville, TN (stated)", "city-centroid")],
    claims=[]),
 52: dict(sg="dead", stage="CAM", region="North America", chem="LFP", dead_cause="exit",
    sites=[site("USACentroid", "USA/China (defunct in West; site not stated)", "country-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2022", basis="historic", scope="company", chem="LFP",
        note="successor to A123 industrial + Valence ('Nanophosphate' carbothermal); assets sold to Reliance (2022); no current Western CAM")]),
 53: dict(sg="operating", stage="CAM", region="Europe", chem="LFP",
    sites=[site("Weimar", "Weimar (stated)", "city-centroid"),
           site("Bitterfeld", "Bitterfeld-Wolfen (stated; under construction)", "city-centroid", primary=False)],
    claims=[
      C(kind="capacity", value_ty=3000, as_of="", basis="built", scope="site", chem="LFP",
        note="Weimar >3,000 tpa producing now — '>' floor; proprietary spray-calcination / rotary kiln, 'no Chinese tech'"),
      C(kind="capacity", value_ty=15000, as_of="", basis="construction", scope="site", chem="LFP", site_key="bitterfeld",
        target_date="2028", note="Bitterfeld 15,000 tpa (PowerCo 10-yr offtake), operations ~2028"),
    ],
    links=[("PowerCo","q","10-year offtake (Bitterfeld)")]),
 54: dict(sg="pilot", stage="CAM", region="Europe", chem="LMFP", scale="pilot",
    sites=[site("MiltonKeynes", "Milton Keynes (stated)", "city-centroid")],
    claims=[
      C(kind="capacity", value_ty=20, as_of="", basis="built", scope="site", chem="LFP", scale="pilot", note="pilot 20 tpa producing"),
      C(kind="capacity", value_ty=100, as_of="", basis="target", scope="site", chem="LFP", note="scaling to 100 tpa demo"),
      C(kind="capacity", value_ty=1000, as_of="", basis="target", scope="site", chem="LFP", note="engineering for 1,000 tpa (DRIVE35); LMFP high-Mn ~80%"),
    ]),
 55: dict(sg="pilot", stage="CAM", region="Europe", chem="LFP", scale="pilot",
    sites=[site("Moosburg", "Moosburg (stated; ex-JM tech centre)", "city-centroid")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2024", basis="reported", scope="site", chem="LFP",
        note="Germany pilot/qualification line (hydrothermal); bought from Johnson Matthey 2024")]),
 56: dict(sg="uncertain", stage="CAM", region="Europe", chem="LFP",
    sites=[site("Weimar", "Weimar (stated; toll-made by IBU-tec)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=3000, as_of="2014", basis="built", scope="site", chem="LFP",
        counted=False, count_reason="status 'Historical / limited' — current output unclear; not confirmed operating",
        note="~3,000 tpa Weimar plant launched 2014 (licensed LiFePO4+C); strategic focus moved to NCM")]),
 57: dict(sg="operating", stage="CAM", region="Europe", chem="LFP",
    sites=[site("Engis", "Engis (stated)", "city-centroid")],
    claims=[C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="company", chem="LFP",
        note="small production, JV-based (sublicensed process; JV w/ Pulead); scale uncertain")]),
 58: dict(sg="dead", stage="CAM", region="Europe", chem="LFP", dead_cause="exit",
    sites=[site("UKCentroid", "UK/Canada/Germany (exited)", "region-only")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2021", basis="historic", scope="company", chem="LFP",
        note="EXITED battery materials (Nov 2021); ran solid-state + hydrothermal at Candiac; Candiac → Nano One, Moosburg → Epsilon")]),
 59: dict(sg="announced", stage="CAM", region="India", chem="LFP",
    sites=[site("Bengaluru", "Karnataka (stated region)", "region-only")],
    claims=[
      C(kind="capacity", value_ty=30000, as_of="", basis="planned", scope="site", chem="LFP",
        target_date="2027", note="India plant planned 30,000 tpa by 2027"),
      C(kind="capacity", value_ty=100000, as_of="", basis="target", scope="site", chem="LFP",
        target_date="2030", note="→ 100,000 tpa by 2030"),
    ]),
 60: dict(sg="pilot", stage="CAM", region="India", chem="LFP", scale="pilot",
    sites=[site("Hyderabad", "Hyderabad; Divitipalli, Telangana (stated)", "city-centroid")],
    claims=[
      C(kind="output_rate", value_ty=None, value_native="~100 kg/day pilot", as_of="", basis="reported", scope="site", chem="LFP",
        note="pilot ~100 kg/day producing (ARCI collaboration) — rate kept in native units, never converted"),
      C(kind="capacity", value_ty=20000, as_of="", basis="announced", scope="site", chem="LFP",
        note="giga-factory 20,000+ tpa announced — '+' floor"),
    ]),
 61: dict(sg="announced", stage="CAM", region="India", chem="LFP",
    sites=[site("Jamnagar", "Jamnagar (stated)", "city-centroid")],
    claims=[C(kind="qualitative", value_ty=None, as_of="2022", basis="announced", scope="company", chem="LFP",
        note="bought Lithium Werks assets (2022): 219 LFP patents + China plant; own merchant CAM output not yet confirmed")]),
 62: dict(sg="pilot", stage="CAM", region="Australia", chem="LFP", scale="pilot",
    sites=[site("Brisbane", "Brisbane (stated)", "city-centroid")],
    claims=[
      C(kind="qualitative", value_ty=None, as_of="", basis="reported", scope="site", chem="LFP", note="pilot producing (proprietary hybrid solid-state + solution)"),
      C(kind="capacity", value_ty=250, as_of="", basis="announced", scope="site", chem="LFP", note="250 tpa demo plant ($30M ARENA grant)"),
    ]),
 63: dict(sg="announced", stage="CAM", region="Australia", chem="LFP",
    sites=[site("Darwin", "Darwin, NT (stated)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=10000, as_of="", basis="announced", scope="site", chem="LFP",
        note="Phase 1 ~10,000 tpa (→ 30k → 100k later phases, not counted); licensed Aleees process; integrated w/ Wonarah phosphate; timelines extended")]),
 64: dict(sg="dead", stage="CAM", region="Europe", chem="LFP", dead_cause="cancellation",
    sites=[site("Vaasa", "Vaasa, Finland (stated planned site)", "city-centroid")],
    claims=[C(kind="capacity", value_ty=30000, as_of="", basis="announced", scope="site", chem="LFP",
        counted=False, count_reason="company pivoted to solar Feb 2025 (US Georgia plant abandoned); Finland project status unclear — greyed, counts nothing",
        note="Finland CAM 30,000 tpa (EUR 122M EU grant); licensed Aleees process")]),
 65: dict(sg="building", stage="CAM", region="Morocco", chem="LFP",
    sites=[site("MoroccoCentroid", "Morocco (cluster; specific sites not stated in seed)", "country-only")],
    claims=[
      C(kind="capacity", value_ty=50000, as_of="", basis="construction", scope="site", chem="LFP",
        target_date="2026", note="LG Chem–Youshan/Huayou JV ~50,000 tpa by 2026 (the figure counts HERE; LG Chem row cross-references it)"),
      C(kind="qualitative", value_ty=None, as_of="", basis="announced", scope="site", chem="LFP",
        note="BTR & others; >$700M pledged across the cluster — no per-plant figures in seed"),
    ]),
}

# customers / non-plant nodes that receive links
CUSTOMERS = [
  {"name": "CATL",        "country": "China",       "key": "Ningde"},
  {"name": "BYD",         "country": "China",       "key": "Shenzhen"},
  {"name": "CALB",        "country": "China",       "key": "ChinaCentroid"},
  {"name": "ATL",         "country": "China",       "key": "Ningde"},
  {"name": "LG Chem",     "country": "South Korea", "key": "Seoul"},
  {"name": "PowerCo",     "country": "Germany",     "key": "Salzgitter"},
  {"name": "Samsung SDI", "country": "South Korea", "key": "Yongin"},
  {"name": "SK On",       "country": "South Korea", "key": "Seoul"},
  {"name": "Gotion High-tech", "country": "China",  "key": "Hefei"},
  {"name": "Prayon",      "country": "Belgium",     "key": "Engis"},
  {"name": "Reliance New Energy", "country": "India", "key": "Jamnagar"},
  {"name": "Mitra Chem",  "country": "USA",         "key": "MountainView"},
  {"name": "Nano One Materials", "country": "Canada", "key": "Candiac"},
  {"name": "ICL Group",   "country": "USA",         "key": "StLouis"},
  {"name": "FREYR / T1 Energy", "country": "Finland", "key": "Vaasa"},
  {"name": "Avenira",     "country": "Australia",   "key": "Darwin"},
  {"name": "Formosa Lithium Iron Oxide (FEMTC)", "country": "Taiwan", "key": "TaiwanCentroid"},
]

# method id by Excel row -> plants' method_ids (route mapping, from the sheet's own producer lists + row method text)
FAMILY_OF_ROW = {}   # filled while parsing methods

print("Parsing methods…")
METHODS, FAMILIES, PATENTS, REFERENCES = [], [], [], []
SCALE_GROUP = {"FFC6EFCE": "commercial", "FFFFEB9C": "pilot", "FFDDEBF7": "lab"}
for r in cells("Synthesis Methods"):
    n = txt(r, "A")
    if not n.isdigit(): continue
    mid = "m%02d" % int(n)
    fam = txt(r, "C")[:1]
    FAMILY_OF_ROW[int(n)] = fam
    METHODS.append({
        "id": mid, "n": int(n), "name": txt(r, "B"), "family": fam,
        "applies": txt(r, "D"), "scale_today": txt(r, "E"),
        "scale_group": SCALE_GROUP.get(fill(r, "E"), "lab"),
        "how": txt(r, "F"), "adv": txt(r, "G"), "dis": txt(r, "H"),
        "producers_text": txt(r, "I"), "ref": txt(r, "J"),
        "src": src_id(link(r, "K"), txt(r, "J")), "conf": txt(r, "L"),
    })
for r in cells("Big Categories"):
    a = txt(r, "A")
    if a not in list("ABCDE"): continue
    FAMILIES.append({"id": a, "name": txt(r, "B"), "defines": txt(r, "C"),
                     "includes": txt(r, "D"), "relevance": txt(r, "E"), "nmc_analogy": txt(r, "F")})

# patent timeline; y0/y1 hand-parsed from the date labels (label kept verbatim)
PATENT_YEARS = {1:(1996,1997),2:(1997,1997.6),3:(1999,2001),4:(2001,2008),5:(2001,2003),6:(2005,2005.6),
                7:(2011.5,2011.9),8:(2011,2011.6),9:(2011.75,2012.1),10:(2012.4,2012.7),11:(2012,2012.6),
                12:(2012.8,2013.1),13:(2014,2015),14:(2018,2018.6),15:(2021.85,2022.4),16:(2022.2,2022.7),
                17:(2022.9,2023.2),18:(2024.1,2024.6)}
for r in cells("Patent & Licensing"):
    n = txt(r, "A")
    if not n.isdigit(): continue
    i = int(n)
    y0, y1 = PATENT_YEARS[i]
    PATENTS.append({"id": "e%02d" % i, "date_label": txt(r, "B"), "y0": y0, "y1": y1,
                    "event": txt(r, "C"), "entities": txt(r, "D"),
                    "src": src_id(link(r, "E"), txt(r, "C")[:80])})
for r in cells("Key References"):
    n = txt(r, "A")
    if not n.isdigit(): continue
    REFERENCES.append({"id": "r%02d" % int(n), "type": txt(r, "B"), "citation": txt(r, "C"),
                       "link_label": txt(r, "D"), "src": src_id(link(r, "D"), txt(r, "C")[:90])})

# route family of each plant from its method text (explicit mapping; "" = not disclosed)
ROUTE_FAMILY = {
 1:"A",2:"A",3:"C",4:"A",5:"A",6:"A",7:"A",12:"A",14:"A",15:"C",16:"C",17:"E",20:"C",
 28:"A",31:"C",33:"E",34:"A",35:"A",36:"A",38:"C",39:"C",41:"",42:"",43:"",44:"E",
 45:"E",46:"C",47:"E",48:"",49:"E",50:"A",52:"A",53:"D",54:"E",55:"C",56:"A",57:"A",
 58:"A",59:"C",60:"A",61:"A",62:"E",63:"A",64:"A",65:"",
}
FAMILY_NAMES = {"A": "A. Solid-State (dry)", "B": "B. Melt / Molten-State",
                "C": "C. Wet-Chemistry / Solution", "D": "D. Aerosol / Spray",
                "E": "E. Novel / Hybrid", "": "not disclosed"}

print("Parsing producers…")
PLANTS = []
current_section = ""
for r in cells("CAM Producers"):
    a = txt(r, "A")
    if a and not a.isdigit() and txt(r, "B") == "":
        current_section = a
        continue
    if not a.isdigit(): continue
    n = int(a)
    ov = OVERLAY[n]
    company = txt(r, "B")
    surl = link(r, "I")
    sid = src_id(surl, company + " — seed row source")
    claims = []
    for j, c in enumerate(ov.get("claims", [])):
        cc = dict(c)
        cc["id"] = "p%03d.c%d" % (n, j + 1)
        cc.setdefault("product", "FePO4" if cc.get("chem") == "FePO4" else "CAM")
        cc.setdefault("src", sid)
        cc.setdefault("value_native", None)
        cc.setdefault("bundle", False)
        cc.setdefault("duplicate_of", None)
        cc.setdefault("target_date", None)
        cc.setdefault("site_key", None)
        cc.setdefault("scale", ov.get("scale", "commercial"))
        cc.setdefault("counted", None)          # resolved by the build
        cc.setdefault("count_reason", "")
        cc["seed_row_source"] = True            # row-level source inherited; figure-level pending
        claims.append(cc)
    PLANTS.append({
        "id": "p%03d" % n, "n": n, "company": company, "country": txt(r, "C"),
        "region": ov["region"], "section": current_section,
        "makes": txt(r, "D"), "method": txt(r, "E"),
        "route_family": FAMILY_NAMES[ROUTE_FAMILY.get(n, "")],
        "stage": ov["stage"], "chem_focus": ov["chem"],
        "status_raw": txt(r, "G"), "sgroup": ov["sg"],
        "dead_cause": ov.get("dead_cause"), "scale": ov.get("scale", "commercial"),
        "capacity_text": txt(r, "F"), "notes": txt(r, "H"), "conf": txt(r, "J"),
        "src": sid, "claims": claims, "sites": ov["sites"],
        "no_marker": ov.get("no_marker", False),
        "links": [{"to": t, "k": k, "note": note} for (t, k, note) in ov.get("links", [])],
    })

# read-me key findings + market context (verbatim from the workbook)
READ = {c_coord: v for row in cells("Read Me") for c_coord, v in row.items()}
key_findings = [str(READ[k]["v"]).strip() for k in ["C11","C12","C13","C14","C15","C16"] if k in READ]
legend = {"C19": "operating", "C20": "building/announced/pilot", "C21": "lab", "C22": "dead/precursor/not-CAM"}

CANON = {
  "schema": 1,
  "chemistry": "LFP/LMFP",
  "meta": {
    "name": "LFP Atlas",
    "version": VERSION,
    "dataset_date": DATASET_DATE,
    "seed_compiled": SEED_COMPILED,
    "as_of": "27 July 2026",
    "generated": DATASET_DATE,
    "plants": len(PLANTS),
    "seed": "LFP_LMFP_Synthesis_Methods_and_Producers.xlsx (compiled 19 Jul 2026)",
    "cite": "LFP Atlas v%s — global LFP/LMFP cathode synthesis-route and producer census. CC-BY 4.0, attribution 'LFP Atlas' + version. Companion to NMC Atlas; both fold into Cathodes ATLAS." % VERSION,
    "license": "CC-BY 4.0",
    "key_findings": key_findings,
    "market_context": {
      "china_share": "~95–98%",
      "note": "China makes ~95–98% of global LFP CAM (seed workbook key finding; backbone reviews cited on the References pane). 2024 leader Hunan Yuneng ~28.8% share; 2025 Yuneng shipments >1 Mt.",
      "dominant_route": "High-temperature solid-state CARBOTHERMAL REDUCTION fed by a precipitated FePO4 precursor — ~90% of global LFP tonnage (seed workbook; Big Categories sheet).",
    },
    "counting_rule": ("The olivine rule, seed edition (v0.1): a figure enters the operating bands only if the plant is operating at commercial scale, "
        "the claim is a CAPACITY (not shipments, output, cumulative or a rate), its basis is built/reported, it is not a bundle "
        "(no precursor or mixed-cathode tonnage inside), and it is not a duplicate of another row's project. "
        "Lower = chemistry stated outright (LFP or LMFP). Headline = lower + L(M)FP-unsplit. Upper = headline + bundles and unsplit-cathode figures. "
        "Announced / under-construction capacity is a separate PIPELINE total (basis announced/planned/construction; targets excluded) and is never mixed into operating bands. "
        "Shipments and output figures are shown as market context only."),
  },
  "sources": sorted(SOURCES.values(), key=lambda s: s["id"]),
  "plants": PLANTS,
  "customers": [{"name": c["name"], "country": c["country"],
                 "lat": GEO[c["key"]][0], "lon": GEO[c["key"]][1]} for c in CUSTOMERS],
  "methods": METHODS,
  "families": FAMILIES,
  "patent_events": PATENTS,
  "references": REFERENCES,
  "status_legend": legend,
  "gap_log": [
    {"id": "g01", "gap": "World #1 producer (Hunan Yuneng) carries no nameplate-capacity figure in the seed — shipments only. The operating bands therefore UNDERSTATE China badly; treat them as a documented floor, not an estimate of the market."},
    {"id": "g02", "gap": "Claims inherit ROW-level seed sources (one source per producer row). Figure-level re-sourcing to the NMC standard (filings/registries, two sources for top tonnage, SHA-256 snapshots) is the v0.2 work programme."},
    {"id": "g03", "gap": "Most claims carry no as-of vintage; vintages exist only where the seed text states one."},
    {"id": "g04", "gap": "No source snapshot archive yet (NMC archive_sources.py port pending); hash fields are null."},
    {"id": "g05", "gap": "Chinese plant locations are province- or country-precision (from company names / stated projects only). No site-level geocoding pass yet; map dots are flagged accordingly."},
    {"id": "g06", "gap": "LMFP market shares (~80% H1-2025, Ronbay + Hengchuang jointly) are shares with no absolute base disclosed in the seed."},
    {"id": "g07", "gap": "Ranking-derived figures (Yuneng ~700 kt 2024, Wanrun ~375 kt 2025) are trade-ranking shipments, not audited filings."},
  ],
  "changelog": [
    {"version": VERSION, "date": DATASET_DATE, "changes": [
      "First seeded edition: 65 producer rows (incl. precursor-only / exited / cell-maker context rows), 28 synthesis methods in 5 families, 18 patent & licensing events, 10 backbone references — from the 19 Jul 2026 compilation workbook.",
      "Every t/y figure restructured as a discrete claim (kind, basis, scope, chemistry tag, source, note); bundles, duplicates, ranges, floors and cumulative figures flagged; nothing interpolated or unit-converted.",
      "Counting rule (seed edition) separates operating bands from the announced/construction pipeline; shipments are context only.",
      "Gaps register opened with the seven known seed weaknesses (g01–g07)."]},
  ],
}

out = os.path.join(ROOT, "canonical.json")
json.dump(CANON, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Wrote", out, "| plants:", len(PLANTS), "| sources:", len(SOURCES),
      "| methods:", len(METHODS), "| patents:", len(PATENTS))
claims_n = sum(len(p["claims"]) for p in PLANTS)
fig_n = sum(1 for p in PLANTS for c in p["claims"] if c["value_ty"] is not None)
print("claims:", claims_n, "| with t/y figure:", fig_n)
