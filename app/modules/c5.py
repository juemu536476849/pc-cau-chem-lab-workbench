# -*- coding: utf-8 -*-
"""C5 筛板精馏实验：折光率–组成标定平面 + McCabe-Thiele 图解法。

数据来源（data/化工实验/05-筛板精馏实验/）：
- 原始数据/全回流图.xlsx：乙醇–正丙醇常压平衡线 11 点（x 液相、y 气相，摩尔分率，含泡点温度）。
- 原始数据/回归插值原始数据.xlsx：25/30/35 ℃ 下折光率 n_D 与乙醇质量分数 W_A 的标定表。
- 原始数据/实验5数据处理.xlsx：五个取样点折光率、平面方程、A–E 各点与两段操作线系数。
"""
from __future__ import annotations

import math

from ..core import interp, num, spline_points, xy

M_ETHANOL = 46.0       # g/mol
M_PROPANOL = 60.0      # g/mol
T_CAL = (25.0, 30.0, 35.0)

# t / ℃, x 液相摩尔分率, y 气相摩尔分率（全回流图.xlsx 前两行，按泡点温度配对）
EQ_ROWS = [
    [97.60, 0.000, 0.000],
    [93.85, 0.126, 0.240],
    [92.66, 0.188, 0.318],
    [91.60, 0.210, 0.349],
    [88.32, 0.358, 0.550],
    [86.25, 0.461, 0.650],
    [84.98, 0.546, 0.711],
    [84.13, 0.600, 0.760],
    [83.06, 0.663, 0.799],
    [80.50, 0.884, 0.914],
    [78.38, 1.000, 1.000],
]

# W_A 质量分数, n(25 ℃), n(30 ℃), n(35 ℃)（回归插值原始数据.xlsx B1:P4）
CAL_ROWS = [
    [0.0000, 1.3827, 1.3809, 1.3790],
    [0.05052, 1.3815, 1.3796, 1.3775],
    [0.09985, 1.3797, 1.3784, 1.3762],
    [0.1974, 1.3770, 1.3759, 1.3740],
    [0.2950, 1.3750, 1.3755, 1.3719],
    [0.3977, 1.3730, 1.3712, 1.3692],
    [0.4970, 1.3705, 1.3690, 1.3670],
    [0.5990, 1.3680, 1.3668, 1.3650],
    [0.6445, 1.3607, 1.3657, 1.3634],
    [0.7101, 1.3658, 1.3640, 1.3620],
    [0.7983, 1.3640, 1.3620, 1.3600],
    [0.8442, 1.3628, 1.3607, 1.3590],
    [0.9064, 1.3618, 1.3593, 1.3573],
    [0.9509, 1.3606, 1.3584, 1.3653],
    [1.0000, 1.3589, 1.3574, 1.3551],
]

# 取样点：名称, 折光率测定温度/℃, 折光率, 报告摩尔分率（实验5实验报告 表9/表10，仅作对照）
SAMPLES = [
    ("全回流 · 塔顶馏出液", 29.9, 1.3611, 0.8765),
    ("全回流 · 塔底釜液", 29.9, 1.3775, 0.1583),
    ("部分回流 · 塔顶馏出液", 29.0, 1.3688, 0.5835),
    ("部分回流 · 塔底釜液", 29.0, 1.3785, 0.1176),
    ("部分回流 · 进料液", 29.0, 1.3756, 0.2687),
]

MODE_OPTIONS = [
    {"value": "total", "label": "全回流"},
    {"value": "partial", "label": "部分回流"},
]

SPEC = {
    "id": "c5",
    "code": "C5",
    "group": "化工",
    "name": "筛板精馏实验",
    "subtitle": "折光率–组成标定平面 + 全/部分回流 McCabe-Thiele 图解法",
    "tags": ["精馏", "McCabe-Thiele", "折光率标定", "图解法"],
    "desc": "先用 25/30/35 ℃ 的折光率–质量分数数据最小二乘拟合标定平面，把塔顶、塔底与进料"
            "取样点的折光率反算成摩尔分率；再在以摩尔分率表示的乙醇–正丙醇平衡线上，按全回流"
            "（y = x）或部分回流（精馏段 + 提馏段 + q 线）逐级作阶梯，得到理论板数、总板效率与回流比。",
    "method": [
        "① 由 45 个标定点拟合 n = a·W_A + b·t + c，反算 W_A = (n − b·t − c)/a；",
        "② 质量分数按 M_乙醇 = 46、M_正丙醇 = 60 换算摩尔分率 x；",
        "③ 11 点平衡线（x, y）三次样条平滑，作为图解法基准曲线；",
        "④ 自 (x_D, x_D) 起水平交平衡线、垂直交操作线，逐级作阶梯至 x ≤ x_W；",
        "⑤ 末级按跨越 x_W 的比例折算，取整得理论板数，总板效率 = 理论板数 / 实际板数。",
    ],
    "tables": [
        {
            "key": "eq",
            "title": "乙醇–正丙醇平衡线数据",
            "note": "来自 全回流图.xlsx 前两行（11 点，x 液相组成、y 气相组成，摩尔分率）；"
                    "温度列为对应泡点，不参与计算。可直接修改任意点，曲线按三次样条重新平滑。",
            "columns": [
                {"key": "t", "label": "泡点 t / ℃", "type": "number"},
                {"key": "x", "label": "液相组成 x", "type": "number"},
                {"key": "y", "label": "气相组成 y", "type": "number"},
            ],
            "rows": EQ_ROWS,
        },
        {
            "key": "cal",
            "title": "折光率–组成标定原始数据",
            "note": "来自 回归插值原始数据.xlsx（B1:P1 质量分数、A2:A4 温度 25/30/35 ℃、B2:P4 折光率）；"
                    "三列温度固定为 25/30/35 ℃，缺测单元格留空即可。",
            "columns": [
                {"key": "w", "label": "W_A 质量分数", "type": "number"},
                {"key": "n25", "label": "n_D (25 ℃)", "type": "number"},
                {"key": "n30", "label": "n_D (30 ℃)", "type": "number"},
                {"key": "n35", "label": "n_D (35 ℃)", "type": "number"},
            ],
            "rows": CAL_ROWS,
        },
    ],
    "params": [
        {"key": "mode", "label": "回流方式", "type": "select", "default": "total",
         "options": MODE_OPTIONS},
        {"key": "R", "label": "回流比 R", "type": "number", "default": 4,
         "step": 0.1, "hint": "仅部分回流使用；全回流 R → ∞，操作线 y = x"},
        {"key": "xD", "label": "塔顶组成 x_D", "type": "number", "default": 0.8765,
         "step": 0.0001, "hint": "全回流 0.8765；部分回流 0.5835（摩尔分率）"},
        {"key": "xW", "label": "塔底组成 x_W", "type": "number", "default": 0.1583,
         "step": 0.0001, "hint": "全回流 0.1583；部分回流 0.1176"},
        {"key": "xF", "label": "进料组成 x_F", "type": "number", "default": 0.2687,
         "step": 0.0001, "hint": "仅部分回流使用；实验值 0.2687"},
        {"key": "q", "label": "进料热状态 q", "type": "number", "default": 1.25225,
         "step": 0.001, "hint": "仅部分回流使用；冷液进料 q > 1，实验值 1.2523"},
        {"key": "plates", "label": "实际板数 N_实", "type": "number", "default": 7,
         "step": 1, "hint": "筛板塔实际板数，用于总板效率；实验塔为 7 块"},
    ],
}


def _solve3(mat, vec):
    """3×3 线性方程组（列主元高斯消元）。"""
    a = [list(mat[i]) + [vec[i]] for i in range(3)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-12:
            raise ValueError("折光标定数据退化（质量分数或温度没有变化），无法解出平面方程")
        a[col], a[piv] = a[piv], a[col]
        p = a[col][col]
        for j in range(col, 4):
            a[col][j] /= p
        for r in range(3):
            if r != col and a[r][col] != 0.0:
                f = a[r][col]
                for j in range(col, 4):
                    a[r][j] -= f * a[col][j]
    return a[0][3], a[1][3], a[2][3]


def _fit_plane(pts):
    """最小二乘拟合 n = a·W_A + b·t + c，pts = [(W, t, n)]。"""
    cnt = len(pts)
    sw = sum(w for w, _, _ in pts)
    st = sum(t for _, t, _ in pts)
    sv = sum(v for _, _, v in pts)
    sww = sum(w * w for w, _, _ in pts)
    stt = sum(t * t for _, t, _ in pts)
    swt = sum(w * t for w, t, _ in pts)
    swv = sum(w * v for w, _, v in pts)
    stv = sum(t * v for _, t, v in pts)
    a, b, c = _solve3([[sww, swt, sw], [swt, stt, st], [sw, st, cnt]], [swv, stv, sv])
    ss_res = sum((v - (a * w + b * t + c)) ** 2 for w, t, v in pts)
    mean = sv / cnt
    ss_tot = sum((v - mean) ** 2 for _, _, v in pts)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-18 else 1.0
    return {"a": a, "b": b, "c": c, "r2": r2, "rmse": (ss_res / cnt) ** 0.5, "n": cnt}


def _curve(xs, ys):
    """平衡线三次样条加密，并按 x 单调方向把 y 整理成不减序列以便反查。"""
    if len(xs) < 5:
        raise ValueError("平衡线至少需要 5 个数据点")
    for x, y in zip(xs, ys):
        if not (0.0 <= x <= 1.0) or not (0.0 <= y <= 1.0):
            raise ValueError("平衡线的液相/气相组成都应在 0~1 之间，请检查数据表")
    pairs = sorted(zip(xs, ys))
    for i in range(1, len(pairs)):
        if pairs[i][0] - pairs[i - 1][0] < 1e-9:
            raise ValueError("平衡线存在重复的液相组成 x，无法作样条插值")
    px = [p[0] for p in pairs]
    py = [p[1] for p in pairs]
    sx, sy = spline_points(px, py, 600)
    if sx[0] > 1e-6 or sx[-1] < 1.0 - 1e-6:
        raise ValueError("平衡线数据未覆盖液相组成 0~1（两端需有点），无法完成图解法")
    drop = 0.0
    mono = [sy[0]]
    for v in sy[1:]:
        if v < mono[-1]:
            drop = max(drop, mono[-1] - v)
        mono.append(max(mono[-1], v))
    if drop > 0.02:
        raise ValueError("平衡线在液相组成方向上不单调（y 随 x 下降），阶梯法无法求解，请检查数据")
    return sx, mono, drop


def _x_at(y, sx, sy):
    """平衡线上由气相组成反查液相组成。"""
    if y <= sy[0]:
        return sx[0]
    if y >= sy[-1]:
        return sx[-1]
    lo, hi = 0, len(sy) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if sy[mid] <= y:
            lo = mid
        else:
            hi = mid
    y0, y1 = sy[lo], sy[hi]
    if y1 - y0 < 1e-15:
        return sx[hi]
    return sx[lo] + (y - y0) * (sx[hi] - sx[lo]) / (y1 - y0)


def _staircase(xD, xW, sx, sy, op):
    """McCabe-Thiele 逐级作阶梯，返回级列表与折算后的阶梯数。"""
    if xD >= sy[-1] - 1e-9:
        raise ValueError("塔顶组成 x_D 不低于平衡线最高气相组成，无法作阶梯")
    steps = []
    x, y = xD, xD
    for i in range(1, 121):
        xe = _x_at(y, sx, sy)
        yn = op(xe)
        if i > 1 and yn >= y - 1e-12:
            raise ValueError("阶梯不再前进：操作线已与平衡线相交（夹点），请提高回流比 R 或调整进料状态")
        steps.append({"n": i, "x": x, "y": y, "xe": xe, "yn": yn})
        if xe <= xW + 1e-12:
            break
        x, y = xe, yn
    else:
        raise ValueError("阶梯超过 120 级仍未达到塔底组成，请检查 x_D、x_W 与操作线参数")

    last = steps[-1]
    span = last["x"] - last["xe"]
    frac = 1.0 if span <= 1e-12 else min(max((last["x"] - xW) / span, 0.0), 1.0)
    stages = (len(steps) - 1) + frac
    return steps, stages, frac


def run(data):
    data = data or {}
    tab = data.get("tables") or {}
    p = data.get("params") or {}

    # ---------------- 参数 ----------------
    mode = str(p.get("mode") or "total").strip()
    if mode not in ("total", "partial"):
        raise ValueError("回流方式只能是 全回流（total）或 部分回流（partial）")
    R = num(p.get("R"), 4.0)
    xD = num(p.get("xD"), 0.8765)
    xW = num(p.get("xW"), 0.1583)
    xF = num(p.get("xF"), 0.2687)
    qv = num(p.get("q"), 1.25225)
    plates = num(p.get("plates"), 7.0)

    for name, val in (("塔顶组成 x_D", xD), ("塔底组成 x_W", xW), ("进料组成 x_F", xF)):
        if not (0.0 < val < 1.0):
            raise ValueError(f"{name} 应在 0~1 之间（摩尔分率）")
    if xD <= xW:
        raise ValueError("塔顶组成 x_D 必须大于塔底组成 x_W")
    if plates is None or plates < 1:
        raise ValueError("实际板数必须是不小于 1 的整数")
    n_act = int(round(plates))

    # ---------------- 平衡线 ----------------
    eq_rows = tab.get("eq") or EQ_ROWS
    exs, eys = xy(eq_rows, 1, 2)
    if len(exs) < 5:
        raise ValueError("平衡线数据不足 5 点，请检查数据表")
    sx, sy, drop = _curve(exs, eys)
    warnings = []
    if drop > 1e-6:
        warnings.append(f"平衡线样条出现 {drop:.4f} 的轻微回落，已按单调曲线处理（原始点不变）")

    # ---------------- 折光标定 ----------------
    cal_rows = tab.get("cal") or CAL_ROWS
    pts = []
    for r in cal_rows:
        if not r:
            continue
        w = num(r[0])
        if w is None:
            continue
        if not (0.0 <= w <= 1.0):
            raise ValueError("折光标定表的质量分数 W_A 应在 0~1 之间")
        for j, t in enumerate(T_CAL):
            if len(r) <= j + 1:
                continue
            v = num(r[j + 1])
            if v is not None:
                pts.append((w, t, v))
    if len(pts) < 6:
        raise ValueError("折光标定数据不足 6 个有效点，请检查标定表")
    fit = _fit_plane(pts)
    a, b, c, r2 = fit["a"], fit["b"], fit["c"], fit["r2"]
    if a >= -1e-9:
        raise ValueError("折光率随质量分数没有下降趋势（拟合系数 a ≥ 0），无法反算组成，请检查标定表")

    for w, t, v in pts:
        res = v - (a * w + b * t + c)
        if abs(res) > 2.5 * fit["rmse"]:
            warnings.append(
                f"标定点 W_A={w:.4f}、t={t:.0f} ℃ 的折光率 {v:.4f} 偏离拟合平面 {res:+.4f}"
                f"（原始记录，已保留，R² 因此偏低）")

    # ---------------- 操作线 ----------------
    rect = qline = D = None
    xd_int = k_strip = b_strip = None
    if mode == "partial":
        if R <= 0:
            raise ValueError("回流比 R 必须大于 0；全回流请把回流方式切到“全回流”")
        if qv <= 1:
            raise ValueError("q 值必须大于 1（冷液/泡点进料），否则 q 线无法用于图解法")
        if not (xW < xF < xD):
            raise ValueError("进料组成 x_F 应介于塔底组成 x_W 与塔顶组成 x_D 之间")
        rect = {"slope": R / (R + 1.0), "intercept": xD / (R + 1.0)}
        qline = {"slope": qv / (qv - 1.0), "intercept": -xF / (qv - 1.0)}
        if abs(rect["slope"] - qline["slope"]) < 1e-9:
            raise ValueError("精馏段操作线与 q 线平行（R 与 q 取值异常），无交点")
        xd_int = (qline["intercept"] - rect["intercept"]) / (rect["slope"] - qline["slope"])
        yd_int = rect["slope"] * xd_int + rect["intercept"]
        if not (xW < xd_int < xD):
            raise ValueError(
                f"两操作线交点 D 的 x={xd_int:.4f} 不在 x_W~x_D 之间，请检查 R、q 与 x_F")
        k_strip = (yd_int - xW) / (xd_int - xW)
        b_strip = xW - k_strip * xW
        D = (xd_int, yd_int)
        if yd_int >= interp(xd_int, sx, sy) - 1e-9:
            raise ValueError("两操作线交点 D 落在平衡线之上（夹点），请提高回流比 R")

        def op(x, _r=rect, _ks=k_strip, _bs=b_strip, _xi=xd_int):
            if x >= _xi:
                return _r["slope"] * x + _r["intercept"]
            return _ks * x + _bs
    else:
        if xD < 0.7:
            warnings.append("全回流实验塔顶组成约 0.8765，当前 x_D 偏小；若在复算部分回流，"
                            "请把回流方式切到“部分回流”")

        def op(x):
            return x

    if mode == "partial" and xD > 0.8:
        warnings.append("部分回流实验塔顶组成约 0.5835，当前 x_D 偏大；若在复算全回流，"
                        "请把回流方式切到“全回流”")

    # ---------------- 阶梯 ----------------
    steps, stages, frac = _staircase(xD, xW, sx, sy, op)
    n_theo = int(round(stages))
    if n_theo < 1:
        raise ValueError("计算得到的理论板数小于 1 块，请检查 x_D、x_W 与操作线参数")
    eta = 100.0 * n_theo / n_act
    if eta > 100.0:
        warnings.append(f"实际板数 {n_act} 少于理论板数 {n_theo}，总板效率超过 100%，请核对实际板数")

    # ---------------- 取样点组成反算 ----------------
    comp_rows = []
    for name, t, n, rep in SAMPLES:
        w = (n - b * t - c) / a
        if not (0.0 <= w <= 1.0):
            warnings.append(f"{name} 折光率 {n:.4f} 反算 W_A={w:.4f} 超出 0~1，已截断，"
                            "请检查标定表温度与折光率是否匹配")
            w = min(max(w, 0.0), 1.0)
        xm = (w / M_ETHANOL) / (w / M_ETHANOL + (1.0 - w) / M_PROPANOL)
        comp_rows.append([name, t, n, round(w, 4), round(xm, 4), rep])

    # ---------------- 图 1：McCabe-Thiele ----------------
    def rp(v):
        return round(v, 4)

    curve_pts = [[max(0.0, min(1.0, rp(x))), max(0.0, min(1.0, rp(y)))] for x, y in zip(sx, sy)]
    step_pts = [[rp(xD), rp(xD)]]
    for st in steps:
        step_pts.append([rp(st["xe"]), rp(st["y"])])
        step_pts.append([rp(st["xe"]), rp(st["yn"])])

    series = [
        {"name": "平衡线 y*–x", "type": "line", "color": "#d64541", "width": 2.2,
         "points": curve_pts},
    ]
    vlines = [{"x": rp(xD), "label": f"x_D={xD:.4f}"}, {"x": rp(xW), "label": f"x_W={xW:.4f}"}]
    marks = []
    if mode == "total":
        series.append({"name": "操作线 y = x", "type": "line", "color": "#2f6df6", "width": 2.0,
                       "points": [[0.0, 0.0], [1.0, 1.0]]})
        title = f"全回流 McCabe-Thiele 图解法（阶梯 {stages:.2f} → {n_theo} 块理论板）"
    else:
        series.append({"name": "精馏段操作线", "type": "line", "color": "#1f9d6b", "width": 2.0,
                       "points": [[0.0, rp(rect["intercept"])], [rp(xD), rp(xD)]]})
        series.append({"name": "提馏段操作线", "type": "line", "color": "#a03bb0", "width": 2.0,
                       "points": [[rp(xW), rp(xW)], [rp(D[0]), rp(D[1])]]})
        series.append({"name": "q 线", "type": "line", "color": "#12a594", "width": 1.6, "dash": True,
                       "points": [[rp(xF), rp(xF)], [rp(D[0]), rp(D[1])]]})
        vlines.append({"x": rp(xF), "label": f"x_F={xF:.4f}"})
        marks = [
            {"x": rp(xD), "y": rp(xD), "label": "A"},
            {"x": 0.0, "y": rp(rect["intercept"]), "label": "B"},
            {"x": rp(xW), "y": rp(xW), "label": "C"},
            {"x": rp(D[0]), "y": rp(D[1]), "label": "D"},
            {"x": rp(xF), "y": rp(xF), "label": "E"},
        ]
        title = (f"部分回流 McCabe-Thiele 图解法（R={R:.2f}，阶梯 {stages:.2f} → "
                 f"{n_theo} 块理论板）")
    series.append({"name": "图解法阶梯", "type": "line", "color": "#333333", "width": 1.4,
                   "points": step_pts})
    series.append({"name": "平衡线数据点", "type": "scatter", "color": "#d64541", "r": 4,
                   "points": [[rp(x), rp(y)] for x, y in zip(exs, eys)]})

    mccabe = {
        "title": title,
        "xlabel": "液相组成 x（乙醇摩尔分率）",
        "ylabel": "气相组成 y（乙醇摩尔分率）",
        "series": series,
        "vlines": vlines,
        "points": marks,
        "xrange": [0.0, 1.0],
        "yrange": [0.0, 1.0],
    }

    # ---------------- 图 2：折光标定 ----------------
    colors = ("#2f6df6", "#e5533d", "#12967a")
    cal_series = []
    for j, t in enumerate(T_CAL):
        pts_t = [[rp(w), rp(v)] for (w, tt, v) in pts if tt == t]
        cal_series.append({"name": f"{t:.0f} ℃ 实测", "type": "scatter", "color": colors[j],
                           "r": 3, "points": pts_t})
    for j, t in enumerate(T_CAL):
        cal_series.append({"name": f"{t:.0f} ℃ 拟合", "type": "line", "color": colors[j],
                           "width": 1.8, "dash": True,
                           "points": [[0.0, rp(b * t + c)], [1.0, rp(a + b * t + c)]]})
    ns = [v for _, _, v in pts]
    y_lo = math.floor((min(ns) - 0.004) * 100.0) / 100.0
    y_hi = math.ceil((max(ns) + 0.004) * 100.0) / 100.0
    if y_hi - y_lo < 0.03:
        y_hi = y_lo + 0.03
    eqn = "n = {:.6f}·W_A {} {:.6f}·t + {:.6f}".format(
        a, "+" if b >= 0 else "−", abs(b), c)
    cal_chart = {
        "title": f"折光率–组成标定（{eqn}，R²={r2:.4f}）",
        "xlabel": "乙醇质量分数 W_A",
        "ylabel": "折光率 n_D",
        "series": cal_series,
        "xrange": [0.0, 1.0],
        "yrange": [y_lo, y_hi],
    }

    # ---------------- 输出表 ----------------
    stage_rows = []
    total_steps = len(steps)
    for st in steps:
        if mode == "total":
            tag = "全回流"
        elif st["x"] >= xd_int > st["xe"]:
            tag = "进料级"
        elif st["x"] >= xd_int:
            tag = "精馏段"
        else:
            tag = "提馏段"
        if st["n"] == total_steps:
            tag += "（末级）"
        stage_rows.append([st["n"], rp(st["x"]), rp(st["y"]), rp(st["xe"]), rp(st["yn"]), tag])

    chk_rows = []
    for t in T_CAL:
        vt = [v for (w, tt, v) in pts if tt == t]
        wt = [w for (w, tt, v) in pts if tt == t]
        if len(vt) < 2:
            continue
        res = [v - (a * w + b * t + c) for w, v in zip(wt, vt)]
        mean = sum(vt) / len(vt)
        ss_res = sum(r * r for r in res)
        ss_tot = sum((v - mean) ** 2 for v in vt)
        rr2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-18 else 1.0
        mae = sum(abs(r) for r in res) / len(res)
        chk_rows.append([t, round(a, 6), round(b * t + c, 6), round(rr2, 4), round(mae, 5)])

    kpis = [
        {"label": "理论板数", "value": n_theo, "unit": "块", "digits": 0,
         "hint": f"图解法阶梯 {stages:.2f} 级（末级折算 {frac:.3f}），取整得 {n_theo} 块"},
        {"label": "总板效率", "value": round(eta, 1), "unit": "%", "digits": 1,
         "hint": f"理论板数 {n_theo} / 实际板数 {n_act}"},
        {"label": "实际板数", "value": n_act, "unit": "块", "digits": 0,
         "hint": "筛板塔实际板数（可在参数中修改）"},
        {"label": "回流比 R", "value": (round(R, 2) if mode == "partial" else "∞"),
         "unit": "", "digits": 2,
         "hint": ("精馏段操作线斜率 = R/(R+1)" if mode == "partial"
                  else "全回流 R → ∞，操作线 y = x")},
        {"label": "标定系数 a", "value": round(a, 6), "unit": "", "digits": 6,
         "hint": "n = a·W_A + b·t + c 中 W_A 的系数"},
        {"label": "标定系数 b", "value": round(b, 6), "unit": "1/℃", "digits": 6,
         "hint": "温度 t 的系数"},
        {"label": "拟合 R²", "value": round(r2, 4), "unit": "", "digits": 4,
         "hint": f"{fit['n']} 个标定点对平面的决定系数，RMSE={fit['rmse']:.2e}"},
    ]

    notes = [
        "平衡线为乙醇–正丙醇常压 11 点数据（x 液相、y 气相，摩尔分率），用三次样条（k=3）平滑后"
        "作为图解法基准，原始点在校核图中以散点给出。",
        "全回流操作线 y = x；部分回流精馏段 y = R/(R+1)·x + x_D/(R+1)，"
        "q 线 y = q/(q−1)·x − x_F/(q−1)（本实验 q=1.2523 > 1，冷液进料），"
        "提馏段过 (x_W, x_W) 与两操作线交点 D。",
        "阶梯自 (x_D, x_D) 起：水平交平衡线得 x*，垂直交当时适用的操作线得下一级 y；"
        "末级按 (x_前 − x_W)/(x_前 − x*) 折算，阶梯数四舍五入即理论板数，"
        "总板效率 = 理论板数 / 实际板数。",
        "报告图解法结果：全回流 x_D=0.8765、x_W=0.1583，N=5，总板效率 71.4%；"
        "部分回流 x_D=0.5835、x_W=0.1176、x_F=0.2687，N=4，总板效率 57.1%；"
        "平面拟合 R²=0.9567。",
        "折光标定：W_A = (n − b·t − c)/a，摩尔分率 x = (W_A/46)/(W_A/46 + (1−W_A)/60)，"
        "M_乙醇 = 46 g/mol、M_正丙醇 = 60 g/mol。",
        "原始标定表在 W_A=0.6445（25 ℃ 为 1.3607）与 W_A=0.9509（35 ℃ 为 1.3653）处各有一个"
        "偏离点，按原始记录保留，R² 主要由这两点拉低。",
    ]

    return {
        "kpis": kpis,
        "charts": [mccabe, cal_chart],
        "tables": [
            {"title": f"McCabe-Thiele 阶梯（{stages:.2f} 级 → {n_theo} 块）",
             "columns": ["级序", "起点 x", "起点 y", "平衡线 x*", "下一级 y", "所属"],
             "rows": stage_rows},
            {"title": "取样点折光率–组成反算",
             "columns": ["样品", "测定温度/℃", "折光率 n", "质量分数 W_A", "摩尔分率 x", "报告值 x"],
             "rows": comp_rows},
            {"title": "折光标定分温度校验",
             "columns": ["温度/℃", "斜率 a", "截距 b·t+c", "r²（对拟合平面）", "平均绝对残差"],
             "rows": chk_rows},
        ],
        "notes": notes,
        "warnings": warnings,
    }

# 计算用到的公式（LaTeX 子集；前端与 Word 报告都会渲染成真正的公式）
SPEC["formulas"] = [
    r"y = \frac{R}{R+1}x + \frac{x_{D}}{R+1}",
    r"x_{A} = \frac{W_{A}/46}{W_{A}/46 + (1-W_{A})/60}",
]
