#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upgrade_v0_3.py — v0.2.0 -> v0.3.0: second sources for trade-tier counted figures,
status corrections they surfaced (XTC Ya'an operating; Easpring Panzhihua ph-1 built),
documented-city geocoding pass (~20 rows), and the source-snapshot archiver wiring.

Same append-only discipline as v0.2: corrected figures enter as new claims; the old
claim gets superseded_by and ships visible, counting toward nothing. Every figure was
confirmed on a fetched document (research pass 28 Jul 2026, two parallel evidence agents).
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
can = json.load(open(os.path.join(ROOT, "canonical.json"), encoding="utf-8"))
assert can["meta"]["version"] == "0.2.0", "expected v0.2.0 input"

NEW_SOURCES = [
 ("s_wanrun_ir0526", "https://www.stcn.com/article/detail/4033487.html", "证券时报 (relaying the May-2026 exchange-disclosed IR record)", "company IR statement via press", "Wanrun: LFP capacity in production 468,000 t/y (May 2026 IR record)", "company", "2026-07-22"),
 ("s_wanrun_base24", "https://www.stcn.com/article/detail/1392503.html", "证券时报 (Q3-2024 results briefing)", "company statement via press", "Wanrun per-base capacity: Hubei 311k + Anhui 37k + Shandong 120k t/y", "company", "2024-10-31"),
 ("s_wanrun_hongmai","https://file.finance.qq.com/finance/hs/pdf/2026/01/17/1224938478.PDF", "SSE (QQ mirror)", "sponsor verification opinion", "Wanrun: Hongmai Gaoke 70,000 t/y high-compaction LFP project (Danjiangkou, Shiyan)", "primary", "2026-01-17"),
 ("s_wanrun_catl",   "https://www.stcn.com/article/detail/1836364.html", "证券时报", "trade press (quoting announcement)", "Wanrun–CATL supply agreement: ~1.3231 Mt LFP, 2025-05 → 2030-05", "trade", "2025-05-19"),
 ("s_xtc_ann013",    "https://static.cninfo.com.cn/finalpage/2026-04-23/1225146636.PDF", "SSE STAR / CNINFO", "exchange announcement", "XTC 2026-013: Ya'an +40,000 t/y LFMP line; total 80,000 t/y on completion (Jun 2028)", "primary", "2026-04-23"),
 ("s_xtc_ar25",      "http://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESH_STOCK/2026/2026-4/2026-04-23/12142192.PDF", "SSE (Sina mirror)", "annual report", "XTC 2025 Annual Report: Ya'an LFP ph-1 producing, ph-2 commissioning; 2025 LFP sales 22,000 t", "primary", "2026-04-23"),
 ("s_lopal_prosp",   "https://statichk.iqdii.com/stockdata/notice/02465/2024/2024102200008_c.pdf", "HKEX (iqdii mirror of the prospectus)", "IPO prospectus", "Lopal H-share prospectus: LFP designed capacity 200,670 t/y (FY2023); five China plants; global #4, 6.5% share", "primary", "2024-10-22"),
 ("s_lopal_jintan",  "https://finance.sina.com.cn/stock/hkstock/ggscyd/2026-05-12/doc-inhxqvat8525840.shtml", "Sina (relaying HKEX announcement 2026-05-11)", "exchange announcement via press", "常州锂源 B-round: RMB 440m exclusively for the Jintan 120,000 t high-compaction LFP base", "company", "2026-05-12"),
 ("s_easpring_jv22", "http://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESZ_STOCK/2022/2022-12/2022-12-02/8704379.PDF", "SZSE (Sina mirror)", "exchange announcement", "Easpring 2022-070: 300,000 t/y L(M)FP cooperation with Shudao New Materials, Panzhihua, phased to 2028-12-31", "primary", "2022-12-02"),
 ("s_easpring_ir25", "https://file.finance.qq.com/finance/hs/pdf/2025/09/16/1224665131.PDF", "SZSE (QQ mirror)", "filed IR activity record", "Easpring IR 2025-006: Panzhihua ph-1 = 120 kt plan; stage 1 (40 kt) built at full output; stage 2 (80 kt) commissioning", "primary", "2025-09-15"),
 ("s_easpring_ar25", "http://static.cninfo.com.cn/finalpage/2026-03-31/1225057127.PDF", "SZSE / CNINFO", "annual report", "Easpring 2025 Annual Report: Panzhihua first-phase 120,000 t/y main lines built and in production", "primary", "2026-03-31"),
 ("s_easpring_km",   "https://disc.static.szse.cn/download/disc/disk03/finalpage/2026-04-16/a5102dab-4910-44a7-bc53-3887f6f73290.PDF", "SZSE", "exchange announcement", "Easpring 2026-021: Kunming (Anning) 150,000 t/y LFP + 200,000 t/y FePO4 precursor projects", "primary", "2026-04-16"),
 ("s_rt_top10exit",  "https://finance.sina.com.cn/roll/2026-01-30/doc-inhkakfm3646531.shtml", "SMM via Sina", "trade press", "SMM 2025 LFP shipments TOP10: Rongtong fell out of the top 10", "trade", "2026-01-30"),
 ("s_gotion_cnr",    "https://www.cnr.cn/ah/jhfc/20260107/t20260107_527485919.shtml", "央广网 (CNR state media)", "state media", "Gotion Lujiang 200,000 t/y 4th-gen LFP CAM project groundbreaking (second source)", "trade", "2026-01-07"),
 ("s_yuneng_site",   "https://www.hunanyuneng.com/zjyn/1.html", "Hunan Yuneng official website", "company website", "Yuneng five production bases: Xiangtan, Jingxi, Suining, Fuquan, Anning", "company", "2026-07-28"),
 ("s_lb_ar24",       "https://pdf.dfcfw.com/pdf/H2_AN202504231661131362_1.pdf", "SZSE (Eastmoney mirror)", "annual report", "LB Group 2024 Annual Report: HQ Jiaozuo; park table — Qinyang EDZ = LFP, Jiaozuo cluster = iron phosphate", "primary", "2025-04-23"),
 ("s_fulin_ann22",   "https://file.finance.qq.com/finance/hs/pdf/2022/10/28/1214937499.PDF", "SZSE (QQ mirror)", "exchange announcement", "Fulin 2022-091: Jiangxi Shenghua LFP base at Yichun EDZ; Shehong (Suining, Sichuan) phase-1 60 kt completed 2022-09", "primary", "2022-10-28"),
 ("s_fulin_deyang",  "https://file.finance.qq.com/finance/hs/pdf/2025/10/29/1224754603.PDF", "SZSE (QQ mirror)", "exchange announcement", "Fulin 2025-070: 350 kt project sited in the Deyang–Aba park (Mianzhu, Deyang)", "primary", "2025-10-28"),
 ("s_cngr_gov",      "https://www.kaiyang.gov.cn/zfbm/xzrzyj/zfxxgk_5777351/fdzdgknr/zrzy_5781601/202407/t20240716_85114317.html", "Kaiyang County government", "government planning notice", "CNGR 200 kt/y iron-phosphate integrated project at Kaiyang County (Guiyang, Guizhou)", "primary", "2024-07-16"),
 ("s_cngr_ar25",     "http://static.cninfo.com.cn/finalpage/2026-03-31/1225054811.PDF", "SZSE / CNINFO", "annual report", "CNGR 2025 Annual Report: HQ Dalong EDZ, Tongren, Guizhou; Kaiyang phosphate resources", "primary", "2026-03-31"),
 ("s_youshan_cnp",   "https://news.cnpowder.com.cn/83229.html", "中国粉体网", "trade press", "Youshan: Tongxiang HQ + six manufacturing bases (Guangxi, Inner Mongolia ×2, Yunnan, Guizhou ×2)", "trade", "2025-06-03"),
 ("s_terui_tl",      "https://libattery.ofweek.com/2022-01/ART-36002-8120-30547042.html", "OFweek锂电网", "trade press", "Terui HQ/plant: Tongliang District, Chongqing; Zhongxian second base", "trade", "2022-01-20"),
 ("s_btr_ar25",      "http://dataclouds.cninfo.com.cn/sjother2/bse_onmarket/2026/20260424/7fb34b543ff011f18c72fa163e296ac0.pdf", "BSE / CNINFO", "annual report", "BTR 2025 Annual Report: HQ Guangming District, Shenzhen", "primary", "2026-04-24"),
 ("s_xyf_hubei",     "https://news.hubeidaily.net/mobile/1006969.html", "湖北日报", "provincial official media", "Xinyangfeng: Zhongxiang (Jingmen) iron-phosphate base operating; Yidu (Yichang) 100 kt FePO4 + 50 kt LFP signed", "trade", "2022-12-14"),
 ("s_ch_h124",       "http://notice.10jqka.com.cn/api/pdf/57ba88d6b7b48d0e.pdf", "SZSE (10jqka mirror)", "half-year report", "Chuanheng H1-2024: Fuquan (Longchang, Luoweitang) is the principal production base incl. iron phosphate", "primary", "2024-08"),
 ("s_eve_ar25",      "https://static.cninfo.com.cn/finalpage/2026-03-28/1225045391.PDF", "SZSE / CNINFO", "annual report", "EVE Energy 2025 Annual Report: HQ Zhongkai High-tech Zone, Huizhou", "primary", "2026-03-28"),
 ("s_calb_site",     "https://www.calb-tech.com/", "CALB official website", "company website", "CALB HQ: Jintan District, Changzhou", "company", "2026-07-28"),
 ("s_rt_itdcw",      "https://www.itdcw.com/news/chuangtouyanjiu/0209153M62026.html", "电池网 (itdcw)", "trade press", "Rongtong F-round (RMB 250m); HQ Daye Lake High-tech Zone, Huangshi; bases Daye/Jiangyou/Neijiang", "trade", "2026-02-09"),
]
SRC_BY_URL = {s["url"]: s for s in can["sources"]}
for sid, url, pub, dt, title, tier, date in NEW_SOURCES:
    assert url not in SRC_BY_URL, "source url already present: " + url
    can["sources"].append({"id": sid, "url": url, "publisher": pub, "doc_type": dt, "title": title,
        "tier": tier, "doc_date": date, "accessed": "2026-07-28", "archived_local": None, "hash": None,
        "note": "v0.3 second-source / geocoding pass (28 Jul 2026); fetched and quote-confirmed; snapshot via archive_sources.py pending."})

P = {p["id"]: p for p in can["plants"]}
def claim(pid, **kw):
    p = P[pid]
    c = {"kind": "capacity", "product": "CAM", "value_ty": None, "value_native": None, "as_of": "",
         "basis": "reported", "scope": "company", "chem": "LFP", "src": None, "note": "",
         "bundle": False, "duplicate_of": None, "target_date": None, "site_key": None,
         "scale": "commercial", "counted": None, "count_reason": "", "seed_row_source": False,
         "supersedes": None, "superseded_by": None}
    c.update(kw)
    c["id"] = "%s.c%d" % (pid, len(p["claims"]) + 1)
    p["claims"].append(c)
    if c.get("supersedes"):
        old = next(x for x in p["claims"] if x["id"] == c["supersedes"])
        old["superseded_by"] = c["id"]
    return c["id"]

def S(key, name, lat, lon, basis, primary=False, note=""):
    return {"key": key, "name": name, "lat": lat, "lon": lon, "geo_basis": basis,
            "primary": primary, "note": note}

# ---------------- p002 Wanrun: company-tier confirmation + Hongmai project ------
claim("p002", value_ty=468000, as_of="2026-05", basis="built", src="s_wanrun_ir0526",
  supersedes="p002.c2",
  note="Company IR record (May 2026, exchange-disclosed; relayed verbatim by Securities Times): '目前公司磷酸铁锂已实现投产产能46.80万吨/年' — 468,000 t/y IN PRODUCTION. Per-base (Q3-2024 briefing): Hubei 311k + Anhui 37k + Shandong 120k. Resolves the g07 Wanrun item: value unchanged, tier trade → company.")
claim("p002", value_ty=70000, basis="construction", scope="site", src="s_wanrun_hongmai",
  note="Hongmai Gaoke 70,000 t/y high-compaction LFP project, Liuliping Industrial Park, Danjiangkou (Shiyan) — sponsor-verified filing, board-approved Jan 2026, ~12-month build.")
P["p002"]["links"].append({"to": "CATL", "k": "q",
  "note": "Supply agreement 2025-05: ~1.3231 Mt LFP committed over 2025-05 → 2030-05; CATL monthly purchases ≥80% of committed volume (announcement via Securities Times)."})
P["p002"]["sites"] = [
  S("shiyan", "Shiyan, Hubei — Yunyang EDZ plants 1&2 + HQ (FY2025 AR registered address)", 32.647, 110.788, "city-centroid", True),
  S("binzhou", "Binzhou (Wudi County), Shandong — Lubei-Wanrun base (120 kt LFP + 240 kt FePO4 ph-1)", 37.740, 117.600, "city-centroid"),
  S("danjiangkou", "Danjiangkou (Shiyan), Hubei — Hongmai 70 kt project", 32.541, 111.081, "city-centroid"),
]

# ---------------- p011 XTC: Ya'an is OPERATING; +40 kt LMFP approved ------------
p11 = P["p011"]
p11["sgroup"] = "operating"
p11["status_raw"] = "Operating (Ya'an LFP; ph-2 commissioning) + 40 kt LFMP line approved (Jun 2028)"
p11["notes"] = (p11["notes"] + " | v0.3 status correction from filings: the Ya'an base has produced LFP since ph-1 reached volume production; FY2025 LFP sales 22,000 t (+2,170.77%). The seed's '~80 kt planned' was the post-expansion TOTAL.").strip(" |")
claim("p011", value_ty=40000, as_of="2026-04", basis="built", chem="LFP", src="s_xtc_ann013",
  supersedes="p011.c1",
  note="Existing Ya'an L(M)FP capacity = 40,000 t/y, stated via the 2026-013 announcement ('建成后…产能将达到 80,000 吨/年' after the NEW 40,000 t line — arithmetic on the filing's own figures). FY2025 AR: liquid-phase LFP ph-1 in volume production/sales, ph-2 equipment installed and commissioning. Supersedes the weak-tier seed figure.")
claim("p011", value_ty=40000, basis="planned", chem="LMFP", scope="site", src="s_xtc_ann013",
  target_date="2028-06",
  note="NEW 40,000 t/y 磷酸铁（锰）锂 (LFMP) line, Ya'an EDZ: capital increase RMB 700m, total ~RMB 734m, 25-month build, production planned June 2028.")
claim("p011", kind="shipments", value_ty=22000, as_of="2025", basis="reported", chem="LFP", src="s_xtc_ar25",
  note="FY2025 AR: LFP sales 2.20万吨, +2,170.77% YoY.")

# ---------------- p004 Lopal: prospectus corrects the website total -------------
claim("p004", value_ty=200670, as_of="2023-12-31", basis="built", src="s_lopal_prosp",
  supersedes="p004.c1",
  note="H-share IPO prospectus designed-capacity table: FY2023 designed capacity 200,670.2 t/y (utilization 57.6%); H1-2024 six-month designed capacity 110,633.4 t (~221 kt/y annualised); five China plants (Jintan, Baodi, Pengxi, Heze, Xiangyang) + Semarang. Global #4, 6.5% share. The seed/website '~310 kt' is NOT restated in any located filing and is retired as an unverified aggregate (FY2025 output 202.1 kt). CONFLICT logged: H-share FY2025 results quote 'sales 202,115 t' where the A-share AR calls that figure production.")
claim("p004", value_ty=120000, basis="construction", scope="site", src="s_lopal_jintan", site_key="jintan",
  note="Jintan (Changzhou) 120,000 t high-compaction LFP base — 常州锂源 B-round RMB 440m contractually restricted to this project (HKEX announcement 2026-05-11). The A-share placement's 110k + 85k 磷酸盐 projects may overlap with this and are NOT counted (unresolved).")
P["p004"]["sites"] = [
  S("changzhou", "Changzhou, Jiangsu — 常州锂源 (cathode subsidiary HQ)", 31.811, 119.974, "city-centroid", True),
  S("jintan", "Jintan District, Changzhou — 120 kt high-compaction base (building)", 31.746, 119.575, "city-centroid"),
  S("baodi", "Baodi, Tianjin — LFP plant (prospectus)", 39.716, 117.310, "city-centroid"),
  S("pengxi", "Pengxi (Suining), Sichuan — LFP plant (prospectus)", 30.758, 105.707, "city-centroid"),
  S("heze", "Heze, Shandong — LFP plant (prospectus)", 35.235, 115.481, "city-centroid"),
  S("xiangyang_lp", "Xiangyang, Hubei — LFP plant (prospectus)", 32.009, 112.122, "city-centroid"),
  S("semarang", "Semarang, Indonesia — overseas base (ph-1 producing; ph-2/3 building)", -6.966, 110.417, "city-centroid"),
]

# ---------------- p009 Easpring: Panzhihua ph-1 BUILT -----------------------------
p9 = P["p009"]
p9["sgroup"] = "operating"
p9["status_raw"] = "Operating — Panzhihua ph-1 (120 kt L(M)FP) built & producing; 300 kt agreement runs to 2028"
p9["notes"] = (p9["notes"] + " | v0.3 status correction: FY2025 AR states the Panzhihua first-phase 120,000 t/y L(M)FP main lines are built and in production ('已建成投产'); IR record 2025-006: stage 1 (40 kt) at full output since completion, stage 2 (80 kt) commissioning H2-2025. FY2025 L(M)FP + sodium cathode revenue RMB 2.84bn (+61.77%). Location corrected to Panzhihua (钒钛高新区团山片区) — an earlier bulletin-page render suggesting Luzhou was disproven against the announcement PDF.").strip(" |")
claim("p009", value_ty=120000, as_of="2026-03", basis="built", chem="L(M)FP-unsplit", src="s_easpring_ar25",
  supersedes="p009.c1",
  note="FY2025 AR: '攀枝花基地…首期项目年产12万吨磷酸（锰）铁锂材料主体产线已建成投产'. Chemistry filed as 磷酸（锰）铁锂 — unsplit, headline band only. Supersedes the seed's 300k 'announced' aggregate (which bundled built + planned).")
claim("p009", value_ty=180000, basis="planned", chem="L(M)FP-unsplit", src="s_easpring_jv22",
  target_date="2028",
  note="Remainder of the 300,000 t/y Shudao cooperation agreement (2022-070; completion/ramp by 2028-12-31, pace adjusted to market; long-term +200 kt more not counted). Start of the remaining 180 kt not yet observed in filings.")
claim("p009", value_ty=150000, basis="planned", chem="LFP", scope="site", src="s_easpring_km", site_key="kunming",
  note="Kunming (Anning Industrial Park, Caopu) 150,000 t/y LFP line — announcement 2026-021 with the Youshan-affiliate stake purchases; ~RMB 4.49bn project investment, 14-month build.")
claim("p009", product="FePO4", chem="FePO4", value_ty=200000, basis="planned", scope="site", src="s_easpring_km", site_key="kunming",
  note="Same announcement: 200,000 t/y high-performance iron-phosphate precursor project (planned — not in the built-precursor stat).")
p9["sites"] = [
  S("panzhihua", "Panzhihua, Sichuan — 钒钛高新区团山片区 (Shudao JV; ph-1 120 kt built)", 26.582, 101.718, "city-centroid", True),
  S("beijing", "Beijing — Easpring HQ (core NCM business)", 39.904, 116.407, "hq-city"),
  S("kunming", "Kunming (Anning), Yunnan — 150 kt LFP + 200 kt FePO4 projects (planned)", 24.919, 102.478, "city-centroid"),
]

# ---------------- notes: Rongtong standing conflict; Gotion inconsistency -------
P["p007"]["notes"] = (P["p007"]["notes"] + " | v0.3: no filing-tier confirmation exists (no public bonds/prospectus; Daye government publications carry no figures). CONFLICT: SMM reports Rongtong FELL OUT of the 2025 LFP shipments top-10, against the SPIR H1-2026 #9 ranking and the company's 'top-3' claim — the counted ~300 kt is single-source-family (SPIR) and some capacity is likely idled.").strip(" |")
P["p007"]["sites"] = [S("daye", "Daye (Huangshi), Hubei — HQ + main base, 大冶湖高新区 (trade-tier evidence)", 30.098, 114.980, "city-centroid", True)]
P["p012"]["notes"] = (P["p012"]["notes"] + " | v0.3: no newer company quantification found (FY2025 AR, 2024 ESG report, 2026 IR records all non-quantitative). A SPIR-based review (Jul 2026) put the Lujiang base at 'at least 50 kt' — inconsistent with the counted 142 kt (Nov 2024 company statement); unresolved. The 200 kt project groundbreaking is second-sourced by CNR state media.").strip(" |")

# ---------------- geocoding pass (documented cities only) ------------------------
P["p001"]["sites"] = [
  S("xiangtan", "Xiangtan, Hunan — HQ + original base (AR registered address; official site)", 27.830, 112.944, "city-centroid", True),
  S("jingxi", "Jingxi (Baise), Guangxi — base (official site)", 23.134, 106.417, "city-centroid"),
  S("suining", "Suining, Sichuan — base (official site; prospectus)", 30.513, 105.573, "city-centroid"),
  S("fuquan_yn", "Fuquan (Qiannan), Guizhou — base (official site)", 26.703, 107.514, "city-centroid"),
  S("anning_yn", "Anning (Kunming), Yunnan — base (official site)", 24.919, 102.478, "city-centroid"),
]
P["p005"]["sites"] = [S("kaiyang", "Kaiyang County (Guiyang), Guizhou — registered seat + LFP base (AR)", 27.058, 106.965, "city-centroid", True)]
P["p003"]["sites"] = [
  S("shenzhen", "Shenzhen (Nanshan) — HQ (AR registered address)", 22.543, 114.058, "hq-city", True),
  S("foshan", "Foshan, Guangdong — production base (FY2025 AR)", 23.022, 113.122, "city-centroid"),
  S("qujing", "Qujing, Yunnan — nano-LFP + LMFP base (FY2025 AR; 3 of 4 production subsidiaries)", 25.490, 103.796, "city-centroid"),
  S("yibin", "Yibin, Sichuan — production base (FY2025 AR)", 28.769, 104.623, "city-centroid"),
]
P["p006"]["sites"] = [
  S("yichun", "Yichun EDZ, Jiangxi — Jiangxi Shenghua main LFP base (announcement 2022-091; company site)", 27.815, 114.417, "city-centroid", True),
  S("shehong", "Shehong (Suining), Sichuan — 60 kt ph-1 (completed 2022-09)", 30.871, 105.375, "city-centroid"),
  S("mianyang", "Mianyang, Sichuan — Fulin Precision HQ (AR)", 31.468, 104.679, "hq-city"),
  S("deyang", "Mianzhu (Deyang), Sichuan — 350 kt project site (announcement 2025-070)", 31.338, 104.220, "city-centroid"),
]
P["p013"]["sites"] = [
  S("tongliang", "Tongliang District, Chongqing — HQ + original plant (trade)", 29.845, 106.056, "city-centroid", True),
  S("zhongxian", "Zhongxian, Chongqing — 100 kt project base (trade/county media)", 30.302, 108.037, "city-centroid"),
]
P["p015"]["sites"] = [
  S("qinyang", "Qinyang EDZ (Jiaozuo), Henan — LFP lines (FY2024 AR park table)", 35.087, 112.947, "city-centroid", True),
  S("jiaozuo", "Jiaozuo, Henan — HQ + iron-phosphate lines (FY2024 AR; EIA notice)", 35.239, 113.233, "city-centroid"),
  S("xiangyang_lb", "Xiangyang, Hubei — LFP project (2022 groundbreaking; status unclear)", 32.009, 112.122, "city-centroid"),
]
P["p018"]["sites"] = [S("tongxiang", "Tongxiang (Jiaxing), Zhejiang — Youshan HQ; six bases (Guangxi, Inner Mongolia ×2, Yunnan, Guizhou ×2 — cities not documented)", 30.630, 120.565, "city-centroid", True)]
P["p022"]["sites"] = [S("shenzhen_btr", "Shenzhen (Guangming) — BTR HQ (FY2025 AR)", 22.543, 114.058, "city-centroid", True)]
P["p024"]["sites"] = [
  S("kaiyang_cngr", "Kaiyang County (Guiyang), Guizhou — 200 kt iron-phosphate integrated base (county planning notice)", 27.058, 106.965, "city-centroid", True),
  S("tongren", "Tongren (Dalong EDZ), Guizhou — CNGR HQ (FY2025 AR)", 27.732, 109.191, "hq-city"),
]
P["p025"]["sites"] = [S("fuquan_ch", "Fuquan (Qiannan), Guizhou — Longchang/Luoweitang plants, principal base incl. iron phosphate (H1-2024 report)", 26.703, 107.514, "city-centroid", True)]
P["p026"]["sites"] = [
  S("zhongxiang", "Zhongxiang (Jingmen), Hubei — 50 kt FePO4 operating; 150 kt building (Hubei Daily)", 31.168, 112.588, "city-centroid", True),
  S("yidu", "Yidu (Yichang), Hubei — 100 kt FePO4 + 50 kt LFP project (洋丰楚元)", 30.378, 111.451, "city-centroid"),
]
P["p029"]["sites"] = [S("huizhou", "Huizhou (Zhongkai), Guangdong — EVE HQ (FY2025 AR)", 23.112, 114.416, "city-centroid", True)]
P["p030"]["sites"] = [S("changzhou_calb", "Changzhou (Jintan), Jiangsu — CALB HQ (official site)", 31.811, 119.974, "city-centroid", True)]
for c in can["customers"]:
    if c["name"] == "CALB":
        c["lat"], c["lon"] = 31.811, 119.974

# ---------------- meta / gaps / changelog ---------------------------------------
can["meta"]["version"] = "0.3.0"
can["meta"]["dataset_date"] = "2026-07-28"
can["meta"]["as_of"] = "28 July 2026"
can["meta"]["cite"] = can["meta"]["cite"].replace("v0.2.0", "v0.3.0")
G = {g["id"]: g for g in can["gap_log"]}
G["g05"]["gap"] = "v0.3 geocoding pass: ~20 rows now carry DOCUMENTED city-level sites (filings/government notices; a few trade-tier, marked). Still undocumented: Wanrun's Anhui base city, Youshan's six base cities, Ronbay's domestic LMFP line location."
G["g07"]["gap"] = ("Updated in v0.3: Wanrun 468 kt is now company-confirmed (May-2026 exchange-disclosed IR record) — resolved. "
  "Still weak: Rongtong ~300 kt remains single-source-family (SPIR) with a standing conflict (SMM: fell out of the 2025 shipments top-10); "
  "Gotion 142 kt remains a Nov-2024 company statement with a conflicting 'at least 50 kt' Lujiang figure in a Jul-2026 SPIR review.")
G["g10"]["gap"] = G["g10"]["gap"] + " New in v0.3: Lopal sales-vs-production figure swap between H-share results and A-share AR; Lopal website ~310 kt vs prospectus 200.7 kt designed (website figure retired); Gotion 142 kt vs 'at least 50 kt' (SPIR)."
can["changelog"].insert(0, {"version": "0.3.0", "date": "2026-07-28", "changes": [
  "Second-source pass on the trade-tier counted figures: Wanrun 468 kt company-confirmed (tier upgraded); Lopal's website 310 kt retired in favour of the HKEX prospectus designed capacity (200,670 t/y, FY2023); Rongtong and Gotion kept with strengthened conflict caveats (g07).",
  "Status corrections from filings: XTC's Ya'an base is OPERATING (40 kt LFP; ph-2 commissioning; FY2025 sales 22 kt) with a new 40 kt LFMP line approved Apr 2026 for Jun 2028; Easpring's Panzhihua first phase (120 kt L(M)FP) is BUILT AND PRODUCING per its FY2025 AR — both rows moved from announced to operating.",
  "Pipeline updates: +70 kt Wanrun Hongmai (filing), +120 kt Lopal Jintan, +330 kt Easpring (agreement remainder 180 kt + Kunming 150 kt), XTC re-based (80 kt seed figure superseded; 40 kt LMFP planned). Wanrun–CATL ~1.32 Mt five-year supply agreement added as a quantified link.",
  "Documented-city geocoding pass: 20 rows re-sited from province/country centroids to filing- or government-documented cities (Yuneng's five bases; Wanrun Shiyan/Binzhou; Lopal's six bases incl. Semarang; Dynanonic Foshan/Qujing/Yibin; Fulin Yichun/Shehong/Deyang; LB Qinyang/Jiaozuo; Anda Kaiyang; CNGR Kaiyang/Tongren; Easpring Panzhihua; Terui Tongliang/Zhongxian; and others).",
  "Source-snapshot archiver shipped (build/archive_sources.py, runs on the maintainer's machine; --check detects silent edits); the gaps register now computes coverage from the canonical.",
  "Bands re-pinned deliberately: lower 1,965,470 · headline 3,529,970 · upper 3,529,970 · pipeline 3,262,250 t/y."]})

# vintage rule: empty as_of on v0.3 claims takes the source document's date
_NEW = {s[0] for s in NEW_SOURCES}
for _p in can["plants"]:
    for _c in _p["claims"]:
        if _c.get("src") in _NEW and not _c.get("as_of"):
            _c["as_of"] = next(s for s in can["sources"] if s["id"] == _c["src"])["doc_date"]

json.dump(can, open(os.path.join(ROOT, "canonical.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_sup = sum(1 for p in can["plants"] for c in p["claims"] if c.get("superseded_by"))
print("v0.3.0 written | sources:", len(can["sources"]), "| claims:", sum(len(p["claims"]) for p in can["plants"]),
      "| superseded:", n_sup)
