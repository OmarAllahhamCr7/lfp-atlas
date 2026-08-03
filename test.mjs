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
eq(D.meta.version, "0.3.5", "dataset version");
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
  if (c.value_ty != null) {
    ok(c.src_url && c.src_url.startsWith("http"), "figure cited: " + c.id);
    ok(c.sources?.length >= 1, "figure has source bundle: " + c.id);
    ok(c.sources.every(s => s.url?.startsWith("http")), "source bundle URLs valid: " + c.id);
  }

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
/* v0.3.1 Morocco status correction */
const morocco = D.plants.find(p => p.id === "p065");
const moroccoOld = morocco.cap_claims.find(c => c.id === "p065.c1");
const moroccoCurrent = morocco.cap_claims.find(c => c.id === "p065.c3");
ok(morocco.sgroup === "announced", "Morocco project is announced, not construction");
ok(moroccoOld.superseded_by === "p065.c3" && !moroccoOld.counted_pipeline, "old Morocco construction claim is superseded");
ok(moroccoCurrent.basis === "announced" && moroccoCurrent.counted_pipeline, "corrected Morocco claim remains in pipeline");
ok(moroccoCurrent.target_date === "2026" && moroccoCurrent.note.includes("unconfirmed"), "Morocco 2026 target is qualified");
/* v0.3.2 Rongtong chemistry-scope correction */
const rongtong = D.plants.find(p => p.id === "p007");
const rongtongOld = rongtong.cap_claims.find(c => c.id === "p007.c2");
const rongtongUnsplit = rongtong.cap_claims.find(c => c.id === "p007.c4");
ok(rongtongOld.superseded_by === "p007.c4" && !rongtongOld.counted_operating, "old Rongtong LFP tag is superseded");
ok(rongtongUnsplit.chem === "L(M)FP-unsplit", "historical Rongtong aggregate preserves its corrected chemistry scope");
/* v0.3.3 Gotion attribution + multi-source correction */
const gotion = D.plants.find(p => p.id === "p012");
const gotionOld = gotion.cap_claims.find(c => c.id === "p012.c3");
const gotionCurrent = gotion.cap_claims.find(c => c.id === "p012.c5");
ok(gotionOld.superseded_by === "p012.c5" && !gotionOld.counted_operating, "old Gotion attribution is superseded");
ok(gotionCurrent.counted_operating && gotionCurrent.value_ty === 142000, "Gotion 142 kt remains counted");
eq(gotionCurrent.components.map(c => c.value_ty), [42000, 100000], "Gotion component sum disclosed");
eq(gotionCurrent.sources.map(s => s.id), [
  "s_gotion_142k",
  "s_gotion_42k_recruitment",
  "s_gotion_42k_field_visit",
  "s_gotion_kehong_100k",
], "Gotion source bundle disclosed");
eq(gotionCurrent.corroboration_sources, ["s_gotion_142k"], "Gotion aggregate corroboration is explicit");
ok(gotionCurrent.public_confidence === "Medium", "Gotion public confidence improves to Medium");
/* v0.3.4 weak-evidence hardening */
const pulead = D.plants.find(p => p.id === "p008");
const puleadCurrent = pulead.cap_claims.find(c => c.id === "p008.c2");
ok(puleadCurrent.evidence_method === "durable-nameplate", "Pulead uses durable-nameplate evidence method");
eq(puleadCurrent.components.map(c => c.value_ty), [25000, 160000], "Pulead exact component sum disclosed");
eq(puleadCurrent.status_sources, ["s_rt_top10exit", "s_rt_h1_26"], "Pulead current-status evidence disclosed");
ok(
  puleadCurrent.sources.filter(s => s.role?.includes("does not restate capacity")).length === 2,
  "Pulead current rankings are not presented as exact-capacity evidence",
);
const terui = D.plants.find(p => p.id === "p013");
const teruiCurrent = terui.cap_claims.find(c => c.id === "p013.c3");
ok(teruiCurrent.evidence_method === "component-sum", "Terui uses component-sum evidence method");
eq(teruiCurrent.components.map(c => c.value_ty), [40000, 60000], "Terui 40 kt + 60 kt commissioning chain disclosed");
eq(teruiCurrent.sources.map(s => s.id), [
  "s_terui_reply",
  "s_terui_termination",
  "s_terui_zhongxian_design_2021",
  "s_terui_zhongxian_env_2025",
  "s_terui_zhongxian_jobs_2025",
  "s_terui_zhongxian_innovation_2026",
], "Terui historical evidence and current context are disclosed");
ok(terui.sites.find(s => s.primary).key === "zhongxian", "Terui primary project site is Zhongxian");
/* v0.3.5 Rongtong site-floor correction */
const rongtongCurrent = rongtong.cap_claims.find(c => c.id === "p007.c5");
const rongtongPipeline = rongtong.cap_claims.find(c => c.id === "p007.c6");
const rongtongConflict = rongtong.cap_claims.find(c => c.id === "p007.c7");
ok(rongtongUnsplit.superseded_by === "p007.c5" && !rongtongUnsplit.counted_operating, "opaque Rongtong aggregate is superseded");
ok(rongtongCurrent.evidence_method === "site-floor" && rongtongCurrent.counted_operating, "Rongtong uses a counted site floor");
ok(rongtongCurrent.chem === "LFP" && rongtong.op_lower === 180000 && rongtong.op_ty === 180000, "Rongtong floor counts in chemistry-stated scope");
eq(rongtongCurrent.components.map(c => c.value_ty), [100000, 80000], "Rongtong site components sum to 180 kt");
eq(rongtongCurrent.components[0].calculation, {
  operation: "difference",
  minuend_ty: 200000,
  subtrahend_ty: 100000,
}, "Rongtong Jiangyou arithmetic is machine-readable");
eq(rongtongCurrent.status_sources, ["s_rt_jy_resume_2026", "s_rt_nj_digital_2025"], "Rongtong fresh site-status evidence disclosed");
eq(rongtongCurrent.conflict_sources, ["s_rt_jy_formed_150k", "s_rt_nj_200k_eia"], "Rongtong conflicts are explicit and excluded");
ok(rongtongPipeline.counted_pipeline && rongtong.pipe_ty === 180000, "Rongtong Jiangyou and India pipeline additions count separately");
ok(!rongtongConflict.counted_operating && rongtongConflict.value_ty === 150000, "Rongtong 150 kt conflict remains visible but uncounted");
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
doc.querySelector('#tbody tr[data-id="p012"]').dispatchEvent(new dom.window.Event("click", { bubbles: true }));
eq(
  [...doc.querySelectorAll('#drawer tr[data-claim-id="p012.c5"] .srcitem')].map(el => el.dataset.sourceId),
  gotionCurrent.sources.map(s => s.id),
  "Gotion drawer exposes every component source",
);
doc.querySelector('#tbody tr[data-id="p007"]').dispatchEvent(new dom.window.Event("click", { bubbles: true }));
eq(
  [...doc.querySelectorAll('#drawer tr[data-claim-id="p007.c5"] .srcrole')].map(el => el.textContent),
  rongtongCurrent.sources.map(s => s.role),
  "Rongtong drawer exposes every source role",
);

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
