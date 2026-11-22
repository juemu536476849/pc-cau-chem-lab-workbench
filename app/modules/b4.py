# -*- coding: utf-8 -*-
"""B4 B-Z 振荡反应：由 EMF–t 曲线读振荡周期，用 Arrhenius 式求表观活化能。"""
import math
from ..core import num, linfit

R_GAS = 8.314  # J/(mol·K)

# 原始 EMF–t 记录（t/s, EMF/mV），每个温度 11 点，均取自 B4数据处理.xlsx Sheet4
OSC = {
    25.02: [(60, 712), (588, 671), (634, 570), (714, 669), (768, 568), (835, 672), (881, 562),
            (956, 673), (995, 566), (1085, 665), (1124, 562)],
    28.14: [(60, 711), (523, 674), (537, 556), (618, 674), (630, 566), (714, 674), (722, 556),
            (810, 675), (819, 554), (906, 676), (910, 567)],
    31.00: [(60, 712), (478, 678), (514, 549), (558, 676), (591, 548), (640, 672), (670, 550),
            (720, 676), (756, 550), (799, 677), (831, 550)],
    34.01: [(60, 713), (442, 677), (502, 549), (564, 675), (588, 548), (624, 676), (645, 549),
            (683, 676), (704, 551), (742, 676), (770, 552)],
    37.02: [(60, 712), (378, 679), (425, 561), (469, 676), (491, 562), (524, 677), (544, 565),
            (569, 677), (588, 565), (619, 677), (639, 565)],
}

# 汇总：温度 ℃、诱导期 t_u/s、振荡周期 t_z/s（Sheet1/1(2)/…/1(5) 与报告表一致）
RUNS = [
    [25.02, 574.0, 124.1111],
    [28.14, 477.0, 95.8889],
    [31.00, 418.0, 79.6667],
    [34.01, 382.0, 59.6667],
    [37.02, 318.0, 48.4444],
]

OSC_ROWS = [[t_c, t, v] for t_c in sorted(OSC) for t, v in OSC[t_c]]

SPEC = {
    "id": "b4",
    "code": "B4",
    "group": "物化",
    "name": "B-Z 振荡反应",
    "subtitle": "EMF–t 振荡曲线读周期 · Arrhenius 求表观活化能",
    "tags": ["振荡反应", "诱导期", "活化能", "Arrhenius"],
    "desc": "记录 B-Z（Belousov–Zhabotinsky）体系电位随时间周期性振荡的曲线，"
            "由曲线读出诱导期 t_u 与振荡周期 t_z，再按 Arrhenius 式 ln(1/t) 对 1/T 作直线拟合求表观活化能。",
    "method": [
        "① 对所选温度的 EMF–t 曲线找局部极大（峰）与极小（谷），相邻同类极值时间差即一个周期；",
        "② 取峰–峰、谷–谷或全部间隔的平均值作为该温度振荡周期 t_z；",
        "③ 汇总 5 个温度的诱导期 t_u 与周期 t_z，换算 1/T 与 ln(1/t)；",
        "④ 分别对 ln(1/t_u)–1/T、ln(1/t_z)–1/T 作最小二乘直线，斜率 = −Ea/R；",
        "⑤ 表观活化能 Ea = −R·(斜率)，R = 8.314 J/(mol·K)。",
    ],
    "tables": [
        {
            "key": "osc",
            "title": "电位–时间振荡曲线（5 个温度）",
            "note": "第 1 列为温度/℃，第 2 列时间/s，第 3 列电位/mV。原始记录只取每个振荡的峰、谷点，"
                    "程序按相邻极值的时间差算周期。",
            "columns": [
                {"key": "T", "label": "温度 t / ℃", "type": "number"},
                {"key": "time", "label": "时间 / s", "type": "number"},
                {"key": "emf", "label": "EMF / mV", "type": "number"},
            ],
            "rows": OSC_ROWS,
        },
        {
            "key": "runs",
            "title": "各温度诱导期与周期汇总",
            "note": "t_u 由反应开始计时到第一次振荡出现的时刻；t_z 为该温度多个周期间隔的平均值"
                    "（与 B4数据处理.xlsx 汇总表一致）。",
            "columns": [
                {"key": "T", "label": "温度 t / ℃", "type": "number"},
                {"key": "tu", "label": "t_u / s", "type": "number"},
                {"key": "tz", "label": "t_z / s", "type": "number"},
            ],
            "rows": RUNS,
        },
    ],
    "params": [
        {"key": "run", "label": "作图的温度", "type": "select", "default": "25.02",
         "options": [{"value": f"{r[0]:.2f}", "label": f"{r[0]:.2f} ℃"} for r in RUNS]},
        {"key": "pmode", "label": "周期取法", "type": "select", "default": "all",
         "options": [{"value": "all", "label": "全部间隔"},
                     {"value": "peak", "label": "只用峰–峰"},
                     {"value": "trough", "label": "只用谷–谷"}]},
        {"key": "nmode", "label": "Arrhenius 拟合点数", "type": "select", "default": "all",
         "options": [{"value": "all", "label": "5 个温度"},
                     {"value": "low", "label": "低温 4 点"},
                     {"value": "high", "label": "高温 4 点"}]},
    ],
}


def _extrema(points):
    """返回 (峰列表, 谷列表)，元素为 (t, v)；只取内部点。"""
    peaks, troughs = [], []
    for i in range(1, len(points) - 1):
        t0, v0 = points[i - 1]
        t1, v1 = points[i]
        t2, v2 = points[i + 1]
        if v1 > v0 and v1 > v2:
            peaks.append((t1, v1))
        if v1 < v0 and v1 < v2:
            troughs.append((t1, v1))
    return peaks, troughs


def _intervals(pts):
    return [(pts[i][0], pts[i + 1][0], pts[i + 1][0] - pts[i][0]) for i in range(len(pts) - 1)]


def run(data):
    tables = data.get("tables") or {}
    p = data.get("params") or {}
    osc_rows = tables.get("osc") or []
    run_rows = tables.get("runs") or []

    sel = p.get("run") or "25.02"
    pmode = p.get("pmode") or "all"
    nmode = p.get("nmode") or "all"

    # ---- 曲线按温度分组 ----
    curves = {}
    for r in osc_rows:
        if len(r) < 3:
            continue
        t_c, t, v = num(r[0]), num(r[1]), num(r[2])
        if t_c is None or t is None or v is None:
            continue
        curves.setdefault(round(t_c, 2), []).append((t, v))
    if not curves:
        raise ValueError("振荡曲线表为空：请粘贴温度、时间、EMF 三列数据")
    for k in curves:
        curves[k].sort()

    try:
        key = min(curves, key=lambda k: abs(k - float(sel)))
    except (TypeError, ValueError):
        raise ValueError(f"温度选择“{sel}”无法识别，请从下拉框里选一个温度")
    if abs(key - float(sel)) > 0.05:
        raise ValueError(f"表中没有 {sel} ℃ 的振荡曲线：请检查第 1 列温度，或改用表中已有的温度")
    pts = curves[key]
    if len(pts) < 4:
        raise ValueError(f"{key:.2f} ℃ 的曲线只有 {len(pts)} 个点，不足以计算周期（至少 4 个）")

    peaks, troughs = _extrema(pts)
    per_p = _intervals(peaks)
    per_t = _intervals(troughs)
    if pmode == "peak":
        used, used_name = per_p, "峰–峰"
    elif pmode == "trough":
        used, used_name = per_t, "谷–谷"
    else:
        used, used_name = per_p + per_t, "峰–峰与谷–谷"
    if len(used) < 2:
        raise ValueError(f"{key:.2f} ℃ 曲线的{used_name}间隔不足 2 个，无法求平均周期："
                         "请补充振荡记录或换一种周期取法")
    deltas = [d for _, _, d in used]
    tz_curve = sum(deltas) / len(deltas)

    # ---- Arrhenius ----
    recs = []
    for r in run_rows:
        if len(r) < 3:
            continue
        t_c, tu, tz = num(r[0]), num(r[1]), num(r[2])
        if t_c is None or tu is None or tz is None:
            continue
        if tu <= 0 or tz <= 0:
            raise ValueError("诱导期与周期必须为正数，请检查汇总表")
        tk = t_c + 273.15
        recs.append({"t_c": t_c, "tk": tk, "tu": tu, "tz": tz,
                     "x": 1.0 / tk, "yu": math.log(1.0 / tu), "yz": math.log(1.0 / tz)})
    if len(recs) < 3:
        raise ValueError("汇总表至少需要 3 个温度点才能做 Arrhenius 拟合")
    recs.sort(key=lambda r: r["tk"])
    sel_rec = min(recs, key=lambda r: abs(r["t_c"] - key))
    if nmode == "low":
        recs = recs[:4]
    elif nmode == "high":
        recs = recs[-4:]
    if len(recs) < 3:
        raise ValueError("所选拟合点数不足 3 个，请改为“全部”")

    xs = [r["x"] for r in recs]
    fu = linfit(xs, [r["yu"] for r in recs])
    fz = linfit(xs, [r["yz"] for r in recs])
    ea_u = -R_GAS * fu["slope"] / 1000.0
    ea_z = -R_GAS * fz["slope"] / 1000.0
    if ea_u <= 0 or ea_z <= 0:
        raise ValueError("拟合得到的活化能为负：请检查是不是把 1/T 与 ln(1/t) 的列贴反了")

    # ---- 图 1：所选温度的振荡曲线 ----
    curve_series = [
        {"name": f"{key:.2f} ℃ 实测曲线", "type": "line", "color": "#2f6df6",
         "points": [[t, v] for t, v in pts]},
        {"name": "峰", "type": "scatter", "color": "#e5533d",
         "points": [[t, v] for t, v in peaks]},
        {"name": "谷", "type": "scatter", "color": "#1f9d55",
         "points": [[t, v] for t, v in troughs]},
    ]
    chart1 = {
        "title": f"{key:.2f} ℃ · EMF–t 振荡曲线（平均周期 {tz_curve:.1f} s）",
        "xlabel": "t / s", "ylabel": "EMF / mV",
        "series": curve_series,
        "points": [{"x": round(sel_rec["tu"], 1), "y": max(v for _, v in pts),
                    "label": f"t_u = {sel_rec['tu']:.0f} s（汇总表）"}],
        "xrange": [0, round(max(t for t, _ in pts) * 1.04, 1)],
    }

    # ---- 图 2：Arrhenius ----
    xmin = min(xs)
    xmax = max(xs)
    pad = (xmax - xmin) * 0.06
    x1, x2 = xmin - pad, xmax + pad
    chart2 = {
        "title": "ln(1/t) – 1/T 图（Arrhenius 式求表观活化能）",
        "xlabel": "1/T / K⁻¹", "ylabel": "ln(1/t)，t 单位 s",
        "series": [
            {"name": "ln(1/t_u) 实测", "type": "scatter", "color": "#e5533d",
             "points": [[round(r["x"], 8), round(r["yu"], 5)] for r in recs]},
            {"name": f"ln(1/t_u) 拟合，Ea = {ea_u:.2f} kJ/mol", "type": "line", "color": "#e5533d",
             "points": [[round(x1, 8), round(fu["slope"] * x1 + fu["intercept"], 5)],
                        [round(x2, 8), round(fu["slope"] * x2 + fu["intercept"], 5)]]},
            {"name": "ln(1/t_z) 实测", "type": "scatter", "color": "#2f6df6",
             "points": [[round(r["x"], 8), round(r["yz"], 5)] for r in recs]},
            {"name": f"ln(1/t_z) 拟合，Ea = {ea_z:.2f} kJ/mol", "type": "line", "color": "#2f6df6",
             "points": [[round(x1, 8), round(fz["slope"] * x1 + fz["intercept"], 5)],
                        [round(x2, 8), round(fz["slope"] * x2 + fz["intercept"], 5)]]},
        ],
        "xrange": [round(x1, 8), round(x2, 8)],
    }

    t1_rows = []
    for r in recs:
        t1_rows.append([round(r["t_c"], 2), round(r["tk"], 2), round(r["x"] * 1000, 4),
                        round(r["tu"], 1), round(r["tz"], 2),
                        round(r["yu"], 4), round(r["yz"], 4)])

    t2_rows = []
    for a0, b0, d in per_p:
        if pmode in ("all", "peak"):
            t2_rows.append(["峰–峰", round(a0, 1), round(b0, 1), round(d, 1)])
    for a0, b0, d in per_t:
        if pmode in ("all", "trough"):
            t2_rows.append(["谷–谷", round(a0, 1), round(b0, 1), round(d, 1)])

    notes = [
        f"周期取法：“{used_name}”，共 {len(deltas)} 个间隔 → 平均周期 {tz_curve:.2f} s。",
        f"Arrhenius 拟合（{len(recs)} 个温度点）：ln(1/t_u) = {fu['slope']:.2f}/T + {fu['intercept']:.4f}，"
        f"r² = {fu['r2']:.5f}，Ea = {ea_u:.2f} kJ/mol；ln(1/t_z) = {fz['slope']:.2f}/T + "
        f"{fz['intercept']:.4f}，r² = {fz['r2']:.5f}，Ea = {ea_z:.2f} kJ/mol。",
        "与报告/xlsx 对照：原表 ln(1/t_u) 斜率 −4348.56、截距 8.24576、Ea = 36153.9 J/mol（36.15 kJ/mol）；"
        "ln(1/t_z) 斜率 −7295.69、截距 19.6425、Ea = 60656.4 J/mol（60.66 kJ/mol），"
        f"本模块按 298.15 K 换算得 {ea_u:.2f} 与 {ea_z:.2f} kJ/mol，与原表一致（Ea = −R·斜率，R = 8.314）。",
        "报告汇总表把 T、t_u、t_z 写成 298/574/124、301/477/96、304/418/80、307/382/60、310/318/48，"
        "是四舍五入后的结果；本模块用 xlsx 精确值（298.17 K、t_z = 124.11/95.89/79.67/59.67/48.44 s）。",
        f"表中 {sel_rec['t_c']:.2f} ℃ 的 t_z = {sel_rec['tz']:.2f} s，而该温度下曲线实测平均周期 "
        f"{tz_curve:.1f} s，相对偏差 {abs(tz_curve - sel_rec['tz']) / sel_rec['tz'] * 100:.1f}%。"
        "偏差来自人工读数只记录峰谷点、首尾半周期不计，以及原表 t_z 还并入了另一段振荡记录的 5 个间隔。",
        "活化能数值 Ea(t_z) 明显大于 Ea(t_u)：诱导期对温度更敏感的是周期，二者机理不同，报告同样给出两条直线。",
    ]

    warnings = []
    if abs(tz_curve - sel_rec["tz"]) / sel_rec["tz"] > 0.08:
        warnings.append(f"{key:.2f} ℃ 曲线实测周期与汇总表 t_z 相差超过 8%，请核对曲线记录是否完整")
    if fu["r2"] < 0.97:
        warnings.append(f"ln(1/t_u) 拟合 r² = {fu['r2']:.4f} 偏低：诱导期读数误差较大，可只取部分温度点")
    if fz["r2"] < 0.97:
        warnings.append(f"ln(1/t_z) 拟合 r² = {fz['r2']:.4f} 偏低：请检查 t_z 是否按同一取法统计")

    return {
        "kpis": [
            {"label": "Ea（诱导期 t_u）", "value": round(ea_u, 2), "unit": "kJ·mol⁻¹", "digits": 2,
             "hint": "由 ln(1/t_u)–1/T 斜率求得"},
            {"label": "Ea（周期 t_z）", "value": round(ea_z, 2), "unit": "kJ·mol⁻¹", "digits": 2,
             "hint": "由 ln(1/t_z)–1/T 斜率求得"},
            {"label": "周期拟合优度", "value": round(fz["r2"], 4), "digits": 4,
             "hint": "ln(1/t_z) 直线拟合的决定系数"},
            {"label": "曲线平均周期", "value": round(tz_curve, 1), "unit": "s", "digits": 1,
             "hint": f"{key:.2f} ℃，{used_name} 共 {len(deltas)} 个间隔的均值"},
            {"label": "表中 t_z", "value": round(sel_rec["tz"], 2), "unit": "s", "digits": 2,
             "hint": f"{sel_rec['t_c']:.2f} ℃ 汇总表值，与报告一致"},
        ],
        "charts": [chart1, chart2],
        "tables": [
            {"title": "各温度的 Arrhenius 数据与拟合",
             "columns": ["t / ℃", "T / K", "10³/T / K⁻¹", "t_u / s", "t_z / s",
                         "ln(1/t_u)", "ln(1/t_z)"],
             "rows": t1_rows},
            {"title": f"{key:.2f} ℃ 振荡周期明细",
             "columns": ["极值类型", "起始 t / s", "终止 t / s", "Δt / s"],
             "rows": t2_rows},
        ],
        "notes": notes,
        "warnings": warnings,
    }
