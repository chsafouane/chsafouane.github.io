// Interactive charts for {{< chart name >}} (see chartkit.lua and
// tools/figkit/charts.py). A port of the Jev Field Guide's chart helpers:
// hand-drawn SVG, no library. Each chart is redrawn when its box changes width,
// and colors come from CSS custom properties (theme.scss), so switching between
// light and dark mode recolors a chart without redrawing it.
//
// Built-in chart types, chosen by spec.type:
//   line    series of points with optional intervals, bands, reference lines,
//           direct labels, and a crosshair or nearest-point tooltip;
//   bar     grouped bars, with negative values and value labels;
//   dot     one row per value with an optional 95% interval, or two values
//           per row (a dumbbell);
//   panels  small multiples of the types above, side by side.
// A post can add its own chart with Chartkit.register(name, draw) in
// posts/<slug>/charts.js; a spec with "widget": name then uses it.
(() => {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  document.documentElement.classList.add("ck-js");

  // ---------- small helpers ----------
  function S(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function txt(parent, x, y, s, o = {}) {
    const t = S("text", { x, y, "text-anchor": o.anchor || "start" }, parent);
    if (o.cls) t.setAttribute("class", o.cls);
    t.textContent = s;
    return t;
  }
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  function lin(d0, d1, r0, r1) {
    const f = (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
    f.inv = (p) => d0 + ((p - r0) / (r1 - r0)) * (d1 - d0);
    return f;
  }
  function logs(d0, d1, r0, r1) {
    const a = Math.log10(d0), b = Math.log10(d1);
    const f = (v) => r0 + ((Math.log10(v) - a) / (b - a)) * (r1 - r0);
    f.inv = (p) => Math.pow(10, a + ((p - r0) / (r1 - r0)) * (b - a));
    return f;
  }
  const pathD = (pts) => pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + "," + p[1].toFixed(1)).join("");

  // Number format from a spec: {decimals, prefix, suffix, signed, thousands, trim}.
  function formatter(o = {}) {
    const decimals = o.decimals ?? 0;
    return (v) => {
      if (v === null || v === undefined || Number.isNaN(v)) return "";
      let a = Math.abs(v), unit = "";
      if (o.thousands && a >= 1000) { a /= 1000; unit = "k"; }
      let s = a.toLocaleString("en-US", { minimumFractionDigits: o.trim ? 0 : decimals, maximumFractionDigits: decimals });
      if (Number(s.replace(/,/g, "")) === 0) return (o.prefix || "") + s + unit + (o.suffix || "");
      const sign = v < 0 ? "−" : o.signed ? "+" : "";
      return sign + (o.prefix || "") + s + unit + (o.suffix || "");
    };
  }
  // Series color: 1, 2, 3 (the chart hues) or "person" (the reference gray).
  const cc = (c) => (c === "person" || c === "p" ? "p" : String(c || 1));
  const swatch = (c) => `<i style="background:var(--${cc(c) === "p" ? "person" : "c" + cc(c)})"></i>`;

  // Draw a chart frame: grid, ticks, axis titles. Returns scales and a group for marks.
  function frame(box, o) {
    box.querySelectorAll(":scope > svg").forEach((s) => s.remove());
    const W = Math.max(220, Math.round(box.clientWidth));
    const H = o.height;
    const m = Object.assign({ t: 26, r: 16, b: 44, l: 46 }, o.m || {});
    if (!o.xTitle) m.b = Math.min(m.b, 30);
    const svg = S("svg", { class: "chart", width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": o.label || "" });
    box.insertBefore(svg, box.firstChild);
    const X = o.x.log ? logs(o.x.d[0], o.x.d[1], m.l, W - m.r) : lin(o.x.d[0], o.x.d[1], m.l, W - m.r);
    const Y = lin(o.y.d[0], o.y.d[1], H - m.b, m.t);
    const axes = S("g", {}, svg);
    for (const t of o.yTicks || []) {
      if (t !== o.y.d[0]) S("line", { class: "grid", x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t) }, axes);
      txt(axes, m.l - 8, Y(t) + 4, o.yFmt(t), { anchor: "end" });
    }
    for (const t of o.xTicks || []) txt(axes, X(t), H - m.b + 17, o.xFmt(t), { anchor: "middle" });
    S("line", { class: "base", x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b }, axes);
    if (o.xTitle) txt(axes, (m.l + W - m.r) / 2, H - 8, o.xTitle, { anchor: "middle", cls: "t-strong" });
    if (o.yTitle) txt(axes, 2, 12, o.yTitle, { cls: "t-strong" });
    const g = S("g", {}, svg);
    return { svg, X, Y, W, H, m, g, box };
  }

  // Hover layer: `at(px, py, layer)` draws hover marks and returns {x, y, html} or null.
  function hover(f, at) {
    const box = f.box;
    let tip = box.querySelector(":scope > .tip");
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "tip";
      tip.hidden = true;
      box.appendChild(tip);
    }
    tip.hidden = true;
    const layer = S("g", {}, f.svg);
    const hit = S("rect", {
      class: "hit", x: f.m.l, y: Math.max(0, f.m.t - 10),
      width: Math.max(0, f.W - f.m.l - f.m.r), height: Math.max(0, f.H - f.m.t - f.m.b + 10),
    }, f.svg);
    const clear = () => { while (layer.firstChild) layer.firstChild.remove(); };
    const hide = () => { tip.hidden = true; clear(); };
    const move = (ev) => {
      const r = f.svg.getBoundingClientRect();
      const b = box.getBoundingClientRect();
      const sx = r.width / f.W, sy = r.height / f.H;
      const px = (ev.clientX - r.left) / sx, py = (ev.clientY - r.top) / sy;
      clear();
      const res = at(px, py, layer);
      if (!res) { tip.hidden = true; return; }
      tip.innerHTML = res.html;
      tip.hidden = false;
      const ax = r.left - b.left + res.x * sx, ay = r.top - b.top + res.y * sy;
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      let left = ax + 14;
      if (left + tw > b.width) left = ax - tw - 14;
      if (left < 0) left = clamp(ax - tw / 2, 0, Math.max(0, b.width - tw));
      let top = ay - th - 12;
      if (top < 0) top = ay + 14;
      tip.style.left = left + "px";
      tip.style.top = top + "px";
    };
    hit.addEventListener("pointermove", move);
    hit.addEventListener("pointerdown", move);
    hit.addEventListener("pointerleave", hide);
    return layer;
  }

  // Nearest point hover over several series: pts = [{x, y, c, html}] in pixel space.
  function nearestHover(f, pts, radius = 50) {
    hover(f, (px, py, layer) => {
      let best = null, bd = Infinity;
      for (const p of pts) {
        const d = Math.hypot(p.x - px, p.y - py);
        if (d < bd) { bd = d; best = p; }
      }
      if (!best || bd > radius) return null;
      S("circle", { class: `dot f${cc(best.c)}`, cx: best.x, cy: best.y, r: 6.5 }, layer);
      return { x: best.x, y: best.y, html: best.html };
    });
  }

  // Redraw when the container width changes; returns a function that forces a redraw.
  function observe(box, draw) {
    let w = 0;
    const run = () => {
      const nw = box.clientWidth;
      if (nw > 0 && Math.abs(nw - w) > 1) { w = nw; draw(); }
    };
    if ("ResizeObserver" in window) new ResizeObserver(run).observe(box);
    else window.addEventListener("resize", run);
    run();
    return () => { if (box.clientWidth > 0) { w = box.clientWidth; draw(); } };
  }

  // ---------- shared pieces of the built-in types ----------
  function axisOptions(spec) {
    const x = spec.x || {}, y = spec.y || {};
    return {
      x: { d: x.domain, log: x.log }, y: { d: y.domain },
      xTicks: x.ticks || [], yTicks: y.ticks || [],
      xFmt: formatter(x.tickFormat || x.format), yFmt: formatter(y.tickFormat || y.format),
      xTitle: x.title, yTitle: y.title, label: spec.alt,
    };
  }

  function drawBands(f, spec) {
    for (const b of spec.bands || []) {
      const x0 = f.X(b.x[0]), x1 = f.X(b.x[1]);
      S("rect", { class: "band", x: Math.min(x0, x1), y: f.m.t, width: Math.abs(x1 - x0), height: f.H - f.m.b - f.m.t }, f.g);
      if (b.label) txt(f.g, Math.min(x0, x1) + 6, f.m.t + 14, b.label, { cls: "t-label" });
    }
  }

  function drawRefs(f, spec) {
    for (const r of spec.refs || []) {
      const cls = r.strong ? "ref-strong" : "ref";
      if (r.y !== undefined) {
        S("line", { class: cls, x1: f.m.l, x2: f.W - f.m.r, y1: f.Y(r.y), y2: f.Y(r.y) }, f.g);
        if (r.label) txt(f.g, f.m.l + 6, f.Y(r.y) - 6, r.label, { cls: "t-label" });
      }
      if (r.x !== undefined) {
        S("line", { class: cls, x1: f.X(r.x), x2: f.X(r.x), y1: f.m.t, y2: f.H - f.m.b }, f.g);
        if (r.label) txt(f.g, f.X(r.x) + 6, f.m.t + 12, r.label, { cls: "t-label" });
      }
    }
  }

  function drawNotes(f, spec) {
    for (const n of spec.notes || []) {
      txt(f.g, f.X(n.x) + (n.dx || 0), f.Y(n.y) + (n.dy || 0), n.text, { anchor: n.anchor || "start", cls: "t-label" });
    }
  }

  // ---------- line ----------
  function segments(points) {
    const out = [];
    let cur = [];
    for (const p of points) {
      if (p === null || p[1] === null) { if (cur.length) out.push(cur); cur = []; } else cur.push(p);
    }
    if (cur.length) out.push(cur);
    return out;
  }

  function lineChart(box, spec) {
    const series = spec.series || [];
    const labelled = series.some((s) => s.label);
    const xf = formatter((spec.x || {}).format), yf = formatter((spec.y || {}).format);
    const xName = (spec.x || {}).name || (spec.x || {}).title || "x";
    observe(box, () => {
      const W = box.clientWidth;
      const wide = W >= 460;
      const m = Object.assign({ t: 22, r: labelled && wide ? 92 : 16, b: 44, l: 46 }, spec.margin || {});
      const f = frame(box, Object.assign(axisOptions(spec), { height: spec.height || 280, m }));
      drawBands(f, spec);
      drawRefs(f, spec);
      const hp = [];
      const ends = [];
      series.forEach((s) => {
        const c = cc(s.color);
        const pts = s.points || [];
        for (const seg of segments(pts)) {
          S("path", {
            class: `line l${c}`, d: pathD(seg.map(([x, y]) => [f.X(x), f.Y(y)])),
            "stroke-width": s.width, "stroke-dasharray": s.dash ? "5 4" : undefined,
          }, f.g);
        }
        pts.forEach((p, i) => {
          if (p === null || p[1] === null) return;
          const [x, y] = p;
          const iv = s.intervals && s.intervals[i];
          if (iv) S("line", { class: `line l${c}`, x1: f.X(x), x2: f.X(x), y1: f.Y(iv[0]), y2: f.Y(iv[1]), "stroke-width": 1.5, opacity: 0.6 }, f.g);
          if (s.dots) S("circle", { class: `dot f${c}`, cx: f.X(x), cy: f.Y(y), r: 4 }, f.g);
          const range = iv ? ` (95% interval ${yf(iv[0])} to ${yf(iv[1])})` : "";
          hp.push({ x: f.X(x), y: f.Y(y), c, html: `<b>${esc(s.name)}</b><br>${esc(xName)} ${xf(x)}: ${yf(y)}${range}` });
        });
        const last = [...pts].reverse().find((p) => p !== null && p[1] !== null);
        if (s.label && last) ends.push({ y: f.Y(last[1]), x: f.X(last[0]), text: s.label });
      });
      // Direct labels at the right end of each line, nudged apart.
      if (wide) {
        ends.sort((a, b) => a.y - b.y);
        for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 14);
        for (const e of ends) txt(f.g, e.x + 8, e.y + 4, e.text, { cls: "t-label" });
      }
      drawNotes(f, spec);
      if (spec.hover === "x") crosshair(f, spec, xf, yf, xName);
      else nearestHover(f, hp);
    });
  }

  // Crosshair tooltip: the value of every series at the x nearest the pointer.
  function crosshair(f, spec, xf, yf, xName) {
    const series = (spec.series || []).filter((s) => s.points && s.points.length);
    hover(f, (px, py, layer) => {
      const xv = f.X.inv(px);
      const rows = [];
      let top = Infinity, xs = null;
      for (const s of series) {
        let best = null, bd = Infinity;
        for (const p of s.points) {
          if (p === null || p[1] === null) continue;
          const d = Math.abs(p[0] - xv);
          if (d < bd) { bd = d; best = p; }
        }
        if (!best) continue;
        xs = xs === null ? best[0] : xs;
        const c = cc(s.color);
        S("circle", { class: `dot f${c}`, cx: f.X(best[0]), cy: f.Y(best[1]), r: 5 }, layer);
        top = Math.min(top, f.Y(best[1]));
        rows.push(`${swatch(s.color)}${esc(s.name)} <b>${yf(best[1])}</b>`);
      }
      if (xs === null) return null;
      S("line", { class: "xhair", x1: f.X(xs), x2: f.X(xs), y1: f.m.t, y2: f.H - f.m.b }, layer);
      layer.insertBefore(layer.lastChild, layer.firstChild);
      return { x: f.X(xs), y: top, html: `<b>${esc(xName)} = ${xf(xs)}</b><br>${rows.join("<br>")}` };
    });
  }

  // ---------- bar ----------
  function barChart(box, spec) {
    const cats = spec.categories || [];
    const series = spec.series || [];
    const yf = formatter((spec.y || {}).format);
    observe(box, () => {
      const m = Object.assign({ t: 22, r: 12, b: 44, l: 46 }, spec.margin || {});
      const o = axisOptions(spec);
      o.x = { d: [0, cats.length] };
      o.xTicks = [];
      o.xTitle = (spec.x || {}).title;
      const f = frame(box, Object.assign(o, { height: spec.height || 250, m }));
      const [y0, y1] = spec.y.domain;
      if (y0 < 0 && y1 > 0) S("line", { class: "base", x1: f.m.l, x2: f.W - f.m.r, y1: f.Y(0), y2: f.Y(0) }, f.g);
      drawRefs(f, spec);
      const gw = f.X(1) - f.X(0);
      const n = series.length;
      const bw = Math.min(56, (gw * 0.72) / n);
      const hp = [];
      cats.forEach((cat, i) => {
        const cx = f.X(i + 0.5);
        txt(f.g, cx, f.H - f.m.b + 18, cat, { anchor: "middle", cls: "t-strong" });
        series.forEach((s, j) => {
          const v = s.values[i];
          if (v === null || v === undefined) return;
          const x = cx - (n * bw + (n - 1) * 4) / 2 + j * (bw + 4);
          const base = f.Y(clamp(0, y0, y1));
          const top = f.Y(v);
          const c = cc(s.color);
          S("rect", { class: `f${c}`, x, y: Math.min(base, top), width: bw, height: Math.max(1, Math.abs(base - top)), rx: 4 }, f.g);
          if (spec.labels !== false) {
            const ly = v >= 0 ? top - 6 : top + 15;
            txt(f.g, x + bw / 2, ly, yf(v), { anchor: "middle", cls: "t-strong" });
          }
          hp.push({ x: x + bw / 2, y: top, c, html: `<b>${esc(s.name)}</b><br>${esc(cat)}: ${yf(v)}` });
        });
      });
      nearestHover(f, hp, 60);
    });
  }

  // ---------- dot ----------
  function dotChart(box, spec) {
    const rows = spec.rows || [];
    const xf = formatter((spec.x || {}).format);
    const names = spec.names || ["", ""];
    observe(box, () => {
      const rowH = spec.rowHeight || 26, groupGap = 18, top = 30;
      const ys = [];
      let y = top, last = null;
      rows.forEach((r) => {
        if (last !== null && r.group !== last) y += groupGap;
        ys.push(y);
        y += rowH;
        last = r.group;
      });
      const H = y + 34;
      const labelWidth = spec.labelWidth || 70;
      const o = axisOptions(spec);
      o.y = { d: [0, 1] };
      o.yTicks = [];
      o.yFmt = () => "";
      const f = frame(box, Object.assign(o, { height: H, m: { t: top - 14, r: 16, b: 40, l: labelWidth } }));
      for (const t of (spec.x || {}).ticks || []) S("line", { class: "grid", x1: f.X(t), x2: f.X(t), y1: f.m.t, y2: H - f.m.b }, f.g);
      for (const r of spec.refs || []) {
        if (r.x === undefined) continue;
        S("line", { class: "ref-strong", x1: f.X(r.x), x2: f.X(r.x), y1: top - 16, y2: H - f.m.b }, f.g);
        if (r.label) txt(f.g, f.X(r.x) - 4, top - 4, r.label, { anchor: "end", cls: "t-label" });
      }
      const hp = [];
      let prev = null;
      rows.forEach((r, i) => {
        if (r.group && r.group !== prev) txt(f.g, 4, ys[i] - 3, r.group, { cls: "t-strong" });
        prev = r.group;
        const cy = ys[i] + 12;
        txt(f.g, f.m.l - 8, cy + 4, r.label, { anchor: "end" });
        const c = cc(r.color);
        const title = [r.group, r.label].filter(Boolean).map(esc).join(", ");
        if (r.value2 !== undefined) {
          const c2 = cc(r.color2 || 2);
          S("line", { class: "gap", x1: f.X(r.value), x2: f.X(r.value2), y1: cy, y2: cy, "stroke-dasharray": "none", "stroke-width": 2 }, f.g);
          S("circle", { class: `dot f${c}`, cx: f.X(r.value), cy, r: 6 }, f.g);
          S("circle", { class: `dot f${c2}`, cx: f.X(r.value2), cy, r: 6 }, f.g);
          const html = `<b>${title}</b><br><span class="k">${esc(names[0])}</span> ${xf(r.value)} · <span class="k">${esc(names[1])}</span> ${xf(r.value2)}`;
          hp.push({ x: f.X(r.value), y: cy, c, html }, { x: f.X(r.value2), y: cy, c: c2, html });
        } else {
          if (r.lo !== undefined) S("line", { class: `line l${c}`, x1: f.X(r.lo), x2: f.X(r.hi), y1: cy, y2: cy }, f.g);
          S("circle", { class: `dot f${c}`, cx: f.X(r.value), cy, r: 5.5 }, f.g);
          const range = r.lo !== undefined ? ` (${xf(r.lo)} to ${xf(r.hi)})` : "";
          hp.push({ x: f.X(r.value), y: cy, c, html: `<b>${title}</b><br>${xf(r.value)}${range}` });
        }
      });
      nearestHover(f, hp, 40);
    });
  }

  // ---------- panels ----------
  function panels(box, spec) {
    const grid = document.createElement("div");
    grid.className = (spec.panels || []).length >= 3 ? "w-grid3" : "w-grid2";
    box.appendChild(grid);
    for (const p of spec.panels || []) {
      const cell = document.createElement("div");
      if (p.title) {
        const t = document.createElement("p");
        t.className = "w-panel-title";
        t.textContent = p.title;
        cell.appendChild(t);
      }
      const inner = document.createElement("div");
      inner.className = "w-panel-chart";
      cell.appendChild(inner);
      grid.appendChild(cell);
      draw(inner, Object.assign({ alt: spec.alt }, p));
    }
  }

  const TYPES = { line: lineChart, bar: barChart, dot: dotChart, panels };
  const WIDGETS = {};
  const helpers = { S, txt, lin, logs, pathD, clamp, esc, formatter, frame, hover, nearestHover, observe, swatch, cc };

  function draw(box, spec) {
    if (spec.widget) {
      const widget = WIDGETS[spec.widget];
      if (!widget) throw new Error(`chartkit: no widget "${spec.widget}" (register it in charts.js)`);
      return widget(box, spec, helpers);
    }
    const type = TYPES[spec.type];
    if (!type) throw new Error(`chartkit: unknown chart type "${spec.type}"`);
    return type(box, spec);
  }

  function init(root = document) {
    root.querySelectorAll(".chartkit .w-chart[data-spec]:not([data-ready])").forEach((box) => {
      box.dataset.ready = "1";
      try {
        draw(box, JSON.parse(box.dataset.spec));
      } catch (e) {
        console.error(e);
        box.innerHTML = '<p class="w-note">This chart could not load in this browser; the numbers are in the table below.</p>';
      }
    });
  }

  window.Chartkit = {
    register(name, widget) { WIDGETS[name] = widget; },
    init,
    helpers,
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => init());
  else init();
})();
