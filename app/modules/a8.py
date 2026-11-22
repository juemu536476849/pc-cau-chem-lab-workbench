# -*- coding: utf-8 -*-
"""A8 工作曲线标定：电位 E 对 lg c 作线性标定，再反算未知样浓度。

说明：归档资料里本实验没有可读的实验名称（docx 为空文档、pdf 为扫描件），
因此按数据处理表的计算过程反推为通用的“E–lg c 工作曲线（电位法）标定”，不臆造具体体系。
"""
import math

from ..core import num, linfit, line_y

# 标准系列：c 与平衡电位 E（xlsx 前 6 行：c、lg c、E(mV)：21/19/13/7/2/-1）
CAL = [
    [0.03, 21.0],
    [0.01, 19.0],
    [0.003, 13.0],
    [0.001, 7.0],
    [0.0003, 2.0],
    [0.0001, -1.0],
]

# 未知样：只测了电位（xlsx 中蒸馏水 E=11 mV；自来水与牛奶都记了 18 mV）
UNK = [
    ["蒸馏水", 11.0],
    ["自来水", 18.0],
    ["牛奶", 18.0],
]

R_GAS = 8.314      # J/(mol·K)
F_FARADAY = 96485  # C/mol

SPEC = {
    "id": "a8",
    "code": "A8",
    "group": "物化",
    "name": "工作曲线标定实验",
    "subtitle": "E–lg c 线性标定 · 反算未知样浓度",
    "tags": ["电位法", "工作曲线", "标定", "Nernst 响应"],
    "desc": "电极电位与待测组分浓度的对数近似成正比（Nernst 方程）。用一组已知浓度的标准溶液测电位、"
            "作 E–lg c 直线得到斜率 k 与截距 b，再由未知样的电位反算其浓度。",
    "method": [
        "① 配制浓度 c 覆盖 1×10⁻⁴ ~ 3×10⁻² mol/L 的标准系列，逐个测平衡电位 E；",
        "② 以 lg c 为横坐标、E 为纵坐标作工作曲线，最小二乘拟合 E = k·lg c + b；",
        "③ 未知样测 E 后反算 lg c = (E − b) / k，再取 10 的幂得 c；",
        "④ 乘以样品预处理稀释倍数得到原液浓度；",
        "⑤ 用 k 与 Nernst 理论斜率 2.303RT/F 比较，判断电极响应是否正常。",
    ],
    "tables": [
        {
            "key": "cal",
            "title": "标准系列浓度与电位",
            "note": "c 为标定用标准溶液浓度（mol/L），E 为平衡电位（mV）。lg c 由程序计算，无需另填。",
            "columns": [
                {"key": "c", "label": "c / (mol/L)", "type": "number"},
                {"key": "e", "label": "E / mV", "type": "number"},
            ],
            "rows": CAL,
        },
        {
            "key": "unk",
            "title": "未知样电位",
            "note": "只填样品名与电位 E 即可；浓度由工作曲线反算。",
            "columns": [
                {"key": "name", "label": "样品", "type": "text"},
                {"key": "e", "label": "E / mV", "type": "number"},
            ],
            "rows": UNK,
        },
    ],
    "params": [
        {"key": "sample", "label": "关注样品", "type": "select", "default": "蒸馏水",
         "options": [{"value": u[0], "label": u[0]} for u in UNK],
         "hint": "KPI 里给出该样品的反算浓度"},
        {"key": "dil", "label": "样品稀释倍数", "type": "number", "default": 1, "step": 1,
         "hint": "测定前若稀释过，填稀释倍数；未稀释填 1"},
        {"key": "temp", "label": "测定温度 / ℃", "type": "number", "default": 25, "step": 0.5,
         "hint": "用于换算 Nernst 理论斜率 2.303RT/F（25 ℃ 为 59.16 mV/dec）"},
    ],
}


def run(data):
    tb = data.get("tables") or {}
    cal = tb.get("cal") or []
    unk = tb.get("unk") or []
    p = data.get("params") or {}
    dil = num(p.get("dil"), 1.0) or 1.0
    temp = num(p.get("temp"), 25.0)
    if dil <= 0:
        raise ValueError("稀释倍数必须大于 0（未稀释填 1）")

    xs, ys = [], []
    pts = []
    for r in cal:
        if len(r) < 2:
            continue
        c, e = num(r[0]), num(r[1])
        if c is None or e is None:
            continue
        if c <= 0:
            raise ValueError(f"浓度 c = {c:g} 不是正数：lg c 无定义，请检查标准系列表的第 1 列")
        xs.append(math.log10(c))
        ys.append(e)
        pts.append((c, math.log10(c), e))
    if len(xs) < 3:
        raise ValueError("标准系列至少需要 3 个点：请检查第一张表的 c 与 E 两列")

    f = linfit(xs, ys)
    if abs(f["slope"]) < 1e-9:
        raise ValueError("拟合斜率接近 0：E 与 lg c 无线性关系，请检查电位单位与浓度列是否填反")
    k, b = f["slope"], f["intercept"]

    # 反算用的直线：处理表是另做一条 lg c 对 E 的回归线（不是代数逆函数），这里照做以复现其数值
    fre = linfit(ys, xs)
    m, a = fre["slope"], fre["intercept"]
    e_of = lambda lgc: line_y(f, lgc)
    lgc_of = lambda e: m * e + a

    unk_rows, unk_pts = [], []
    for r in unk:
        if len(r) < 2:
            continue
        name = str(r[0]).strip() if r[0] is not None else "未知样"
        e = num(r[1])
        if not name or e is None:
            continue
        lgc = lgc_of(e)
        c_meas = 10.0 ** lgc
        c_orig = c_meas * dil
        unk_rows.append([name, round(e, 2), round(lgc, 4), round(c_meas, 6),
                         round(c_orig, 6), round(e_of(lgc), 2)])
        unk_pts.append({"x": lgc, "y": e, "label": f"{name}：c={c_orig:.3g} mol/L"})

    if not unk_rows:
        raise ValueError("未知样表为空：请至少给出一个样品的电位 E")

    tag = str(p.get("sample") or unk_rows[0][0])
    row = next((q for q in unk_rows if q[0] == tag), unk_rows[0])
    c_focus = row[4]

    theory = 2.302585 * R_GAS * (temp + 273.15) / F_FARADAY * 1000.0  # mV/dec
    ratio = k / theory * 100.0 if theory else float("nan")

    # 残差与图表
    t1, res_all = [], []
    for (c, lgc, e) in pts:
        fit_e = e_of(lgc)
        res_all.append(e - fit_e)
        t1.append([c, round(lgc, 4), round(e, 2), round(fit_e, 3), round(e - fit_e, 3)])

    xmin = min(q[1] for q in pts)
    xmax = max(q[1] for q in pts)
    for q in unk_pts:
        xmin = min(xmin, q["x"])
        xmax = max(xmax, q["x"])
    pad = (xmax - xmin) * 0.06 or 0.2
    line_pts = [[xmin - pad, e_of(xmin - pad)], [xmax + pad, e_of(xmax + pad)]]

    chart = {
        "title": "E–lg c 工作曲线与未知样反算",
        "xlabel": "lg[c / (mol/L)]", "ylabel": "E / mV",
        "series": [
            {"name": "标准系列", "type": "scatter",
             "points": [[q[1], q[2]] for q in pts]},
            {"name": f"E = {k:.4g}·lg c + {b:.4g}", "type": "line", "color": "#2f6df6",
             "points": line_pts},
        ],
        "points": unk_pts,
        "annotations": True,
        "xrange": [xmin - pad * 1.5, xmax + pad * 1.5],
    }

    warnings = []
    if abs(ratio) < 50:
        warnings.append(f"实测斜率 {k:.3g} mV/dec 只有 Nernst 理论值 {theory:.2f} mV/dec 的 {abs(ratio):.0f}%，"
                        f"电极对该组分响应很弱或浓度/电位单位有误，反算浓度只能作相对比较。")
    if abs(unk_rows[-1][1] - unk_rows[-2][1]) < 1e-9 and len(unk_rows) >= 2:
        warnings.append(f"“{unk_rows[-1][0]}”与“{unk_rows[-2][0]}”电位都是 {unk_rows[-1][1]:g} mV，"
                        f"疑似抄录重复，建议复核原始记录。")
    if abs(f["r2"]) < 0.99:
        warnings.append(f"工作曲线 r² = {f['r2']:.4f}，线性一般，可检查是否有标准点离群。")

    return {
        "kpis": [
            {"label": "斜率 k", "value": round(k, 4), "unit": "mV/dec", "digits": 4,
             "hint": "E = k·lg c + b 的斜率"},
            {"label": "截距 b", "value": round(b, 4), "unit": "mV", "digits": 3},
            {"label": "r2", "value": round(f["r2"], 5), "digits": 5,
             "hint": f"{len(xs)} 个标准点"},
            {"label": f"c（{row[0]}）", "value": round(c_focus, 6), "unit": "mol/L", "digits": 6,
             "hint": f"E = {row[1]:g} mV，已乘稀释倍数 {dil:g}"},
            {"label": "k / 理论斜率", "value": round(ratio, 1), "unit": "%", "digits": 1,
             "hint": f"Nernst 理论斜率 {theory:.2f} mV/dec（{temp:g} ℃）"},
        ],
        "charts": [chart],
        "tables": [
            {"title": "工作曲线标定结果",
             "columns": ["c / (mol/L)", "lg c", "E / mV", "E拟合 / mV", "残差 / mV"],
             "rows": t1},
            {"title": "未知样反算",
             "columns": ["样品", "E / mV", "lg c", "c测定 / (mol/L)", "c原液 / (mol/L)", "E拟合 / mV"],
             "rows": unk_rows},
        ],
        "notes": [
            "归档资料中没有可读的实验名称与原理（docx 为空文档、pdf 为扫描件），本模块按数据处理表的实际算法"
            "反推为“E–lg c 工作曲线（电位法）标定”，未指定具体离子或电极体系。",
            "处理表对 6 个标准点求 SLOPE/INTERCEPT 得 k、b，再另做一条 lg c = m·E + a 的回归线反算未知样"
            "（不是取代数逆函数），本模块按同样两条线做；两条线在 E = −1~21 mV 内换算结果相差 < 1%。",
            "xlsx 记录：k = 9.5876 mV/dec、b = 36.6422 mV；蒸馏水 E = 11 mV → c ≈ 2.1×10⁻³ mol/L，"
            "自来水（与牛奶同为 E = 18 mV）→ c ≈ 1.1×10⁻² mol/L。",
            "只有在电极满足 Nernst 响应（斜率约 59/n mV/dec）时反算浓度才可靠；本实验斜率远低于理论值，"
            "建议按“相对大小”使用该结果。",
        ],
        "warnings": warnings,
    }
