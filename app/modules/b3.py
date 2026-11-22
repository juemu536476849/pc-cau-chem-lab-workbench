# -*- coding: utf-8 -*-
"""B3 最大气泡压力差法测溶液表面张力：σ = k'·p，Szyszkowski 拟合，Gibbs 吸附量。"""
from ..core import num

# 6 次压力读数，单位 Pa；首尾两行为纯水（实验开始、结束各测一次）
RAW = [
    [0.000, 755, 750, 757, 756, 757, 757],
    [0.0125, 744, 734, 737, 736, 736, 733],
    [0.025, 700, 711, 704, 702, 701, 698],
    [0.050, 650, 647, 648, 613, 651, 649],
    [0.100, 590, 587, 588, 588, 589, 589],
    [0.200, 487, 489, 492, 490, 487, 489],
    [0.300, 468, 439, 436, 435, 438, 437],
    [0.400, 419, 392, 389, 391, 394, 389],
    [0.000, 760, 766, 762, 763, 763, 763],
]

R_GAS = 8.314  # J/(mol·K)

SPEC = {
    "id": "b3",
    "code": "B3",
    "group": "物化",
    "name": "最大气泡压力差法测溶液表面张力",
    "subtitle": "压力读数 → σ–c 曲线 · Szyszkowski 拟合与 Gibbs 吸附量",
    "tags": ["表面张力", "Szyszkowski", "Gibbs 吸附", "最大气泡压力法"],
    "desc": "用最大气泡压力法测不同浓度正丁醇（或同类表面活性物）水溶液的最大压差 Δp，"
            "由纯水标定仪器常数 k' 后换算表面张力 σ，再对 σ–c 曲线作 Szyszkowski 对数拟合，"
            "并由 Gibbs 吸附等温式求表面吸附量 Γ 与饱和吸附量 Γ∞。",
    "method": [
        "① 每种浓度取 6 次压力读数求平均 p̄，纯水测两次（实验首尾），按“行均值再平均”得 p̄水；",
        "② 由 σ水 = k'·p̄水 标定仪器常数 k'（本实验 σ水(25℃) = 71.97×10⁻³ N/m）；",
        "③ σ = k'·p̄ 逐点换算表面张力；",
        "④ 对 σ–c 做 Szyszkowski 拟合 σ = a − b·ln(1 + c·x)（非线性最小二乘，初值 [1,1,1]）；",
        "⑤ Gibbs 吸附量 Γ = −(c/RT)·(dσ/dc) = (b·c·x)/(RT·(1+c·x))，极限 Γ∞ = b/(RT)。",
    ],
    "tables": [{
        "key": "raw",
        "title": "最大压差原始数据（每浓度 6 次读数）",
        "note": "第 1 列为浓度 c/(mol·L⁻¹)，2–7 列为 6 次压力读数/Pa。首行与末行为纯水（c=0），"
                "用于标定 k'：程序把同一浓度的行先各自取均值、再对行均值取平均。",
        "columns": [
            {"key": "c", "label": "c / (mol·L⁻¹)", "type": "number"},
            {"key": "p1", "label": "p₁ / Pa", "type": "number"},
            {"key": "p2", "label": "p₂ / Pa", "type": "number"},
            {"key": "p3", "label": "p₃ / Pa", "type": "number"},
            {"key": "p4", "label": "p₄ / Pa", "type": "number"},
            {"key": "p5", "label": "p₅ / Pa", "type": "number"},
            {"key": "p6", "label": "p₆ / Pa", "type": "number"},
        ],
        "rows": RAW,
    }],
    "params": [
        {"key": "sigma_w", "label": "纯水表面张力 σ水", "type": "number", "default": 0.07197,
         "step": 0.00001, "hint": "25 ℃ 取 0.07197 N/m；温度不同按手册值改"},
        {"key": "T", "label": "实验温度 t", "type": "number", "default": 25.0,
         "step": 0.1, "hint": "℃；只用于 Gibbs 式中的 RT"},
        {"key": "point0", "label": "纯水点是否参与拟合", "type": "select", "default": "yes",
         "options": [{"value": "yes", "label": "是（原脚本）"},
                     {"value": "no", "label": "只用 c>0 各点"}]},
        {"key": "gamma_c", "label": "标注 Γ 的浓度", "type": "number", "default": 0.2,
         "step": 0.01, "hint": "在 σ–c 图上标出该浓度的 σ 与 Γ，便于与报告表 2 对照"},
    ],
}


def _szyszkowski(x, a, b, c):
    import numpy as np
    return a - b * np.log1p(c * x)


def run(data):
    rows = (data.get("tables") or {}).get("raw") or []
    p = data.get("params") or {}
    sigma_w = num(p.get("sigma_w"), 0.07197)
    t_c = num(p.get("T"), 25.0)
    keep0 = (p.get("point0") or "yes") != "no"
    gc = num(p.get("gamma_c"), 0.2)

    if sigma_w is None or sigma_w <= 0:
        raise ValueError("纯水表面张力 σ水 必须是正数（单位 N/m）")
    t_k = t_c + 273.15
    if t_k <= 0:
        raise ValueError("实验温度必须高于 −273.15 ℃")

    # ---- 逐行求均值 ----
    per = []
    for r in rows:
        if not r:
            continue
        c = num(r[0])
        if c is None:
            continue
        vals = [num(v) for v in r[1:7]]
        vals = [v for v in vals if v is not None and v > 0]
        if not vals:
            continue
        per.append((c, sum(vals) / len(vals)))
    if not per:
        raise ValueError("压力表为空：请粘贴浓度列与 6 列压力读数（Pa）")

    groups = {}
    for c, pv in per:
        groups.setdefault(round(c, 10), []).append(pv)
    if 0.0 not in groups:
        raise ValueError("表中缺少纯水（c = 0）行，无法用 σ水 = k'·p水 标定仪器常数 k'")
    p_w = sum(groups[0.0]) / len(groups[0.0])
    if p_w <= 0:
        raise ValueError("纯水压力读数必须为正数，请检查 c = 0 那一行")

    kp = sigma_w / p_w
    cs = sorted(groups)
    pbar = [sum(groups[c]) / len(groups[c]) for c in cs]
    sig = [kp * q for q in pbar]

    # ---- 拟合 ----
    fit_c, fit_s = [], []
    for c, s in zip(cs, sig):
        if (not keep0) and c <= 0:
            continue
        fit_c.append(c)
        fit_s.append(s)
    if len(fit_c) < 4:
        raise ValueError("可用于拟合的浓度点不足 4 个：请检查浓度列是否重复或纯水点是否被排除")

    try:
        import numpy as np
        from scipy.optimize import curve_fit
    except ImportError:
        raise ValueError("需要 numpy 与 scipy 才能做 Szyszkowski 非线性拟合，请先安装 scipy")

    xa = np.asarray(fit_c, dtype=float)
    ya = np.asarray(fit_s, dtype=float)
    retried = False
    try:
        popt, pcov = curve_fit(_szyszkowski, xa, ya, p0=[1.0, 1.0, 1.0], maxfev=20000)
    except Exception:
        try:
            popt, pcov = curve_fit(_szyszkowski, xa, ya,
                                   p0=[float(max(sig)), 0.02, 10.0], maxfev=40000)
            retried = True
        except Exception:
            raise ValueError("Szyszkowski 拟合失败：请检查 σ 是否随浓度单调下降、数据是否为正值")
    a, b, cc = (float(v) for v in popt)
    if b <= 0 or cc <= 0:
        raise ValueError("拟合得到的 b 或 c 不为正，σ–c 数据可能反向或离散过大，请核对压力读数")

    pred = _szyszkowski(xa, a, b, cc)
    ss_res = float(((ya - pred) ** 2).sum())
    ss_tot = float(((ya - ya.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    rms = (ss_res / len(xa)) ** 0.5

    # ---- Gibbs 吸附量 ----
    rt = R_GAS * t_k
    gam = []
    for c in cs:
        if c <= 0:
            gam.append(0.0)
        else:
            gam.append(c * b * cc / (rt * (1 + cc * c)))
    g_inf = b / rt

    def sigma_at(x):
        import math
        return a - b * math.log1p(cc * x)

    def gamma_at(x):
        return x * b * cc / (rt * (1 + cc * x))

    # ---- 图 ----
    cmax = max(cs)
    grid = [cmax * i / 120.0 for i in range(121)]
    sigma_grid = [[round(x, 5), round(sigma_at(x), 6)] for x in grid]
    gam_grid = [[round(x, 5), round(gamma_at(x) * 1e6, 4)] for x in grid]

    gc_use = min(max(gc, 0.0), cmax)
    s_gc = sigma_at(gc_use)
    g_gc = gamma_at(gc_use) * 1e6

    chart1 = {
        "title": "σ–c 曲线与 Szyszkowski 拟合",
        "xlabel": "c / (mol·L⁻¹)", "ylabel": "σ / (N·m⁻¹)",
        "series": [
            {"name": "实测 σ", "type": "scatter",
             "points": [[round(c, 5), round(s, 6)] for c, s in zip(cs, sig)]},
            {"name": f"σ = a − b·ln(1+c·x)", "type": "line", "color": "#e5533d",
             "points": sigma_grid},
        ],
        "points": [{"x": round(gc_use, 4), "y": round(s_gc, 6),
                    "label": f"拟合曲线 c={gc_use:g}：σ={s_gc:.5f}, Γ={g_gc:.2f} μmol/m²"}],
        "vlines": [{"x": round(gc_use, 4), "label": f"标注 c={gc_use:g}"}],
        "xrange": [-0.01, round(cmax * 1.06, 3)],
    }
    chart2 = {
        "title": "Gibbs 吸附量 Γ 随浓度的变化",
        "xlabel": "c / (mol·L⁻¹)", "ylabel": "Γ / (10⁻⁶ mol·m⁻²)",
        "series": [
            {"name": "Γ（拟合曲线）", "type": "line", "color": "#2f6df6", "points": gam_grid},
            {"name": "各浓度 Γ", "type": "scatter",
             "points": [[round(c, 5), round(g * 1e6, 4)] for c, g in zip(cs, gam) if c > 0]},
        ],
        "hlines": [{"y": round(g_inf * 1e6, 4), "label": f"Γ∞ = b/RT = {g_inf * 1e6:.3f}"}],
        "xrange": [0, round(cmax * 1.06, 3)],
    }

    table_rows = []
    for c, q, s, g in zip(cs, pbar, sig, gam):
        table_rows.append([round(c, 4), round(q, 2), round(s, 6), round(g * 1e6, 3)])

    notes = [
        f"仪器常数 k' = σ水 / p̄水 = {sigma_w:.5f} / {p_w:.2f} = {kp:.4e} m，"
        f"故 σ = {kp:.3e}·p̄（Pa → N/m）。",
        f"Szyszkowski 拟合结果：a = {a:.5f} N/m，b = {b:.5f} N/m，c = {cc:.3f} L/mol，"
        f"R² = {r2:.5f}，残差均方根 {rms:.2e} N/m。",
        f"Γ∞ = b/(RT) = {b:.5f}/(8.314×{t_k:.2f}) = {g_inf:.3e} mol/m² = {g_inf * 1e6:.2f} μmol/m²。",
        "与报告对照（报告 PNG 中的 Origin 拟合表）：a = 0.07221、b = 0.01634、c = 18.6257、R² = 0.99962；"
        f"本模块用 xlsx 原始读数得 a = {a:.5f}、b = {b:.5f}、c = {cc:.3f}、R² = {r2:.5f}，"
        "偏差主要来自 σ 数据本身（见下条）。",
        f"报告表 1 的 Δp（789.2/757.6/725.6/670.6/603.9/511.1/457.7/408.1 Pa）比 xlsx 原始读数均值"
        f"（{pbar[0]:.1f}/{pbar[1]:.1f}/{pbar[2]:.1f}/{pbar[3]:.1f}/{pbar[4]:.1f}/{pbar[5]:.1f}/"
        f"{pbar[6]:.1f}/{pbar[7]:.1f} Pa）高 3%～5%，可能出自另一次测量；本模块严格按 workbook 原始读数计算。",
        "报告表 2 的 Γ 列（1.87/2.22/2.93/4.34/7.16/9.99/12.81 ×10⁻⁶ mol/m²）最大值已超过 b/RT = "
        f"{(0.01634 / rt) * 1e6:.2f}，与 Gibbs 公式不自洽，疑为笔误；本模块按 Γ = −(c/RT)·dσ/dc 重算。",
    ]
    if retried:
        notes.append("注：初值 [1,1,1] 未收敛，已自动改用 [σmax, 0.02, 10] 作为初值重新拟合。")

    warnings = []
    if r2 < 0.98:
        warnings.append(f"拟合 R² = {r2:.5f}，偏低：请检查高浓度点的压力读数是否稳定")
    if abs(g_gc) > 0 and g_gc > g_inf * 1e6 * 1.001:
        warnings.append("标注浓度的 Γ 已超过 Γ∞，说明拟合参数异常，请核对浓度列")

    return {
        "kpis": [
            {"label": "a", "value": round(a, 5), "unit": "N·m⁻¹", "digits": 5,
             "hint": "Szyszkowski 方程截距，接近纯溶剂表面张力"},
            {"label": "b", "value": round(b, 5), "unit": "N·m⁻¹", "digits": 5,
             "hint": "吸附引起的表面张力降幅参数"},
            {"label": "c", "value": round(cc, 3), "unit": "L·mol⁻¹", "digits": 3,
             "hint": "吸附平衡常数（ln 括号内系数）"},
            {"label": "拟合优度", "value": round(r2, 5), "digits": 5, "hint": "σ–c 拟合决定系数 R²"},
            {"label": "Γ∞", "value": round(g_inf * 1e6, 3), "unit": "μmol·m⁻²", "digits": 3,
             "hint": "饱和吸附量 b/(RT)"},
        ],
        "charts": [chart1, chart2],
        "tables": [{
            "title": "各浓度压力均值、表面张力与吸附量",
            "columns": ["c / (mol·L⁻¹)", "p̄ / Pa", "σ / (N·m⁻¹)", "Γ / (10⁻⁶ mol·m⁻²)"],
            "rows": table_rows,
        }],
        "notes": notes,
        "warnings": warnings,
    }

# 计算用到的公式（LaTeX 子集；前端与 Word 报告都会渲染成真正的公式）
SPEC["formulas"] = [
    r"\sigma = a - b\ln(1 + cx)",
]
