/* 工作台前端逻辑 */
const $ = s => document.querySelector(s);
const PALETTE = ["#2563eb", "#e5533d", "#0ea5a4", "#8b5cf6", "#f59e0b", "#0e7490", "#db2777", "#65a30d"];

const S = { specs: [], spec: null, data: { tables: {}, params: {} }, result: null, filter: "" };

async function api(url, opt) {
  const r = await fetch(url, opt);
  let j;
  try { j = await r.json(); } catch (e) { j = { ok: false, error: "服务返回异常（HTTP " + r.status + "）" }; }
  if (!r.ok && !j.error) j.error = "HTTP " + r.status;
  return j;
}

const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ---- 上下标与公式：_{x} ^{x} $..$ ---- */
const MATH_SYM = {
  "\\Delta": "Δ", "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\Gamma": "Γ",
  "\\delta": "δ", "\\epsilon": "ε", "\\varepsilon": "ε", "\\zeta": "ζ", "\\eta": "η",
  "\\theta": "θ", "\\kappa": "κ", "\\lambda": "λ", "\\Lambda": "Λ", "\\mu": "μ",
  "\\nu": "ν", "\\xi": "ξ", "\\pi": "π", "\\rho": "ρ", "\\sigma": "σ", "\\Sigma": "Σ",
  "\\tau": "τ", "\\phi": "φ", "\\varphi": "φ", "\\chi": "χ", "\\psi": "ψ", "\\omega": "ω",
  "\\Omega": "Ω", "\\times": "×", "\\cdot": "·", "\\pm": "±", "\\infty": "∞",
  "\\le": "≤", "\\leq": "≤", "\\ge": "≥", "\\geq": "≥", "\\ne": "≠", "\\approx": "≈",
  "\\sum": "∑", "\\int": "∫", "\\partial": "∂", "\\%": "%", "\\,": "\u2009", "\\;": "\u2009",
};
const MATH_FUNCS = ["ln", "lg", "log", "exp", "sin", "cos", "tan", "max", "min"];

/* 取一个参数：{...} 或单个字符 */
function texGroup(s, i) {
  while (i < s.length && s[i] === " ") i++;
  if (s[i] === "{") {
    let depth = 0, j = i;
    for (; j < s.length; j++) {
      if (s[j] === "{") depth++;
      else if (s[j] === "}") { depth--; if (depth === 0) break; }
    }
    return [s.slice(i + 1, j), j + 1];
  }
  if (i < s.length) return [s[i], i + 1];
  return ["", i];
}
/* 把一段 LaTeX 子集渲染成 HTML（递归、括号配对） */
function texHTML(s) {
  let out = "", i = 0;
  while (i < s.length) {
    const ch = s[i];
    if (ch === "\\") {
      let j = i + 1;
      while (j < s.length && /[A-Za-z]/.test(s[j])) j++;
      const cmd = s.slice(i, j);
      const rest = s[j] === " " ? j + 1 : j;
      if (cmd === "\\frac") {
        const [a, i1] = texGroup(s, rest);
        const [b, i2] = texGroup(s, i1);
        out += `<span class="frac"><span class="num">${texHTML(a)}</span><span class="den">${texHTML(b)}</span></span>`;
        i = i2; continue;
      }
      if (cmd === "\\sqrt") {
        const [a, i1] = texGroup(s, rest);
        out += `<span class="sqrt">√<span class="rad">${texHTML(a)}</span></span>`;
        i = i1; continue;
      }
      if (cmd === "\\text" || cmd === "\\mathrm") {
        const [a, i1] = texGroup(s, rest);
        out += `<i class="up">${esc(a)}</i>`;
        i = i1; continue;
      }
      if (cmd === "\\left" || cmd === "\\right") { i = rest; continue; }
      if (MATH_SYM[cmd] !== undefined) { out += MATH_SYM[cmd]; i = rest; continue; }
      if (MATH_FUNCS.indexOf(cmd.slice(1)) >= 0) { out += `<i class="up">${cmd.slice(1)}</i>`; i = rest; continue; }
      out += esc(cmd); i = rest; continue;
    }
    if (ch === "_" || ch === "^") {
      const [a, i1] = texGroup(s, i + 1);
      out += ch === "_" ? `<sub>${texHTML(a)}</sub>` : `<sup>${texHTML(a)}</sup>`;
      i = i1; continue;
    }
    if (ch === "{" || ch === "}") { i++; continue; }
    out += esc(ch);
    i++;
  }
  return out;
}
function plainRich(str) {
  let t = esc(str);
  t = t.replace(/_\{([^{}]*)\}/g, "<sub>$1</sub>");
  t = t.replace(/\^\{([^{}]*)\}/g, "<sup>$1</sup>");
  /* 兜底：未加花括号的 ASCII 写法，如 k_H、M^0.78 */
  t = t.replace(/([^\s{_])_(?:([A-Za-z][A-Za-z0-9]{0,11})|([0-9]{1,2})|([\u4e00-\u9fff]{1,4})|(\u221e))(?![A-Za-z0-9{<])/g, function(m,a,b,c,d){return a+"<sub>"+(b||c||d||e)+"</sub>";});
  t = t.replace(/\^([A-Za-z0-9.\-∞]{1,6})(?![A-Za-z0-9{<])/g, "<sup>$1</sup>");
  return t;
}
/* 统一入口：普通字符、上下标记号、$行内公式$、$$独立公式$$ 可混排 */
function rich(s) {
  const str = String(s == null ? "" : s);
  const parts = str.split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g);
  return parts.map(p => {
    if (p.startsWith("$$") && p.endsWith("$$") && p.length > 4) return `<span class="math">${texHTML(p.slice(2, -2))}</span>`;
    if (p.startsWith("$") && p.endsWith("$") && p.length > 2) return `<span class="math">${texHTML(p.slice(1, -1))}</span>`;
    return plainRich(p);
  }).join("");
}
function toast(msg, bad) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show" + (bad ? " bad" : "");
  clearTimeout(t._h);
  t._h = setTimeout(() => (t.className = "toast"), 2600);
}

/* ---------------- 剪贴板：复制表格到 Excel ---------------- */
async function copyText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (e) { /* 落到下面的兜底方案 */ }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.top = "-1000px";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  ta.setSelectionRange(0, text.length);
  let ok = false;
  try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
  ta.remove();
  return ok;
}

/** 表头里的上下标记号转成 Excel 里好读的纯文本（k^{-1} → k^-1） */
function labelText(s) {
  return String(s == null ? "" : s)
    .replace(/\$\$?/g, "")
    .replace(/\^\{([^{}]*)\}/g, "^$1")
    .replace(/_\{([^{}]*)\}/g, "_$1");
}

/** 按 Excel 习惯用 TSV（制表符 + 换行）拼表格文本，首行是表头 */
function toTSV(head, rows) {
  const cell = v => String(v == null ? "" : v).replace(/[\t\r\n]+/g, " ").trim();
  const lines = [head.map(cell).join("\t")];
  (rows || []).forEach(r => lines.push((r || []).map(cell).join("\t")));
  return lines.join("\r\n");
}

async function copyTable(head, rows, tip) {
  const ok = await copyText(toTSV(head, rows));
  toast(ok
    ? `已复制 ${rows.length} 行 × ${head.length} 列${tip ? "（" + tip + "）" : ""}，可直接粘贴到 Excel`
    : "复制失败：浏览器不允许写剪贴板，请改用「导出 Excel」", !ok);
}

function fmtNum(v, digits) {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v !== "number") return v;
  if (!isFinite(v)) return "—";
  const d = digits === undefined ? 4 : digits;
  if (v === 0) return "0";
  const a = Math.abs(v);
  if (a >= 1e5 || a < 1e-6) return v.toExponential(2).replace("e+", "e");
  if (a < 1e-3) return v.toPrecision(3).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
  return parseFloat(v.toFixed(d)).toString();
}

/** 数据表里显示的数值：10 位有效数字，去掉浮点尾巴（足够保留实验原始精度，又不显示 0.30000000000000004） */
function fmtCell(v) {
  if (typeof v !== "number" || !isFinite(v)) return String(v);
  if (v === 0) return "0";
  return Number(v.toPrecision(10)).toString();
}

/* ---------------- 启动 ---------------- */
window.addEventListener("hashchange", () => {
  const id = (location.hash || "").replace("#", "");
  if (!id) { if (S.spec) goHome(); return; }
  if (S.spec && S.spec.id === id) return;
  selectSpec(id);
});

async function boot() {
  const specs = await api("/api/experiments");
  if (!Array.isArray(specs)) { $("#name").textContent = "无法连接本地服务"; return; }
  S.specs = specs;
  $("#stat-count").textContent = specs.length;
  buildNav();
  const brand = document.querySelector(".brand");
  if (brand) { brand.style.cursor = "pointer"; brand.title = "返回总览"; brand.onclick = goHome; }
  const id = (location.hash || "").replace("#", "");
  if (id && specs.some(s => s.id === id)) selectSpec(id);
  else goHome();
}

/* ---------------- 总览 ---------------- */
function goHome() {
  S.spec = null;
  S.result = null;
  history.replaceState(null, "", location.pathname);
  $("#home").hidden = false;
  document.querySelector(".topbar").hidden = true;
  document.querySelector(".scroll").hidden = true;
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.title = "物化 / 化工实验数据处理工作台";
  renderHome();
}

function renderHome() {
  const specs = S.specs || [];
  const groups = {};
  specs.forEach(s => (groups[s.group] = (groups[s.group] || []).concat(s)));
  $("#hero-stats").innerHTML = [
    `<div class="hero-stat"><b>${specs.length}</b><span>实验模块</span></div>`,
    ...Object.keys(groups).map(g => `<div class="hero-stat"><b>${groups[g].length}</b><span>${esc(g)}实验</span></div>`),
    `<div class="hero-stat"><b>100%</b><span>本机计算</span></div>`,
  ].join("");
  const grid = $("#home-grid");
  grid.innerHTML = "";
  Object.keys(groups).forEach(g => {
    const sec = document.createElement("section");
    sec.innerHTML = `<div class="home-group-title"><span>${esc(g)}实验</span><em>${groups[g].length}</em></div><div class="cards"></div>`;
    const cards = sec.querySelector(".cards");
    groups[g].forEach(s => {
      const c = document.createElement("div");
      c.className = "exp-card";
      c.innerHTML = `<div class="ec-top"><span class="ec-code">${esc(s.code)}</span><span class="ec-go">→</span></div>
        <h4>${esc(s.name)}</h4>
        <p>${rich(s.subtitle || "")}</p>
        <div class="ec-tags">${(s.tags || []).slice(0, 3).map(t => `<span>${esc(t)}</span>`).join("")}</div>`;
      c.onclick = () => selectSpec(s.id);
      cards.appendChild(c);
    });
    grid.appendChild(sec);
  });
}

function buildNav() {
  const q = S.filter.trim().toLowerCase();
  const list = S.specs.filter(s => {
    if (!q) return true;
    return (s.code + " " + s.name + " " + (s.tags || []).join(" ") + " " + s.subtitle).toLowerCase().includes(q);
  });
  const groups = {};
  list.forEach(s => (groups[s.group] = groups[s.group] || []).push(s));
  const nav = $("#nav");
  nav.innerHTML = "";
  const home = document.createElement("div");
  home.className = "nav-item nav-home" + (S.spec ? "" : " active");
  home.innerHTML = '<span class="code">⌂</span><span class="name">全部实验</span>';
  home.onclick = goHome;
  nav.appendChild(home);
  Object.keys(groups).forEach(g => {
    const wrap = document.createElement("div");
    wrap.className = "nav-group";
    wrap.innerHTML = `<div class="nav-title"><span>${esc(g)}实验</span><em>${groups[g].length}</em></div>`;
    groups[g].forEach(s => {
      const a = document.createElement("div");
      a.className = "nav-item" + (S.spec && S.spec.id === s.id ? " active" : "");
      a.dataset.id = s.id;
      a.title = s.name;
      a.innerHTML = `<span class="code">${esc(s.code)}</span><span class="name">${esc(s.name)}</span>`;
      a.onclick = () => selectSpec(s.id);
      wrap.appendChild(a);
    });
    nav.appendChild(wrap);
  });
  if (!list.length) nav.innerHTML += '<div class="nav-empty">没有匹配的实验</div>';
}

/* ---------------- 选择实验 ---------------- */
function selectSpec(id) {
  const spec = S.specs.find(s => s.id === id);
  if (!spec) return;
  $("#home").hidden = true;
  document.querySelector(".topbar").hidden = false;
  document.querySelector(".scroll").hidden = false;
  document.querySelector(".scroll").scrollTop = 0;
  S.spec = spec;
  S.result = null;
  S.data = { tables: {}, params: {} };
  (spec.tables || []).forEach(t => {
    S.data.tables[t.key] = (t.rows || []).map(r => r.slice());
  });
  (spec.params || []).forEach(p => { S.data.params[p.key] = p.default; });

  location.hash = id;
  history.replaceState(null, "", "#" + id);
  document.title = spec.code + " " + spec.name + " · 实验工作台";
  document.querySelectorAll(".nav-item").forEach(n => n.classList.toggle("active", n.dataset.id === id));

  $("#code").textContent = spec.code;
  $("#name").textContent = spec.name;
  $("#subtitle").innerHTML = rich(spec.subtitle || "");
  $("#eyebrow").textContent = (spec.group || "") + "实验 · " + (spec.tags || []).slice(0, 2).join(" / ");
  $("#tags").innerHTML = (spec.tags || []).map((t, i) =>
    `<span class="tag${i % 2 ? " teal" : ""}">${esc(t)}</span>`).join("");
  $("#method").innerHTML = (spec.method || []).map(m => `<li>${rich(m)}</li>`).join("");
  const fml = spec.formulas || [];
  $("#formulas").innerHTML = fml.map(f => `<div class="formula-line">${rich(`$$${f}$$`)}</div>`).join("");
  $("#desc").innerHTML = rich(spec.desc || "");

  renderParams();
  renderInputTables();
  loadMaterials();
  clearResult();
  run();
}

/** 切换实验时立刻清空结果区，避免显示上一个实验的旧结果 */
function clearResult() {
  S.result = null;
  S.runToken = (S.runToken || 0) + 1;
  $("#summary").innerHTML = '<span class="calc-hint">正在计算…</span>';
  $("#kpis").innerHTML = "";
  $("#charts").innerHTML = "";
  $("#tables-out").innerHTML = "";
  $("#warnings").innerHTML = "";
  $("#warnings").classList.remove("show");
  $("#notes").innerHTML = "";
  $("#elapsed").textContent = "";
  $("#messages").innerHTML = "";
}

/* ---------------- 参数 ---------------- */
function renderParams() {
  const spec = S.spec;
  const box = $("#params");
  if (!spec.params || !spec.params.length) { box.innerHTML = ""; return; }
  let h = `<div class="card"><div class="card-head"><h3>参数设置</h3><span class="sub">一般保持默认即可</span></div><div class="param-grid">`;
  spec.params.forEach(p => {
    const v = S.data.params[p.key];
    h += `<div class="param"><label><span class="lb">${rich(p.label)}</span>${p.unit ? `<span class="unit">${rich(p.unit)}</span>` : ""}</label>`;
    if (p.type === "select") {
      h += `<select data-param="${esc(p.key)}">` + (p.options || []).map(o =>
        `<option value="${esc(o.value)}"${String(o.value) === String(v) ? " selected" : ""}>${rich(o.label)}</option>`).join("") + `</select>`;
    } else if (p.type === "checkbox") {
      h += `<input type="checkbox" data-param="${esc(p.key)}"${v ? " checked" : ""}>`;
    } else {
      h += `<input type="number" step="${p.step || "any"}" data-param="${esc(p.key)}" value="${esc(v)}">`;
    }
    if (p.hint) h += `<span class="hint">${rich(p.hint)}</span>`;
    h += `</div>`;
  });
  h += `</div></div>`;
  box.innerHTML = h;
  box.querySelectorAll("[data-param]").forEach(inp => {
    inp.addEventListener("change", () => {
      S.data.params[inp.dataset.param] = inp.type === "checkbox" ? inp.checked : inp.value;
      scheduleRun(0);
    });
    inp.addEventListener("input", () => {
      S.data.params[inp.dataset.param] = inp.type === "checkbox" ? inp.checked : inp.value;
      if (inp.tagName !== "SELECT") scheduleRun(900);
    });
  });
}

/* ---------------- 输入数据表 ---------------- */
function renderInputTables() {
  const box = $("#tables-input");
  box.innerHTML = "";
  (S.spec.tables || []).forEach(t => {
    const card = document.createElement("div");
    card.className = "card table-card";
    card.innerHTML = `
      <div class="card-head">
        <h3>${rich(t.title || t.key)}</h3>
        <div>
          <button class="link-btn" data-act="import">导入文件</button>
        </div>
      </div>
      ${t.note ? `<div class="table-note">${rich(t.note)}</div>` : ""}
      <div class="table-wrap"><table class="data" data-key="${esc(t.key)}">
        <thead><tr><th>#</th>${(t.columns || []).map(c => `<th>${rich(c.label || c.key)}</th>`).join("")}</tr></thead>
        <tbody></tbody>
      </table></div>
      <div class="table-tools">
        <button class="mini-btn" data-act="add">＋ 加行</button>
        <button class="mini-btn" data-act="del">－ 删末行</button>
        <button class="mini-btn" data-act="clear">清空</button>
        <button class="mini-btn" data-act="copy" title="把整张表复制到剪贴板，可直接粘贴到 Excel">复制表格</button>
        <input type="file" accept=".xlsx,.xls,.csv,.txt" hidden>
        <span class="spacer"></span>
        <span class="table-count">${(t.rows || []).length} 行 · 可粘贴 / 复制 Excel 区域</span>
      </div>`;
    box.appendChild(card);
    fillTable(card, t);
    bindTable(card, t);
  });
}

function fillTable(card, t) {
  const tb = card.querySelector("tbody");
  const rows = S.data.tables[t.key] || [];
  tb.innerHTML = rows.map((row, r) => `<tr>` + `<td class="idx" data-r="${r}">${r + 1}</td>` +
    (t.columns || []).map((c, j) => {
      const v = row[j] == null ? "" : (typeof row[j] === "number" ? fmtCell(row[j]) : row[j]);
      return `<td><input data-r="${r}" data-c="${j}" inputmode="decimal" value="${esc(v)}"></td>`;
    }).join("") + `</tr>`).join("");
  tb.querySelectorAll("input").forEach(fitInput);
}

/** 输入框按数字长度自适应宽度（兼容不支持 field-sizing 的浏览器） */
const _fitCtx = document.createElement("canvas").getContext("2d");
function fitInput(inp) {
  _fitCtx.font = "12px ui-monospace, Consolas, monospace";
  const w = _fitCtx.measureText(inp.value || "0").width;
  inp.style.minWidth = Math.max(80, Math.ceil(w) + 20) + "px";
}

function bindTable(card, t) {
  const table = card.querySelector("table");
  table.addEventListener("input", e => {
    const inp = e.target.closest("input[data-r]");
    if (!inp) return;
    const r = +inp.dataset.r, c = +inp.dataset.c;
    S.data.tables[t.key][r][c] = inp.value;
    fitInput(inp);
    scheduleRun(900);
  });
  table.addEventListener("change", e => {
    if (e.target.closest("input[data-r]")) scheduleRun(0);
  });
  table.addEventListener("paste", e => {
    const target = e.target;
    const td = target.closest("td");
    if (!td) return;
    const text = (e.clipboardData || window.clipboardData).getData("text");
    if (text === null || text === undefined) return;
    if (!/[\t\r\n]/.test(text)) return;         // 单元格内正常粘贴单个值
    e.preventDefault();
    /* 起点：优先取输入框上的 data-r/data-c（原来误读 td 的 dataset，导致整块粘贴永远失效） */
    const inp = target.closest("input[data-r]");
    const startR = inp ? +inp.dataset.r : +td.dataset.r || 0;
    const startC = inp ? +inp.dataset.c : (td.classList.contains("idx") ? 0 : 0);
    const lines = text.replace(/\r/g, "").split("\n").filter(l => l.trim() !== "");
    if (!lines.length) return;
    const grid = lines.map(l => l.split("\t"));
    const width = (t.columns || []).length;
    const need = startR + grid.length;
    const rows = S.data.tables[t.key];
    while (rows.length < need) rows.push(new Array(width).fill(""));
    let filled = 0;
    grid.forEach((line, i) => line.forEach((v, j) => {
      const r = startR + i, c = startC + j;
      if (r < rows.length && c < width) { rows[r][c] = v.trim(); filled++; }
    }));
    fillTable(card, t);
    updateCount(card, t);
    toast(`已粘贴 ${grid.length} 行 × ${grid[0].length} 列（写入 ${filled} 个单元格）`);
    scheduleRun();
  });
  card.querySelectorAll("[data-act]").forEach(btn => {
    btn.onclick = async () => {
      const act = btn.dataset.act;
      const rows = S.data.tables[t.key];
      const n = (t.columns || []).length;
      if (act === "add") rows.push(new Array(n).fill(""));
      if (act === "del") { if (rows.length > 1) rows.pop(); }
      if (act === "clear") { S.data.tables[t.key] = [new Array(n).fill("")]; }
      if (act === "copy") {
        const head = (t.columns || []).map(c => labelText(c.label || c.key));
        await copyTable(head, S.data.tables[t.key], t.title || t.key);
        return;
      }
      if (act === "import") { card.querySelector("input[type=file]").click(); return; }
      fillTable(card, t);
      updateCount(card, t);
      if (act !== "clear") scheduleRun();
    };
  });
  const file = card.querySelector("input[type=file]");
  file.onchange = async () => {
    if (!file.files.length) return;
    const n = (t.columns || []).length;
    const fd = new FormData();
    fd.append("file", file.files[0]);
    fd.append("cols", String(n));          // 告诉后端目标列数，便于自动对齐（去掉多余的序号列）
    toast("正在读取文件…");
    const res = await api("/api/import", { method: "POST", body: fd });
    file.value = "";
    if (!res.ok) { toast(res.error || "读取失败", true); return; }
    const num = v => v === "" || !isNaN(Number(String(v).replace(/[\s,]/g, "")));
    let rows = (res.rows || []).map(r => (r || []).slice(0, n));
    rows = rows.filter(r => r.some(v => String(v).trim() !== ""));
    if (!rows.length) { toast("文件里没有数据", true); return; }
    // 旧后端兜底：只有后端没给 header 信息时，才在前端再剔一次可能的文字表头
    // （新后端已经剔过表头，数据行里带文字列时不能再剔，否则会丢第一条数据）
    if (!Array.isArray(res.header) && rows.length > 1 && !rows[0].every(num)) rows = rows.slice(1);
    S.data.tables[t.key] = rows.map(r => { while (r.length < n) r.push(""); return r; });
    fillTable(card, t);
    updateCount(card, t);
    // 逐格检查：不是数字的直接点名，避免"导进去算不出来"却不知道错在哪
    const bad = [];
    rows.forEach((r, i) => r.forEach((v, j) => {
      const col = (t.columns || [])[j] || {};
      if (String(v).trim() === "") return;
      if (col.type && col.type !== "text" && isNaN(Number(String(v).replace(/[\s,]/g, "")))) {
        bad.push(`第 ${i + 1} 行「${labelText(col.label || col.key)}」`);
      }
    }));
    const extra = (res.notes || []).join("；");
    if (bad.length) {
      toast(`已导入 ${rows.length} 行，但有 ${bad.length} 格不是数字（如 ${bad.slice(0, 2).join("、")}）${extra ? "；" + extra : ""}`, true);
    } else {
      toast(`已导入 ${rows.length} 行 × ${rows[0].length} 列${extra ? "（" + extra + "）" : ""}，${res.name || ""}`);
    }
    scheduleRun();
  };
}

function updateCount(card, t) {
  const c = card.querySelector(".table-count");
  if (c) c.textContent = `${S.data.tables[t.key].length} 行 · 可粘贴 / 复制 Excel 区域`;
}

/* ---------------- 原始资料 ---------------- */
const ICONS = {
  py: '<path d="M8 3h6l4 4v14H8z"/><path d="M14 3v4h4"/>',
  xlsx: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 9l8 6M16 9l-8 6"/>',
  docx: '<path d="M7 3h7l4 4v14H7z"/><path d="M13 3v5h5M10 12h5M10 16h5"/>',
  pdf: '<path d="M7 3h7l4 4v14H7z"/><path d="M13 3v5h5"/>',
  png: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="m5 18 5-5 4 3 3-2 3 4"/>',
  other: '<path d="M7 3h7l4 4v14H7z"/><path d="M13 3v5h5"/>',
};

function icon(ext) {
  const p = ICONS[ext] || ICONS.other;
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round">${p}</svg>`;
}

async function loadMaterials() {
  const box = $("#materials");
  box.innerHTML = '<div class="muted">加载中…</div>';
  const res = await api("/api/materials?id=" + encodeURIComponent(S.spec.id));
  const files = res.files || [];
  if (!files.length) { box.innerHTML = '<div class="muted">该实验暂无归档资料</div>'; return; }
  const groups = {};
  files.forEach(f => {
    const parts = f.rel.split("/");
    const g = parts.length > 1 ? parts[0] : "根目录";
    (groups[g] = groups[g] || []).push(f);
  });
  let h = "";
  Object.keys(groups).forEach(g => {
    h += `<div class="mat-group"><b>${esc(g)}</b>`;
    groups[g].forEach(f => {
      const ext = (f.name.split(".").pop() || "").toLowerCase();
      h += `<a class="mat" data-rel="${esc(f.rel)}" data-ext="${ext}" title="${esc(f.rel)}">
        ${icon(ext)}<span>${esc(f.name)}</span><span class="size">${(f.size / 1024).toFixed(0)}K</span></a>`;
    });
    h += `</div>`;
  });
  box.innerHTML = h;
  box.querySelectorAll(".mat").forEach(a => {
    a.onclick = () => {
      const url = `/api/material?id=${encodeURIComponent(S.spec.id)}&path=${encodeURIComponent(a.dataset.rel)}`;
      if (["pdf", "png", "jpg", "jpeg", "svg"].includes(a.dataset.ext)) window.open(url + "&inline=1", "_blank");
      else window.location.href = url;
    };
  });
}

/* ---------------- 运行 ---------------- */
let _runTimer = null;
/** 改完数据后自动重算（防抖），减少“改了却没点运行”的困惑 */
function scheduleRun(delay = 450) {
  clearTimeout(_runTimer);
  _runTimer = setTimeout(() => run(), delay);
}

async function run() {
  if (!S.spec) return;
  const token = (S.runToken = (S.runToken || 0) + 1);
  const btn = $("#btn-run");
  btn.disabled = true;
  const old = btn.innerHTML;
  btn.innerHTML = '<span class="spinner" style="width:14px;height:14px;border-width:2px"></span> 计算中…';
  $("#messages").innerHTML = "";
  const payload = { id: S.spec.id, tables: S.data.tables, params: S.data.params };
  const res = await api("/api/run", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  if (token !== S.runToken) return;   // 已切换实验或有更新的计算，丢弃旧响应
  btn.disabled = false;
  btn.innerHTML = old;
  if (!res.ok) { showError(res); return; }
  S.result = res;
  renderResult(res);
  $("#elapsed").textContent = `耗时 ${res.elapsed_ms} ms`;
}

function showError(res) {
  S.result = null;
  $("#summary").innerHTML = "";
  $("#warnings").innerHTML = "";
  $("#warnings").classList.remove("show");
  $("#kpis").innerHTML = "";
  $("#charts").innerHTML = "";
  $("#tables-out").innerHTML = "";
  $("#notes").innerHTML = "";
  $("#elapsed").textContent = "";
  const raw = String(res.error || "未知错误");
  const friendly = raw.replace(/^\s*\w*Error:\s*/, "").split("\n")[0];
  $("#messages").innerHTML = `<div class="msg err">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.5"/></svg>
    <div><b>这次没能算出结果</b>
    <p class="err-tip">${esc(friendly)}</p>
    <p class="err-hint">请检查：数据是否粘贴完整、每个格子里是不是数字、列的顺序是否和表头一致。</p>
    ${res.trace && res.trace.length ? `<details class="trace"><summary>技术细节</summary><pre>${esc((res.trace || []).join("\n"))}</pre></details>` : ""}</div></div>`;
}

function renderResult(res) {
  // 一句话结论（取第一个 KPI）
  const kpis = res.kpis || [];
  const k0 = kpis[0];
  $("#summary").innerHTML = k0
    ? `本次结果：${rich(k0.label)} = <b>${esc(fmtNum(k0.value, k0.digits))}${k0.unit ? " " + rich(k0.unit) : ""}</b>${k0.hint ? `<em> · ${rich(k0.hint)}</em>` : ""}`
    : "";

  $("#kpis").innerHTML = kpis.map(k => `
    <div class="kpi">
      <div class="k-label"><span>${rich(k.label)}</span></div>
      <div class="k-value"><span class="k-num">${esc(fmtNum(k.value, k.digits))}</span>${k.unit ? `<small>${rich(k.unit)}</small>` : ""}</div>
      ${k.hint ? `<div class="k-hint" title="${esc(k.hint)}">${rich(k.hint)}</div>` : ""}
    </div>`).join("");

  // 提示放到结果末尾，不干扰主要结论
  const warns = res.warnings || [];
  const wbox = $("#warnings");
  wbox.classList.toggle("show", warns.length > 0);
  const wlong = warns.join("").length > 180;
  wbox.innerHTML = wlong
    ? `<details class="notes warn-notes"><summary>⚠ ${warns.length} 条数据提示（点击展开；不影响主要结果）</summary>${warns.map(w => `<div class="msg warn"><span>${rich(w)}</span></div>`).join("")}</details>`
    : warns.map(w => `<div class="msg warn"><span>${rich(w)}</span></div>`).join("");

  // 图表
  const charts = res.charts || [];
  const cbox = $("#charts");
  cbox.innerHTML = "";
  charts.forEach((c, i) => {
    const card = document.createElement("div");
    card.className = "chart-card";
    card.innerHTML = `<div class="chart-head"><h3>${rich(c.title || "图表")}</h3>
        <div class="acts"><button class="link-btn" data-dl="${i}">下载 SVG</button></div></div>
      <div class="chart-body"></div><div class="legend"></div>`;
    cbox.appendChild(card);
    const body = card.querySelector(".chart-body");
    Chart.render(body, c);
    const seen = {};
    const lg = [];
    (c.series || []).forEach((s, k) => {
      if (seen[s.name]) return;
      seen[s.name] = 1;
      lg.push(`<span><i class="${s.type === "scatter" ? "" : "line"}" style="background:${s.color || PALETTE[k % PALETTE.length]}"></i>${rich(s.name)}</span>`);
    });
    card.querySelector(".legend").innerHTML = lg.join("");
    card.querySelector("[data-dl]").onclick = () => Chart.download(body, (S.spec.code + "-" + (c.title || "chart")).replace(/[\\/:*?"<>|]/g, "_"));
  });

  // 结果表
  const tbox = $("#tables-out");
  tbox.innerHTML = "";
  (res.tables || []).forEach(t => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `<div class="card-head"><h3>${rich(t.title || "结果")}</h3>
        <span class="acts"><span class="sub">${(t.rows || []).length} 行</span><button class="link-btn" data-copy-result title="整张结果表复制到剪贴板，可直接粘贴到 Excel">复制</button></span></div>
      <div class="result-wrap"><table class="result">
        <thead><tr>${(t.columns || []).map(c => `<th>${rich(c)}</th>`).join("")}</tr></thead>
        <tbody>${(t.rows || []).map(row => `<tr>${row.map(v => `<td>${typeof v === "number" ? esc(fmtNum(v, 6)) : rich(v)}</td>`).join("")}</tr>`).join("")}</tbody>
      </table></div>`;
    card.querySelector("[data-copy-result]").onclick = () => copyTable(
      (t.columns || []).map(labelText), t.rows || [], t.title || "结果表");
    tbox.appendChild(card);
  });

  // 说明
  const notes = res.notes || [];
  if (!notes.length) { $("#notes").innerHTML = ""; return; }
  const open = notes.length <= 2;
  $("#notes").innerHTML = `<details class="notes"${open ? " open" : ""}>
    <summary>计算说明${notes.length > 2 ? `（${notes.length} 条，点击展开）` : ""}</summary>
    <ul>${notes.map(n => `<li>${rich(n)}</li>`).join("")}</ul></details>`;
}

/* ---------------- 导出 / 复位 / 搜索 ---------------- */
async function exportXlsx() {
  if (!S.spec) return;
  toast("正在生成 Excel…");
  const res = await api("/api/export", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: S.spec.id, tables: S.data.tables, params: S.data.params }),
  });
  if (!res.ok) { toast(res.error || "导出失败", true); return; }
  window.location.href = "/api/download?file=" + encodeURIComponent(res.file);
  toast("已导出 " + res.file);
}

/* ---------------- Word 报告导出（可指定并记住保存位置） ---------------- */
const FS_DB = "lab-workbench";
function idbOpen() {
  return new Promise((res, rej) => {
    const r = indexedDB.open(FS_DB, 1);
    r.onupgradeneeded = () => { if (!r.result.objectStoreNames.contains("kv")) r.result.createObjectStore("kv"); };
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}
async function idbGet(k) {
  try {
    const db = await idbOpen();
    return await new Promise(res => {
      const q = db.transaction("kv").objectStore("kv").get(k);
      q.onsuccess = () => res(q.result || null);
      q.onerror = () => res(null);
    });
  } catch { return null; }
}
async function idbSet(k, v) {
  try { const db = await idbOpen(); db.transaction("kv", "readwrite").objectStore("kv").put(v, k); } catch {}
}

function svgToPng(svg, scale = 2) {
  return new Promise(resolve => {
    const box = svg.getBoundingClientRect();
    const w = Math.max(360, Math.round(box.width || 720));
    const h = Math.max(240, Math.round(box.height || 360));
    const clone = svg.cloneNode(true);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    clone.setAttribute("width", w);
    clone.setAttribute("height", h);
    const xml = new XMLSerializer().serializeToString(clone);
    const img = new Image();
    img.onload = () => {
      const cv = document.createElement("canvas");
      cv.width = w * scale; cv.height = h * scale;
      const ctx = cv.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, cv.width, cv.height);
      ctx.drawImage(img, 0, 0, cv.width, cv.height);
      resolve(cv.toDataURL("image/png").split(",")[1]);
    };
    img.onerror = () => resolve(null);
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(xml);
  });
}

async function saveDocxBlob(blob, name) {
  let dir = await idbGet("dir");
  let granted = false;
  if (dir) {
    try {
      granted = (await dir.queryPermission({ mode: "readwrite" })) === "granted";
      if (!granted) granted = (await dir.requestPermission({ mode: "readwrite" })) === "granted";
    } catch { granted = false; }
  }
  if (!dir && window.showDirectoryPicker) {
    try {
      dir = await window.showDirectoryPicker({ id: "lab-report-dir", mode: "readwrite", startIn: "documents" });
      await idbSet("dir", dir);
      granted = true;
      toast("以后报告都会自动存进这个文件夹");
    } catch { dir = null; }
  }
  if (dir && granted) {
    try {
      const fh = await dir.getFileHandle(name, { create: true });
      const w = await fh.createWritable();
      await w.write(blob);
      await w.close();
      toast("已保存：" + name);
      return;
    } catch (e) { toast("保存失败，改为下载", true); }
  }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  toast("已下载：" + name);
}

async function exportDocx(opts) {
  opts = opts || {};
  if (!S.spec) return;
  if (!S.result) { toast("先点「运行计算」再导出报告", true); return; }
  toast("正在生成 Word 报告…");
  const images = [];
  const cards = [...document.querySelectorAll("#charts .chart-card")];
  for (const card of cards) {
    const svg = card.querySelector("svg");
    if (!svg) continue;
    const png = await svgToPng(svg, 3);
    if (png) images.push({ title: (card.querySelector("h3") || {}).textContent || "", png });
  }
  let res;
  try {
    res = await fetch("/api/report-docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: S.spec.id, tables: S.data.tables, params: S.data.params, images }),
    });
  } catch (e) { toast("生成失败：连接中断", true); return; }
  if (!res.ok) {
    let msg = "生成失败";
    try { const j = await res.json(); msg = j.error || msg; } catch {}
    toast(msg.slice(0, 90), true);
    return;
  }
  if (opts.repick) await idbSet("dir", null);
  const blob = await res.blob();
  const name = `${S.spec.code}-${S.spec.name}-实验报告.docx`.replace(/[\\/:*?"<>|]/g, "_");
  await saveDocxBlob(blob, name);
}

function resetAll() {  if (!S.spec) return;
  (S.spec.tables || []).forEach(t => { S.data.tables[t.key] = (t.rows || []).map(r => r.slice()); });
  (S.spec.params || []).forEach(p => { S.data.params[p.key] = p.default; });
  renderParams();
  renderInputTables();
  run();
  toast("已恢复示例数据");
}

$("#search").addEventListener("input", e => { S.filter = e.target.value; buildNav(); });
$("#btn-run").onclick = run;
$("#btn-export").onclick = exportXlsx;
$("#btn-docx").onclick = (e) => exportDocx({ repick: e.shiftKey });
$("#btn-reset").onclick = resetAll;
$("#btn-folder").onclick = async () => {
  const r = await api("/api/open-folder?id=" + encodeURIComponent(S.spec.id));
  toast(r.ok ? "已打开资料文件夹" : (r.msg || "打开失败"), !r.ok);
};
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); }
});

boot();
