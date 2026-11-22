# -*- coding: utf-8 -*-
"""A3 固体在溶液中的吸附：由醋酸浓度差算吸附量，作 Freundlich 等温线（附 Langmuir 对照）。"""
import math

from ..core import xy, num, linfit

# 原表 Sheet1 (3)：四份吸附体系，m 为活性炭质量，V(NaOH) 为滴定剩余醋酸的用碱量，
# V(HAc) 为配液时取用的原始醋酸体积，Vc 为滴定时的取样体积。
RAW = [
    [1, 1.0065, 18.02, 50.00, 10],
    [2, 1.0193, 21.35, 25.00, 25],
    [3, 0.9933, 15.81, 12.50, 40],
    [4, 0.9974, 7.14, 6.25, 40],
]

SPEC = {
    "id": "a3",
    "code": "A3",
    "group": "物化",
    "name": "固体在溶液中的吸附",
    "subtitle": "浓度差法测吸附量 · Freundlich 等温线求 k、n",
    "tags": ["吸附", "Freundlich", "Langmuir", "等温线"],
    "desc": "用活性炭吸附醋酸水溶液，滴定吸附前后醋酸的浓度差，算出单位质量吸附剂的吸附量 Γ。"
            "以 lgΓ 对 lgc 作 Freundlich 等温线，直线斜率即 1/n、截距即 lg k；另附 Langmuir 线性化结果作对照。",
    "method": [
        "① 用 NaOH 标定原始醋酸：c₀,stock = c(NaOH)·V标定 / V(HAc)取用；",
        "② 各份吸附液初始浓度 c₀ = c₀,stock·V(HAc)/V定容；",
        "③ 滴定剩余醋酸：c = c(NaOH)·V(NaOH)/Vc；",
        "④ 吸附量 Γ = (c₀ − c)·V定容 / m（换算为 mmol/g）；",
        "⑤ Freundlich：lgΓ = lg k + (1/n)·lgc，线性拟合求 1/n、k、r；",
        "⑥ Langmuir 对照：c/Γ = c/Γ∞ + 1/(K_L·Γ∞)，由斜率、截距求 Γ∞ 与 K_L。",
    ],
    "tables": [{
        "key": "raw",
        "title": "吸附实验原始数据",
        "note": "V(NaOH) 为滴定吸附后剩余醋酸的用碱体积；Vc 为取样体积。原始醋酸标定为："
                "取 5.00 mL 原液，消耗 NaOH 19.97、19.98 mL（均值 19.975 mL）。",
        "columns": [
            {"key": "no", "label": "序号", "type": "number"},
            {"key": "m", "label": "m(吸附剂) / g", "type": "number"},
            {"key": "vnaoh", "label": "V(NaOH) / mL", "type": "number"},
            {"key": "vhac", "label": "V(HAc) / mL", "type": "number"},
            {"key": "vc", "label": "Vc 取样量 / mL", "type": "number"},
        ],
        "rows": RAW,
    }],
    "params": [
        {"key": "cnaoh", "label": "c(NaOH)", "type": "number", "default": 0.1002,
         "step": 0.0001, "hint": "NaOH 标准溶液浓度，mol/L"},
        {"key": "vstd", "label": "标定用碱体积", "type": "number", "default": 19.975,
         "step": 0.001, "hint": "标定原始醋酸时消耗 NaOH 的平均体积，mL（19.97 与 19.98 的均值）"},
        {"key": "vha0", "label": "标定取原醋酸体积", "type": "number", "default": 5.00,
         "step": 0.01, "hint": "标定时取用的原始醋酸体积，mL"},
        {"key": "vflask", "label": "吸附液定容体积", "type": "number", "default": 100,
         "step": 1, "hint": "每份吸附液的总体积，mL；用于把浓度差换算成吸附量"},
    ],
}


def run(data):
    rows = (data.get("tables") or {}).get("raw") or []
    p = data.get("params") or {}

    cnaoh = num(p.get("cnaoh"), 0.1002)
    vstd = num(p.get("vstd"), 19.975)
    vha0 = num(p.get("vha0"), 5.0)
    vflask = num(p.get("vflask"), 100.0)

    if cnaoh <= 0:
        raise ValueError("NaOH 浓度必须为正值（mol/L）")
    if vstd <= 0 or vha0 <= 0:
        raise ValueError("标定用碱体积与取用醋酸体积都必须为正值（mL）")
    if vflask <= 0:
        raise ValueError("吸附液定容体积必须为正值（mL）")

    c_stock = cnaoh * vstd / vha0          # 原始醋酸浓度 mol/L
    pts = []
    for r in rows:
        no = num(r[0]) if len(r) > 0 else None
        m = num(r[1]) if len(r) > 1 else None
        vnaoh = num(r[2]) if len(r) > 2 else None
        vhac = num(r[3]) if len(r) > 3 else None
        vc = num(r[4]) if len(r) > 4 else None
        if m is None or vnaoh is None or vhac is None or vc is None:
            continue
        if m <= 0:
            raise ValueError(f"第 {int(no) if no else '?'} 组吸附剂质量必须为正值（g）")
        if vc <= 0:
            raise ValueError(f"第 {int(no) if no else '?'} 组取样体积 Vc 必须为正值（mL）")
        c0 = c_stock * vhac / vflask
        c = cnaoh * vnaoh / vc
        if c >= c0:
            raise ValueError(f"第 {int(no) if no else '?'} 组剩余浓度不小于初始浓度，"
                             f"吸附量为负，请检查滴定体积或定容体积")
        gamma = (c0 - c) * vflask / m     # mmol/g
        pts.append({"no": no, "m": m, "c_0": c0, "c": c, "gamma": gamma,
                    "lgc": math.log10(c), "lgg": math.log10(gamma)})

    if len(pts) < 3:
        raise ValueError("有效数据不足 3 组，无法拟合 Freundlich 等温线，请检查表格")

    lgc = [q["lgc"] for q in pts]
    lgg = [q["lgg"] for q in pts]
    f = linfit(lgc, lgg)
    if f["slope"] == 0:
        raise ValueError("lgΓ–lgc 拟合斜率为 0，无法求出 1/n，请检查数据")
    inv_n = f["slope"]
    n_exp = 1.0 / inv_n
    lg_k = f["intercept"]
    k_f = 10 ** lg_k

    # Langmuir 线性化 c/Γ = c/Γ∞ + 1/(K_LΓ∞)
    cg = [q["c"] / q["gamma"] for q in pts]
    cs = [q["c"] for q in pts]
    lf = linfit(cs, cg)
    g_inf = 1.0 / lf["slope"] if lf["slope"] > 0 else None
    k_l = (lf["slope"] / lf["intercept"]) if (lf["intercept"] > 0 and g_inf) else None

    # ---------------- 图 1：lgΓ–lgc ----------------
    x_lo, x_hi = min(lgc), max(lgc)
    fit_line = [[x_lo, f["slope"] * x_lo + f["intercept"]],
                [x_hi, f["slope"] * x_hi + f["intercept"]]]
    chart1 = {
        "title": "Freundlich 等温线 · lgΓ–lgc",
        "xlabel": "lg[c /(mol·L⁻¹)]", "ylabel": "lg[Γ /(mmol·g⁻¹)]",
        "series": [
            {"name": "实验点", "type": "scatter", "color": "#2f6df6",
             "points": [[q["lgc"], q["lgg"]] for q in pts]},
            {"name": f"lgΓ = {inv_n:.4f}·lgc + {lg_k:.4f}", "type": "line", "color": "#e5533d",
             "points": fit_line},
        ],
        "annotations": True,
    }

    # ---------------- 图 2：Γ–c 等温线 ----------------
    c_min = min(q["c"] for q in pts)
    c_max = max(q["c"] for q in pts)
    grid = [c_min + (c_max - c_min) * i / 60 for i in range(61)]
    freund = [[c, k_f * c ** inv_n] for c in grid]
    series2 = [
        {"name": "实验点", "type": "scatter", "color": "#2f6df6",
         "points": [[q["c"], q["gamma"]] for q in pts]},
        {"name": "Freundlich 拟合", "type": "line", "color": "#e5533d", "points": freund},
    ]
    if g_inf and k_l:
        series2.append({"name": "Langmuir 拟合", "type": "line", "dash": True, "color": "#2f6df6",
                        "points": [[c, g_inf * k_l * c / (1 + k_l * c)] for c in grid]})
    chart2 = {
        "title": "吸附等温线 · Γ–c",
        "xlabel": "c /(mol·L⁻¹)", "ylabel": "Γ /(mmol·g⁻¹)",
        "series": series2,
        "annotations": True,
    }

    point_rows = [[q["no"] if q["no"] is not None else "", round(q["m"], 4),
                   round(q["c_0"], 5), round(q["c"], 5), round(q["gamma"], 4),
                   round(q["lgc"], 4), round(q["lgg"], 4)] for q in pts]
    fit_rows = [
        ["Freundlich", round(inv_n, 4), round(lg_k, 4), round(f["r"], 4),
         f"k = {k_f:.3f} mmol/g，n = {n_exp:.3f}"],
        ["Langmuir", round(lf["slope"], 4), round(lf["intercept"], 4), round(lf["r"], 4),
         (f"Γ∞ = {g_inf:.3f} mmol/g，K_L = {k_l:.3f}" if (g_inf and k_l) else "线性化不成立")],
    ]

    warnings = []
    if abs(f["r"]) < 0.99:
        warnings.append(f"Freundlich 拟合 r = {f['r']:.4f}，线性度偏低，可检查低浓度点的滴定误差")
    if g_inf is None or g_inf <= 0:
        warnings.append("Langmuir 线性化斜率非正，Γ∞ 与 K_L 无物理意义，仅保留 Freundlich 结果")
    if abs(n_exp - 1) < 0.05:
        warnings.append("n 接近 1，等温线接近线性，吸附位点差异不明显")

    return {
        "kpis": [
            {"label": "1/n", "value": round(inv_n, 4), "digits": 4,
             "hint": "Freundlich 直线斜率"},
            {"label": "n", "value": round(n_exp, 2), "digits": 2,
             "hint": "吸附强度指数，n > 1 表示优惠吸附"},
            {"label": "k", "value": round(k_f, 3), "unit": "mmol·g⁻¹", "digits": 3,
             "hint": "Freundlich 常数，10^(截距)"},
            {"label": "r（Freundlich）", "value": round(f["r"], 4), "digits": 4,
             "hint": "lgΓ–lgc 线性相关系数"},
        ],
        "charts": [chart1, chart2],
        "tables": [
            {"title": "各点浓度与吸附量", "columns": ["序号", "m / g", "c₀ /(mol·L⁻¹)",
                                                 "c /(mol·L⁻¹)", "Γ /(mmol·g⁻¹)",
                                                 "lgc", "lgΓ"], "rows": point_rows},
            {"title": "两种等温线拟合结果", "columns": ["模型", "斜率", "截距", "r", "参数"],
             "rows": fit_rows},
        ],
        "notes": [
            f"原始醋酸浓度 c₀,stock = {cnaoh:g}×{vstd:g}/{vha0:g} = {c_stock:.5f} mol/L；"
            "c₀ = c₀,stock·V(HAc)/V定容；c = c(NaOH)·V(NaOH)/Vc。",
            "吸附量 Γ = (c₀−c)·V定容/m，本模块用 mmol/g。原表 x = (c₀−c)×100（V=100 mL 时的 mmol 数），"
            "lgx/m 用的是 lg(Γ/mol·g⁻¹)，比本表的 lg[Γ/(mmol·g⁻¹)] 恰好小 3.000；两种写法斜率、r 完全相同，"
            "只是截距差 3（lg k 相差 3），本模块统一用 mmol/g。",
            f"Freundlich：1/n = {inv_n:.4f}，n = {n_exp:.3f}，k = {k_f:.3f} (mmol·g⁻¹)(L·mol⁻¹)^(1/n)，"
            f"r = {f['r']:.4f}。与原表逐点对照：第 1 点 lgc = −0.7434、原表 lgx/m = −2.7108，"
            "本模块 lgc = −0.7434、lgΓ = %.4f（差 3.000 见上条），其余三点同理。" % lgg[0],
            ("Langmuir 对照：Γ∞ = " + (f"{g_inf:.3f} mmol/g，K_L = {k_l:.3f}" if (g_inf and k_l) else "—")
             + f"，r = {lf['r']:.4f}。原表只做了 Freundlich，Langmuir 为附加对照。"),
            "本实验无原始脚本与报告，全部公式取自 A3数据处理.xlsx 的单元格公式（c₀、c、x、lgx/m、lgc 五行）。",
        ],
        "warnings": warnings,
    }
