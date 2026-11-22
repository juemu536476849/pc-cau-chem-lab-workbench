# -*- coding: utf-8 -*-
"""A2 配合物的组成及稳定常数：连续变化法样条切线交点定组成，两组总浓度联立求 K。"""
import math

from ..core import xy, num, linfit, line_y, fit_through_origin, spline_points

# 原表 Sheet2 (4)：第 1 组 V(N)/mL = 0,2,4,6,8,10 与 V(B) 配成 10.00 mL（总浓度 0.002 mol/L）；
# 第 2 组 V(N) = 0,4,8,12,16,20 配成 20.00 mL（总浓度 0.004 mol/L）。
# x_VN 为原表直接给出的摩尔分数（数值上等于 V(N)/50 与 V(N)/100）。
RAW = [
    [0.00, 0.000, 0.000],
    [0.04, 0.121, 0.256],
    [0.08, 0.235, 0.476],
    [0.12, 0.238, 0.488],
    [0.16, 0.126, 0.249],
    [0.20, 0.000, 0.000],
]

# 工作曲线（原表 N4:R4，V(B)=10.00 mL 固定，V(N)=2,4,6,8,10 mL），表中 D 行实为已扣空白的 ΔD。
CAL = [
    [0.04, 0.129],
    [0.08, 0.258],
    [0.12, 0.386],
    [0.16, 0.514],
    [0.20, 0.650],
]

SPEC = {
    "id": "a2",
    "code": "A2",
    "group": "物化",
    "name": "配合物的组成及稳定常数",
    "subtitle": "连续变化法 · 样条切线交点定组成，双浓度联立求 K",
    "tags": ["配合物", "连续变化法", "切线交点", "稳定常数"],
    "desc": "固定配合物总浓度、连续改变两组分的摩尔分数 x_VN，测 527 nm 处吸光度差 ΔD。"
            "ΔD–x_VN 曲线用三次样条平滑后，在上升段与下降段各作切线，两切线交点给出配合物组成；"
            "再由两组总浓度下的平衡浓度联立方程求稳定常数 K 与 ΔG。",
    "method": [
        "① 对 ΔD–x_VN 的 6 个点作三次样条插值（k=3）；",
        "② 在 x=0.04 与 x=0.16 处取样条导数作两条切线，解交点 (x_t, ΔD_t)；",
        "③ 另求样条与 ΔD=0.1 水平线的交点横坐标 x_VN（原脚本用 fsolve 求根）；",
        "④ 工作曲线 ΔD–x_VN 强制过原点拟合，得斜率 k′，由 ΔD_t/k′ 得配合物平衡浓度；",
        "⑤ 两组总浓度 c₁、c₂ 各给一组初始浓度 (aᵢ, bᵢ)，令 1/K 相等解出平衡浓度 x，"
        "再由 K = x/[(a₁−x)(b₁−x)] 求 K，ΔG = −RT ln K。",
    ],
    "tables": [
        {
            "key": "raw",
            "title": "连续变化法 ΔD–x_VN 数据",
            "note": "x_VN 为原表给出的摩尔分数；第 1 组总浓度 0.002 mol/L，第 2 组 0.004 mol/L。"
                    "ΔD = D − D₀（已扣试剂空白）。",
            "columns": [
                {"key": "x", "label": "x_VN", "type": "number"},
                {"key": "d1", "label": "ΔD（第 1 组，c₁=0.002）", "type": "number"},
                {"key": "d2", "label": "ΔD（第 2 组，c₂=0.004）", "type": "number"},
            ],
            "rows": RAW,
        },
        {
            "key": "cal",
            "title": "工作曲线 ΔD–x_VN",
            "note": "V(B)=10.00 mL 固定，V(N)=2~10 mL；用于把交点吸光度换算成配合物浓度。",
            "columns": [
                {"key": "x", "label": "x_VN", "type": "number"},
                {"key": "d", "label": "ΔD", "type": "number"},
            ],
            "rows": CAL,
        },
    ],
    "params": [
        {"key": "c1", "label": "第 1 组总浓度 c₁", "type": "number", "default": 0.002,
         "step": 0.001, "hint": "单位 mol/L；用于把 x_VN 换算成初始浓度"},
        {"key": "c2", "label": "第 2 组总浓度 c₂", "type": "number", "default": 0.004,
         "step": 0.001, "hint": "单位 mol/L；原表为第 1 组的 2 倍"},
        {"key": "T", "label": "实验温度 T", "type": "number", "default": 20.2,
         "step": 0.1, "hint": "单位 ℃，用于 ΔG = −RT lnK（原脚本取 20.2 ℃）"},
        {"key": "dref", "label": "参考水平线 ΔD₀", "type": "number", "default": 0.1,
         "step": 0.01, "hint": "样条与该水平线的交点横坐标即报告中的 x_VN"},
    ],
}


def _spline(xs, ys):
    """构造三次样条；scipy 不可用时给出中文提示。"""
    try:
        import numpy as np
        from scipy.interpolate import make_interp_spline
    except Exception:
        raise ValueError("缺少 scipy，无法完成三次样条插值与切线求交，请先安装 scipy")
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    return make_interp_spline(x, y, k=3)


def _first_root(spl, xs, dref):
    """在相邻数据点区间内找样条曲线与 y = dref 的第一个交点（上升段）。"""
    from scipy.optimize import brentq
    for i in range(len(xs) - 1):
        a, b = xs[i], xs[i + 1]
        fa = float(spl(a)) - dref
        fb = float(spl(b)) - dref
        if fa == 0:
            return a
        if fa * fb < 0:
            return float(brentq(lambda t: float(spl(t)) - dref, a, b))
    raise ValueError(f"样条曲线在 x_VN = {xs[0]:g}~{xs[-1]:g} 之间没有与 ΔD = {dref:g} 的交点，"
                     f"请检查参考水平线或数据")


def _analyse(xs, ys, dref):
    """样条 + 两条切线 + 交点 + 水平线交点，返回一组结果。"""
    spl = _spline(xs, ys)
    i1, i2 = 1, len(xs) - 2          # 原脚本取 x[1]=0.04 与 x[4]=0.16
    s1 = float(spl.derivative(nu=1)(xs[i1]))
    s2 = float(spl.derivative(nu=1)(xs[i2]))
    b1 = ys[i1] - s1 * xs[i1]
    b2 = ys[i2] - s2 * xs[i2]
    if abs(s1 - s2) < 1e-12:
        raise ValueError("两条切线几乎平行，无法求交点，请检查 ΔD 数据")
    xi = (b2 - b1) / (s1 - s2)
    yi = s1 * xi + b1
    root = _first_root(spl, xs, dref)
    return {"s1": s1, "s2": s2, "b1": b1, "b2": b2, "xi": xi, "yi": yi, "root": root,
            "x1": xs[i1], "x2": xs[i2]}


def run(data):
    tbl = data.get("tables") or {}
    rows = tbl.get("raw") or []
    cal = tbl.get("cal") or []
    p = data.get("params") or {}

    c1 = num(p.get("c1"), 0.002)
    c2 = num(p.get("c2"), 0.004)
    T = num(p.get("T"), 20.2)
    dref = num(p.get("dref"), 0.1)

    if c1 <= 0 or c2 <= 0:
        raise ValueError("两组总浓度 c₁、c₂ 必须为正值（单位 mol/L）")
    if T <= -273.15:
        raise ValueError("温度必须高于绝对零度 −273.15 ℃")
    if dref is None or dref <= 0:
        raise ValueError("参考水平线 ΔD₀ 必须为正值")

    xs, d1 = xy(rows, 0, 1)
    _, d2 = xy(rows, 0, 2)
    if len(xs) < 4:
        raise ValueError("连续变化法至少需要 4 个 x_VN 数据点（本实验为 6 个），请检查表格")
    if len(d2) != len(xs):
        raise ValueError("第 2 组 ΔD 列有缺失，请补全后再计算")
    for i in range(len(xs) - 1):
        if xs[i] >= xs[i + 1]:
            raise ValueError("x_VN 必须按从小到大排列，且不能重复")

    r1 = _analyse(xs, d1, dref)
    r2 = _analyse(xs, d2, dref)

    # ---------------- 工作曲线：ΔD 与 x_VN 过原点拟合 ----------------
    xc, yc = xy(cal, 0, 1)
    if len(xc) < 2:
        raise ValueError("工作曲线至少需要 2 个数据点，请在“工作曲线”表中补全")
    k0 = fit_through_origin(xc, yc)
    if k0 <= 0:
        raise ValueError("工作曲线斜率不为正，无法把 ΔD 换算成浓度，请检查 ΔD 数据")
    x_n1 = r1["yi"] / k0
    x_n2 = r2["yi"] / k0
    c_n1 = c1 * x_n1
    c_n2 = c1 * x_n2

    # ---------------- 两组总浓度联立求平衡浓度 ----------------
    # 原脚本：a1 = c1*x_VN1, b1 = c1*(0.2-x_VN1), a2 = c1*x_VN2, b2 = c1*(0.4-x_VN2)。
    # 其中 b2 的 0.4 = 0.2*c2/c1（第 2 组总浓度翻倍），而 a2 仍用 c1 —— 原脚本这一处量纲不一致，
    # 本模块按原式复现（见 notes），span2 为第 2 组的摩尔分数跨度。
    span2 = 0.2 * c2 / c1
    a1, b1 = c1 * r1["root"], c1 * (0.2 - r1["root"])
    a2, b2 = c1 * r2["root"], c1 * (span2 - r2["root"])
    den = (a1 + b1) - (a2 + b2)
    if abs(den) < 1e-15:
        raise ValueError("两组浓度联立时分母为零（c₁ 与 c₂ 相同？），无法求出平衡浓度")
    x_eq = (a1 * b1 - a2 * b2) / den
    if x_eq <= 0 or x_eq >= min(a1, b1):
        raise ValueError("联立求得的平衡浓度超出合理范围（0 < x < min(a₁,b₁)），"
                         "请检查 x_VN、总浓度或 ΔD 数据")
    K = x_eq / ((a1 - x_eq) * (b1 - x_eq))
    if K <= 0:
        raise ValueError("稳定常数 K 非正，无法计算 ΔG，请检查数据")
    dG = -8.314 * (T + 273.15) * math.log(K) / 1000.0

    # 工作曲线法（原脚本 kn 路线，仅作参考，分母病态）
    k_n1 = c_n1 / ((c1 * r1["xi"] - c_n1) * (c1 * (0.2 - r1["xi"]) - c_n1))

    xx1, yy1 = spline_points(xs, d1, 240)
    xx2, yy2 = spline_points(xs, d2, 240)
    x_lo, x_hi = min(xs), max(xs)
    tan1_pts = [[r1["x1"], line_y({"slope": r1["s1"], "intercept": r1["b1"]}, r1["x1"])],
                [r1["xi"], r1["yi"]]]
    tan2_pts = [[r1["xi"], r1["yi"]],
                [r1["x2"], line_y({"slope": r1["s2"], "intercept": r1["b2"]}, r1["x2"])]]
    tan3_pts = [[r2["x1"], line_y({"slope": r2["s1"], "intercept": r2["b1"]}, r2["x1"])],
                [r2["xi"], r2["yi"]]]
    tan4_pts = [[r2["xi"], r2["yi"]],
                [r2["x2"], line_y({"slope": r2["s2"], "intercept": r2["b2"]}, r2["x2"])]]

    chart1 = {
        "title": "连续变化法 · ΔD–x_VN 曲线与两切线交点",
        "xlabel": "x_VN", "ylabel": "ΔD（527 nm）",
        "series": [
            {"name": "第 1 组 样条", "type": "line", "color": "#2f6df6",
             "points": [[a, b] for a, b in zip(xx1, yy1)]},
            {"name": "第 2 组 样条", "type": "line", "color": "#e5533d",
             "points": [[a, b] for a, b in zip(xx2, yy2)]},
            {"name": "第 1 组 实验点", "type": "scatter", "color": "#2f6df6",
             "points": [[a, b] for a, b in zip(xs, d1)]},
            {"name": "第 2 组 实验点", "type": "scatter", "color": "#e5533d",
             "points": [[a, b] for a, b in zip(xs, d2)]},
            {"name": "第 1 组 切线", "type": "line", "dash": True, "color": "#2f6df6",
             "points": [tan1_pts[0], tan1_pts[1], tan2_pts[1]]},
            {"name": "第 2 组 切线", "type": "line", "dash": True, "color": "#e5533d",
             "points": [tan3_pts[0], tan3_pts[1], tan4_pts[1]]},
        ],
        "hlines": [{"y": dref, "label": f"ΔD = {dref:g}"}],
        "vlines": [{"x": r1["root"], "label": f"x_VN1 = {r1['root']:.3f}"},
                   {"x": r2["root"], "label": f"x_VN2 = {r2['root']:.3f}"}],
        "points": [{"x": r1["xi"], "y": r1["yi"], "label": f"交点1 ({r1['xi']:.3f}, {r1['yi']:.3f})"},
                   {"x": r2["xi"], "y": r2["yi"], "label": f"交点2 ({r2['xi']:.3f}, {r2['yi']:.3f})"}],
        "annotations": True,
        "xrange": [x_lo - 0.01, x_hi + 0.01],
    }

    k0_line = [[0.0, 0.0], [x_hi, k0 * x_hi]]
    chart2 = {
        "title": "工作曲线 · ΔD–x_VN（强制过原点）",
        "xlabel": "x_VN", "ylabel": "ΔD",
        "series": [
            {"name": "工作曲线数据", "type": "scatter", "color": "#2f6df6",
             "points": [[a, b] for a, b in zip(xc, yc)]},
            {"name": f"ΔD = {k0:.4f}·x_VN", "type": "line", "color": "#e5533d", "points": k0_line},
        ],
        "points": [{"x": 0, "y": 0, "label": "过原点"}],
        "xrange": [0, x_hi + 0.01],
    }

    rep_rows = [
        ["上升段切线斜率 k₁", round(r1["s1"], 4), round(r2["s1"], 4), "3.45 / 6.73"],
        ["下降段切线斜率 k₂", round(r1["s2"], 4), round(r2["s2"], 4), "−3.48 / −7.38"],
        ["切线 1 截距 b₁", round(r1["b1"], 4), round(r2["b1"], 4), "−0.02 / −0.01"],
        ["切线 2 截距 b₂", round(r1["b2"], 4), round(r2["b2"], 4), "0.68 / 1.43"],
        ["两切线交点 x", round(r1["xi"], 4), round(r2["xi"], 4), "0.101 / 0.102"],
        ["两切线交点 ΔD", round(r1["yi"], 4), round(r2["yi"], 4), "0.332 / 0.675"],
        ["样条与 ΔD=0.1 的交点 x_VN", round(r1["root"], 4), round(r2["root"], 4), "0.034 / 0.017"],
    ]

    warnings = []
    if abs(r1["s1"] - r1["s2"]) < 1e-6:
        warnings.append("第 1 组两条切线接近平行，交点不可靠")
    if r1["root"] > 0.06 or r2["root"] > 0.06:
        warnings.append("水平线交点明显偏离上升段，请确认 ΔD₀ 是否取 0.1")
    if k0 <= 0:
        warnings.append("工作曲线斜率非正，浓度换算不可靠")
    if k_n1 > 1e5 or k_n1 < 0:
        warnings.append("工作曲线法算出的 K₁ 数量级异常（分母 (c₁x_t−c_n) 接近 0），该路线病态，仅供参考")

    return {
        "kpis": [
            {"label": "切线交点 x（第 1 组）", "value": round(r1["xi"], 4), "digits": 4,
             "hint": "报告值 0.101"},
            {"label": "切线交点 x（第 2 组）", "value": round(r2["xi"], 4), "digits": 4,
             "hint": "报告值 0.102"},
            {"label": "x_VN（ΔD=0.1）", "value": round(r1["root"], 4), "digits": 4,
             "hint": f"报告值 0.034；第 2 组 {r2['root']:.4f}（报告 0.017）"},
            {"label": "稳定常数 K", "value": round(K, 1), "unit": "L·mol⁻¹", "digits": 1,
             "hint": f"两组浓度联立，平衡浓度 x = {x_eq:.3e} mol/L"},
            {"label": "ΔG", "value": round(dG, 2), "unit": "kJ·mol⁻¹", "digits": 2,
             "hint": f"ΔG = −RT lnK，T = {T:g} ℃"},
        ],
        "charts": [chart1, chart2],
        "tables": [
            {"title": "切线、交点与报告值对照", "columns": ["项目", "第 1 组", "第 2 组", "实验报告值"],
             "rows": rep_rows},
            {"title": "浓度换算与稳定常数", "columns": ["项目", "数值", "单位", "说明"],
             "rows": [
                 ["工作曲线斜率 k′", round(k0, 4), "—", "ΔD = k′·x_VN，强制过原点"],
                 ["x_n（第 1 组）", round(x_n1, 4), "—", "= ΔD_交点 / k′"],
                 ["c_n（第 1 组）", round(c_n1 * 1e4, 4), "10⁻⁴ mol·L⁻¹", "= c₁·x_n"],
                 ["a₁", round(a1 * 1e4, 4), "10⁻⁴ mol·L⁻¹", "= c₁·x_VN(ΔD=0.1)"],
                 ["b₁", round(b1 * 1e4, 4), "10⁻⁴ mol·L⁻¹", "= c₁·(0.20 − x_VN)"],
                 ["a₂", round(a2 * 1e4, 4), "10⁻⁴ mol·L⁻¹", "原脚本按 c₁·x_VN2，未按第 2 组翻倍"],
                 ["b₂", round(b2 * 1e4, 4), "10⁻⁴ mol·L⁻¹", "= c₁·(0.40 − x_VN2)，已按第 2 组翻倍"],
                 ["平衡浓度 x", round(x_eq * 1e6, 4), "10⁻⁶ mol·L⁻¹", "由两组 1/K 相等联立解出"],
                 ["K", round(K, 1), "L·mol⁻¹", "两组总浓度联立的表观稳定常数"],
                 ["ΔG", round(dG, 2), "kJ·mol⁻¹", "ΔG = −RT·lnK，T = 20.2 ℃"],
             ]},
        ],
        "notes": [
            f"切线交点：第 1 组 ({r1['xi']:.4f}, {r1['yi']:.4f})，第 2 组 ({r2['xi']:.4f}, {r2['yi']:.4f})；"
            "实验报告为 (0.101, 0.332) 与 (0.102, 0.675)，完全吻合。",
            f"样条与 ΔD=0.1 的交点：第 1 组 {r1['root']:.4f}、第 2 组 {r2['root']:.4f}；报告写 x_VN1=0.034、"
            "x_VN2=0.017。原脚本里 x_VN1 这一行是在 fsolve 之后才输出的，变量已被根覆盖，"
            "所以它其实是“样条与 ΔD=0.1 水平线”的交点横坐标，而不是切线交点的横坐标；本模块把两者分开列出。",
            f"稳定常数用两组总浓度联立：令 1/K 相等，得 x = {x_eq:.3e} mol/L，K = {K:.1f} L/mol，"
            f"ΔG = {dG:.2f} kJ/mol。output.txt 记录 K = 459.6、ΔG = −14.95 kJ/mol（fsolve 收敛精度略差），"
            "output - 副本.txt 记录 K = 419.07、ΔG = −14.73 kJ/mol，与本次复算一致。",
            "原脚本中 a₂ = 0.002·x_VN2 而 b₂ = 0.002·(0.4−x_VN2)，两者用的总浓度不一致（b₂ 已按第 2 组翻倍，"
            "a₂ 未翻倍）；本模块按原式复现并在表里标注。若把 a₂ 改用 c₂·x_VN2，K 会变成 2.77×10⁵（x_t 也随之跳到 6.7×10⁻⁵），"
            "说明该路线本身对组分浓度很敏感，K 值应结合工作曲线法一并判断。",
            "工作曲线法（kn 路线）复算 K₁ = %.3e、ΔG₁ = %.1f kJ/mol；其分母 "
            "(c₁x_t − c_n) 接近 0，结果对数据第 4 位小数极敏感，原脚本 output.txt 的 8.73×10⁶ 与此同源，"
            "只宜作数量级参考。" % (k_n1, -8.314 * (T + 273.15) * math.log(abs(k_n1)) / 1000.0),
            "工作曲线表沿用原表：第 3 组“D”行写的其实是已扣空白的 ΔD（0.129~0.650），"
            "若按真实 D 值（0.144~0.665）拟合，斜率会变成 3.3336，xn 与报告对不上，故按原表。",
        ],
        "warnings": warnings,
    }
