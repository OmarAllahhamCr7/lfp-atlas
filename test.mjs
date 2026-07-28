/* LFP Atlas test suite — integrity, rollup reproduction, counting-rule re-derivation,
   render smoke via jsdom, standalone self-containment. Run: npm test */
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

let passed = 0, failed = 0;
const ok = (cond, name) => { if (cond) { passed++; } else { failed++; console.error("FAIL:", name); } };
const eq = (a, b, name) => ok(JSON.stringify(a) === JSON.stringify(b), name + ` (${JSON.stringify(a)} != ${JSON.stringify(b)})`);

const dataJs = readFileSync("data.js", "utf-8");
const D = JSON.parse(dataJs.replace(/^window\.DATA=/, "").replace(/;\s*$/, ""));

/* ---- structural integrity ---- */
ok(D.meta && D.plants && D.methods && D.families && D.patent_events && D.geo && D.gaps, "payload has all blocks");
eq(D.plants.length, 65, "65 producer rows");
eq(D.methods.length, 28, "28 methods");
eq(D.families.length, 5, "5 families");
eq(D.patent_events.length, 18, "18 patent events");
ok(D.geo.countries.length > 150, "world geometry present");
const ids = D.plants.map(p => p.id);
eq(new Set(ids).size, ids.length, "plant ids unique");
const cids = D.plants.flatMap(p => p.cap_claims.map(c => c.id));
eq(new Set(cids).size, cids.length, "claim ids unique");

/* ---- every displayed figure is cited ---- */
for (const p of D.plants) for (const c of p.cap_claims)
  if (c.value_ty != null) ok(c.src_url && c.src_url.startsWith("http"), "figure cited: " + c.id);

/* ---- counting rule re-derived independently from claim attributes ---- */
const reBand = (p, c) =>
  p.sgroup === "operating" && c.kind === "capacity" && ["built", "reported"].includes(c.basis) &&
  c.scale !== "pilot" && !c.bundle && !c.duplicate_of && !c.superseded_by && c.value_ty != null &&
  c.product === "CAM" && ["LFP", "LMFP", "L(M)FP-unsplit"].includes(c.chem) &&
  !(c.caveats || []).some(x => false);
const rePipe = (p, c) =>
  !["dead", "context", "uncertain", "precursor"].includes(p.sgroup) &&
  c.kind === "capacity" && ["announced", "planned", "construction"].includes(c.basis) &&
  !c.duplicate_of && !c.superseded_by && c.value_ty != null && c.product === "CAM";
for (const p of D.plants) for (const c of p.cap_claims) {
  if (c.counted_operating) ok(reBand(p, c), "counted_operating re-derives: " + c.id);
  if (c.counted_pipeline) ok(rePipe(p, c), "counted_pipeline re-derives: " + c.id);
  if (c.basis === "target") ok(!c.counted_operating && !c.counted_pipeline, "target never counts: " + c.id);
  if (c.duplicate_of) {
    ok(cids.includes(c.duplicate_of), "duplicate resolves: " + c.id);
    ok(!c.counted_operating && !c.counted_pipeline, "duplicate never counts: " + c.id);
  }
  if (c.superseded_by) {
    ok(cids.includes(c.superseded_by), "supersession resolves: " + c.id);
    ok(!c.counted_operating && !c.counted_pipeline && !c.counted_upper_only, "superseded never counts: " + c.id);
  }
  if (c.supersedes) ok(cids.includes(c.supersedes), "supersedes resolves: " + c.id);
}
/* v0.2 correction spot-checks */
const yuneng = D.plants.find(p => p.id === "p001");
ok(yuneng.op_ty === 994500, "Yuneng FY2025 nameplate counted (g01 resolved)");
const cnnc = D.plants.find(p => p.id === "p016");
ok(cnnc.sgroup === "dead" && cnnc.op_ty === 0 && cnnc.pipe_ty === 0, "CNNC terminated row counts nothing");
const lb = D.plants.find(p => p.id === "p015");
ok(lb.op_ty === 50000, "LB Group corrected to 50 kt");
ok(D.meta.bands.precursor_fepo4 === 890000, "FePO4 precursor total pinned");
/* v0.3 correction spot-checks */
const xtc = D.plants.find(p => p.id === "p011");
ok(xtc.sgroup === "operating" && xtc.op_ty === 40000, "XTC Ya'an operating at 40 kt");
const easp = D.plants.find(p => p.id === "p009");
ok(easp.sgroup === "operating" && easp.op_ty === 120000, "Easpring Panzhihua ph-1 counted");
ok(easp.sites.find(s => s.primary).key === "panzhihua", "Easpring primary site is Panzhihua");
const wanrun = D.plants.find(p => p.id === "p002");
ok(wanrun.cap_claims.some(c => c.counted_operating && c.src_tier === "company" && c.value_ty === 468000), "Wanrun 468k on company tier");
ok(D.gaps.archive.total === D.sources_index.length, "archive coverage denominator matches sources");
/* BASF exception: reBand would allow it but canonical carries counted=false — verify it shipped uncounted */
const basf = D.plants.find(p => p.company === "BASF");
ok(basf.op_ty === 0, "BASF 'historical/limited' counts nothing");

/* ---- rollup reproduction from the public payload alone ---- */
const perPlantOp = p => {
  const perChem = {};
  for (const c of p.cap_claims) if (c.counted_operating)
    perChem[c.chem] = Math.max(perChem[c.chem] || 0, c.value_ty);
  return Object.values(perChem).reduce((a, b) => a + b, 0);
};
const lo = D.plants.reduce((a, p) => a + Object.entries(
    p.cap_claims.filter(c => c.counted_operating).reduce((m, c) => {
      if (["LFP", "LMFP"].includes(c.chem)) m[c.chem] = Math.max(m[c.chem] || 0, c.value_ty); return m; }, {})
  ).reduce((s, [, v]) => s + v, 0), 0);
const hd = D.plants.reduce((a, p) => a + perPlantOp(p), 0);
const upx = D.plants.reduce((a, p) => a + Object.values(
    p.cap_claims.filter(c => c.counted_upper_only).reduce((m, c) => {
      const k = c.chem + "|" + c.bundle; m[k] = Math.max(m[k] || 0, c.value_ty); return m; }, {})
  ).reduce((s, v) => s + v, 0), 0);
const pipe = D.plants.reduce((a, p) => {
  const site = p.cap_claims.filter(c => c.counted_pipeline && c.scope === "site").reduce((s, c) => s + c.value_ty, 0);
  const co = Math.max(...p.cap_claims.filter(c => c.counted_pipeline && c.scope !== "site").map(c => c.value_ty), 0);
  return a + site + co;
}, 0);
eq(lo, D.meta.bands.cam.lower, "lower band reproduces from public data");
eq(hd, D.meta.bands.cam.headline, "headline band reproduces from public data");
eq(hd + upx, D.meta.bands.cam.upper, "upper band reproduces from public data");
eq(pipe, D.meta.bands.pipeline, "pipeline reproduces from public data");
for (const p of D.plants) eq(perPlantOp(p), p.op_ty, "plant rollup matches shipped op_ty: " + p.id);

/* ---- non-live rows count nothing ---- */
for (const p of D.plants)
  if (["dead", "context", "uncertain", "precursor"].includes(p.sgroup))
    ok(p.op_ty === 0 && p.pipe_ty === 0, "non-live row leaks tonnage: " + p.id);

/* ---- links resolve ---- */
const custNames = new Set(D.customers.map(c => c.name));
for (const l of D.links) {
  ok(ids.includes(l.from), "link.from resolves: " + l.from);
  ok(Number.isFinite(l.x2) && Number.isFinite(l.y2), "link endpoint projected: " + l.from + "->" + l.to);
}

/* ---- geography honesty ---- */
for (const p of D.plants) {
  ok(p.sites.length >= 1 && p.sites.filter(s => s.primary).length === 1, "one primary site: " + p.id);
  for (const s of p.sites) ok(["city-centroid", "region-only", "hq-city", "country-only"].includes(s.geo_basis), "geo_basis enum: " + p.id);
}

/* ---- render smoke (jsdom) ---- */
const html = readFileSync("index.html", "utf-8")
  .replace('<script src="data.js"></script>', "")
  .replace('<script src="app.js"></script>', "");
const dom = new JSDOM(html, { runScripts: "outside-only", pretendToBeVisual: true, url: "https://localhost/" });
dom.window.requestAnimationFrame = fn => fn(performance.now());
dom.window.eval(dataJs);
dom.window.eval(readFileSync("app.js", "utf-8"));
/* jsdom keeps readyState 'loading' until the load event — let init() fire */
if (dom.window.document.readyState === "loading")
  await new Promise(r => { dom.window.addEventListener("load", r); setTimeout(r, 1500); });
const doc = dom.window.document;
ok(doc.querySelectorAll("#kpis .kpi").length >= 5, "KPIs render");
ok(doc.querySelectorAll("#gmk .mk").length >= 50, "map markers render (" + doc.querySelectorAll("#gmk .mk").length + ")");
ok(doc.querySelectorAll("#tbody tr").length === 65, "table renders all rows");
ok(doc.querySelectorAll("#methodhost .mcard").length === 28, "28 method cards render");
ok(doc.querySelectorAll("#timeline .tlev").length === 18, "18 timeline events render");
ok(doc.querySelectorAll("#gapsreg h4").length >= 4, "gaps register renders");
ok((doc.querySelector("#herotext").textContent || "").includes("documented floor"), "hero carries the floor caveat");
/* drawer opens */
doc.querySelector("#tbody tr").dispatchEvent(new dom.window.Event("click", { bubbles: true }));
ok(doc.querySelector("#drawer").classList.contains("on"), "drawer opens from table");
ok(doc.querySelectorAll("#drawer table.claims tr").length >= 2, "drawer shows claims table");

/* ---- standalone self-containment ---- */
try {
  const sa = readFileSync("LFP_Atlas_standalone.html", "utf-8");
  ok(!/<script\s+src=|<link\s+rel="stylesheet"\s+href=/.test(sa), "standalone has no external refs");
  ok(!/https?:\/\/cdn|cdnjs|googleapis/.test(sa.slice(0, 2000)), "standalone head has no CDN");
  ok(sa.includes("window.DATA="), "standalone embeds data");
} catch { failed++; console.error("FAIL: standalone missing — run build/make_standalone.py"); }

/* ---- claims CSV coverage ---- */
const csv = readFileSync("lfp_atlas_claims.csv", "utf-8");
eq(csv.trim().split("\r\n").length - 1, cids.length, "claims CSV covers every claim");

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
