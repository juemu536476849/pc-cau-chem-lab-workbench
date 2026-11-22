# -*- coding: utf-8 -*-
"""A1 积分溶解热的测定：双直线外推求温差 ΔT。"""
from ..core import xy, num, linfit, line_y

RAW = [
    [1, -0.019, -0.019, 0.001, 0.001],
    [2, -0.020, -0.020, 0.002, 0.002],
    [3, -0.021, -0.021, 0.002, 0.002],
    [4, -0.021, -0.021, 0.003, 0.003],
    [5, -0.022, -0.022, 0.004, 0.004],
    [6, -1.429, -1.429, -0.854, -0.854],
    [7, -1.029, -1.029, -1.246, -1.246],
    [8, -1.014, -1.014, -1.055, -1.055],
    [9, -1.000, -1.000, -1.040, -1.040],
    [10, -0.990, -0.990, -1.033, -1.033],
    [11, -0.982, -0.982, -1.028, -1.028],
    [12, -0.975, -0.975, -1.024, -1.024],
    [13, -0.970, -0.970, -1.020, -1.020],
    [14, -0.963, -0.963, -1.018, -1.018],
    [15, -0.960, -0.960, -1.017, -1.017],
]

SERIES = [
    {"value": "kno3_1", "label": "KNO₃ ①", "col": 1},
    {"value": "kno3_2", "label": "KNO₃ ②", "col": 2},
    {"value": "kcl_1", "label": "KCl ①", "col": 3},
    {"value": "kcl_2", "label": "KCl ②", "col": 4},
]

SPEC = {
    "id": "a1",
    "code": "A1",
    "group": "物化",
    "name": "积分溶解热的测定",
    "subtitle": "双直线外推 · 求溶解过程温差 ΔT",
    "tags": ["热化学", "量热", "双直线外推"],
    "desc": "记录盐溶解过程中的温度–时间曲线：溶解瞬间温度突变，随后体系缓慢趋近环境温度。"
            "对升温段与降温段分别作直线拟合，取两线在拐点中点处的纵坐标差即为真实温差 ΔT。",
    "method": [
        "① 选取升温段终点 t₁ 与降温段起点 t₂（即两个拐点）；",
        "② 分别对 [0, t₁] 与 [t₂, t_end] 区间做最小二乘直线拟合；",
        "③ 在 x = (t₁+t₂)/2 处取两条拟合直线的纵坐标差 ΔT = |y₂ − y₁|；",
        "④ ΔT 用于结合量热计热容换算积分溶解热 ΔH（本页只做数据前半段）。",
    ],
    "tables": [{
        "key": "raw",
        "title": "温度–时间原始数据",
        "note": "直接粘贴 Excel 两列以上即可；空白单元格自动跳过。原始记录为相对温度变化（K）。",
        "columns": [
            {"key": "t", "label": "t / min", "type": "number"},
            {"key": "k1", "label": "KNO₃ ①", "type": "number"},
            {"key": "k2", "label": "KNO₃ ②", "type": "number"},
            {"key": "c1", "label": "KCl ①", "type": "number"},
            {"key": "c2", "label": "KCl ②", "type": "number"},
        ],
        "rows": RAW,
    }],
    "params": [
        {"key": "g1", "label": "升温段终点 t₁", "type": "number", "default": 5,
         "step": 1, "hint": "温度开始突降前的最后一个点"},
        {"key": "g2", "label": "降温段起点 t₂", "type": "number", "default": 7,
         "step": 1, "hint": "温度突变后进入降温直线的第一个点"},
        {"key": "endp", "label": "末点 t_end", "type": "number", "default": 15,
         "step": 1, "hint": "参与第二段拟合的最后一个点"},
        {"key": "series", "label": "作图体系", "type": "select", "default": "kno3_1",
         "options": [{"value": s["value"], "label": s["label"]} for s in SERIES]},
    ],
}


def run(data):
    rows = (data.get("tables") or {}).get("raw") or []
    p = data.get("params") or {}
    g1 = num(p.get("g1"), 5)
    g2 = num(p.get("g2"), 8)
    endp = num(p.get("endp"), 15)
    if g2 <= g1:
        raise ValueError("降温段起点 t₂ 必须大于升温段终点 t₁")

    results = {}
    for s in SERIES:
        xs, ys = xy(rows, 0, s["col"])
        if len(xs) < 3:
            continue
        seg1 = [(x, y) for x, y in zip(xs, ys) if x <= g1]
        seg2 = [(x, y) for x, y in zip(xs, ys) if g2 <= x <= endp]
        if len(seg1) < 2 or len(seg2) < 2:
            continue
        f1 = linfit([a for a, _ in seg1], [b for _, b in seg1])
        f2 = linfit([a for a, _ in seg2], [b for _, b in seg2])
        mid = (g1 + g2) / 2
        y1, y2 = line_y(f1, mid), line_y(f2, mid)
        results[s["value"]] = {"fit1": f1, "fit2": f2, "mid": mid, "y1": y1, "y2": y2,
                               "dT": abs(y2 - y1), "xs": xs, "ys": ys, "meta": s}

    if not results:
        raise ValueError("数据不足：请检查时间列与温度列，并让两个拐点之间留出数据段")

    sel = p.get("series") or "kno3_1"
    if sel not in results:
        sel = next(iter(results))
    r = results[sel]

    # ---------------- 图 ----------------
    f1, f2, mid = r["fit1"], r["fit2"], r["mid"]
    xmin = min(r["xs"])
    xmax = max(r["xs"])
    y_lo = line_y(f1, mid)
    y_hi = line_y(f2, mid)
    series = [
        {"name": "实验点", "type": "scatter", "points": [[x, y] for x, y in zip(r["xs"], r["ys"])]},
        {"name": "第一段拟合", "type": "line", "color": "#e5533d",
         "points": [[xmin, line_y(f1, xmin)], [g1, line_y(f1, g1)]]},
        {"name": "第二段拟合", "type": "line", "color": "#2f6df6",
         "points": [[g2, line_y(f2, g2)], [xmax, line_y(f2, xmax)]]},
        {"name": "第一段外推", "type": "line", "dash": True, "color": "#e5533d",
         "points": [[g1, line_y(f1, g1)], [mid, line_y(f1, mid)]]},
        {"name": "第二段外推", "type": "line", "dash": True, "color": "#2f6df6",
         "points": [[mid, line_y(f2, mid)], [g2, line_y(f2, g2)]]},
    ]
    chart = {
        "title": f"{r['meta']['label']} · 双直线外推",
        "xlabel": "t / min", "ylabel": "温度变化 / K",
        "series": series,
        "vlines": [{"x": mid, "label": f"中点 t={mid:g}"}],
        "points": [{"x": mid, "y": (y_lo + y_hi) / 2, "label": f"ΔT = {abs(y_hi - y_lo):.4f} K"}],
        "annotations": True,
        "xrange": [xmin - 0.3, xmax + 0.3],
    }

    table_rows = []
    for s in SERIES:
        if s["value"] not in results:
            continue
        q = results[s["value"]]
        table_rows.append([s["label"],
                           round(q["fit1"]["slope"], 5), round(q["fit1"]["intercept"], 5),
                           round(q["fit1"]["r"], 4),
                           round(q["fit2"]["slope"], 5), round(q["fit2"]["intercept"], 5),
                           round(q["fit2"]["r"], 4), round(q["dT"], 4)])

    warnings = []
    if abs(r["fit2"]["r"]) < 0.98:
        warnings.append(f"第二段拟合 r = {r['fit2']['r']:.2f}，直线性一般，可微调 t₂ / t_end 后重算")
    _ref = {"kno3_1": 7, "kno3_2": 7, "kcl_1": 8, "kcl_2": 8}
    _want = _ref.get(sel)
    if _want is not None and abs(g2 - _want) > 1e-9:
        warnings.append(f"这一组报告用的是 t₂ = {_want}（当前 {g2:g}），所以 ΔT 会和报告值不一致；把 t₂ 改成 {_want} 即可对上")
    if abs(r["dT"]) < 1e-6:
        warnings.append("ΔT 接近 0，请确认拐点位置是否正确")

    return {
        "kpis": [
            {"label": "ΔT", "value": round(r["dT"], 4), "unit": "K", "digits": 4,
             "hint": f"{r['meta']['label']} · 中点 t={mid:g}"},
            {"label": "第一段斜率", "value": round(f1["slope"], 5), "unit": "K/min", "digits": 5},
            {"label": "第二段斜率", "value": round(f2["slope"], 5), "unit": "K/min", "digits": 5},
            {"label": "第二段 r", "value": round(f2["r"], 4), "digits": 4},
        ],
        "charts": [chart],
        "tables": [{
            "title": "四种体系的拟合结果",
            "columns": ["体系", "k₁", "b₁", "r₁", "k₂", "b₂", "r₂", "ΔT / K"],
            "rows": table_rows,
        }],
        "notes": [
            f"ΔT 取两条拟合直线在 x = ({g1:g}+{g2:g})/2 = {mid:g} min 处的纵坐标差的绝对值。",
            "原始记录为相对温度变化，若换成绝对温度（K），ΔT 不变。",
            "与实验报告对照：KNO₃ 组（t₂=7）复算 ΔT = 1.0063 K，KCl 组（t₂=8）复算 ΔT = 1.0592 K，与报告 output.xlsx 一致。",
            "积分溶解热 ΔH = −(C_量热计 · ΔT) / n，需另用量热计标定常数；本模块只给到 ΔT。",
        ],
        "warnings": warnings,
    }
