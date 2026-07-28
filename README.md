# LFP Atlas

Every documented producer of LFP / LMFP cathode active material (CAM) — operating, announced,
pilot, precursor-only, exited, or a cell maker with in-house CAM — with the synthesis route,
the patent history that shaped the industry, capacity claims and the sourcing shown.
Sibling of **NMC Atlas**; the two are schema-compatible by design and fold into **Cathodes ATLAS**.

**65 producer rows · 28 synthesis routes in 5 families · 18 patent & licensing events ·
138 discrete claims (103 with figures, 20 superseded) · 169 sources · v0.3.0 ·
dataset date 28 July 2026.**

Headline: **3.53 Mt/y of operating nameplate documented at producer level** (lower bound 1.97 —
chemistry stated outright), a further **3.26 Mt/y announced or under construction**, and
**0.89 Mt/y of documented FePO₄ precursor** — all kept strictly apart. The bands remain a
**documented floor, not a market estimate**; the main uncertainty is the lower–headline gap:
1.56 Mt/y (Yuneng 994.5k, Dynanonic 450k, Easpring 120k) is filed as phosphate-family totals
with no LFP/LMFP split. China makes ~95–98% of global LFP CAM; ~90% of tonnage moves through
one route (carbothermal reduction fed by a precipitated FePO₄ precursor).

---

## Editions

**v0.1 (seeded)** restructured one compiled research workbook
(`build/seed/LFP_LMFP_Synthesis_Methods_and_Producers.xlsx`, 19 July 2026) into the NMC Atlas
claim architecture, shipping its weaknesses openly in the gaps register.

**v0.2 (re-sourced)** upgraded the top-tonnage rows to filings and company documents
(`build/upgrade_v0_2.py` is the full provenance): FY2025 annual reports for Yuneng, Wanrun,
Dynanonic, Lopal, Fulin, LB Group, Ronbay, Yuntianhua, 五矿新能; exchange announcements for
Anda, Pulead/Taifeng, Terui, Ronbay-Korea, Lopal-Batang; company releases for IBU-tec. Every
correction is an **append-only supersession chain** — 16 seed claims superseded, none deleted.
Notable corrections: Yuneng counted at last (994,500 t/y, resolving g01); Anda un-bundled
(150 kt LFP + 150 kt FePO₄); LB Group is 50 kt not 200 kt; CNNC Huayuan's lithium project was
TERMINATED in June 2025 (LFP stage never built); Ronbay's Korea LMFP is construction, not
operating; IBU-tec's Weimar tonnage is undisclosed and was retired from the totals. What still
rests on trade tier (Wanrun 468k, Rongtong 300k, Gotion 142k) and what is stale (Terui 2023,
Pulead 2023) is flagged in the register (g07–g08).

**v0.3 (verified + geocoded)** added second sources for the trade-tier counted figures
(Wanrun 468 kt now company-confirmed via a May-2026 exchange-disclosed IR record; Lopal's
website 310 kt retired in favour of its HKEX prospectus designed capacity, 200,670 t/y),
two status corrections filings forced (XTC's Ya'an base is OPERATING at 40 kt with a 40 kt
LFMP line approved for 2028; Easpring's Panzhihua first phase, 120 kt, is built and
producing), a documented-city geocoding pass (20 rows re-sited from province/country
centroids), the Wanrun–CATL ~1.32 Mt five-year supply agreement as a quantified link, and
`build/archive_sources.py` — the SHA-256 snapshot archiver (run it on your machine; `--check`
detects silent edits; the gaps register computes coverage from the canonical).

## Two ways to run it

**Standalone** — `LFP_Atlas_standalone.html`. One file, ~0.5 MB. Double-click it. No server,
no network, no CDN, no tracking. This is the one to send.

**Project** — `index.html`. The maintainable version (data loads via `data.js`, so `file://`
works). Edit `build/canonical.json` and rebuild — never edit the generated files by hand.

## Pipeline (one source of truth)

```
build/seed_from_excel.py         one-time provenance: workbook -> canonical.json (already run)
build/canonical.json             THE canonical file: plants, claims, sources, methods,
    |                            families, patent events, references, gap log, changelog
    v
python build/build_v1.py         regenerates, with build-failing assertions:
    ├─ data.json / data.js       public payload (per-claim citations; caveat model; gaps register)
    └─ lfp_atlas_claims.csv      every claim row, flat
python build/archive_sources.py  SHA-256 source snapshots (YOUR machine — downloads the cited pages)
python build/verify_archive.py   integrity pass: complete vs proxy/partial (block pages, stubs,
                                 fake PDFs) — only clean captures count as coverage
python build/make_standalone.py  inlines styles+data+app into LFP_Atlas_standalone.html
npm install && npm test          the jsdom suite: integrity, rollup reproduction, independent
                                 re-derivation of the counting rule, render smoke, self-containment
python build/release_check.py    the one-command release gate
```

Python needs `openpyxl` only to re-run the seed script. `build/geo_projected.json` is the
pre-projected Natural Earth geometry (shared with NMC Atlas); a rebuild never regenerates it.

**Claim model.** Every figure is a discrete claim with a kind (capacity / shipments / output /
cumulative / rate / share / qualitative), a basis (built, reported, construction, announced,
planned, target, historic, cancelled), a scope (site / company / group), a chemistry tag
(LFP / LMFP / L(M)FP-unsplit / cathode-unsplit / FePO₄ / not-LFP), a source and a note. Floors
(">"), ceilings ("up to"), ranges (lower bound recorded), bundles and duplicates are flagged and
handled by the counting rule, never silently normalised.

**The olivine rule (seed edition).** Only operating plants at commercial scale count, only
capacity claims, only basis built/reported, no bundles, no duplicates. Lower = chemistry stated
outright; headline = + L(M)FP-unsplit; upper = + bundles and unsplit-cathode figures. Announced /
planned / construction claims form a separate pipeline total; **targets count toward nothing**.
Shipments and output are context. The build fails if published totals stop being reproducible
from `data.json` alone (and the node suite re-derives every counted flag from claim attributes).

**The rule this was built on** (inherited from NMC Atlas): no figure is interpolated, averaged,
or unit-converted to make a chart look complete. Where a number does not exist, the interface
shows a gap and says so. Altmin's "~100 kg/day" ships as a rate in native units; Aleees' "~30 kt
cumulative" ships as cumulative; neither enters any total.

## Roadmap

- [x] v0.2 — figure-level re-sourcing of the top-tonnage rows (filings-first); supersession
      chains; vintages on re-sourced claims; gaps register rewritten (g01–g10)
- [x] v0.3 — second sources for trade-tier counted figures (Wanrun resolved; Rongtong/Gotion
      conflict-flagged); XTC + Easpring status corrections; documented-city geocoding pass;
      `archive_sources.py` shipped (RUN IT LOCALLY to populate the snapshot archive)
- [ ] v0.4 — run the archiver + commit snapshots; supply links with tonnage; LMFP
      absolute-base resolution; charts pane; long-tail re-sourcing (Taiwan, Japan, Western
      announced projects); Rongtong/Gotion second-source retry after their next disclosures
- [ ] Cathodes ATLAS — merge with NMC Atlas (the OOP band engine already treats chemistry
      rules as configuration; this repo's canonical schema is compatible by construction)

## Licence / attribution

Dataset and site: CC-BY 4.0, attribution "LFP Atlas" + version. Per-figure citations in the
drawer. World geometry: Natural Earth (public domain). No third-party code ships in the bundle.
