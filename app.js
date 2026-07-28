/* LFP Atlas — client-side data layer + views. No runtime dependencies.
   Sibling of NMC Atlas; same machinery, olivine-specific views. */
(function () {
"use strict";
const D = window.DATA;
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const NS = "http://www.w3.org/2000/svg";
const el = (t, a) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = n => n >= 1000 ? (n / 1000).toLocaleString(undefined, { maximumFractionDigits: 1 }) + "k" : String(n);

const SC = { operating: "#3fb950", building: "#d29922", announced: "#58a6ff", pilot: "#2ea043",
             uncertain: "#8b949e", dead: "#6e7681", precursor: "#7c5cff", context: "#4b5563" };
const SLBL = { operating: "Operating", building: "Under construction", announced: "Announced",
               pilot: "Pilot / demo", uncertain: "Uncertain / limited", dead: "Exited / cancelled",
               precursor: "Precursor only", context: "Context (not a CAM maker)" };
const CHEMLBL = { "LFP": "LFP", "LMFP": "LMFP-led", "L(M)FP-unsplit": "L(M)FP unsplit",
                  "FePO4": "FePO₄ precursor", "not-LFP": "Not LFP", "cathode-unsplit": "Cathode unsplit" };
const FAMC = { A: "#4da3ff", B: "#d29922", C: "#3fb950", D: "#e3b341", E: "#b57bff" };
const LINKC = { q: "#4da3ff", lic: "#b57bff", n: "#43536b", x: "#f85149" };
const LINKLBL = { q: "customer / offtake", lic: "process license", n: "JV / partnership", x: "terminated / dead" };

const LIC_SET = new Set();
D.plants.forEach(p => (p.links || []).forEach(l => { if (l.k === "lic" || l.k === "x") { LIC_SET.add(p.id); LIC_SET.add(l.to); } }));

/* ---------------- state ---------------- */
const S = { q: "", status: new Set(), country: new Set(), route: new Set(), chem: new Set(),
            cap: false, pipe: false, lmfp: false, lic: false,
            sort: "op", dir: -1, sel: null, focus: null, region: "World" };

function filtered() {
  const q = S.q.toLowerCase().trim();
  return D.plants.filter(p => {
    if (S.status.size && !S.status.has(p.sgroup)) return false;
    if (S.country.size && !S.country.has(p.country)) return false;
    if (S.route.size && !S.route.has(p.route_family)) return false;
    if (S.chem.size && !S.chem.has(p.chem_focus)) return false;
    if (S.cap && !p.op_ty) return false;
    if (S.pipe && !p.pipe_ty) return false;
    if (S.lmfp && !(/LMFP/i.test(p.makes) || p.chem_focus === "LMFP")) return false;
    if (S.lic && !(LIC_SET.has(p.id) || LIC_SET.has(p.company))) return false;
    if (q) {
      const hay = (p.company + " " + p.country + " " + p.makes + " " + p.method + " " + p.route_family + " " +
                   p.capacity_text + " " + p.notes + " " + p.status_raw).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

/* ---------------- KPIs ---------------- */
function kpis(F) {
  const op = F.filter(p => p.sgroup === "operating").length;
  const cam = F.reduce((a, p) => a + p.op_ty, 0), pipe = F.reduce((a, p) => a + p.pipe_ty, 0);
  const cs = new Set(F.filter(p => p.sgroup !== "context").map(p => p.country.split(" (")[0])).size;
  const B = D.meta.bands;
  const box = (v, l, cls) => `<div class="kpi ${cls || ""}"><b>${v}</b><span>${l}</span></div>`;
  const boxT = (v, l, t, cls) => `<div class="kpi kpit ${cls || ""}" data-scope="${esc(t)}"><b>${v}</b><span>${l}</span></div>`;
  const kh = $("#kpis"); kh.onclick = e => {
    const k = e.target.closest(".kpit"); if (!k) return;
    tip(e, `<div class="s">${esc(k.dataset.scope)}</div>`); clearTimeout(tip._t); tip._t = setTimeout(hideTip, 5000);
  };
  kh.innerHTML =
    box(F.length, "producer rows") + box(op, "operating") + box(cs, "countries") +
    boxT(fmt(cam) + " t/y", "operating · counted", "Counted operating nameplate in the current filter. All-plants bands: lower " + fmt(B.cam.lower) + " · headline " + fmt(B.cam.headline) + " · upper " + fmt(B.cam.upper) + " t/y. A documented FLOOR, not a market estimate — see Methodology.") +
    boxT(fmt(pipe) + " t/y", "pipeline · filtered", "Announced / planned / under-construction capacity in the current filter (targets never count). All plants: " + fmt(B.pipeline) + " t/y.", "pipe") +
    boxT("~95–98%", "made in China", D.meta.market_context.note, "gold");
}

/* ---------------- filter rail ---------------- */
function counts(key) {
  const m = new Map();
  D.plants.forEach(p => { const v = key(p); m.set(v, (m.get(v) || 0) + 1); });
  return m;
}
function chips(host, m, set, colour, lbl) {
  const h = $(host); h.innerHTML = "";
  Array.from(m.entries()).sort((a, b) => b[1] - a[1]).forEach(([k, n]) => {
    const c = document.createElement("div");
    c.className = "chip" + (set.has(k) ? " on" : "");
    c.innerHTML = (colour ? `<i class="dot" style="background:${colour(k)}"></i>` : "") +
      `${esc((lbl || (x => x))(k))}<span class="n">${n}</span>`;
    c.onclick = () => { set.has(k) ? set.delete(k) : set.add(k); render(); };
    h.appendChild(c);
  });
}
function rail() {
  chips("#f-status", counts(p => p.sgroup), S.status, k => SC[k], k => SLBL[k]);
  chips("#f-country", counts(p => p.country.split(" (")[0]), S.country);
  chips("#f-route", counts(p => p.route_family), S.route);
  chips("#f-chem", counts(p => p.chem_focus), S.chem, null, k => CHEMLBL[k] || k);
}

/* ---------------- map ---------------- */
let vb = { x: 0, y: 0, w: 1000, h: 500 }, drag = null;
function drawMapBase() {
  const svg = $("#map"); svg.innerHTML = "";
  const g = el("g", { id: "gworld" });
  g.appendChild(el("path", { d: D.geo.sphere, class: "sph" }));
  g.appendChild(el("path", { d: D.geo.graticule, class: "grat" }));
  D.geo.countries.forEach(c => {
    const p = el("path", { d: c.d, class: "land" + (c.hl ? " hl" : "") });
    p.addEventListener("mousemove", e => tip(e, `<b>${esc(c.n)}</b>`));
    p.addEventListener("mouseleave", hideTip);
    g.appendChild(p);
  });
  g.appendChild(el("path", { d: D.geo.borders, class: "bord" }));
  g.appendChild(el("g", { id: "garcs" }));
  g.appendChild(el("g", { id: "gcust" }));
  g.appendChild(el("g", { id: "gmk" }));
  g.appendChild(el("g", { id: "glab" }));
  svg.appendChild(g);
  $("#mleg").innerHTML = Object.keys(SC).filter(k => k !== "context").map(k =>
    `<div class="row"><i style="background:${SC[k]}"></i>${SLBL[k]}</div>`).join("") +
    `<div class="row"><i class="hollow"></i>pipeline (hollow, dashed)</div>` +
    `<div class="row" style="margin-top:5px;color:#64748b">filled area ∝ counted operating t/y</div>`;
  const sl = [300000, 100000, 20000].map(v =>
    `<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px">
      <svg width="${2 * radPx(v) + 4}" height="${2 * radPx(v) + 4}"><circle cx="${radPx(v) + 2}" cy="${radPx(v) + 2}" r="${radPx(v)}" fill="#4da3ff" opacity=".55" stroke="#0d1117"/></svg>
      <span style="font-size:10.5px;color:#9fb0c4">${fmt(v)} t/y</span></span>`).join("");
  $("#sizeleg").innerHTML = sl +
    `<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px">
      <svg width="18" height="18"><circle cx="9" cy="9" r="6" fill="none" stroke="#58a6ff" stroke-width="1.4" stroke-dasharray="3 2"/></svg>
      <span style="font-size:10.5px;color:#9fb0c4">pipeline</span></span>
    <span style="display:inline-flex;align-items:center;gap:6px">
      <svg width="9" height="9"><circle cx="4.5" cy="4.5" r="3" fill="#6e7681" stroke="#0d1117"/></svg>
      <span style="font-size:10.5px;color:#64748b">no counted figure</span></span>`;
}
const radPx = t => t > 0 ? Math.max(3.4, Math.min(15, Math.sqrt(t) / 42)) : 3;
const scale = () => vb.w / 1000;

function layout(F) {
  const k = scale(), spider = $("#t-spider").checked && k < 0.45;
  const groups = new Map();
  D.plants.forEach(p => {
    if (p.x == null || p.no_marker) return;
    const key = p.x.toFixed(1) + "," + p.y.toFixed(1);
    (groups.get(key) || groups.set(key, []).get(key)).push(p);
  });
  const pos = new Map();
  groups.forEach(g => {
    if (g.length === 1 || !spider) { g.forEach(p => pos.set(p.id, { x: p.x, y: p.y, off: false })); return; }
    const r = 13 * k, step = (Math.PI * 2) / g.length;
    g.forEach((p, i) => {
      const a = -Math.PI / 2 + i * step;
      pos.set(p.id, { x: p.x + Math.cos(a) * r, y: p.y + Math.sin(a) * r, off: true, ox: p.x, oy: p.y });
    });
  });
  return pos;
}

const focusName = () => { const p = D.plants.find(x => x.id === S.focus); return p ? p.company : null; };

function drawMarkers(F) {
  const ids = new Set(F.map(p => p.id));
  const gm = $("#gmk"); gm.innerHTML = "";
  const arcs = $("#garcs"); arcs.innerHTML = "";
  const gc = $("#gcust"); gc.innerHTML = "";
  const k = scale();
  const pos = layout(F);
  const showLab = $("#t-labels").checked || k < 0.30;
  const showFlow = $("#t-flow").checked, showLic = $("#t-liclinks").checked;

  D.links.forEach(l => {
    if (!ids.has(l.from)) return;
    if ((l.k === "lic" || l.k === "x") ? !showLic : !showFlow) return;
    const lit = !S.focus || l.from === S.focus || l.to === focusName();
    const a = pos.get(l.from) || { x: l.x1, y: l.y1 };
    const dx = l.x2 - a.x, dy = l.y2 - a.y, dr = Math.sqrt(dx * dx + dy * dy) * 1.7;
    if (!dr) return;
    const p = el("path", {
      d: `M${a.x},${a.y}A${dr},${dr} 0 0,1 ${l.x2},${l.y2}`, class: "arc",
      stroke: LINKC[l.k], "stroke-width": 0.7 * k,
      opacity: S.focus && !lit ? .05 : (l.k === "n" ? .45 : .72)
    });
    if (l.k === "x") p.setAttribute("stroke-dasharray", (3 * k) + " " + (2.5 * k));
    if (l.k === "lic") p.setAttribute("stroke-dasharray", (5 * k) + " " + (2 * k));
    arcs.appendChild(p);
  });

  if ($("#t-cust-dots").checked) {
    const active = new Set(D.links.filter(l => ids.has(l.from)).map(l => l.to));
    D.customers.forEach(c => {
      if (!active.has(c.name)) return;
      const n = D.links.filter(l => l.to === c.name && ids.has(l.from)).length;
      const lit = !S.focus || c.name === focusName() || D.links.some(l => l.from === S.focus && l.to === c.name);
      const g = el("g", { class: "mk", opacity: lit ? 1 : .12 });
      g.appendChild(el("circle", { cx: c.x, cy: c.y, r: (n >= 4 ? 4 : 2.4) * k, fill: "#e3b341", opacity: .9, "stroke-width": .9 * k }));
      g.addEventListener("mousemove", e => tip(e, `<b>${esc(c.name)}</b><div class="s">link destination · ${n} in view</div>`));
      g.addEventListener("mouseleave", hideTip);
      gc.appendChild(g);
    });
  }

  D.plants.forEach(p => {
    if (p.x == null || p.no_marker) return;
    const on = ids.has(p.id);
    const q = pos.get(p.id);
    const lit = !S.focus || p.id === S.focus || D.links.some(l => l.from === S.focus && l.to === p.company);
    const g = el("g", { class: "mk" + (on && lit ? "" : " dim") + (S.sel === p.id ? " sel" : "") });
    if (q.off) g.appendChild(el("line", { x1: q.ox, y1: q.oy, x2: q.x, y2: q.y, class: "leader", "stroke-width": .5 * k }));
    if (p.pipe_ty) {
      g.appendChild(el("circle", { cx: q.x, cy: q.y, r: radPx(p.pipe_ty) * k, fill: "none",
        stroke: SC[p.sgroup], "stroke-width": 1.1 * k, "stroke-dasharray": (3 * k) + " " + (2 * k), opacity: .85 }));
    }
    g.appendChild(el("circle", { cx: q.x, cy: q.y, r: radPx(p.op_ty) * k, fill: SC[p.sgroup],
      opacity: p.op_ty ? .82 : .95, "stroke-width": .9 * k }));
    if (on) {
      const gb = (p.sites.find(s => s.primary) || {}).geo_basis || "";
      g.addEventListener("mousemove", e => tip(e,
        `<b>${esc(p.company)}</b><div class="s">${esc(p.country)}</div>
         <div class="s" style="margin-top:3px;color:${SC[p.sgroup]}">${esc(p.status_raw || p.status)}</div>
         ${p.op_ty ? `<div class="s">${fmt(p.op_ty)} t/y counted operating</div>` : `<div class="s" style="color:#e3b341">no counted operating figure</div>`}
         ${p.pipe_ty ? `<div class="s" style="color:#58a6ff">${fmt(p.pipe_ty)} t/y pipeline</div>` : ""}
         <div class="s" style="color:#64748b">location precision: ${esc(gb)}</div>
         <div class="s" style="margin-top:3px;color:#4da3ff">click: evidence · shift+click: isolate links</div>`));
      g.addEventListener("mouseleave", hideTip);
      g.addEventListener("click", e => {
        if (e.shiftKey) { S.focus = S.focus === p.id ? null : p.id; focusBar(); drawMarkers(filtered()); }
        else openDrawer(p);
      });
    }
    gm.appendChild(g);
  });

  const gl = $("#glab"); gl.innerHTML = "";
  if (showLab) {
    const placed = [];
    const fits = (x, y, w, h) => {
      const b = { x1: x - w / 2, y1: y - h, x2: x + w / 2, y2: y };
      if (b.x2 < vb.x || b.x1 > vb.x + vb.w || b.y2 < vb.y || b.y1 > vb.y + vb.h) return false;
      for (const o of placed) if (b.x1 < o.x2 && b.x2 > o.x1 && b.y1 < o.y2 && b.y2 > o.y1) return false;
      placed.push(b); return true;
    };
    const cand = [];
    F.forEach(p => {
      if (p.x == null || p.no_marker) return;
      const q = pos.get(p.id); if (!q) return;
      if (S.focus && !(p.id === S.focus || D.links.some(l => l.from === S.focus && l.to === p.company))) return;
      const t = p.op_ty + p.pipe_ty;
      cand.push({ pri: 1e6 + t, x: q.x, y: q.y - (radPx(Math.max(p.op_ty, p.pipe_ty)) + 3.5) * k, fs: 9 * k, fill: "#c8d6e6",
                  s: p.company.split("(")[0].split(" - ")[0].split("/")[0].trim().slice(0, 24) });
    });
    cand.sort((a, b) => b.pri - a.pri).forEach(c => {
      if (!fits(c.x, c.y, c.s.length * c.fs * 0.55, c.fs * 1.2)) return;
      const t = el("text", { x: c.x, y: c.y, class: "mlabel", "text-anchor": "middle", fill: c.fill });
      t.setAttribute("style", "font-size:" + c.fs + "px;stroke-width:" + (2.4 * k) + "px");
      t.textContent = c.s; gl.appendChild(t);
    });
  }
  supplyPanel(F);
}
function focusBar() {
  const b = $("#focusbar"), p = D.plants.find(x => x.id === S.focus);
  if (!p) { b.hidden = true; return; }
  b.hidden = false;
  const n = D.links.filter(l => l.from === p.id).length;
  $("#focustxt").innerHTML = `Isolated: <b>${esc(p.company.split("(")[0].trim())}</b> · ${n} named link${n === 1 ? "" : "s"}`;
}

/* ---------------- in-view panel ---------------- */
const inView = p => p.x != null && !p.no_marker && p.x >= vb.x && p.x <= vb.x + vb.w && p.y >= vb.y && p.y <= vb.y + vb.h;
function supplyPanel(F) {
  const V = F.filter(inView);
  const vids = new Set(V.map(p => p.id));
  const cam = V.reduce((a, p) => a + p.op_ty, 0), pipe = V.reduce((a, p) => a + p.pipe_ty, 0);
  const op = V.filter(p => p.sgroup === "operating").length;
  const L = D.links.filter(l => vids.has(l.from));
  const dest = new Map();
  L.forEach(l => { const d = dest.get(l.to) || { n: 0, k: l.k }; d.n++; dest.set(l.to, d); });
  const top = Array.from(dest.entries()).sort((a, b) => b[1].n - a[1].n).slice(0, 8);
  const sm = (v, l, c) => `<div class="sm ${c || ""}"><b>${v}</b><span>${l}</span></div>`;
  $("#supply").innerHTML = `
    <h3>In view</h3>
    <div class="rgn">${esc(S.region)}${V.length !== F.length ? ` · ${V.length} of ${F.length} filtered` : ""}</div>
    <div class="smetrics">
      ${sm(V.length, "producers in view")}
      ${sm(op, "operating")}
      ${sm(fmt(cam), "t/y counted operating", "a")}
      ${sm(fmt(pipe), "t/y pipeline", "pp")}
    </div>
    ${!L.length ? `<div class="sub" style="font-size:10.5px;color:#64748b">No named links originate from the producers in this view.</div>` : `
      <div class="sh">Link destinations</div>
      ${top.map(([n, d]) => `
        <div class="dest"><span class="bar" style="width:${Math.max(6, d.n * 14)}px;background:${LINKC[d.k]}"></span>
          <span class="nm">${esc(n)}</span><span class="v">${d.n}×</span></div>`).join("")}`}
    <div class="sh">Producers in view</div>
    <div class="slist">${V.sort((a, b) => (b.op_ty + b.pipe_ty) - (a.op_ty + a.pipe_ty)).map(p => `
      <div class="sitem" data-id="${p.id}">
        ${esc(p.company.split("(")[0].split(" - ")[0].trim())}
        <div class="c">${esc(p.status)} · ${p.op_ty ? fmt(p.op_ty) + " t/y" : (p.pipe_ty ? fmt(p.pipe_ty) + " t/y pipeline" : "no counted figure")}</div>
      </div>`).join("") || '<div class="c" style="color:#64748b;font-size:11px">Nothing in view.</div>'}</div>`;
  $$("#supply .sitem").forEach(i => i.onclick = () => {
    const p = D.plants.find(x => x.id === i.dataset.id); if (p) openDrawer(p);
  });
}
function tip(e, html) {
  const t = $("#tip"); t.innerHTML = html; t.style.opacity = 1;
  const r = t.getBoundingClientRect();
  t.style.left = Math.min(e.clientX + 13, innerWidth - r.width - 8) + "px";
  t.style.top = Math.max(8, e.clientY - r.height - 10) + "px";
}
const hideTip = () => $("#tip").style.opacity = 0;

let raf = 0;
function setVB(redraw) {
  $("#map").setAttribute("viewBox", `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
  const z = (1000 / vb.w);
  $("#mhint").textContent = z > 1.05 ? `${z.toFixed(1)}× · drag to pan · shift+click a producer to isolate its links`
                                     : "drag to pan · scroll to zoom · click a producer";
  if (redraw === false) return;
  if (raf) return;
  raf = requestAnimationFrame(() => { raf = 0; drawMarkers(filtered()); });
}
function zoom(k, cx, cy) {
  const nw = Math.max(18, Math.min(1000, vb.w * k)), nh = nw / 2;
  if (cx == null) { cx = vb.x + vb.w / 2; cy = vb.y + vb.h / 2; }
  vb.x = cx - (cx - vb.x) * (nw / vb.w); vb.y = cy - (cy - vb.y) * (nh / vb.h);
  vb.w = nw; vb.h = nh; setVB();
}
function bboxOf(region) {
  const P = D.plants.filter(p => p.x != null && !p.no_marker && (!region || p.region === region));
  if (!P.length) return { x: 0, y: 0, w: 1000, h: 500 };
  const xs = P.map(p => p.x), ys = P.map(p => p.y);
  let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const padX = Math.max(28, (x1 - x0) * 0.32), padY = Math.max(20, (y1 - y0) * 0.32);
  x0 -= padX; x1 += padX; y0 -= padY; y1 += padY;
  let w = Math.max(x1 - x0, (y1 - y0) * 2, 26);
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  return { x: cx - w / 2, y: cy - w / 4, w, h: w / 2 };
}
function flyTo(t, ms) {
  const a = { ...vb }, t0 = performance.now(); ms = ms || 620;
  (function step(now) {
    const u = Math.min(1, (now - t0) / ms), e = u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
    vb = { x: a.x + (t.x - a.x) * e, y: a.y + (t.y - a.y) * e, w: a.w + (t.w - a.w) * e, h: a.h + (t.h - a.h) * e };
    setVB(u === 1);
    if (u < 1) requestAnimationFrame(step); else drawMarkers(filtered());
  })(t0);
}
function regionBar() {
  const h = $("#regions"); h.innerHTML = "";
  const regions = ["World"].concat(Array.from(new Set(D.plants.filter(p => !p.no_marker).map(p => p.region))));
  regions.forEach(r => {
    const isW = r === "World";
    const n = isW ? D.plants.filter(p => !p.no_marker).length : D.plants.filter(p => p.region === r && !p.no_marker).length;
    if (!n) return;
    const b = document.createElement("button");
    b.className = "rb" + (S.region === r ? " on" : "");
    b.innerHTML = `${esc(r)}<span class="n">${n}</span>`;
    b.onclick = () => { S.region = r; regionBar(); flyTo(isW ? { x: 0, y: 0, w: 1000, h: 500 } : bboxOf(r)); };
    h.appendChild(b);
  });
}
function mapEvents() {
  const svg = $("#map");
  svg.addEventListener("wheel", e => {
    e.preventDefault();
    const r = svg.getBoundingClientRect();
    const cx = vb.x + (e.clientX - r.left) / r.width * vb.w;
    const cy = vb.y + (e.clientY - r.top) / r.height * vb.h;
    zoom(e.deltaY > 0 ? 1.18 : 0.85, cx, cy);
    S.region = "Custom"; regionBar();
  }, { passive: false });
  svg.addEventListener("mousedown", e => { drag = { x: e.clientX, y: e.clientY, vx: vb.x, vy: vb.y }; svg.classList.add("drag"); });
  addEventListener("mousemove", e => {
    if (!drag) return;
    const r = svg.getBoundingClientRect();
    vb.x = drag.vx - (e.clientX - drag.x) / r.width * vb.w;
    vb.y = drag.vy - (e.clientY - drag.y) / r.height * vb.h;
    setVB();
  });
  addEventListener("mouseup", () => { drag = null; svg.classList.remove("drag"); });
  let pinch = null;
  svg.addEventListener("touchstart", e => {
    if (e.touches.length === 1) drag = { x: e.touches[0].clientX, y: e.touches[0].clientY, vx: vb.x, vy: vb.y };
    else if (e.touches.length === 2) {
      drag = null;
      const [a, b] = e.touches;
      pinch = { d: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY), vb: { ...vb } };
    }
  }, { passive: true });
  svg.addEventListener("touchmove", e => {
    const r = svg.getBoundingClientRect();
    if (e.touches.length === 1 && drag) {
      e.preventDefault();
      vb.x = drag.vx - (e.touches[0].clientX - drag.x) / r.width * vb.w;
      vb.y = drag.vy - (e.touches[0].clientY - drag.y) / r.height * vb.h;
      setVB();
    } else if (e.touches.length === 2 && pinch) {
      e.preventDefault();
      const [a, b] = e.touches;
      const d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
      const k = Math.max(0.2, Math.min(5, pinch.d / d));
      const cx = pinch.vb.x + ((a.clientX + b.clientX) / 2 - r.left) / r.width * pinch.vb.w;
      const cy = pinch.vb.y + ((a.clientY + b.clientY) / 2 - r.top) / r.height * pinch.vb.h;
      const nw = Math.max(18, Math.min(1000, pinch.vb.w * k)), nh = nw / 2;
      vb = { x: cx - (cx - pinch.vb.x) * (nw / pinch.vb.w), y: cy - (cy - pinch.vb.y) * (nh / pinch.vb.h), w: nw, h: nh };
      setVB();
    }
  }, { passive: false });
  svg.addEventListener("touchend", () => { drag = null; pinch = null; });
  svg.addEventListener("dblclick", e => {
    const r = svg.getBoundingClientRect();
    zoom(0.5, vb.x + (e.clientX - r.left) / r.width * vb.w, vb.y + (e.clientY - r.top) / r.height * vb.h);
  });
  $("#zin").onclick = () => zoom(0.7); $("#zout").onclick = () => zoom(1.42);
  $("#zfit").onclick = () => { S.region = "World"; regionBar(); flyTo({ x: 0, y: 0, w: 1000, h: 500 }); };
  $("#focusoff").onclick = () => { S.focus = null; focusBar(); drawMarkers(filtered()); };
  ["t-flow", "t-liclinks", "t-cust-dots", "t-labels", "t-spider"].forEach(i => $("#" + i).onchange = () => drawMarkers(filtered()));
}

/* ---------------- producers table ---------------- */
const COLS = [
  { k: "company", n: "Company", w: "20%" },
  { k: "country", n: "Country" },
  { k: "makes", n: "Makes", f: p => esc(p.makes) },
  { k: "route_family", n: "Route family", f: p => {
      const f = p.route_family[0];
      return FAMC[f] ? `<span style="color:${FAMC[f]}">${esc(p.route_family)}</span>` : `<span class="muted">${esc(p.route_family)}</span>`; } },
  { k: "status", n: "Status", f: p => `<span class="pill" style="background:${SC[p.sgroup]}22;color:${SC[p.sgroup]}">${esc(p.status_raw || p.status)}</span>` },
  { k: "op", n: "Operating t/y", num: 1, f: p => {
      if (!p.op_ty) return '<span class="muted">—</span>';
      const tags = Object.keys(p.per_chem || {}).filter(c => c !== "LFP").map(c => ` <span class="scopetag">${esc(c)}</span>`).join("");
      return fmt(p.op_ty) + tags + (p.upper_extra ? ` <span class="scopetag" title="additional bundle tonnage in the upper band only">+${fmt(p.upper_extra)} bundle</span>` : "");
    }, s: p => p.op_ty },
  { k: "pipe", n: "Pipeline t/y", num: 1, f: p => p.pipe_ty ? `<span style="color:#79b8ff">${fmt(p.pipe_ty)}</span>` : '<span class="muted">—</span>', s: p => p.pipe_ty },
  { k: "conf", n: "Seed conf.", f: p => `<span class="muted">${esc(p.conf || "—")}</span>` }
];
function table(F) {
  $("#thead").innerHTML = "<tr>" + COLS.map(c =>
    `<th data-k="${c.k}" ${c.w ? `style="width:${c.w}"` : ""}>${c.n}${S.sort === c.k ? ` <span class="ar">${S.dir > 0 ? "▲" : "▼"}</span>` : ""}</th>`).join("") + "</tr>";
  $$("#thead th").forEach(th => th.onclick = () => {
    const k = th.dataset.k; S.dir = S.sort === k ? -S.dir : 1; S.sort = k; render();
  });
  const col = COLS.find(c => c.k === S.sort) || COLS[0];
  const val = p => col.s ? col.s(p) : String(p[S.sort] || "");
  const rows = F.slice().sort((a, b) => {
    const x = val(a), y = val(b);
    return (typeof x === "number" ? x - y : String(x).localeCompare(String(y))) * S.dir;
  });
  $("#tbody").innerHTML = rows.map(p => `<tr data-id='${p.id}' class='${["dead","context","precursor","uncertain"].includes(p.sgroup) ? "ghost" : ""}'>` + COLS.map(c =>
    `<td class="${c.num ? "tnum" : ""}">${c.f ? c.f(p) : esc(p[c.k])}</td>`).join("") + "</tr>").join("") ||
    '<tr><td colspan="8"><div class="empty">Nothing matches these filters.</div></td></tr>';
  $$("#tbody tr").forEach(tr => tr.onclick = () => {
    const p = D.plants.find(x => x.id === tr.dataset.id); if (p) openDrawer(p);
  });
}

/* ---------------- drawer ---------------- */
function openDrawer(p) {
  S.sel = p.id;
  if (location.hash !== "#p/" + p.id) history.replaceState(null, "", "#p/" + p.id);
  const mine = D.links.filter(l => l.from === p.id);
  const F = [
    ["Makes", p.makes], ["Synthesis method (as disclosed)", p.method || "not publicly disclosed"],
    ["Capacity / market position — seed text, verbatim", p.capacity_text, 1],
    ["Notes (seed)", p.notes]
  ];
  const countChip = c =>
    (c.counted_operating ? ' <span class="countchip">counted · operating</span>' : "") +
    (c.counted_pipeline ? ' <span class="countchip pipe">counted · pipeline</span>' : "") +
    (c.counted_upper_only ? ' <span class="countchip upx">upper band only</span>' : "") +
    (!c.counted_operating && !c.counted_pipeline && !c.counted_upper_only && c.value_ty != null ? ' <span class="flagchip">counts nothing</span>' : "");
  $("#drawer").innerHTML = `
    <div class="dhead">
      <button class="dclose">×</button>
      <h2>${esc(p.company)}</h2>
      <div class="loc">${esc(p.country)} · ${esc(p.section)}</div>
      <div class="loc" style="margin-top:2px">Permalink: <a class="plink" href="#p/${p.id}">#p/${p.id}</a></div>
    </div>
    <div class="dbody">
      <div class="badges">
        <span class="pill" style="background:${SC[p.sgroup]}22;color:${SC[p.sgroup]}">${esc(p.status_raw || p.status)}</span>
        ${p.scale === "pilot" ? '<span class="pill" style="background:#8b949e22;color:#8b949e">Pilot scale</span>' : ""}
        <span class="pill" style="background:#4da3ff22;color:#4da3ff">${esc(p.route_family)}</span>
        <span class="pill" style="background:#7c5cff22;color:#b39dff">${esc(CHEMLBL[p.chem_focus] || p.chem_focus)}</span>
        ${p.op_ty ? `<span class="pill" style="background:#3fb95022;color:#3fb950">${fmt(p.op_ty)} t/y counted</span>`
                  : `<span class="pill" style="background:#e3b34122;color:#e3b341">No counted operating figure</span>`}
        ${p.pipe_ty ? `<span class="pill" style="background:#58a6ff22;color:#79b8ff">${fmt(p.pipe_ty)} t/y pipeline</span>` : ""}
        ${p.conf ? `<span class="pill" style="background:#64748b22;color:#94a3b8">Seed confidence: ${esc(p.conf)}</span>` : ""}
      </div>
      ${mine.length ? `<div class="f"><h5>Named links (${mine.length})</h5>
        ${mine.map(l => `<div class="dest" style="cursor:default">
            <span class="bar" style="width:22px;background:${LINKC[l.k]}"></span>
            <span class="nm">${esc(l.to)} — ${esc(LINKLBL[l.k])}</span></div>
            <div class="cav" style="margin:0 0 4px 29px">${esc(l.note)}</div>`).join("")}
        <button class="btn" style="margin-top:7px" id="isolate">Isolate on map</button></div>` : ""}
      ${F.filter(f => f[1]).map(f => `<div class="f ${f[2] ? "hi" : ""}"><h5>${f[0]}</h5><p>${esc(f[1])}</p></div>`).join("")}
      <div class="f"><h5>Site${p.sites.length > 1 ? "s" : ""} (${p.sites.length}) — precision honoured</h5>
        ${p.sites.map(s => `<div class="dest" style="cursor:default"><span class="nm">${s.primary ? "&#9679; " : "&#9675; "}${esc(s.name)}</span><span class="v">${esc(s.geo_basis)}</span></div>`).join("")}</div>
      ${(p.cap_claims || []).length ? `<div class="f"><h5>Claims (${p.cap_claims.length})</h5>
        <div class="tblwrap"><table class="claims"><tr><th>Kind</th><th>Figure</th><th>As of</th><th>Basis</th><th>Scope</th><th>Chem</th><th>Source</th></tr>
        ${p.cap_claims.map(c => `<tr${c.superseded_by ? ' class="supr" title="Superseded by ' + esc(c.superseded_by) + ' — shown for history, counts toward no total."' : (c.duplicate_of ? ' class="dupp" title="Same project as ' + esc(c.duplicate_of) + ' — counts once there."' : ((!c.counted_operating && !c.counted_pipeline && !c.counted_upper_only && c.value_ty != null) ? ' class="ncount"' : ""))}>
          <td>${esc(c.kind)}${c.superseded_by ? ' <span class="flagchip">superseded</span>' : ""}${c.supersedes ? ' <span class="flagchip" style="border-color:#4cc38a66;color:#4cc38a">supersedes ' + esc(c.supersedes) + '</span>' : ""}${c.bundle ? ' <span class="flagchip">bundle</span>' : ""}</td>
          <td class="tnum">${c.value_ty != null ? fmt(c.value_ty) + " t/y" : (c.value_native ? esc(c.value_native) : "—")}${countChip(c)}</td>
          <td>${esc(c.as_of || "—")}</td><td>${esc(c.basis)}${c.target_date ? `<span class="asof">→ ${esc(c.target_date)}</span>` : ""}</td>
          <td>${esc(c.scope)}</td><td>${esc(c.chem)}</td>
          <td><a href="${esc(c.src_url)}" target="_blank" rel="noopener" title="${esc(c.src_pub)} — ${esc(c.src_type)}${c.src_date ? ", " + esc(c.src_date) : ""}">${esc(c.src_pub)}</a>
              <span class="tierchip t-${esc(c.src_tier)}">${esc(c.src_tier)}</span>
              <span class="confchip cf-${esc(c.public_confidence)}">${esc(c.public_confidence)}</span>
              ${c.note ? `<div class="cav">${esc(c.note)}</div>` : ""}
              ${(c.caveats || []).length ? `<div class="cav">⚠ ${c.caveats.map(esc).join(" · ")}</div>` : ""}</td></tr>`).join("")}
        </table></div></div>` : ""}
      ${p.row_src ? `<div class="f"><h5>Seed row source</h5><p><a class="plink" href="${esc(p.row_src.url)}" target="_blank" rel="noopener">${esc(p.row_src.publisher)}</a>
        <span class="tierchip t-${esc(p.row_src.tier)}">${esc(p.row_src.tier)}</span> — ${esc(p.row_src.doc_type)}</p></div>` : ""}
    </div>`;
  $("#drawer").classList.add("on");
  $(".dclose").onclick = closeDrawer;
  const iso = $("#isolate");
  if (iso) iso.onclick = () => {
    S.focus = p.id; focusBar(); closeDrawer();
    $$("nav button[data-p]").forEach(x => x.classList.remove("on"));
    document.querySelector('nav button[data-p="map"]').classList.add("on");
    $$(".pane").forEach(x => x.classList.remove("on")); $("#p-map").classList.add("on");
    drawMarkers(filtered());
  };
  drawMarkers(filtered());
}
function closeDrawer() { S.sel = null; $("#drawer").classList.remove("on"); if (location.hash.startsWith("#p/")) history.replaceState(null, "", " "); drawMarkers(filtered()); }

/* ---------------- methods explorer ---------------- */
function methodsPane() {
  const host = $("#methodhost"); host.innerHTML = "";
  const fb = $("#fambar"); fb.innerHTML = "";
  D.families.forEach(f => {
    const n = D.methods.filter(m => m.family === f.id).length;
    const b = document.createElement("button");
    b.className = "rb";
    b.innerHTML = `<i class="dot" style="width:8px;height:8px;border-radius:50%;background:${FAMC[f.id]};display:inline-block"></i>${esc(f.name)}<span class="n">${n}</span>`;
    b.onclick = () => { const t = $("#fam-" + f.id); if (t) t.scrollIntoView({ behavior: "smooth", block: "start" }); };
    fb.appendChild(b);
  });
  D.families.forEach(f => {
    const head = document.createElement("div");
    head.className = "famhead"; head.id = "fam-" + f.id;
    head.style.borderLeftColor = FAMC[f.id];
    head.innerHTML = `<h3>${esc(f.name)}</h3><div class="an">NMC analogy: ${esc(f.nmc_analogy)}</div>
      <p><b>${esc(f.defines)}.</b> ${esc(f.relevance)}</p>`;
    host.appendChild(head);
    const grid = document.createElement("div"); grid.className = "mcards";
    D.methods.filter(m => m.family === f.id).forEach(m => {
      const c = document.createElement("div");
      c.className = "mcard"; c.style.borderTopColor = FAMC[f.id];
      c.innerHTML = `
        <h4>${esc(m.name)}<span class="scalechip sc-${esc(m.scale_group)}" title="${esc(m.scale_today)}">${esc(m.scale_today.length > 26 ? m.scale_group : m.scale_today)}</span></h4>
        <div class="how">${esc(m.how)}</div>
        <div class="advdis">
          <div class="a"><h6>Advantages</h6>${esc(m.adv)}</div>
          <div class="d"><h6>Disadvantages</h6>${esc(m.dis)}</div>
        </div>
        <div class="pr"><b>Applies to:</b> ${esc(m.applies)} · <b>Who:</b> ${esc(m.producers_text)}<br>
        <b>Ref:</b> ${m.src_url ? `<a class="plink" href="${esc(m.src_url)}" target="_blank" rel="noopener">${esc(m.ref)}</a>` : esc(m.ref)}
        <span class="confchip cf-${esc((m.conf || "Medium").split("-")[0] === "Low" ? "Low" : (m.conf === "High" ? "High" : "Medium"))}">${esc(m.conf)}</span></div>`;
      grid.appendChild(c);
    });
    host.appendChild(grid);
  });
}

/* ---------------- patent timeline ---------------- */
const EV_KIND = { e01: "found", e02: "found", e03: "found", e04: "suit", e05: "corp", e06: "corp", e07: "pool",
                  e08: "pool", e09: "suit", e10: "suit", e11: "corp", e12: "corp", e13: "corp", e14: "corp",
                  e15: "corp", e16: "corp", e17: "cliff", e18: "corp" };
const EVC = { found: "#b57bff", suit: "#f85149", corp: "#4da3ff", pool: "#e3b341", cliff: "#f85149" };
const EVLBL = { found: "Foundational science / patents", suit: "Litigation", corp: "Corporate hands-changing",
                pool: "The patent pool", cliff: "The patent cliff" };
function patentsPane() {
  const h = $("#timeline"); h.innerHTML = "";
  const E = D.patent_events;
  const W = 1160, LB = 8, RB = 460, rowH = 24, top = 30, H = top + E.length * rowH + 34;
  const x0 = 1995.6, x1 = 2025.4, sx = v => LB + (v - x0) / (x1 - x0) * (W - LB - RB);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, style: "min-width:900px" });
  for (let y = 1996; y <= 2025; y += 2) {
    svg.appendChild(el("line", { x1: sx(y), y1: top - 12, x2: sx(y), y2: H - 26, class: "axis" }));
    const t = el("text", { x: sx(y), y: top - 18, class: "tick", "text-anchor": "middle" }); t.textContent = y; svg.appendChild(t);
  }
  const cw = sx(2022.9);
  svg.appendChild(el("line", { x1: cw, y1: top - 12, x2: cw, y2: H - 26, class: "cliff" }));
  const wl = el("text", { x: cw + 6, y: H - 12, class: "tick", fill: "#f85149" });
  wl.textContent = "◀ ~end-2022 — the LFP patent cliff"; svg.appendChild(wl);
  E.forEach((d, i) => {
    const y = top + i * rowH, kind = EV_KIND[d.id] || "corp";
    const g = el("g", { class: "tlev" });
    const x = sx(d.y0), w = Math.max(7, sx(d.y1) - sx(d.y0));
    g.appendChild(el("rect", { x, y: y + 3, width: w, height: 12, rx: 3, fill: EVC[kind], opacity: kind === "cliff" ? .95 : .8 }));
    const lbl = el("text", { x: x + w + 7, y: y + 12.5, class: "tick", fill: "#9fb0c4", "font-size": "10.5" });
    lbl.textContent = d.date_label + " — " + (d.event.length > 76 ? d.event.slice(0, 76) + "…" : d.event);
    g.appendChild(lbl);
    g.addEventListener("mousemove", e => tip(e, `<b>${esc(d.event)}</b><div class="s">${esc(d.date_label)} · ${esc(d.entities)}</div><div class="s" style="color:#4da3ff">click for source</div>`));
    g.addEventListener("mouseleave", hideTip);
    const url = (D.sources_index.find(s => s.id === d.src) || {}).url;
    if (url) g.addEventListener("click", () => window.open(url, "_blank", "noopener"));
    svg.appendChild(g);
  });
  h.appendChild(svg);
  h.insertAdjacentHTML("beforeend", `<div style="display:flex;gap:14px;margin-top:9px;font-size:10.5px;color:#9fb0c4;flex-wrap:wrap">
    ${Object.entries(EVLBL).map(([k, v]) => `<span style="display:flex;align-items:center;gap:5px"><i style="width:11px;height:11px;border-radius:2px;background:${EVC[k]};display:inline-block"></i>${v}</span>`).join("")}</div>`);
  $("#tlist").innerHTML = D.patent_events.map(d => {
    const url = (D.sources_index.find(s => s.id === d.src) || {}).url;
    return `<div class="dest" style="cursor:default;padding:5px 0"><span class="bar" style="width:16px;background:${EVC[EV_KIND[d.id] || "corp"]}"></span>
      <span class="nm" style="white-space:normal"><b style="color:#e6edf5">${esc(d.date_label)}</b> — ${esc(d.event)} <span style="color:#64748b">(${esc(d.entities)})</span>
      ${url ? ` <a class="plink" href="${esc(url)}" target="_blank" rel="noopener">source</a>` : ""}</span></div>`;
  }).join("");
}

/* ---------------- csv ---------------- */
function csv(F) {
  const cols = ["id", "company", "country", "region", "makes", "method", "route_family", "status_raw", "sgroup",
                "capacity_text", "op_ty", "pipe_ty", "conf", "notes", "lat", "lon"];
  const q = v => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
  const body = [cols.join(",")].concat(F.map(p => cols.map(c => q(p[c])).join(","))).join("\r\n");
  const b = new Blob(["﻿" + body], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = "lfp_atlas_" + F.length + "_rows.csv"; a.click();
  URL.revokeObjectURL(a.href);
}

/* ---------------- render ---------------- */
function render() {
  const F = filtered();
  kpis(F); rail(); drawMarkers(F); table(F);
}

/* ---------------- init ---------------- */
function init() {
  const B = D.meta.bands;
  $("#asof").textContent = "v" + D.meta.version + " · re-sourced edition · " + D.meta.dataset_date;
  $("#herotext").innerHTML =
    `${esc(D.meta.market_context.dominant_route)} ` +
    `This atlas documents <b>${D.plants.length} producer rows</b> across <b>${new Set(D.plants.map(p => p.country.split(" (")[0])).size} countries</b>: ` +
    `<b>${fmt(B.cam.headline)} t/y</b> of counted operating nameplate (lower ${fmt(B.cam.lower)} — chemistry stated outright), plus <b>${fmt(B.pipeline)} t/y</b> announced or under construction and <b>${fmt(B.precursor_fepo4)} t/y</b> of documented FePO₄ precursor — all kept strictly apart. ` +
    `The bands remain a <b>documented floor, not a market estimate</b>. The main uncertainty is now the lower–headline gap: <b>${fmt(B.cam.headline - B.cam.lower)} t/y</b> (Yuneng 994.5k, Dynanonic 450k) is filed as phosphate-FAMILY totals with no LFP/LMFP split. ` +
    `Corrections are append-only supersession chains — superseded figures stay visible and count nothing. Every figure carries its basis, scope, chemistry tag and source.`;
  drawMapBase(); mapEvents(); regionBar(); methodsPane(); patentsPane();
  $("#q").oninput = e => { S.q = e.target.value; render(); };
  ["cap", "pipe", "lmfp", "lic"].forEach(k => $("#t-" + k).onchange = e => { S[k] = e.target.checked; render(); });
  $$(".clr").forEach(b => b.onclick = () => { S[b.dataset.c].clear(); render(); });
  $("#reset").onclick = () => {
    S.q = ""; $("#q").value = "";
    ["status", "country", "route", "chem"].forEach(k => S[k].clear());
    ["cap", "pipe", "lmfp", "lic"].forEach(k => { S[k] = false; $("#t-" + k).checked = false; });
    S.focus = null; focusBar();
    render();
  };
  $("#csv").onclick = () => csv(filtered());
  $("#filtersbtn").onclick = () => document.body.classList.toggle("filters-open");
  $$("nav button[data-p]").forEach(b => b.onclick = () => {
    $$("nav button[data-p]").forEach(x => x.classList.remove("on")); b.classList.add("on");
    $$(".pane").forEach(p => p.classList.remove("on")); $("#p-" + b.dataset.p).classList.add("on");
  });
  addEventListener("keydown", e => {
    if (e.key === "Escape") { if (S.focus) { S.focus = null; focusBar(); drawMarkers(filtered()); } closeDrawer(); }
  });
  /* cite & downloads */
  $("#citeblock").innerHTML = esc(D.meta.cite) +
    `<br><br><b>Operating bands (all plants):</b> ${fmt(B.cam.lower)} – ${fmt(B.cam.headline)} – ${fmt(B.cam.upper)} t/y (lower · headline · upper) · ` +
    `<b>Pipeline:</b> ${fmt(B.pipeline)} t/y · <b>FePO₄ precursor documented:</b> ${fmt(B.precursor_fepo4)} t/y<br>` + esc(B.rule) +
    `<br><br><b>Version:</b> ${esc(D.meta.version)} · <b>Dataset date:</b> ${esc(D.meta.dataset_date)} · <b>Seed compiled:</b> ${esc(D.meta.seed_compiled)} · <b>Rows:</b> ${D.plants.length}`;
  $("#refs").innerHTML = D.references.map(r =>
    `<div class="dest" style="cursor:default;padding:4px 0"><span class="bar" style="width:12px"></span>
     <span class="nm" style="white-space:normal">[${esc(r.type)}] ${esc(r.citation)} ${r.src_url ? `<a class="plink" href="${esc(r.src_url)}" target="_blank" rel="noopener">link</a>` : ""}</span></div>`).join("");
  $("#changelog").innerHTML = (D.changelog || []).map(v =>
    `<div class="f"><h5>v${esc(v.version)} — ${esc(v.date)}</h5><p>${v.changes.map(esc).join("<br>")}</p></div>`).join("");
  const dl = (name, text, mime) => { const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: mime })); a.download = name; a.click(); URL.revokeObjectURL(a.href); };
  $("#dl-json").onclick = () => { const { geo, ...rest } = D; dl("lfp_atlas_v" + D.meta.version + ".json", JSON.stringify(rest, null, 1), "application/json"); };
  $("#dl-claims").onclick = () => {
    const q = v => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
    const rows = [["plant_id","company","country","status","claim_id","kind","product","value_t_per_year","value_native","as_of","basis","scope","chem","counted_operating","counted_pipeline","counted_upper_only","public_confidence","caveats","note","source_tier","source_publisher","source_url"].join(",")];
    D.plants.forEach(p => (p.cap_claims || []).forEach(c => rows.push([p.id,p.company,p.country,p.status,c.id,c.kind,c.product,c.value_ty,c.value_native||"",c.as_of,c.basis,c.scope,c.chem,c.counted_operating?"Y":"",c.counted_pipeline?"Y":"",c.counted_upper_only?"Y":"",c.public_confidence,(c.caveats||[]).join("; "),c.note,c.src_tier,c.src_pub,c.src_url].map(q).join(","))));
    dl("lfp_atlas_claims_v" + D.meta.version + ".csv", "﻿" + rows.join("\r\n"), "text/csv;charset=utf-8");
  };
  $("#dl-plants").onclick = () => csv(filtered());
  /* methodology */
  $("#rulep").textContent = B.rule;
  $("#kfhost").innerHTML = "<h2>Key findings carried from the seed</h2>" +
    D.meta.key_findings.map(k => `<div class="kf">${esc(k.replace(/^•\s*/, ""))}</div>`).join("");
  renderGaps();
  /* per-plant permalinks */
  const openHash = () => { const m = location.hash.match(/^#p\/(p\d+)$/); if (!m) return;
    const p = D.plants.find(x => x.id === m[1]); if (p) openDrawer(p); };
  addEventListener("hashchange", openHash);
  render();
  openHash();
}

function renderGaps() {
  const g = D.gaps, host = $("#gapsreg");
  if (!g || !host) return;
  const fmtT = n => n == null ? "—" : n.toLocaleString("en-US");
  host.innerHTML = `
    <h2>Gaps register</h2>
    <p>${esc(g.about)} Snapshot coverage: <b>${g.archive.complete || 0} complete</b> · ${g.archive.proxy_partial || 0} proxy/partial · ${g.archive.total - (g.archive.snapshotted || 0)} unarchived — of ${g.archive.total} sources. ${esc(g.archive.about)}</p>
    <h4>Structural seed gaps (${g.seed_gaps.length})</h4>
    ${g.seed_gaps.map(r => `<p><b>${esc(r.id)}</b> — ${esc(r.gap)}</p>`).join("")}
    <h4>Operating producers with no counted capacity figure (${g.no_figure.length})</h4>
    <p>${g.no_figure.map(r => `${esc(r.company)} <span class="gr-dim">(${esc(r.country)})</span>`).join(" · ")}</p>
    <h4>Capacity claims with no vintage (${g.undated_capacity_claims.length})</h4>
    <table class="gr-t"><tr><th>Producer</th><th>Claim</th><th>t/y</th></tr>
      ${g.undated_capacity_claims.slice().sort((a, b) => (b.value_ty || 0) - (a.value_ty || 0)).slice(0, 15).map(r =>
        `<tr><td>${esc(r.company)}</td><td>${esc(r.claim)}</td><td class="tnum">${fmtT(r.value_ty)}</td></tr>`).join("")}
    </table>
    ${g.undated_capacity_claims.length > 15 ? `<p class="gr-dim">…and ${g.undated_capacity_claims.length - 15} more (all in the claims CSV).</p>` : ""}
    <h4>Counted figures resting on trade- or weak-tier sources (${g.counted_on_trade_or_weak_tier.length})</h4>
    <table class="gr-t"><tr><th>Producer</th><th>Claim</th><th>t/y</th><th>Tier</th></tr>
      ${g.counted_on_trade_or_weak_tier.map(r => `<tr><td>${esc(r.company)}</td><td>${esc(r.claim)}</td><td class="tnum">${fmtT(r.value_ty)}</td><td>${esc(r.tier)}</td></tr>`).join("")}
    </table>
    <h4>Location-precision flags (${g.location_precision_flags.length})</h4>
    <p class="gr-dim">${g.location_precision_flags.map(r => `${esc(r.company)} (${esc(r.basis)})`).join(" · ")}</p>
    <p><b>Row-level-sourced figures:</b> ${g.row_sourced_figures} of the displayed figures currently cite the producer row's seed source rather than a figure-specific document. That is the v0.2 re-sourcing backlog.</p>`;
}

document.readyState === "loading" ? addEventListener("DOMContentLoaded", init) : init();
})();
