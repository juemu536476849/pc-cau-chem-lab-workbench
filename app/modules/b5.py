# -*- coding: utf-8 -*-
"""B5 乙酸乙酯皂化反应速率常数：电导率线性化求二级反应 k 与活化能。"""
import math
from ..core import num, linfit

R_GAS = 8.314  # J/(mol·K)

# 电导率随时间变化（t/min, κ/(μS·cm⁻¹)），取自 B5数据处理.xlsx 的 25℃ 与 35℃ 两张表
T25 = [(0.5, 2180), (1, 2140), (1.5, 2100), (2, 2070), (2.5, 2030), (3, 1998), (3.5, 1964),
       (4, 1933), (4.5, 1903), (5, 1872), (6, 1799), (7, 1757), (8, 1726), (9, 1657), (10, 1679),
       (12, 1625), (14, 1574), (16, 1528), (18, 1489), (20, 1454), (22, 1423), (24, 1396),
       (26, 1370), (28, 1345), (30, 1312), (35, 1267)]
T35 = [(0.5, 2180), (1, 2120), (1.5, 2070), (2, 2000), (2.5, 1956), (3, 1916), (3.5, 1884),
       (4, 1852), (4.5, 1823), (5, 1795), (6, 1741), (7, 1692), (8, 1649), (9, 1607), (10, 1582),
       (12, 1522), (14, 1472), (16, 1429), (18, 1392), (20, 1359), (22, 1340), (24, 1307),
       (26, 1286), (28, 1263), (30, 1247), (35, 1232)]

T1_K = 298.15  # 25.00 ℃
T2_K = 308.15  # 35.00 ℃

SPEC = {
    "id": "b5",
    "code": "B5",
    "group": "物化",
    "name": "乙酸乙酯皂化反应速率常数",
    "subtitle": "电导率法测二级反应 k · 两温度求活化能 Ea",
    "tags": ["反应动力学", "二级反应", "电导率法", "活化能"],
    "desc": "乙酸乙酯在碱性条件下皂化是二级反应，反应过程中 OH⁻ 被 CH₃COO⁻ 取代，体系电导率单调下降。"
            "由 κ_t = κ_∞ + [1/(c₀k)]·(κ₀−κ_t)/t 线性化求速率常数 k 与 κ_∞，再用 25 ℃、35 ℃ 两组 k 求活化能。",
    "method": [
        "① 记录不同时刻的电导率 κ_t（μS/cm），初始浓度 c₀ 与初始电导率 κ₀ 由实验给定；",
        "② 二级反应 1/(a−x) = 1/a + k·t，而 κ 与离子浓度成正比，可推得 κ_t = κ_∞ + (1/(c₀k))·(κ₀−κ_t)/t；",
        "③ 以 y = κ_t 对 x = (κ₀−κ_t)/t 作最小二乘直线：斜率 = 1/(c₀k)，截距 = κ_∞；",
        "④ 于是 k = 1/(c₀·斜率)，同时得到 κ_∞（反应完全时的电导率）；",
        "⑤ 两个温度各得 k₁、k₂，按 Arrhenius 式 Ea = R·ln(k₂/k₁)/(1/T₁ − 1/T₂) 求活化能。",
    ],
    "tables": [
        {
            "key": "t25",
            "title": "25 ℃ 电导率–时间数据",
            "note": "第 1 列时间/min，第 2 列电导率/(μS·cm⁻¹)。起始一段混合未均匀，原表回归时剔除了 t = 0.5 min 的点，"
                    "可用参数“参与拟合的最早时刻”控制。",
            "columns": [
                {"key": "t", "label": "t / min", "type": "number"},
                {"key": "k", "label": "κ_t / (μS·cm⁻¹)", "type": "number"},
            ],
            "rows": [[t, g] for t, g in T25],
        },
        {
            "key": "t35",
            "title": "35 ℃ 电导率–时间数据",
            "note": "与 25 ℃ 表相同的记录方式，两表用同一套线性化公式处理后再求活化能。",
            "columns": [
                {"key": "t", "label": "t / min", "type": "number"},
                {"key": "k", "label": "κ_t / (μS·cm⁻¹)", "type": "number"},
            ],
            "rows": [[t, g] for t, g in T35],
        },
    ],
    "params": [
        {"key": "c_0", "label": "初始浓度 c₀", "type": "number", "default": 0.01019,
         "step": 0.0001, "hint": "mol/L，乙酸乙酯与 NaOH 等浓度混合后的初值"},
        {"key": "g0a", "label": "25 ℃ 初始电导率 κ₀", "type": "number", "default": 2250,
         "step": 1, "hint": "μS/cm，反应刚开始时体系的电导率（原表 G0 单元格）"},
        {"key": "g0b", "label": "35 ℃ 初始电导率 κ₀", "type": "number", "default": 2280,
         "step": 1, "hint": "μS/cm，同上，35 ℃ 组"},
        {"key": "t_start", "label": "参与拟合的最早时刻", "type": "number", "default": 1.0,
         "step": 0.5, "hint": "min；取 1.0 与原表一致（剔除 0.5 min 首点），取 0.5 则用全部点"},
    ],
}


def _fit(rows, g0, c0, t_start):
    pts = []
    for r in rows:
        if len(r) < 2:
            continue
        t, g = num(r[0]), num(r[1])
        if t is None or g is None or t <= 0:
            continue
        if t < t_start - 1e-9:
            continue
        pts.append((t, g))
    if len(pts) < 5:
        raise ValueError(f"可用数据点只有 {len(pts)} 个（t ≥ {t_start:g} min）："
                         "请把“参与拟合的最早时刻”调小或补录电导率数据")
    xs = [(g0 - g) / t for t, g in pts]
    ys = [g for _, g in pts]
    if max(xs) - min(xs) < 1e-9:
        raise ValueError("线性化的 x = (κ_0-κ_t)/t 全部相同，请检查 κ_0 是否填错")
    f = linfit(xs, ys)
    if f["slope"] <= 0:
        raise ValueError("线性化斜率不为正：请检查 κ_0 是否大于各时刻读数、以及 t 是否为正")
    k = 1.0 / (c0 * f["slope"])
    return {"pts": pts, "xs": xs, "ys": ys, "fit": f, "k": k, "kinf": f["intercept"]}


def run(data):
    tables = data.get("tables") or {}
    p = data.get("params") or {}
    rows25 = tables.get("t25") or []
    rows35 = tables.get("t35") or []

    c0 = num(p.get("c_0"), 0.01019)
    g0a = num(p.get("g0a"), 2250.0)
    g0b = num(p.get("g0b"), 2280.0)
    t_start = num(p.get("t_start"), 1.0)
    if c0 is None or c0 <= 0:
        raise ValueError("初始浓度 c_0 必须是正数（mol/L）")
    if g0a is None or g0b is None:
        raise ValueError("初始电导率 κ_0 必须填数值（μS/cm）")
    if t_start is None or t_start < 0:
        raise ValueError("参与拟合的最早时刻不能为负，一般取 0.5 或 1.0 min")

    a = _fit(rows25, g0a, c0, t_start)
    b = _fit(rows35, g0b, c0, t_start)
    if abs(b["k"] - a["k"]) < 1e-12:
        raise ValueError("两个温度得到的 k 相同，无法求活化能：请检查两张表是否贴成了同一组数据")

    ea = R_GAS * math.log(b["k"] / a["k"]) / (1.0 / T1_K - 1.0 / T2_K) / 1000.0
    if ea <= 0:
        raise ValueError("计算得到的活化能为负：35 ℃ 的 k 应大于 25 ℃，请检查两表是否贴反")

    # ---- 图 1：线性化 ----
    def fit_line(q):
        x1, x2 = 0.0, max(q["xs"]) * 1.04
        return [[0.0, round(q["fit"]["intercept"], 2)],
                [round(x2, 3), round(q["fit"]["slope"] * x2 + q["fit"]["intercept"], 2)]]

    chart1 = {
        "title": "κ_t – (κ₀−κ_t)/t 线性化（斜率 = 1/(c₀k)）",
        "xlabel": "(κ₀−κ_t)/t / (μS·cm⁻¹·min⁻¹)", "ylabel": "κ_t / (μS·cm⁻¹)",
        "series": [
            {"name": "25 ℃ 实测", "type": "scatter", "color": "#2f6df6",
             "points": [[round(x, 4), round(y, 2)] for x, y in zip(a["xs"], a["ys"])]},
            {"name": f"25 ℃ 拟合，k = {a['k']:.3f}", "type": "line", "color": "#2f6df6",
             "points": fit_line(a)},
            {"name": "35 ℃ 实测", "type": "scatter", "color": "#e5533d",
             "points": [[round(x, 4), round(y, 2)] for x, y in zip(b["xs"], b["ys"])]},
            {"name": f"35 ℃ 拟合，k = {b['k']:.3f}", "type": "line", "color": "#e5533d",
             "points": fit_line(b)},
        ],
        "hlines": [{"y": round(a["kinf"], 1), "label": f"κ∞(25℃) = {a['kinf']:.1f}"},
                   {"y": round(b["kinf"], 1), "label": f"κ∞(35℃) = {b['kinf']:.1f}"}],
    }

    chart2 = {
        "title": "电导率随时间的衰减",
        "xlabel": "t / min", "ylabel": "κ_t / (μS·cm⁻¹)",
        "series": [
            {"name": "25 ℃", "type": "line", "color": "#2f6df6",
             "points": [[t, g] for t, g in a["pts"]]},
            {"name": "35 ℃", "type": "line", "color": "#e5533d",
             "points": [[t, g] for t, g in b["pts"]]},
        ],
        "points": [{"x": a["pts"][0][0], "y": a["pts"][0][1],
                    "label": f"拟合起点 t = {a['pts'][0][0]:g} min"}],
    }

    t_rows = [
        [25.00, len(a["pts"]), round(a["fit"]["slope"], 4), round(a["kinf"], 2),
         round(a["k"], 4), round(a["fit"]["r"], 5), round(a["fit"]["r2"], 5)],
        [35.00, len(b["pts"]), round(b["fit"]["slope"], 4), round(b["kinf"], 2),
         round(b["k"], 4), round(b["fit"]["r"], 5), round(b["fit"]["r2"], 5)],
    ]
    arr_rows = [
        [round(T1_K, 2), round(1000.0 / T1_K, 4), round(a["k"], 4), round(math.log(a["k"]), 5)],
        [round(T2_K, 2), round(1000.0 / T2_K, 4), round(b["k"], 4), round(math.log(b["k"]), 5)],
    ]

    notes = [
        "线性化依据：1/(a−x) = 1/a + k·t，且 κ 与离子浓度成正比（κ_t−κ_∞ ∝ c_t），可推得 "
        "κ_t = κ_∞ + (1/(c₀k))·(κ₀−κ_t)/t；故斜率 = 1/(c₀k)、截距 = κ_∞，不需预先估 κ_∞。",
        f"拟合结果：25 ℃ 斜率 = {a['fit']['slope']:.4f}、κ∞ = {a['kinf']:.2f}、k = {a['k']:.4f} "
        f"L·mol⁻¹·min⁻¹（r² = {a['fit']['r2']:.5f}，n = {len(a['pts'])}）；35 ℃ 斜率 = "
        f"{b['fit']['slope']:.4f}、κ∞ = {b['kinf']:.2f}、k = {b['k']:.4f}（r² = {b['fit']['r2']:.5f}）。",
        "与 B5数据处理.xlsx 对照：该表 25 ℃ 处斜率 11.3567、截距 994.13、k = 8.6412；35 ℃ 斜率 7.2846、"
        "k = 13.4716 —— 二者都是剔除 t = 0.5 min 首点后的回归结果，与本模块 t_start = 1.0 完全一致。"
        "若改用全部 26 点，则为 25 ℃ 斜率 9.7975/κ_∞ 1079.70/k = 10.0164、35 ℃ 斜率 6.5436/k = 14.9973。",
        "原表 35 ℃ 的 κ_∞ 单元格写 1089.60，那是“全部点”回归的截距，与它自己用的斜率 7.2846（剔除首点）"
        "不是同一次回归，属原表内部不一致；本模块把斜率与截距取自同一次回归。",
        f"活化能：Ea = 8.314×ln({b['k']:.4f}/{a['k']:.4f})/(1/{T1_K:.2f} − 1/{T2_K:.2f}) = "
        f"{ea:.2f} kJ/mol。原表 33884.6 J/mol（33.88 kJ/mol）是按 298 K、308 K 的整数温度算的，"
        "本模块按 298.15/308.15 K，两者相差约 0.1%。",
        "实验报告 docx 几乎没有正文，只有 25 ℃、35 ℃ 的 (κ₀−κ_t)/t 序列柱线图与嵌入的 Excel，"
        "没有给出 k 的文字结论，故数值对照以上面的 xlsx 单元格为准。",
    ]

    warnings = []
    if min(a["fit"]["r2"], b["fit"]["r2"]) < 0.99:
        warnings.append(f"线性化 r² 偏低（25 ℃ {a['fit']['r2']:.4f}、35 ℃ {b['fit']['r2']:.4f}）："
                        "原始数据本身较分散（原表同样如此），可把“参与拟合的最早时刻”调大到 1.5～2 min、"
                        "或剔除 0.5～1 min 的混合段后再试")
    if a["kinf"] >= min(g for _, g in a["pts"]):
        warnings.append("25 ℃ 的 κ_∞ 不小于最小读数：说明 κ₀ 取得偏小，可适当调大 κ₀")

    return {
        "kpis": [
            {"label": "k（25 ℃）", "value": round(a["k"], 4), "unit": "L·mol⁻¹·min⁻¹",
             "digits": 4, "hint": "斜率 = 1/(c₀k) 反算"},
            {"label": "k（35 ℃）", "value": round(b["k"], 4), "unit": "L·mol⁻¹·min⁻¹",
             "digits": 4, "hint": "同一线性化方法"},
            {"label": "κ_∞（25 ℃）", "value": round(a["kinf"], 2), "unit": "μS·cm⁻¹", "digits": 2,
             "hint": "线性化截距，t→∞ 时的电导率"},
            {"label": "拟合优度（25 ℃）", "value": round(a["fit"]["r2"], 5), "digits": 5,
             "hint": "κ_t–(κ₀−κ_t)/t 直线拟合决定系数"},
            {"label": "Ea", "value": round(ea, 2), "unit": "kJ·mol⁻¹", "digits": 2,
             "hint": f"由 25 ℃ 与 35 ℃ 两点 k 按 Arrhenius 式求得（T = {T1_K:.2f}/{T2_K:.2f} K）"},
        ],
        "charts": [chart1, chart2],
        "tables": [
            {"title": "两温度线性化拟合结果",
             "columns": ["T / ℃", "点数", "斜率 / (μS·cm⁻¹·min)", "κ_∞ / (μS·cm⁻¹)",
                         "k / (L·mol⁻¹·min⁻¹)", "r", "R²"],
             "rows": t_rows},
            {"title": "Arrhenius 数据",
             "columns": ["T / K", "10³/T / K⁻¹", "k / (L·mol⁻¹·min⁻¹)", "ln k"],
             "rows": arr_rows},
        ],
        "notes": notes,
        "warnings": warnings,
    }

# 计算用到的公式（LaTeX 子集；前端与 Word 报告都会渲染成真正的公式）
SPEC["formulas"] = [
    r"kt = \frac{1}{c_{0}} \cdot \frac{\kappa_{0} - \kappa_{t}}{\kappa_{t} - \kappa_{\infty}}",
    r"\kappa_{t} = \kappa_{\infty} + \frac{1}{c_{0} k} \cdot \frac{\kappa_{0} - \kappa_{t}}{t}",
    r"\ln k = -\frac{E_{a}}{R} \cdot \frac{1}{T} + C",
]
