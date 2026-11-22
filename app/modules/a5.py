# -*- coding: utf-8 -*-
"""A5 黏度法测高聚物相对分子质量：Huggins / Kraemer 作图外推求特性黏度 [η]，再由 Mark-Houwink 方程求 M。"""
import math

from ..core import linfit, line_y, num

# 原表 Sheet1 (2)（有三次平行流出时间）：
# A 列为加水量（mL），c 列为稀释后的相对浓度（原表 F 列，c = 100/(10+A)），
# t1..t3 为乌氏黏度计三次流出时间（s）。纯溶剂 t0 三次为 87.88/87.71/87.77 s。
RAW = [
    [0, 10.0, 128.02, 128.12, 128.07],
    [5, 20 / 3, 112.97, 112.99, 113.04],
    [15, 4.0, 102.13, 102.22, 102.16],
    [25, 20 / 7, 97.83, 97.78, 97.92],
]

T0_PARALLEL = [87.88, 87.71, 87.77]

METHODS = [
    {"value": "huggins", "label": "Huggins"},
    {"value": "kraemer", "label": "Kraemer"},
    {"value": "both", "label": "两者平均"},
]

SPEC = {
    "id": "a5",
    "code": "A5",
    "group": "物化",
    "name": "黏度法测高聚物相对分子质量",
    "subtitle": "Huggins 作图外推特性黏度 [η] · Mark-Houwink 方程求 M",
    "tags": ["黏度", "特性黏度", "Huggins", "Kraemer", "Mark-Houwink"],
    "desc": "用乌氏黏度计测聚乙二醇（或同类高聚物）稀溶液在不同浓度下的流出时间，"
            "以 η_sp/c 对 c 作 Huggins 直线、lnη_r/c 对 c 作 Kraemer 直线，两条直线在 c→0 时交于同一点，"
            "该截距即特性黏度 [η]；再由 [η] = K·Mᵅ 反解黏均相对分子质量 M。",
    "method": [
        "① 相对黏度 ηr = t/t_0，增比黏度 η_sp = ηr − 1；",
        "② Huggins 方程：η_sp/c = [η] + k_H·[η]²·c；",
        "③ Kraemer 方程：lnη_r/c = [η] − k_K·[η]²·c；",
        "④ 两式对 c 线性拟合，纵截距即 [η]；",
        "⑤ Mark-Houwink：[η] = K·Mᵅ ⇒ M = ([η]/K)^(1/α)。",
    ],
    "tables": [{
        "key": "raw",
        "title": "流出时间原始数据",
        "note": "t_0 为纯溶剂三次平行测定的均值（87.88、87.71、87.77 s）；"
                "每份溶液三次平行流出时间取算术平均后使用。c 为原表浓度列（c = 100/(10+A)）。",
        "columns": [
            {"key": "a", "label": "加水量 A /mL", "type": "number"},
            {"key": "c", "label": "c", "type": "number"},
            {"key": "t1", "label": "t1 /s", "type": "number"},
            {"key": "t2", "label": "t2 /s", "type": "number"},
            {"key": "t3", "label": "t3 /s", "type": "number"},
        ],
        "rows": RAW,
    }],
    "params": [
        {"key": "method", "label": "外推方法", "type": "select", "default": "huggins",
         "options": [{"value": m["value"], "label": m["label"]} for m in METHODS],
         "hint": "决定用哪条直线的截距算 [η] 与 M"},
        {"key": "t_0", "label": "t_0 纯溶剂流出时间", "type": "number", "default": 87.7867,
         "step": 0.0001, "hint": "s，三次平行均值"},
        {"key": "K", "label": "K（Mark-Houwink 常数）", "type": "number", "default": 1.25e-5,
         "step": 1e-6, "hint": "原表取 1.25×10⁻⁵，25 ℃ 下该溶剂体系的文献值"},
        {"key": "alpha", "label": "α（Mark-Houwink 指数）", "type": "number", "default": 0.78,
         "step": 0.01, "hint": "原表取 0.78"},
    ],
}


def run(data):
    rows = (data.get("tables") or {}).get("raw") or []
    p = data.get("params") or {}

    t0 = num(p.get("t_0"), 87.7867)
    kk = num(p.get("K"), 1.25e-5)
    alpha = num(p.get("alpha"), 0.78)
    method = p.get("method") or "huggins"

    if t0 is None or t0 <= 0:
        raise ValueError("纯溶剂流出时间 t_0 必须为正值（s）")
    if kk is None or kk <= 0:
        raise ValueError("Mark-Houwink 常数 K 必须为正值")
    if alpha is None or alpha <= 0:
        raise ValueError("Mark-Houwink 指数 α 必须为正值")

    pts = []
    for i, r in enumerate(rows, start=1):
        if len(r) < 5:
            raise ValueError(f"第 {i} 行数据不足 5 列（加分水量、c、t1、t2、t3）")
        a = num(r[0])
        c = num(r[1])
        ts = [num(r[2]), num(r[3]), num(r[4])]
        if c is None or any(v is None for v in ts):
            raise ValueError(f"第 {i} 行有非数字单元格，请检查表格")
        if c <= 0:
            raise ValueError(f"第 {i} 行浓度 c 必须为正值")
        if any(v <= 0 for v in ts):
            raise ValueError(f"第 {i} 行流出时间必须为正值（s）")
        t = sum(ts) / len(ts)
        if t <= t0:
            raise ValueError(f"第 {i} 行溶液流出时间不大于纯溶剂 t0，η_sp ≤ 0，请检查 t0 或该组数据")
        eta_r = t / t0
        eta_sp = eta_r - 1.0
        pts.append({"a": a, "c": c, "t": t, "eta_r": eta_r, "eta_sp": eta_sp,
                    "red": eta_sp / c, "inh": math.log(eta_r) / c})

    if len(pts) < 2:
        raise ValueError("至少需要 2 个浓度点才能外推特性黏度，请检查表格")

    cs = [q["c"] for q in pts]
    red = [q["red"] for q in pts]
    inh = [q["inh"] for q in pts]

    fh = linfit(cs, red)      # Huggins
    fk = linfit(cs, inh)      # Kraemer

    eta_h = fh["intercept"]
    eta_k = fk["intercept"]
    if method == "kraemer":
        eta = eta_k
    elif method == "both":
        eta = (eta_h + eta_k) / 2.0
    else:
        eta = eta_h

    if eta <= 0:
        raise ValueError("外推得到的特性黏度 [η] 非正，无法计算相对分子质量，请检查浓度或 t_0")

    mw = (eta / kk) ** (1.0 / alpha)
    k_h = fh["slope"] / eta_h ** 2 if eta_h > 0 else None

    c_hi = max(cs)
    chart = {
        "title": "Huggins / Kraemer 作图外推 [η]",
        "xlabel": "c", "ylabel": "η_sp/c  与  lnη_r/c",
        "series": [
            {"name": "η_sp/c（Huggins）", "type": "scatter", "color": "#2f6df6",
             "points": [[q["c"], q["red"]] for q in pts]},
            {"name": "lnη_r/c（Kraemer）", "type": "scatter", "color": "#e5533d",
             "points": [[q["c"], q["inh"]] for q in pts]},
            {"name": f"η_sp/c = {fh['slope']:.5f}c + {eta_h:.5f}", "type": "line",
             "color": "#2f6df6",
             "points": [[0.0, eta_h], [c_hi * 1.05, line_y(fh, c_hi * 1.05)]]},
            {"name": f"lnη_r/c = {fk['slope']:.5f}c + {eta_k:.5f}", "type": "line", "dash": True,
             "color": "#e5533d",
             "points": [[0.0, eta_k], [c_hi * 1.05, line_y(fk, c_hi * 1.05)]]},
        ],
        "points": [{"x": 0.0, "y": eta, "label": f"[η] = {eta:.5f}"}],
        "annotations": True,
    }

    data_rows = [[q["a"], round(q["c"], 4), round(q["t"], 2), round(q["eta_r"], 5),
                  round(q["eta_sp"], 5), round(q["red"], 5), round(q["inh"], 5)] for q in pts]
    fit_rows = [
        ["Huggins", round(fh["slope"], 6), round(eta_h, 5), round(fh["r"], 4),
         round((eta_h / kk) ** (1 / alpha), 0)],
        ["Kraemer", round(fk["slope"], 6), round(eta_k, 5), round(fk["r"], 4),
         round((eta_k / kk) ** (1 / alpha), 0)],
        ["两者平均", "", round((eta_h + eta_k) / 2, 5), "",
         round((((eta_h + eta_k) / 2) / kk) ** (1 / alpha), 0)],
    ]

    warnings = []
    if abs(fh["r"]) < 0.99:
        warnings.append(f"Huggins 拟合 r = {fh['r']:.4f}，线性度偏低，[η] 外推不确定度较大")
    if abs(fk["r"]) < 0.99:
        warnings.append(f"Kraemer 拟合 r = {fk['r']:.4f}，线性度偏低")
    if abs(eta_h - eta_k) / eta_h > 0.05:
        warnings.append(f"Huggins 与 Kraemer 截距相差 {abs(eta_h - eta_k) / eta_h * 100:.1f}%，"
                        "两条直线未交于一点，建议检查浓度范围或流出时间读数")
    if k_h is not None and not (0.2 <= k_h <= 1.0):
        warnings.append(f"k_H = {k_h:.3f} 偏离常见范围 0.3–0.8，可能浓度过高或溶剂不良")

    return {
        "kpis": [
            {"label": "特性黏度 [η]", "value": round(eta, 5), "digits": 5,
             "hint": f"按{METHODS[[m['value'] for m in METHODS].index(method)]['label']}的 c→0 截距"},
            {"label": "相对分子质量 M", "value": round(mw, 0), "unit": "g·mol⁻¹", "digits": 0,
             "hint": f"[η] = {kk:g}·M^{alpha:g} 反解"},
            {"label": "k_H（Huggins 常数）", "value": round(k_h, 4) if k_h else 0,
             "digits": 4, "hint": "直线斜率 / [η]²，反映高分子–溶剂相互作用"},
            {"label": "r（Huggins）", "value": round(fh["r"], 4), "digits": 4,
             "hint": "η_sp/c–c 线性相关系数"},
        ],
        "charts": [chart],
        "tables": [
            {"title": "黏度数据处理", "columns": ["加水量/mL", "c", "t /s", "ηr", "η_sp",
                                            "η_sp/c", "lnη_r/c"], "rows": data_rows},
            {"title": "外推结果与相对分子质量", "columns": ["方法", "斜率", "截距 [η]", "r",
                                                "M /(g·mol⁻¹)"], "rows": fit_rows},
        ],
        "notes": [
            f"t0 = {t0:.4f} s（原表三次 87.88、87.71、87.77 s 的均值）；t 为该组三次平行流出时间的均值。",
            "ηr = t/t_0；η_sp = ηr − 1；Huggins：η_sp/c = [η] + k_H[η]²c；"
            "Kraemer：lnη_r/c = [η] − k_K[η]²c。两式截距都等于 [η]，本模块两条直线都给出。",
            "与实验报告对照：报告图注为 η_sp/c 直线 y = 0.0008x + 0.0377（R² = 0.9996）、"
            "lnη_r/c 直线 y = −3E−05x + 0.038（R² = 0.9934）；本模块复算 Huggins 斜率 0.000812、"
            "截距 0.037731、R² = 0.99962，Kraemer 斜率 −2.7×10⁻⁵、截距 0.038041、R² = 0.99339，与之吻合。",
            f"取 K = {kk:g}、α = {alpha:g}，M = ([η]/K)^(1/α)。原表 M = (K8/K9)^(1/K10)，"
            "K8 为截距、K9 = 0.0000125、K10 = 0.78；Huggins 支路得 M ≈ 28924（原表 28924.3153），"
            "Kraemer 支路 ≈ 29230，两者平均 ≈ 29077。",
            "原表另有一个 Sheet1（只有单次流出时间、t_0 = 86.27 s），本模块采用带三次平行的 Sheet1 (2)，"
            "与原表 K11 单元格所用数据一致。",
        ],
        "warnings": warnings,
    }
