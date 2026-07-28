#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upgrade_v0_2.py — v0.1.0 -> v0.2.0: figure-level re-sourcing sprint (filings-first).

Append-only discipline (inherited from NMC Atlas): existing claims are NEVER deleted or
re-valued. A corrected figure enters as a NEW claim citing its own document; the old claim
gets superseded_by set and ships visible, flagged, counting toward no total.

Every figure below was confirmed on a fetched document (research pass 27-28 Jul 2026,
four parallel evidence agents + independent spot-verification of the two largest figures
on the CNINFO/mirror PDFs). Quotes live in the claim notes; URLs in the sources table.
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
can = json.load(open(os.path.join(ROOT, "canonical.json"), encoding="utf-8"))
assert can["meta"]["version"] == "0.1.0", "expected v0.1.0 input"

# ---------------- new sources ---------------------------------------------------
NEW_SOURCES = [
 ("s_yuneng_ar25",   "https://static.cninfo.com.cn/finalpage/2026-04-23/1225155057.PDF", "SZSE / CNINFO", "annual report", "Hunan Yuneng 2025 Annual Report (湖南裕能2025年年度报告)", "primary", "2026-04-23"),
 ("s_wanrun_ar25",   "https://stockmc.xueqiu.com/202604/688275_20260425_M1WW.pdf", "SSE (Xueqiu mirror)", "annual report", "Hubei Wanrun 2025 Annual Report (万润新能2025年年度报告)", "primary", "2026-04-25"),
 ("s_wanrun_delay",  "https://file.finance.qq.com/finance/hs/pdf/2025/11/13/1224802255.PDF", "SSE (QQ mirror)", "exchange announcement", "Wanrun fundraising-project delay announcement 2025-032", "primary", "2025-11-13"),
 ("s_wanrun_21j",    "https://www.21jingji.com/article/20250520/herald/8da85a8b1acf02df0a91de910b592144.html", "21st Century Business Herald", "trade press", "Wanrun domestic LFP capacity 468,000 t/y", "trade", "2025-05-20"),
 ("s_wanrun_us",     "https://news.smm.cn/news/102967450", "SMM", "trade press", "Wanrun US (South Carolina) 50,000 t/y LFP plan, phase 1 9,000 t/y", "trade", "2024-09-25"),
 ("s_dyn_ar25",      "http://notice.10jqka.com.cn/api/pdf/4e61ab4249c7399f.pdf", "SZSE (10jqka mirror)", "annual report", "Shenzhen Dynanonic 2025 Annual Report (德方纳米2025年年度报告)", "primary", "2026-04-29"),
 ("s_dyn_ir1030",    "http://static.cninfo.com.cn/finalpage/2025-10-30/1224777415.PDF", "SZSE / CNINFO", "filed IR activity record", "Dynanonic IR record 2025-006 (37万吨 built + 8万吨 commissioning)", "primary", "2025-10-30"),
 ("s_lopal_ar25",    "http://dataclouds.cninfo.com.cn/shgonggao/hsomarket/2026/20260424/7d95dbe4155d44f09a2d611e4d71a485.PDF", "SSE / CNINFO", "annual report", "Jiangsu Lopal 2025 Annual Report (龙蟠科技2025年年度报告)", "primary", "2026-04-24"),
 ("s_lopal_batang",  "https://www.hkexnews.hk/listedco/listconews/sehk/2026/0610/2026061001481_c.pdf", "HKEX", "exchange announcement", "Lopal: Indonesia Batang 120,000 t/y gen-2/3 LFP investment announcement", "primary", "2026-06-10"),
 ("s_lopal_ph2",     "https://www.nbd.com.cn/articles/2026-05-25/4407632.html", "NBD (每日经济新闻)", "trade press (company investor-platform reply)", "Lopal: Indonesia phase 2 90,000 t in installation/commissioning", "trade", "2026-05-25"),
 ("s_lopal_ph3",     "https://www.nbd.com.cn/articles/2025-12-24/4193800.html", "NBD (每日经济新闻)", "trade press (quoting SSE/HKEX announcement)", "Lopal: Indonesia phase 3 raised to 100,000 t/y", "trade", "2025-12-24"),
 ("s_anda_ir112",    "https://qxb-pdf-osscache.qixin.com/AnBaseinfo/4c52c2fcb56c4edbc5717635a1f2384f.pdf", "BSE / CNINFO (Qixin mirror)", "filed IR activity record", "Anda IR record 2025-112: 150 kt/y LFP + 150 kt/y FePO4; 240 kt LFP + 450 kt precursor in construction", "primary", "2025-11-11"),
 ("s_anda_ar25",     "https://news.10jqka.com.cn/20260429/c676383927.shtml", "10jqka (quoting FY2025 AR)", "trade press", "Anda FY2025: revenue +131%, LFP sales 111,100 t; 15万吨/15万吨 capacity restated", "trade", "2026-04-29"),
 ("s_fulin_ar25",    "http://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESZ_STOCK/2026/2026-4/2026-04-29/12268128.PDF", "SZSE (Sina mirror)", "annual report", "Fulin Precision 2025 Annual Report (富临精工2025年年度报告)", "primary", "2026-04-29"),
 ("s_fulin_sum25",   "http://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESZ_STOCK/2026/2026-4/2026-04-29/12268129.PDF", "SZSE (Sina mirror)", "annual report summary", "Fulin FY2025 AR summary: 350 kt Deyang + 175 kt JV phase-1 LFP projects", "primary", "2026-04-29"),
 ("s_lb_ar25",       "http://notice.10jqka.com.cn/api/pdf/1a1f729b0db274c2.pdf", "SZSE (10jqka mirror)", "annual report", "LB Group 2025 Annual Report (龙佰集团2025年年度报告)", "primary", "2026-04"),
 ("s_rt_h1_26",      "https://finance.sina.com.cn/wm/2026-07-06/doc-inifxatp1743108.shtml", "起点锂电 via Sina Finance", "trade press", "H1-2026 LFP producer review: Rongtong ~300 kt built, 525 kt planned", "trade", "2026-07-06"),
 ("s_rt_india",      "https://news.smm.cn/news/103144053", "SMM", "trade press", "Rongtong India JV (with Reliance): phase-1 80,000 t/y, MP expected Mar 2026", "trade", "2025-01-17"),
 ("s_terui_reply",   "http://epaper.zqrb.cn/images/2022-08/18/D49/zqrb20220818D49.pdf", "SSE inquiry reply (证券日报 print of 万里股份 disclosure)", "exchange inquiry reply", "Terui: 40 kt operating + 60 kt building, 100 kt design capacity", "primary", "2022-08-18"),
 ("s_terui_yicai",   "https://m.yicai.com/news/101681021.html", "Yicai (第一财经)", "trade press (quoting listed-company announcement)", "Terui additional 60 kt onstream by Feb 2023 (deal-termination context)", "trade", "2023-02-21"),
 ("s_cnnc_term",     "https://www.yzwb.net/news/ch/202506/t20250602_215840.html", "扬子晚报 (quoting 2025-06-02 announcement)", "trade press", "CNNC Huayuan terminates the 500 kt iron-phosphate project; 100 kt/y FePO4 built", "trade", "2025-06-02"),
 ("s_cnnc_util",     "https://finance.sina.com.cn/roll/2025-06-04/doc-ineyximx0157415.shtml", "Sina Finance", "trade press", "CNNC: 100 kt FePO4 in operation; 2024 utilization 1.95%", "trade", "2025-06-04"),
 ("s_pulead_wm",     "https://pdf.dfcfw.com/pdf/H2_AN202306141590945065_1.pdf", "SSE announcement by 西部矿业 (Eastmoney mirror)", "exchange announcement", "Taifeng Xianxing (Pulead lineage): 185,000 t/y LFP (25k legacy + 160k phase 1), phase 2 140k planned", "primary", "2023-06-14"),
 ("s_gotion_142k",   "https://cn.solarbe.com/news/20241126/91516.html", "碳索储能网 (company investor-platform reply)", "trade press", "Gotion in-house LFP CAM total 142,000 t/y; Lujiang plant 42,000 t/y", "trade", "2024-11-26"),
 ("s_gotion_200k",   "https://news.cnpowder.com.cn/87285.html", "中国粉体网", "trade press", "Gotion 200,000 t/y 4th-gen LFP CAM project construction start (Lujiang)", "trade", "2026-01-07"),
 ("s_wkxn_h1",       "https://static.cninfo.com.cn/finalpage/2025-08-23/1224557582.PDF", "SSE / CNINFO", "half-year report", "五矿新能 (ex-Changyuan Lico) H1-2025: 60 kt LFP project acceptance; LFP sales +217.53%", "primary", "2025-08-23"),
 ("s_wkxn_ccxi",     "https://stockmc.xueqiu.com/202606/688779_20260627_62Y8.pdf", "CCXI rating report (Xueqiu mirror)", "bond-market rating report", "五矿新能 2026 tracking rating: 60 kt LFP project basically complete", "primary", "2026-06-26"),
 ("s_ronbay_kr",     "https://star.sse.com.cn/disclosure/listedinfo/announcement/c/new/2023-08-21/688005_20230821_E050.pdf", "SSE STAR", "exchange announcement", "Ronbay: Korea 20,000 t/y LMFP + 40,000 t/y ternary project announcement 2023-064", "primary", "2023-08-21"),
 ("s_ronbay_cls",    "https://m.cls.cn/detail/1887173", "财联社 (company investor-platform reply)", "trade press", "Ronbay: domestic 10,000 t solid-phase LMFP complete; Korea 20 kt LMFP MP expected 2026", "trade", "2024-12-12"),
 ("s_ronbay_ar25",   "http://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESH_STOCK/2026/2026-4/2026-04-11/12080315.PDF", "SSE (Sina mirror)", "annual report", "Ronbay 2025 Annual Report (容百科技2025年年度报告)", "primary", "2026-04-11"),
 ("s_hc_xhby",       "https://www.xhby.net/content/s69afe938e4b0a737d394c74c.html", "新华日报财经", "provincial official media", "珩创纳米 (Jiangsu Hengchuang): Yancheng LMFP capacity 15,000 t/y; B-round Mar 2026", "trade", "2026-03-10"),
 ("s_hc_gasgoo",     "https://i.gasgoo.com/news/70451482.html", "盖世汽车 (Gasgoo)", "trade press", "珩创 Ningxia 130 kt LMFP project: phase 1 30 kt ground broken, target Dec 2026", "trade", "2026-03-27"),
 ("s_ibu_eqs",       "https://www.onvista.de/news/2026/07-15-eqs-news-ibu-tec-mit-weiteren-planmaessigen-baufortschritten-beim-aufbau-von-lfp-produktionsanlage-in-bitterfeld-0-37-26532436", "IBU-tec advanced materials AG via EQS (onvista mirror)", "corporate news release", "IBU-tec: Bitterfeld 15,000 t LFP plant, operation from 2028, PowerCo 10-yr full offtake", "company", "2026-07-15"),
 ("s_ibu_weimar",    "https://www.ibu-tec.de/investor-relations/finanzmeldungen/newsbeitrag/ibu-tec-erfolgreiches-richtfest-fuer-neuen-spruehturm-als-zwischenschritt-fuer-grossvolumige-lfp-produktion-am-standort-bitterfeld/", "IBU-tec advanced materials AG", "corporate news release", "IBU-tec: transition-phase LFP production on existing Weimar plants until 2028 (no tonnage stated)", "company", "2026-04-15"),
 ("s_ytn_ar25",      "https://stockmc.xueqiu.com/202603/600096_20260324_43PU.pdf", "SSE (Xueqiu mirror)", "annual report", "Yuntianhua 2025 Annual Report: 100 kt/y FePO4 (output 70.8 kt); LFP via cross-shareholding partners", "primary", "2026-03-24"),
 ("s_wanhua_hy",     "https://finance.sina.com.cn/jjxw/2025-02-28/doc-inemzuik9893891.shtml", "Sina Finance", "trade press", "Wanhua Haiyang base ground broken (RMB 16.8bn): 500 kt LFP planned, full production by end-2032; Zhuoneng cell unit acquired 2020", "trade", "2025-02-28"),
 ("s_zn_neeq",       "http://pdf.dfcfw.com/pdf/H2_AN201511090011336891_1.pdf", "NEEQ listing document (Eastmoney mirror)", "legal opinion (listing)", "Yantai Zhuoneng: 800 t/y LFP project environmental acceptance (2010)", "primary", "2015-11-09"),
 ("s_ronbay_csrc",   "https://news.qq.com/rain/a/20260118A06ION00", "澎湃新闻 via QQ", "trade press", "CSRC investigation into Ronbay over CATL LFP mega-contract announcement", "trade", "2026-01-18"),
]
SRC_BY_URL = {s["url"]: s for s in can["sources"]}
for sid, url, pub, dt, title, tier, date in NEW_SOURCES:
    assert url not in SRC_BY_URL, "source url already present: " + url
    can["sources"].append({"id": sid, "url": url, "publisher": pub, "doc_type": dt, "title": title,
        "tier": tier, "doc_date": date, "accessed": "2026-07-28", "archived_local": None, "hash": None,
        "note": "v0.2 re-sourcing sprint (27-28 Jul 2026); fetched and quote-confirmed; snapshot archive still pending."})

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

# ---------------- p001 Hunan Yuneng --------------------------------------------
claim("p001", value_ty=994500, as_of="2025-12-31", basis="built", chem="L(M)FP-unsplit", src="s_yuneng_ar25",
  note="FY2025 AR capacity table, 磷酸盐正极材料 (phosphate cathode materials — AR does not split LFP/LMFP; LMFP is at trial-production stage): 产能 994,500.00 t, utilization 113.76%. Spot-verified on the CNINFO PDF. Fills the seed's biggest hole (g01).")
claim("p001", value_ty=70000, basis="construction", chem="L(M)FP-unsplit", src="s_yuneng_ar25",
  note="FY2025 AR: 在建产能 70,000.00 t (under construction), same table.")
claim("p001", kind="shipments", value_ty=1137085, as_of="2025", basis="reported", src="s_yuneng_ar25",
  supersedes="p001.c2",
  note="FY2025 AR: 销售量 1,137,084.83 t; 生产量 1,131,305.32 t. Supersedes the seed's '>1 Mt' ranking floor with the filed figure. Production exceeds year-end nameplate (capacity added in-year; AR's own utilization 113.76%).")

# ---------------- p002 Hubei Wanrun --------------------------------------------
claim("p002", value_ty=468000, as_of="2025-05", basis="reported", src="s_wanrun_21j",
  note="Domestic LFP capacity 46.8万吨/年 (Hubei 311k + Shandong 120k + Anhui 37k). Trade tier: the FY2025 AR (confirmed absence, three targeted reads) publishes no company capacity table; filing-tier component: '12万吨/年磷酸铁锂及24万吨/年磷酸铁项目产能已建成投产' (announcement 2025-032). Second Binzhou 120k line delayed to Dec 2026 — unclear if inside the 468k.")
claim("p002", kind="shipments", value_ty=375100, as_of="2025", basis="reported", src="s_wanrun_ar25",
  supersedes="p002.c1",
  note="FY2025 AR: 磷酸铁锂累计出货量为37.51万吨, +64.33% YoY. Supersedes the seed ranking figure with the filed one (same value, source upgraded to filing).")
claim("p002", product="FePO4", chem="FePO4", value_ty=240000, basis="built", as_of="2025-11", src="s_wanrun_delay",
  note="Filing 2025-032: '24万吨/年磷酸铁项目产能已建成投产' — 240,000 t/y iron phosphate built and producing (Binzhou).")
claim("p002", value_ty=9000, basis="planned", scope="site", src="s_wanrun_us",
  target_date="2028", note="US South Carolina plan: 50,000 t/y LFP total, phase 1 9,000 t/y (only the committed phase is counted; '分期开展建设').")

# ---------------- p003 Dynanonic -----------------------------------------------
claim("p003", value_ty=450000, as_of="2025-12-31", basis="built", chem="L(M)FP-unsplit", src="s_dyn_ar25",
  supersedes="p003.c1",
  note="FY2025 AR: '公司已建成磷酸盐系正极材料产能 45 万吨/年' — 450,000 t/y built, phosphate-FAMILY (nano-LFP + LMFP, no split published). Spot-verified. Utilization table (different measure, monthly-summed): 333,625 t effective, 85.66%, 53,333 t in construction. IR record Oct-2025: 37万吨 built + 8万吨 commissioning — consistent if commissioning finished by year-end. Supersedes the seed's LFP-only 345k.")
c_dyn_q = next(x for x in P["p003"]["claims"] if x["id"] == "p003.c2")
c_dyn_q["superseded_by"] = None  # keep visible; handled below as inside-total
c_dyn_q["counted"] = False
c_dyn_q["count_reason"] = "Qujing 110 kt LMFP site figure sits INSIDE the 450 kt phosphate-family company total (p003.c3) — shown for site detail, counts nothing since v0.2."
claim("p003", kind="shipments", value_ty=280000, as_of="2025", basis="reported", chem="L(M)FP-unsplit", src="s_dyn_ar25",
  note="FY2025 AR: 销量 28.00万吨 (+24.04%); 产量 28.58万吨 (+20.76%), phosphate-family CAM.")

# ---------------- p004 Lopal ----------------------------------------------------
claim("p004", kind="shipments", value_ty=202481, as_of="2025", basis="reported", src="s_lopal_ar25",
  note="FY2025 AR: LFP 销售量 202,480.88 t; 生产量 202,115.13 t. Six bases incl. Semarang, Indonesia. The AR's reachable portion publishes no group capacity total — the seed's ~310k company figure stands unconfirmed by filing (flagged).")
claim("p004", value_ty=90000, basis="construction", scope="site", src="s_lopal_ph2",
  note="Indonesia Semarang phase 2: 90,000 t under construction, in installation/commissioning (company investor-platform reply, May 2026). CONFLICT: EnergyTrend (Dec 2025) had phase 2 = 62,500 t 'completed' — later-dated company statement carried.")
claim("p004", value_ty=100000, basis="construction", scope="site", src="s_lopal_ph3", target_date="2026",
  note="Indonesia Semarang phase 3 raised 62,500 → 100,000 t/y (announcement of 2025-12-24; completion expected May 2026 — not yet confirmed complete).")
claim("p004", value_ty=120000, basis="planned", scope="site", src="s_lopal_batang", target_date="2027",
  note="NEW Batang (Central Java) plant: 120,000 t/y gen-2/3 LFP, USD 160m, construction start expected Jul 2026, 12-month build (HKEX filing 2026-06-10).")

# ---------------- p005 Anda — bundle correction --------------------------------
claim("p005", value_ty=150000, as_of="2025-12-31", basis="built", src="s_anda_ir112",
  supersedes="p005.c1",
  note="CORRECTION of the seed bundle: filing 2025-112 states SEPARATELY '15万吨/年磷酸铁及15万吨/年磷酸铁锂产能' — 150,000 t/y LFP CAM (this claim) AND 150,000 t/y FePO4 (own claim). Restated as of end-2025 in the FY2025 AR. Utilization >95% excl. lines under retrofit; Q1-2026 effective capacity 110,000 t during technical upgrades. Listed venue renumbered BSE 830809 → 920809.")
claim("p005", product="FePO4", chem="FePO4", value_ty=150000, as_of="2025-12-31", basis="built", src="s_anda_ir112",
  note="Filing 2025-112 / FY2025 AR: 150,000 t/y iron-phosphate precursor capacity (separate from the LFP CAM lines).")
claim("p005", value_ty=240000, basis="construction", src="s_anda_ir112",
  note="Filing 2025-112: '在建项目有24万吨/年磷酸铁锂项目' — 240,000 t/y LFP under construction (2027 target ~350 kt total per IR). The separate 450 kt/y PRECURSOR project (phase 1 300 kt, completion slipped Jun→Oct 2026) is FePO4 and not counted here.")
claim("p005", kind="shipments", value_ty=111100, as_of="2025", basis="reported", src="s_anda_ar25",
  note="FY2025 (via 10jqka quoting the AR): LFP sales 11.11万吨, +150% YoY; revenue +131%; Q1-2026 returned to profit after 12 loss-making quarters.")

# ---------------- p006 Fulin ----------------------------------------------------
claim("p006", value_ty=300000, as_of="2026-04", basis="built", src="s_fulin_ar25",
  supersedes="p006.c1",
  note="FY2025 AR: '江西升华现有高压实密度磷酸铁锂正极材料产能 30 万吨' — 300,000 t/y existing. Source upgraded trade→filing, value unchanged.")
claim("p006", kind="shipments", value_ty=273828, as_of="2025", basis="reported", src="s_fulin_ar25",
  note="FY2025 AR: 销售量 273,827.64 t (+117.06%); 生产量 273,795.32 t. The seed's 128 kt output-2024 figure matches the AR's 2024 comparative (128,239.75 t).")
claim("p006", value_ty=350000, basis="planned", scope="site", src="s_fulin_sum25",
  note="AR summary: 350,000 t/y new high-compaction LFP project, Deyang–Aba park. A further '年产50万吨高端储能用磷酸铁锂' is 'being advanced' with unclear overlap — noted, not counted.")
claim("p006", value_ty=175000, basis="planned", scope="site", src="s_fulin_sum25",
  note="AR summary: JV with Deyang Chuanfa Longmang — phase-1 175,000 t/y LFP project.")

# ---------------- p007 Rongtong -------------------------------------------------
claim("p007", value_ty=300000, as_of="2026-07", basis="reported", src="s_rt_h1_26",
  supersedes="p007.c1",
  note="H1-2026 producer review: '整体规划产能52.5万吨/年，当前已建成落地产能约30万吨/年' — ~300,000 t/y built (planned total 525k incl. LMFP). Q1-2026 capacity sold out per SMM. Supersedes the seed's 100–145k range. Still no filing tier: IPO tutoring only, no prospectus public.")
claim("p007", value_ty=80000, basis="construction", scope="site", src="s_rt_india", target_date="2026",
  note="India JV with Reliance (see p061): phase-1 80,000 t/y LFP plant, mass production expected Mar 2026 (not yet confirmed started).")

# ---------------- p012 Gotion ---------------------------------------------------
claim("p012", value_ty=142000, as_of="2024-11", basis="reported", src="s_gotion_142k",
  supersedes="p012.c1",
  note="Company investor-platform reply (via trade): in-house LFP CAM total 142,000 t/y (~70 GWh of cells); Lujiang plant 42,000 t/y; Kehong lines inside. FY2025 AR discloses no quantified CAM capacity (confirmed absence, three targeted reads).")
claim("p012", value_ty=200000, basis="construction", src="s_gotion_200k",
  supersedes="p012.c2",
  note="200,000 t/y 4th-generation LFP CAM project construction formally started 2026-01-06 (Lujiang). Supersedes the seed's 200k 'target' — now under construction. Unclear whether identical to Kehong's earlier planned 200k or incremental.")

# ---------------- p013 Terui ----------------------------------------------------
claim("p013", value_ty=100000, as_of="2023-02", basis="built", src="s_terui_reply",
  supersedes="p013.c1",
  note="SSE inquiry reply (2022-08): 40,000 t/y operating + 60,000 t/y building = 100,000 t/y design; Yicai (Feb 2023) confirms the 60k came onstream. STALENESS FLAG: no post-2023 confirmation; absent from 2025/2026 top-producer lists; company site unreachable (expired SSL). Output history: 6,711 t (2020), 11,489 t (2021).")

# ---------------- p015 LB Group — value correction -----------------------------
claim("p015", value_ty=50000, as_of="2025-12-31", basis="built", src="s_lb_ar25",
  supersedes="p015.c1",
  note="CORRECTION: FY2025 AR (same wording FY2024): '磷酸铁锂产能 5 万吨/年，磷酸铁产能 10 万吨/年' — LFP is 50,000 t/y, NOT the seed's '~200 kt added 2022' (2021-era ambition, since scaled back: management publicly '已收缩关于磷酸铁、磷酸铁锂的后续投资'). No LFP output/sales disclosed in filings — utilization unconfirmed.")
claim("p015", product="FePO4", chem="FePO4", value_ty=100000, as_of="2025-12-31", basis="built", src="s_lb_ar25",
  note="FY2025 AR: 100,000 t/y iron phosphate; 2025 output 97,600 t (+72.17%), sales 96,000 t. Phase 3 (100k) of the 200k project in commissioning — not yet nameplate.")

# ---------------- p016 CNNC Huayuan — TERMINATED -------------------------------
p16 = P["p016"]
p16["sgroup"] = "dead"; p16["dead_cause"] = "cancellation"
p16["status_raw"] = "Terminated (Jun 2025) — LFP stage never built"
p16["notes"] = (p16["notes"] + " | v0.2 status correction: board terminated the fundraising-invested 500 kt/y IRON-PHOSPHATE project on 2025-06-02 (RMB 1.309bn of 3.385bn invested; remaining funds to working capital). Only a 100 kt/y FePO4 plant was ever built (2024 utilization 1.95%); no LFP plant was constructed. The 2021 headline plan was 磷酸铁锂 but the funded project was 磷酸铁.").strip(" |")
claim("p016", value_ty=500000, basis="cancelled", src="s_cnnc_term",
  supersedes="p016.c1",
  note="Terminated 2025-06-02 (announcement quoted by 扬子晚报/Sina): '拟终止…年产50万吨磷酸铁项目'. Reason: downstream supply-demand shift, demand growth slowed. Investment-amount conflict across reports (33.85亿 committed vs 38.3亿 total) — both reported, different bases.")
claim("p016", product="FePO4", chem="FePO4", value_ty=100000, as_of="2025-06", basis="built", src="s_cnnc_util",
  note="'已建成10万吨/年磷酸铁装置并实现销售' — 100 kt/y FePO4 built and selling; 2024 utilization 1.95%.")

# ---------------- p010 Ronbay — Korea LMFP not built yet ------------------------
claim("p010", value_ty=20000, basis="construction", scope="site", chem="LMFP", src="s_ronbay_kr",
  supersedes="p010.c1", site_key="chungju", target_date="2026",
  note="Filing 2023-064: Chungju 20,000 t/y LMFP project (≤RMB 642m), originally trial production H1-2025; company statement Dec-2024: '韩国2万吨产能建设已完成论证，预计2026年实现量产'. FY2024/FY2025 ARs list Korea capacity as ternary only — the LMFP line is NOT confirmed built. Moved from operating to pipeline.")
claim("p010", value_ty=10000, as_of="2024-12", basis="built", chem="LMFP", src="s_ronbay_cls",
  note="'国内磷酸锰铁锂固相1万吨产能项目已建设完成' — domestic 10,000 t/y solid-phase LMFP complete (company statement via CLS). FY2025 AR: LMFP 满产满销, sales doubled third year running — no nameplate stated.")
P["p010"]["notes"] = (P["p010"]["notes"] + " | v0.2: CSRC opened an investigation (Jan 2026) into Ronbay over alleged misleading statements in its CATL LFP mega-contract announcement (~3.05 Mt); separately announced acquiring 贵州新仁 with a 60 kt/y LFP line (Dec 2025, trade) — neither counted.").strip(" |")

# ---------------- p017 珩创 (Hengchuang) — entity + figures ---------------------
p17 = P["p017"]
p17["company"] = "Hengchuang Nano (珩创纳米, Jiangsu Hengchuang)"
p17["sgroup"] = "operating"   # status correction: Yancheng base operating since 2022/2024 (15 kt LMFP)
p17["status_raw"] = "Operating (Yancheng 15 kt LMFP) + Ningxia phase 1 building"
p17["notes"] = (p17["notes"] + " | v0.2 entity correction: 江苏珩创纳米科技有限公司 (Yancheng, Jiangsu) — the seed's 恒创/Zhuhai attribution was wrong (first character is 珩). Private, VC-funded (B round Mar 2026); claimed LMFP shipment share #1 globally three years running.").strip(" |")
p17["sites"] = [
  {"key": "yancheng", "name": "Yancheng, Jiangsu (operating base; city-centroid)", "lat": 33.347, "lon": 120.163, "geo_basis": "city-centroid", "primary": True, "note": "v0.2 correction"},
  {"key": "yinchuan", "name": "Yinchuan, Ningxia (130 kt project site; phase 1 under construction)", "lat": 38.487, "lon": 106.231, "geo_basis": "region-only", "primary": False, "note": ""},
]
claim("p017", value_ty=15000, as_of="2024-04", basis="built", chem="LMFP", src="s_hc_xhby",
  note="Yancheng base: 15,000 t/y LMFP operating ('2024年4月底，年产1万吨产线建成，总产能达1.5万吨'; 'stable operation' May 2025). First 5,000 t line onstream end-2022.")
claim("p017", value_ty=30000, basis="construction", scope="site", chem="LMFP", src="s_hc_gasgoo",
  supersedes="p017.c1", site_key="yinchuan", target_date="2026-12",
  note="Ningxia (Yinchuan ETDZ) 130 kt/y LMFP plan (RMB 4.8bn, signed 2025-12-26): phase 1 30,000 t/y ground broken 2026-03-26, target Dec 2026. Only the phase under construction counts — supersedes the seed's 130k 'planned' total. CONFLICT: SMM (Dec 2025) had phase 1 = 25k; later sources say 30k.")

# ---------------- p019 五矿新能 (ex-Changyuan Lico) ------------------------------
p19 = P["p019"]
p19["notes"] = (p19["notes"] + " | v0.2: company renamed 五矿新能源材料（湖南）股份有限公司 (Minmetals New Energy, same ticker 688779).").strip(" |")
claim("p019", value_ty=60000, basis="construction", src="s_wkxn_ccxi",
  supersedes="p019.c1", target_date="2026",
  note="60,000 t/y LFP project '已基本完工' (basically complete — CCXI tracking rating, Jun 2026); experimental-building environmental acceptance May 2025 (H1-2025 filing); H1-2025 LFP sales +217.53% (no absolute volume disclosed). Conservatively kept in the PIPELINE until commissioning is confirmed — supersedes the seed's 20k 'initial line' figure, which no filing restates.")

# ---------------- p008 Pulead / 泰丰先行 ------------------------------------------
p8 = P["p008"]
p8["notes"] = (p8["notes"] + " | v0.2 entity note: LFP operating entity is 青海泰丰先行锂能科技有限公司 (Taifeng Xianxing, Xining) in the 北大先行/Pulead lineage; HK IPO filed ~May 2024, listing outcome unconfirmed. Ranked #11 in H1-2026 LFP review.").strip(" |")
p8["sites"] = [
  {"key": "xining", "name": "Xining, Qinghai (Taifeng Xianxing cathode base; city-centroid)", "lat": 36.617, "lon": 101.766, "geo_basis": "city-centroid", "primary": True, "note": "v0.2 correction — seed had Beijing (university origin)"},
  {"key": "beijing", "name": "Beijing (R&D; Peking University origin)", "lat": 39.904, "lon": 116.407, "geo_basis": "region-only", "primary": False, "note": ""},
]
claim("p008", value_ty=185000, as_of="2023-06", basis="built", src="s_pulead_wm",
  note="Western Mining SSE announcement (2023-06-14): '18.5万吨/年磷酸铁锂（原有2.5万吨/年…新建一期16万吨/年…2023年5月投料试生产）' — 185,000 t/y (phase 1 in trial feed-in production at disclosure). STALENESS FLAG: latest confirmed figure; no post-2023 update found. Fills a seed no-figure hole.")
claim("p008", value_ty=140000, basis="planned", src="s_pulead_wm",
  note="Same filing: phase-2 140,000 t/y LFP planned.")

# ---------------- p053 IBU-tec — Weimar figure unconfirmed ----------------------
claim("p053", kind="qualitative", value_ty=None, basis="reported", scope="site", src="s_ibu_weimar",
  supersedes="p053.c1",
  note="Company release (Apr 2026): transition-phase LFP is produced on EXISTING Weimar plants until 2028 — no tonnage stated anywhere reachable (2024 annual report and IR archive checked). The seed's '>3,000 tpa' could not be confirmed in any company document and stops counting. Weimar revenue guidance: mid-double-digit €m over three years.")
claim("p053", value_ty=15000, basis="construction", scope="site", src="s_ibu_eqs",
  supersedes="p053.c2", site_key="bitterfeld", target_date="2028",
  note="EQS release 2026-07-15: 'Die 2028 in Betrieb gehende LFP-Produktionsanlage wird eine Kapazität von 15.000 Tonnen haben'; spray-tower trial operation from Q4 2026; PowerCo has secured the entire volume ≥10 years. Source upgraded trade→company, value unchanged.")

# ---------------- p020 Yuntianhua — precursor, LFP via partners ------------------
claim("p020", product="FePO4", chem="FePO4", value_ty=100000, as_of="2025-12-31", basis="built", src="s_ytn_ar25",
  note="FY2025 AR: 100,000 t/y iron phosphate (continuous-process retrofit completed); 2025 output 70,800 t. The AR discloses NO owned LFP CAM capacity — LFP integration runs through cross-shareholding partners ('与合作方以交叉持股的方式实现磷酸铁和磷酸铁锂上下游一体化运营'). The seed's product-page LFP listing stands, but no capacity is bookable.")

# ---------------- p014 Wanhua — Haiyang mega-project ----------------------------
claim("p014", value_ty=500000, basis="planned", scope="site", src="s_wanhua_hy", target_date="2032",
  note="Haiyang (Shandong) base ground broken 2025-02-24 (RMB 16.8bn): 500,000 t/y LFP CAM planned, full production by end-2032. Provincial platform (Mar 2026) lists three Wanhua projects totalling 1.05 Mt planned incl. Laizhou 650k — overlap with this and the seed's Shandong 100k unresolved, so ONLY Haiyang is added. Wanhua acquired Yantai Zhuoneng's cell unit in Apr 2020 (see p021).")

# ---------------- p021 Zhuoneng — status correction -----------------------------
p21 = P["p021"]
p21["sgroup"] = "uncertain"
p21["status_raw"] = "Uncertain — public disclosure ceased 2019; battery unit sold to Wanhua 2020"
p21["notes"] = (p21["notes"] + " | v0.2 status correction: materials arm (卓能材料, NEEQ 834314) failed to publish its H1-2019 report and faced delisting; the cell company 烟台卓能锂电池 was acquired 100% by Wanhua Chemical (Apr 2020, RMB 100m). Only LFP capacity ever documented at filing tier: 800 t/y (2010 environmental acceptance). Any current Yantai-area LFP capacity books under Wanhua (p014).").strip(" |")
claim("p021", kind="qualitative", value_ty=None, basis="historic", src="s_zn_neeq",
  note="NEEQ listing legal opinion (2015): 800 t/y LFP project environmental acceptance 2010-11-25 — the only filing-tier capacity ever documented. No post-2019 disclosure found.")

# ---------------- meta / gaps / changelog ---------------------------------------
can["meta"]["version"] = "0.2.0"
can["meta"]["dataset_date"] = "2026-07-28"
can["meta"]["generated"] = "2026-07-28"
can["meta"]["as_of"] = "28 July 2026"
can["meta"]["cite"] = can["meta"]["cite"].replace("v0.1.0", "v0.2.0")
can["meta"]["counting_rule"] = (
  "The olivine rule (v0.2): a figure enters the operating bands only if the plant is operating at commercial scale, "
  "the claim is a CAPACITY (not shipments, output, cumulative or a rate), its basis is built/reported, it is not a bundle, "
  "not a duplicate of another row's project, and NOT SUPERSEDED — corrections are append-only supersession chains: the old "
  "figure stays visible, flagged, counting toward nothing. Lower = chemistry stated outright (LFP or LMFP). Headline = lower "
  "+ L(M)FP-unsplit (phosphate-family totals that don't split LFP from LMFP — Yuneng and Dynanonic publish only these). "
  "Upper = headline + bundles and unsplit-cathode figures. Announced / planned / construction claims form a separate PIPELINE "
  "total; targets count toward nothing. Shipments and output are market context only.")
can["gap_log"] = [
  {"id": "g01", "gap": "RESOLVED in v0.2 (was: Yuneng no-figure): Yuneng's FY2025 AR nameplate (994.5 kt) is now counted. NEW top gap: 1.44 Mt/y of the headline (Yuneng 994.5k + Dynanonic 450k) is phosphate-FAMILY totals with no published LFP/LMFP split — the lower–headline gap is now the atlas's main uncertainty."},
  {"id": "g02", "gap": "v0.2 re-sourced the top-tonnage rows to filings/company documents (17 new figure-level sources). Remaining figure-bearing claims still on row-level seed sources: the long tail (Taiwan, Japan, announced Western projects)."},
  {"id": "g03", "gap": "Vintages now stated on re-sourced claims; most seed-tail claims remain undated."},
  {"id": "g04", "gap": "No SHA-256 source snapshot archive yet (archive_sources.py port pending); several filings are cited via mirror hosts (Xueqiu/10jqka/Sina/QQ/Eastmoney) because CNINFO's site blocks direct fetch — originals exist on CNINFO."},
  {"id": "g05", "gap": "Chinese plant locations largely province/country precision. v0.2 corrected two (Pulead → Xining; 珩创 → Yancheng); no full site-level geocoding pass yet."},
  {"id": "g06", "gap": "LMFP absolute bases now partially documented (珩创 15 kt built; Ronbay 10 kt domestic built; Korea 20 kt in pipeline), but the '~80% share' duopoly claim still has no disclosed absolute market base."},
  {"id": "g07", "gap": "Two large counted figures rest on trade tier with no reachable filing: Wanrun 468 kt (AR confirmed to publish NO capacity table) and Rongtong 300 kt (private; no prospectus public). Gotion 142 kt is a company statement relayed by trade press; its FY2025 AR publishes no CAM capacity."},
  {"id": "g08", "gap": "Staleness: Terui 100 kt design (2022-23 filings; absent from 2025-26 producer lists) and Pulead/Taifeng 185 kt (Jun 2023 filing; phase 1 was in trial production then) are counted with no newer confirmation."},
  {"id": "g09", "gap": "IBU-tec Weimar produces LFP through 2028 with NO disclosed tonnage; the seed's '>3,000 tpa' was not confirmable in any company document and was retired from the totals."},
  {"id": "g10", "gap": "Open conflicts shipped, not resolved: Lopal Indonesia phase-2 (62.5 kt 'complete' per trade vs 90 kt 'commissioning' per company); 珩创 Ningxia phase-1 (25 kt vs 30 kt); FEMTC (4.8 kt vs 5 kt, both weak); Dynanonic 450 kt AR total vs 370+80 kt Oct-2025 IR record; Wanhua Shandong project overlaps (1.05 Mt provincial listing vs counted Haiyang 500 kt only)."},
]
can["changelog"].insert(0, {"version": "0.2.0", "date": "2026-07-28", "changes": [
  "Figure-level re-sourcing sprint (filings-first): 40 new sources — FY2025 annual reports and exchange filings for Yuneng, Wanrun, Dynanonic, Lopal, Anda, Fulin, LB Group, 五矿新能, Ronbay, Yuntianhua; exchange announcements for Pulead/Taifeng, Terui, Ronbay Korea, Lopal Batang; company releases for IBU-tec. All corrections are append-only supersession chains — 14 seed claims superseded, none deleted.",
  "Yuneng counted at last: 994,500 t/y FY2025 nameplate (phosphate-family, unsplit) + 70 kt construction + filed 2025 sales 1,137,085 t. Resolves g01.",
  "Corrections: Anda un-bundled (150 kt LFP + 150 kt FePO4, separately); LB Group LFP is 50 kt not 200 kt; CNNC Huayuan's lithium project TERMINATED Jun 2025 (row now dead; only 100 kt FePO4 was ever built); Ronbay Korea 20 kt LMFP is construction, not operating (domestic 10 kt LMFP built); IBU-tec Weimar tonnage unconfirmed and retired from totals; 珩创纳米 entity corrected (Jiangsu, not Zhuhai) with 15 kt LMFP operating; Pulead/Taifeng 185 kt filing found (Xining); Rongtong ~300 kt; Gotion 142 kt; Terui 100 kt design (stale, flagged); Fulin/Dynanonic upgraded to filings; 五矿新能 60 kt held in pipeline until commissioning confirmed.",
  "Pipeline re-based: adds Anda 240 kt, Fulin 525 kt, Lopal Indonesia 310 kt, Gotion 200 kt (construction started), Wanhua Haiyang 500 kt (2032), Rongtong-Reliance India 80 kt, Yuneng 70 kt, Korea/Ningxia phase corrections; removes CNNC 500 kt (terminated) and 珩创's unphased 130 kt.",
  "Precursor (FePO4) documented capacity now tracked: 890 kt/y across CNGR, Anda, Wanrun, CNNC, LB, Yuntianhua.",
  "Bands re-pinned deliberately: lower 2,034,800 · headline 3,479,300 · upper 3,479,300 · pipeline 3,082,250 t/y. Gaps register rewritten (g01–g10)."]})

json.dump(can, open(os.path.join(ROOT, "canonical.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_claims = sum(len(p["claims"]) for p in can["plants"])
n_sup = sum(1 for p in can["plants"] for c in p["claims"] if c.get("superseded_by"))
print("v0.2.0 written | sources:", len(can["sources"]), "| claims:", n_claims, "| superseded:", n_sup)

# ---- vintage rule for v0.2 claims: empty as_of takes the source document's date ----
# (the figure describes status as of that document; run after all claim ops)
_NEW = {s[0] for s in NEW_SOURCES}
for _p in can["plants"]:
    for _c in _p["claims"]:
        if _c.get("src") in _NEW and not _c.get("as_of"):
            _c["as_of"] = next(s for s in can["sources"] if s["id"] == _c["src"])["doc_date"]
