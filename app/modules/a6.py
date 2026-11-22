# -*- coding: utf-8 -*-
"""A6 旋光法测蔗糖转化速率常数：ln(αₜ−α∞)–t 线性回归求 k、半衰期，多组 c(H⁺) 求反应级数。"""
import math

from ..core import num, linfit, line_y

# 原始记录：每组自 t₀ 起每隔 60 s 读一次旋光度 αₜ（与 xlsx Sheet1 的 t/αₜ 两列逐行一致）
GROUPS = [
    {"id": 1, "t_0": 180, "a": [5.7, 5.45, 5.05, 4.7, 4.3, 4.0, 3.8, 3.45, 3.1, 3.05, 2.8, 2.7, 2.5,
                               2.25, 2.1, 1.95, 1.65, 1.3, 1.1, 0.85, 0.6, 0.55, 0.25, 0.1, -0.05]},
    {"id": 2, "t_0": 60, "a": [6.35, 6.1, 5.65, 5.3, 5.25, 5.15, 5.1, 4.85, 4.7, 4.4, 4.35, 4.15, 4.1,
                              3.85, 3.75, 3.6, 3.45, 3.2, 2.85, 2.6, 2.4, 2.1, 1.95, 1.8, 1.7]},
    {"id": 3, "t_0": 140, "a": [5.75, 5.5, 5.45, 5.35, 5.2, 5.05, 5.0, 4.8, 4.75, 4.5, 4.35, 4.1, 3.95,
                               3.9, 3.85, 3.7, 3.5, 3.35, 3.3, 3.15, 3.05, 3.0, 3.0, 2.9, 2.85]},
    {"id": 4, "t_0": 150, "a": [5.65, 5.55, 5.25, 4.95, 4.95, 4.85, 4.7, 4.65, 4.55, 4.55, 4.5, 4.4,
                               4.35, 4.1, 3.95, 3.9, 3.9, 3.75, 3.7, 3.65, 3.45, 3.4, 3.4, 3.3, 3.25]},
    {"id": 5, "t_0": 120, "a": [2.7, 2.45, 2.3, 2.2, 1.9, 1.9, 1.75, 1.6, 1.4, 1.25, 1.0, 0.9, 0.85,
                               0.8, 0.7, 0.55, 0.5, 0.4, 0.15, 0.1, 0.0, -0.05, -0.1, -0.1, -0.15]},
]

# 每组 α∞（xlsx F 列均值）与配液浓度：c(H⁺) 取 Sheet2 用于 k–c(H⁺) 回归的混合液浓度 2/1.5/1/0.5 mol/L
# （Sheet1 记的是酸储液 4/3/2/1 mol/L，两列相差 2 倍）；c(蔗糖) 第 5 组为 0.1 mol/L，其余 0.2 mol/L。
INF = [
    [1, -1.87, 2.0, 0.2],
    [2, -1.85, 1.5, 0.2],
    [3, -1.83, 1.0, 0.2],
    [4, -1.80, 0.5, 0.2],
    [5, -1.08, 2.0, 0.1],
]

RAW = [[g["id"], g["t_0"] + 60 * i, y] for g in GROUPS for i, y in enumerate(g["a"])]

SPEC = {
    "id": "a6",
    "code": "A6",
    "group": "物化",
    "name": "旋光法测蔗糖转化速率常数",
    "subtitle": "ln(αₜ−α∞)–t 线性回归 · 求 k、半衰期与反应级数",
    "tags": ["化学动力学", "旋光法", "一级反应", "反应级数"],
    "desc": "蔗糖水解为葡萄糖与果糖，体系旋光度随时间单调下降。以 ln(αₜ−α∞) 对 t 作图得直线，"
            "斜率即速率常数；改变盐酸浓度做多组，由 ln k–ln c(H⁺) 求反应级数。",
    "method": [
        "① 每组实验在恒温下每隔 60 s 读旋光度 αₜ，并测完全反应后的 α∞；",
        "② 计算 αₜ−α∞（须为正），作 ln(αₜ−α∞)–t 图，最小二乘拟合直线；",
        "③ 一级反应 ln(αₜ−α∞) = ln A₀ − kt，故 k = −斜率，半衰期 t½ = ln2 / k；",
        "④ 多组不同 c(H⁺) 的 k 作 ln k = ln k_H + n·ln c(H⁺)，斜率取整得反应级数 n；",
        "⑤ 再由 k = k_H·c(H⁺)ⁿ + k₀ 的截距检查是否存在与酸浓度无关的平行项 k₀。",
    ],
    "tables": [
        {
            "key": "raw",
            "title": "各组的 αₜ–t 记录",
            "note": "长表：第 1 列组号、第 2 列时间 t/s、第 3 列旋光度 αₜ/(°)。"
                    "原始记录从各组起始时刻开始、间隔 60 s，共 25 点；按组号与第二张表对应。",
            "columns": [
                {"key": "g", "label": "组号", "type": "number"},
                {"key": "t", "label": "t / s", "type": "number"},
                {"key": "a", "label": "αₜ / (°)", "type": "number"},
            ],
            "rows": RAW,
        },
        {
            "key": "inf",
            "title": "分组参数：α∞ 与配液浓度",
            "note": "α∞ 为反应完全后的旋光度（xlsx 中 F 列均值）。c(H⁺) 默认取混合液实际浓度 2/1.5/1/0.5 mol/L；"
                    "若你的记录是酸储液浓度（4/3/2/1），整列乘以 2 即可，n 不变、k_H 减半。",
            "columns": [
                {"key": "g", "label": "组号", "type": "number"},
                {"key": "ainf", "label": "α∞ / (°)", "type": "number"},
                {"key": "ch", "label": "c(H⁺) / (mol/L)", "type": "number"},
                {"key": "ct", "label": "c(蔗糖) / (mol/L)", "type": "number"},
            ],
            "rows": INF,
        },
    ],
    "params": [
        {"key": "grp", "label": "作图组别", "type": "select", "default": "1",
         "options": [{"value": str(g["id"]), "label": f"第 {g['id']} 组"} for g in GROUPS],
         "hint": "只影响第一张图与 KPI；其余组仍算在结果表里"},
        {"key": "skip", "label": "剔除起始点数", "type": "number", "default": 0, "step": 1,
         "hint": "起始段温度未稳、读数偏差大时可剔除前 n 点"},
        {"key": "drop", "label": "剔除末尾点数", "type": "number", "default": 0, "step": 1,
         "hint": "末期 αₜ 接近 α∞ 时 ln 值抖动，可剔除末尾 n 点"},
        {"key": "use5", "label": "k–c(H⁺) 拟合含第 5 组", "type": "select", "default": "no",
         "options": [{"value": "no", "label": "不含"}, {"value": "yes", "label": "含"}],
         "hint": "第 5 组蔗糖浓度是 0.1 mol/L，与其他组不同，默认不参与级数拟合"},
    ],
}


def _collect(rows):
    """把长表拆成 {组号: [(t, α)]}。"""
    out = {}
    for r in rows:
        if len(r) < 3:
            continue
        gid, t, a = num(r[0]), num(r[1]), num(r[2])
        if gid is None or t is None or a is None:
            continue
        out.setdefault(int(round(gid)), []).append((t, a))
    return out


def run(data):
    tb = data.get("tables") or {}
    rows = tb.get("raw") or []
    inf_rows = tb.get("inf") or []
    p = data.get("params") or {}
    skip = int(num(p.get("skip"), 0) or 0)
    drop = int(num(p.get("drop"), 0) or 0)
    use5 = str(p.get("use5") or "no") == "yes"

    meta = {}
    for r in inf_rows:
        if len(r) < 2:
            continue
        gid = num(r[0])
        if gid is None:
            continue
        meta[int(round(gid))] = {
            "a_inf": num(r[1]),
            "ch": num(r[2]) if len(r) > 2 else None,
            "ct": num(r[3]) if len(r) > 3 else None,
        }
    if not meta:
        raise ValueError("缺少“分组参数”表：请给出每组的 α∞（第二张表的第 2 列）")

    groups = _collect(rows)
    if not groups:
        raise ValueError("数据不足：请检查第一张表的组号、t、αₜ 三列是否填全")

    res = {}
    for gid, pts in groups.items():
        info = meta.get(gid)
        if info is None or info["a_inf"] is None:
            continue
        pts = sorted(pts, key=lambda q: q[0])
        if skip > 0:
            pts = pts[skip:]
        if drop > 0:
            pts = pts[:len(pts) - drop]
        if len(pts) < 3:
            continue
        xs = [q[0] for q in pts]
        ys = []
        for t, a in pts:
            d = a - info["a_inf"]
            if d <= 0:
                raise ValueError(f"第 {gid} 组在 t = {t:g} s 处 αₜ−α∞ ≤ 0，无法取对数："
                                 f"请检查第二张表中该组的 α∞ 是否偏大")
            ys.append(math.log(d))
        try:
            f = linfit(xs, ys)
        except ValueError:
            continue
        k = -f["slope"]
        if k <= 0:
            raise ValueError(f"第 {gid} 组 ln(αₜ−α∞) 随 t 上升（k = {k:.3g} s⁻¹），"
                             f"请检查该组 α∞ 是否取值过大")
        res[gid] = {"info": info, "xs": xs, "ys": ys, "fit": f,
                    "k": k, "kmin": k * 60.0, "thalf": math.log(2) / k}

    if not res:
        raise ValueError("没有可拟合的组：请确认组号在两张表中一致，且每组至少 3 个点")

    # ---------- 反应级数：ln k = ln k_H + n ln c(H⁺) ----------
    elig = [(gid, q["info"]["ch"], q["k"]) for gid, q in sorted(res.items())
            if q["info"]["ch"] and q["info"]["ch"] > 0 and (gid != 5 or use5)]
    if len(elig) < 3:
        raise ValueError("k–c(H⁺) 拟合至少需要 3 组不同 c(H⁺) 的数据："
                         "请检查第二张表的 c(H⁺) 列，或把“含第 5 组”改为“含”")
    lc = [math.log(c) for _, c, _ in elig]
    lk = [math.log(k) for _, _, k in elig]
    fl = linfit(lc, lk)
    n_raw = fl["slope"]
    n = int(round(n_raw))
    warn = []
    if n < 1:
        n_use = n_raw
        warn.append(f"ln k–ln c(H⁺) 斜率 {n_raw:.3f} 取整得 0，按实测斜率 {n_raw:.3f} 继续计算")
    else:
        n_use = float(n)
    kH_ln = math.exp(fl["intercept"])
    fk = linfit([c ** n_use for _, c, _ in elig], [k for _, _, k in elig])
    kH = fk["slope"]
    k0 = fk["intercept"]

    # ---------- 选中组的 ln 图 ----------
    sel = str(p.get("grp") or "1")
    gid_sel = int(sel) if sel.strip().lstrip("-").isdigit() else None
    if gid_sel not in res:
        gid_sel = sorted(res)[0]
    r = res[gid_sel]
    f = r["fit"]
    x0, x1 = min(r["xs"]), max(r["xs"])
    y_a, y_b = line_y(f, x0), line_y(f, x1)
    chart1 = {
        "title": f"第 {gid_sel} 组 ln(αₜ−α∞)–t（α∞ = {r['info']['a_inf']:g}°）",
        "xlabel": "t / s", "ylabel": "ln(αₜ−α∞)",
        "series": [
            {"name": "实测点", "type": "scatter",
             "points": [[x, y] for x, y in zip(r["xs"], r["ys"])]},
            {"name": "线性拟合", "type": "line", "color": "#e5533d",
             "points": [[x0, y_a], [x1, y_b]]},
        ],
        "annotations": True,
        "xrange": [x0 - 60, x1 + 60],
    }

    # ---------- k–c(H⁺) 图 ----------
    cmin = min(c for _, c, _ in elig)
    cmax = max(c for _, c, _ in elig)
    pon = [[c, k * 1e3] for _, c, k in elig]
    line_pts = []
    for i in range(41):
        c = cmin + (cmax - cmin) * i / 40
        line_pts.append([c, (kH * c ** n_use + k0) * 1e3])
    chart2 = {
        "title": "k–c(H⁺) 关系（n 取整后线性）",
        "xlabel": "c(H⁺) / (mol/L)", "ylabel": "k / (10⁻³ s⁻¹)",
        "series": [
            {"name": f"{len(elig)} 组实测 k", "type": "scatter", "points": pon},
            {"name": f"k = k_H·c^{n_use:g} + k₀", "type": "line", "color": "#2f6df6",
             "points": line_pts},
        ],
        "annotations": True,
    }

    # ---------- 表 ----------
    t1 = []
    for gid in sorted(res):
        q = res[gid]
        t1.append([gid, q["info"]["ch"], q["info"]["ct"], q["info"]["a_inf"],
                   round(q["k"] * 1e3, 4), round(q["kmin"], 5), round(q["fit"]["intercept"], 4),
                   round(q["fit"]["r"], 4), round(q["thalf"] / 60.0, 2), len(q["xs"])])
    t2 = [
        ["反应级数 n（取整）", n, "由 ln k–ln c(H⁺) 斜率四舍五入"],
        ["ln k–ln c(H⁺) 斜率", round(n_raw, 4), "未取整的实测值"],
        ["k_H（ln 截距换算）", round(kH_ln, 6), "exp(截距)，与处理表 M4 口径一致"],
        ["k_H（k–c ⁿ 斜率）", round(kH, 6), "取整级数下的动力学常数"],
        ["k₀（k–c ⁿ 截距）", round(k0, 6), "接近 0 说明表观一级成立"],
        ["k–c ⁿ 拟合 r²", round(fk["r2"], 4), ""],
    ]

    return {
        "kpis": [
            {"label": "k", "value": round(r["kmin"], 4), "unit": "min⁻¹", "digits": 4,
             "hint": f"第 {gid_sel} 组 · 一级反应速率常数"},
            {"label": "半衰期", "value": round(r["thalf"] / 60.0, 1), "unit": "min", "digits": 1,
             "hint": "t½ = ln2 / k"},
            {"label": "拟合 r", "value": round(f["r"], 4), "digits": 4,
             "hint": f"第 {gid_sel} 组 ln(αₜ−α∞)–t 的相关系数"},
            {"label": "反应级数 n", "value": n, "digits": 0,
             "hint": f"ln k–ln c(H⁺) 斜率 = {n_raw:.3f}，取整得 {n}"},
            {"label": "k_H", "value": round(kH_ln, 6),
             "unit": "L·mol⁻¹·s⁻¹" if abs(n_use - 1) < 1e-9 else f"(mol/L)^-{n_use:g}·s⁻¹",
             "digits": 4,
             "hint": f"exp(ln k–ln c(H⁺) 截距)，与处理表 M4 一致；k–c 斜率口径为 {kH:.3g}"},
        ],
        "charts": [chart1, chart2],
        "tables": [
            {"title": "各组拟合结果",
             "columns": ["组", "c(H⁺) / (mol/L)", "c(蔗糖) / (mol/L)", "α∞ / (°)",
                         "k / (10⁻³ s⁻¹)", "k / min⁻¹", "b", "r", "t½ / min", "点数"],
             "rows": t1},
            {"title": "反应级数与动力学常数", "columns": ["项目", "数值", "说明"], "rows": t2},
        ],
        "notes": [
            "一级反应积分式 ln(αₜ−α∞) = ln A₀ − kt，斜率取负即 k；α∞ 用反应完全后的旋光度，"
            "不能用末点代替，否则 k 会明显偏大。",
            "处理表（A6数据处理.xlsx）用 SLOPE 数组公式对全部 25 点回归，复算 k = 9.50/5.55/3.57/2.59/10.2 ×10⁻⁴ s⁻¹"
            "（即 0.0570/0.0333/0.0214/0.0156/0.0612 min⁻¹），与本模块结果一致。",
            "实验报告 PDF 里 5 张 ln 图以序号 1–25 为横轴、拟合得斜率 0.0481/0.0338/0.0232/0.0176/0.0576（每 60 s），"
            "与处理表全区间回归的同名组相差 5%–15%，原因是报告用 Origin 手工取舍了数据点（截距 1.49 的图对应第 5 组）。",
            "反应级数：处理表 Sheet2 对 k 与 c(H⁺) 取对数后的 SLOPE 再 ROUND，得 n = 1，"
            "k_H = exp(截距) = 4.29×10⁻⁴，k₀ ≈ −6×10⁻⁶（本模块同法复算 −3.7×10⁻⁵，同量级，均可视为 0，即表观一级）。",
            "第 5 组蔗糖浓度与其他组不同，默认只参与 k 计算、不参与级数拟合，可在参数里改为参与。",
        ],
        "warnings": warn + ([f"第 {gid_sel} 组只用 {len(r['xs'])} 个点拟合（原 25 点）"]
                             if (skip or drop) else []) + (
            [f"k–c(H⁺) 线性拟合 r² 只有 {fk['r2']:.3f}：k 与 c(H⁺) 的一级关系不算好，"
             f"可能级数不严格或存在 k₀"] if fk["r2"] < 0.95 else []),
    }

# 计算用到的公式（LaTeX 子集；前端与 Word 报告都会渲染成真正的公式）
SPEC["formulas"] = [
    r"\ln(\alpha_{t} - \alpha_{\infty}) = -kt + \ln(\alpha_{0} - \alpha_{\infty})",
    r"t_{1/2} = \frac{\ln 2}{k}",
]
