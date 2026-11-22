/* 轻量 SVG 图表渲染器（无外部依赖；支持线性/对数坐标） */
(function (global) {

  const PALETTE = ["#2563eb", "#e5533d", "#0ea5a4", "#8b5cf6", "#f59e0b", "#0e7490", "#db2777", "#65a30d"];
  const NS = "http://www.w3.org/2000/svg";

  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  /* 上下标记号：_{x} / ^{x}（也接受 k_H、M^0.78 这类 ASCII 写法） */
  function richText(node, s) {
    node.textContent = "";
    let str = String(s == null ? "" : s);
    str = str.replace(/([^\s{_])_(?:([A-Za-z][A-Za-z0-9]{0,11})|([0-9]{1,2})|([\u4e00-\u9fff]{1,4})|(\u221e))(?![A-Za-z0-9{])/g, function(m,a,b,c,d){return a+"_{"+(b||c||d||e)+"}";});
    str = str.replace(/\^([A-Za-z0-9.\-∞]{1,6})(?![A-Za-z0-9{])/g, "^{$1}");
    const re = /(_\{[^{}]*\}|\^\{[^{}]*\})/g;
    let idx = 0, m;
    const push = (txt, mode) => {
      if (!txt) return;
      const t = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      t.textContent = txt;
      if (mode === "sub") { t.setAttribute("baseline-shift", "sub"); t.setAttribute("font-size", "80%"); }
      else if (mode === "sup") { t.setAttribute("baseline-shift", "super"); t.setAttribute("font-size", "80%"); }
      node.appendChild(t);
    };
    while ((m = re.exec(str))) {
      push(str.slice(idx, m.index));
      push(m[0].slice(2, -1), m[0][0] === "_" ? "sub" : "sup");
      idx = re.lastIndex;
    }
    push(str.slice(idx));
    return node;
  }

  function fmtNum(v, digits) {
    if (v === 0) return "0";
    const a = Math.abs(v);
    if (a >= 1e5 || a < 1e-6) return v.toExponential(1).replace("e+", "e");
    if (a < 1e-3) return v.toPrecision(2).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
    const d = digits === undefined ? (a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3) : digits;
    return parseFloat(v.toFixed(d)).toString();
  }

  function niceTicks(lo, hi, count) {
    if (!isFinite(lo) || !isFinite(hi)) return [0, 1];
    if (lo === hi) { lo -= 1; hi += 1; }
    const span = hi - lo;
    const step0 = span / Math.max(1, count);
    const mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const norm = step0 / mag;
    let step;
    if (norm <= 1) step = 1; else if (norm <= 2) step = 2; else if (norm <= 5) step = 5; else step = 10;
    step *= mag;
    const start = Math.ceil(lo / step) * step;
    const ticks = [];
    for (let v = start; v <= hi + step * 1e-6; v += step) ticks.push(parseFloat(v.toPrecision(12)));
    return ticks;
  }

  /** 对数轴的刻度：按跨度自动选 1..9 / 1,2,5 / 1,5 / 整十次幂 */
  function logTicks(lo, hi, budget) {
    const a0 = Math.floor(lo) - 1, a1 = Math.ceil(hi) + 1;
    const build = mult => {
      const out = [];
      for (let e = a0; e <= a1; e++) {
        const base = Math.pow(10, e);
        mult.forEach(k => {
          const v = k * base, t = Math.log10(v);
          if (t >= lo - 1e-9 && t <= hi + 1e-9) out.push(v);
        });
      }
      return out;
    };
    const limit = Math.max(3, budget || 6);
    const sets = [[1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 5, 6, 8], [1, 2, 3, 5, 7], [1, 2, 5], [1, 3], [1, 5], [1]];
    for (const mult of sets) {
      const ticks = build(mult);
      if (ticks.length && ticks.length <= limit) return ticks;
    }
    return build([1]).slice(0, limit);
  }

  function extent(values) {
    let lo = Infinity, hi = -Infinity;
    values.forEach(v => { if (isFinite(v)) { if (v < lo) lo = v; if (v > hi) hi = v; } });
    if (!isFinite(lo)) return [0, 1];
    return [lo, hi];
  }

  function pad(lo, hi, ratio) {
    if (lo === hi) { const d = Math.abs(lo) * 0.1 || 1; return [lo - d, hi + d]; }
    const d = (hi - lo) * (ratio === undefined ? 0.07 : ratio);
    return [lo - d, hi + d];
  }

  function render(container, spec) {
    container.innerHTML = "";
    const width = Math.max(320, container.clientWidth || 640);
    const aspect = spec.aspect || 0.52;
    const height = Math.round(Math.min(Math.max(width * aspect, 250), 420));
    const m = { l: 62, r: 22, t: 14, b: 46 };
    const iw = width - m.l - m.r, ih = height - m.t - m.b;

    const xlog = !!spec.xlog, ylog = !!spec.ylog;
    const tx = v => (xlog ? Math.log10(v) : v);
    const ty = v => (ylog ? Math.log10(v) : v);
    const ok = (v, isLog) => isFinite(v) && (!isLog || v > 0);

    const allX = [], allY = [];
    (spec.series || []).forEach(s => (s.points || []).forEach(p => {
      const x = +p[0], y = +p[1];
      if (ok(x, xlog) && ok(y, ylog)) { allX.push(tx(x)); allY.push(ty(y)); }
    }));
    (spec.hlines || []).forEach(h => { if (ok(+h.y, ylog)) allY.push(ty(+h.y)); });
    (spec.vlines || []).forEach(v => { if (ok(+v.x, xlog)) allX.push(tx(+v.x)); });
    (spec.points || []).forEach(p => {
      if (ok(+p.x, xlog)) allX.push(tx(+p.x));
      if (ok(+p.y, ylog)) allY.push(ty(+p.y));
    });

    let [x0, x1] = spec.xrange ? [tx(+spec.xrange[0]), tx(+spec.xrange[1])] : pad(...extent(allX));
    let [y0, y1] = spec.yrange ? [ty(+spec.yrange[0]), ty(+spec.yrange[1])] : pad(...extent(allY));
    if (x1 === x0) x1 = x0 + 1;
    if (y1 === y0) y1 = y0 + 1;

    const sx = v => m.l + (tx(v) - x0) / (x1 - x0) * iw;
    const sy = v => m.t + (1 - (ty(v) - y0) / (y1 - y0)) * ih;

    const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, width: "100%", height: height, role: "img" }, container);

    // 网格与刻度
    const maxXt = Math.max(3, Math.floor(iw / 84));
    const maxYt = Math.max(3, Math.floor(ih / 46));
    const xt = xlog ? logTicks(x0, x1, Math.max(3, maxXt)) : niceTicks(x0, x1, maxXt);
    const yt = ylog ? logTicks(y0, y1, Math.max(4, maxYt + 1)) : niceTicks(y0, y1, maxYt);
    const gGrid = el("g", {}, svg);
    yt.forEach(v => {
      const y = sy(v);
      el("line", { x1: m.l, x2: m.l + iw, y1: y, y2: y, stroke: "#eef2f8", "stroke-width": 1 }, gGrid);
      el("text", { x: m.l - 9, y: y + 3.5, "text-anchor": "end", "font-size": 10.5, fill: "#475569", "font-family": "var(--mono)" }, gGrid).textContent = fmtNum(v);
    });
    xt.forEach(v => {
      const x = sx(v);
      el("line", { x1: x, x2: x, y1: m.t, y2: m.t + ih, stroke: "#f3f6fb", "stroke-width": 1 }, gGrid);
      el("text", { x: x, y: m.t + ih + 17, "text-anchor": "middle", "font-size": 10.5, fill: "#475569", "font-family": "var(--mono)" }, gGrid).textContent = fmtNum(v);
    });

    // 轴
    el("line", { x1: m.l, x2: m.l + iw, y1: m.t + ih, y2: m.t + ih, stroke: "#cbd5e1", "stroke-width": 1.2 }, svg);
    el("line", { x1: m.l, x2: m.l, y1: m.t, y2: m.t + ih, stroke: "#cbd5e1", "stroke-width": 1.2 }, svg);

    // 轴标题
    if (spec.xlabel) {
      const t = richText(el("text", { x: m.l + iw / 2, y: height - 8, "text-anchor": "middle", "font-size": 11.5, fill: "#64748b" }, svg), spec.xlabel);
    }
    if (spec.ylabel) {
      const t = richText(el("text", { x: 14, y: m.t + ih / 2, "text-anchor": "middle", "font-size": 11.5, fill: "#64748b", transform: `rotate(-90 14 ${m.t + ih / 2})` }, svg), spec.ylabel);
    }

    // 水平 / 垂直参考线
    const usedLblY = [];
    (spec.hlines || []).forEach(h => {
      if (!ok(+h.y, ylog)) return;
      const y = sy(+h.y);
      el("line", { x1: m.l, x2: m.l + iw, y1: y, y2: y, stroke: h.color || "#64748b", "stroke-width": 1.2, "stroke-dasharray": "5 4" }, svg);
      if (h.label) {
        let ly = y - 5;
        while (usedLblY.some(v => Math.abs(v - ly) < 12)) ly -= 12;
        usedLblY.push(ly);
        richText(el("text", { x: m.l + iw - 4, y: ly, "text-anchor": "end", "font-size": 10.5, fill: h.color || "#64748b", stroke: "#fff", "stroke-width": 3.2, "paint-order": "stroke" }, svg), h.label);
      }
    });
    const labelTops = [];
    (spec.vlines || []).forEach(v => {
      if (!ok(+v.x, xlog)) return;
      const x = sx(+v.x);
      el("line", { x1: x, x2: x, y1: m.t, y2: m.t + ih, stroke: v.color || "#f59e0b", "stroke-width": 1.2, "stroke-dasharray": "5 4" }, svg);
      if (v.label) {
        // 靠近的竖线标签自动错层，避免叠字
        let y = m.t + 11;
        while (labelTops.some(o => Math.abs(o.x - x) < 64 && Math.abs(o.y - y) < 12)) y += 13;
        labelTops.push({ x: x, y: y });
        richText(el("text", { x: x + 4, y: y, "font-size": 10.5, fill: v.color || "#b45309", stroke: "#fff", "stroke-width": 3.2, "paint-order": "stroke" }, svg), v.label);
      }
    });

    // 数据系列（线先画，点最后画）
    const order = (spec.series || []).map((s, i) => ({ s, i }))
      .sort((a, b) => (a.s.type === "scatter" ? 1 : 0) - (b.s.type === "scatter" ? 1 : 0));
    order.forEach(({ s, i }) => {
      const color = s.color || PALETTE[i % PALETTE.length];
      const pts = (s.points || []).filter(p => ok(+p[0], xlog) && ok(+p[1], ylog));
      if (!pts.length) return;
      if (s.type === "scatter") {
        const g = el("g", {}, svg);
        pts.forEach(p => {
          el("circle", { cx: sx(+p[0]), cy: sy(+p[1]), r: s.r || 3.1, fill: color, "fill-opacity": 0.82, stroke: "#fff", "stroke-width": 1 }, g);
        });
        s._g = g;
      } else {
        let d = "";
        if (s.type === "step") {
          d = `M ${sx(+pts[0][0])} ${sy(+pts[0][1])}`;
          for (let k = 1; k < pts.length; k++) {
            d += ` H ${sx(+pts[k][0])} V ${sy(+pts[k][1])}`;
          }
        } else {
          d = pts.map((p, k) => `${k ? "L" : "M"} ${sx(+p[0])} ${sy(+p[1])}`).join(" ");
        }
        el("path", {
          d, fill: "none", stroke: color, "stroke-width": s.width || 2,
          "stroke-linecap": "round", "stroke-linejoin": "round",
          "stroke-dasharray": s.dash ? "6 5" : null
        }, svg);
      }
    });

    // 标注点
    (spec.points || []).forEach(p => {
      if (!ok(+p.x, xlog) || !ok(+p.y, ylog)) return;
      const x = sx(+p.x), y = sy(+p.y);
      el("circle", { cx: x, cy: y, r: 4.2, fill: "#fff", stroke: p.color || "#e11d48", "stroke-width": 2 }, svg);
      if (p.label) {
        richText(el("text", { x: x + 8, y: y - 8, "font-size": 10.5, fill: p.color || "#be123c", "font-weight": 600 }, svg), p.label);
        let bb;
        try { bb = txt.getBBox(); } catch (e) { bb = null; }
        if (bb && bb.width) {
          const rect = el("rect", { x: bb.x - 4, y: bb.y - 2, width: bb.width + 8, height: bb.height + 4, rx: 4, fill: "#fff", "fill-opacity": 0.85 }, null);
          svg.insertBefore(rect, txt);
        }
      }
    });

    // hover 提示
    const tip = document.getElementById("tooltip");
    const flat = [];
    (spec.series || []).forEach(s => (s.points || []).forEach(p => {
      const x = +p[0], y = +p[1];
      if (ok(x, xlog) && ok(y, ylog)) flat.push({ x, y, name: s.name || "", color: s.color });
    }));
    svg.addEventListener("mousemove", ev => {
      const rect = svg.getBoundingClientRect();
      const px = (ev.clientX - rect.left) * (width / rect.width);
      const py = (ev.clientY - rect.top) * (height / rect.height);
      if (px < m.l - 6 || px > m.l + iw + 6 || py < m.t - 6 || py > m.t + ih + 6) { tip.style.opacity = 0; return; }
      let best = null, bd = 26 * 26;
      flat.forEach(p => {
        const dx = sx(p.x) - px, dy = sy(p.y) - py;
        const d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = p; }
      });
      if (!best) { tip.style.opacity = 0; return; }
      tip.innerHTML = `<b>${best.name}</b><br>${spec.xlabel ? spec.xlabel.split("/")[0].trim() : "x"} = ${fmtNum(best.x)}<br>${spec.ylabel ? spec.ylabel.split("/")[0].trim() : "y"} = ${fmtNum(best.y)}`;
      tip.style.left = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 10) + "px";
      tip.style.top = (ev.clientY - tip.offsetHeight - 12) + "px";
      tip.style.opacity = 1;
    });
    svg.addEventListener("mouseleave", () => { tip.style.opacity = 0; });

    container._spec = spec;
    container._svg = svg;
    return svg;
  }

  // 宽度变化时重绘
  const ro = new ResizeObserver(entries => {
    entries.forEach(e => {
      const c = e.target;
      if (c._spec && c._lastW !== Math.round(c.clientWidth)) {
        c._lastW = Math.round(c.clientWidth);
        render(c, c._spec);
      }
    });
  });

  global.Chart = {
    render(container, spec) {
      container._lastW = Math.round(container.clientWidth);
      ro.observe(container);
      return render(container, spec);
    },
    download(container, name) {
      const svg = container._svg;
      if (!svg) return;
      const clone = svg.cloneNode(true);
      clone.setAttribute("xmlns", NS);
      const bg = document.createElementNS(NS, "rect");
      bg.setAttribute("width", "100%"); bg.setAttribute("height", "100%"); bg.setAttribute("fill", "#ffffff");
      clone.insertBefore(bg, clone.firstChild);
      const blob = new Blob([new XMLSerializer().serializeToString(clone)], { type: "image/svg+xml;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = (name || "chart") + ".svg";
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 3000);
    },
  };
})(window);
