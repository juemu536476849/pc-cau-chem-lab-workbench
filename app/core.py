# -*- coding: utf-8 -*-
"""通用数值工具：拟合、插值、格式化。"""
import math


def num(v, default=None):
    """把单元格值转成 float，空/非法返回 default。"""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return default
        return float(v)
    s = str(v).strip().replace(",", "").replace("，", "")
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def column(rows, idx):
    """提取第 idx 列（0 基）数值，跳过空行。"""
    out = []
    for r in rows:
        if idx < len(r):
            v = num(r[idx])
            if v is not None:
                out.append(v)
    return out


def xy(rows, ix, iy):
    """提取两列组成 (x, y)，任一侧为空则跳过。"""
    xs, ys = [], []
    for r in rows:
        if ix < len(r) and iy < len(r):
            x, y = num(r[ix]), num(r[iy])
            if x is not None and y is not None:
                xs.append(x)
                ys.append(y)
    return xs, ys


def linfit(xs, ys):
    """最小二乘直线拟合，返回 dict(slope, intercept, r, r2, n, se)。"""
    n = len(xs)
    if n < 2:
        raise ValueError("线性拟合至少需要 2 个数据点")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        raise ValueError("x 值全部相同，无法拟合")
    k = sxy / sxx
    b = my - k * mx
    ss_res = sum((y - (k * x + b)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    r = math.copysign(math.sqrt(max(r2, 0.0)), k)
    se = math.sqrt(ss_res / (n - 2) / sxx) if n > 2 else float("nan")
    return {"slope": k, "intercept": b, "r": r, "r2": r2, "n": n, "se": se}


def fit_through_origin(xs, ys):
    """过原点最小二乘 y = k x。"""
    sxx = sum(x * x for x in xs)
    if sxx == 0:
        raise ValueError("x 值全为 0")
    k = sum(x * y for x, y in zip(xs, ys)) / sxx
    return k


def line_y(fit, x):
    return fit["slope"] * x + fit["intercept"]


def intersect(fit1, fit2):
    d = fit1["slope"] - fit2["slope"]
    if abs(d) < 1e-12:
        raise ValueError("两条直线平行，无交点")
    x = (fit2["intercept"] - fit1["intercept"]) / d
    return x, line_y(fit1, x)


def interp(x, xs, ys):
    """分段线性插值（xs 需单调递增）。"""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if xs[i] >= x:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return ys[-1]


def trapz(xs, ys):
    """梯形积分。"""
    return sum((ys[i] + ys[i + 1]) / 2 * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1))


def spline_points(xs, ys, n=240):
    """三次样条加密（scipy 可用时），失败回退线性插值。"""
    try:
        from scipy.interpolate import make_interp_spline
        import numpy as np
        x = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        order = np.argsort(x)
        x, y = x[order], y[order]
        k = min(3, len(x) - 1)
        sp = make_interp_spline(x, y, k=k)
        xx = np.linspace(x[0], x[-1], n)
        return xx.tolist(), sp(xx).tolist()
    except Exception:
        out_x, out_y = [], []
        for i in range(len(xs) - 1):
            for j in range(10):
                t = j / 10
                out_x.append(xs[i] + (xs[i + 1] - xs[i]) * t)
                out_y.append(ys[i] + (ys[i + 1] - ys[i]) * t)
        out_x.append(xs[-1])
        out_y.append(ys[-1])
        return out_x, out_y


def fmt(v, digits=4):
    """数值格式化：保留有效位、去掉多余 0。"""
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    try:
        if v == 0:
            return "0"
        if abs(v) >= 1e5 or abs(v) < 1e-3:
            return f"{v:.{digits}g}"
        return f"{v:.{digits}f}".rstrip("0").rstrip(".")
    except Exception:
        return str(v)


def fmt_sci(v, digits=3):
    if v is None:
        return "—"
    return f"{v:.{digits}e}"
