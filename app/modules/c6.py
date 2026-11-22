# -*- coding: utf-8 -*-
"""C6 填料吸收实验：干/湿填料层 ΔP/Z–u 双对数曲线与泛点气速估算。

数据取自实验报告表 6（干填料层）与表 8（水淋量 25 L/h），
即工作簿 Sheet3 (2) 的复算结果；表中 ΔP、ΔP/Z、u 均按报告值录入。
"""
import math

from ..core import num, linfit, intersect

# 列：V(m³/h)、Δh(cm)、t(℃)、ΔP(Pa)、ΔP/Z(Pa/m)、u(m/s)
WET = [
    [2.5, 0.33, 53.2, 31.85, 79.63, 0.1662],
    [5.0, 0.89, "—", 85.90, 214.8, 0.3324],
    [7.5, 1.92, "—", 185.3, 463.3, 0.4986],
    [10.0, 3.56, "—", 343.6, 859.0, 0.6648],
    [12.5, 5.98, "—", 577.2, 1443.0, 0.8311],
    [15.0, 9.96, "—", 961.3, 2403.4, 0.9973],
    [17.5, 15.25, 56.0, 1471.9, 3679.9, 1.1635],
]

DRY = [
    [2.5, 0.26, 35.7, 25.24, 63.10, 0.1626],
    [5.0, 0.71, "—", 68.92, 172.30, 0.3252],
    [7.5, 1.38, "—", 134.0, 334.9, 0.4879],
    [10.0, 2.43, "—", 235.9, 589.7, 0.6505],
    [12.5, 3.62, "—", 351.4, 878.5, 0.8131],
    [15.0, 5.10, "—", 495.1, 1237.6, 0.9757],
    [17.5, 6.69, "—", 649.4, 1623.5, 1.1384],
    [20.0, 9.34, 45.5, 906.6, 2266.6, 1.3010],
]

SPEC = {
    "id": "c6",
    "code": "C6",
    "group": "化工",
    "name": "填料吸收实验",
    "subtitle": "ΔP/Z–u 双对数曲线 · 泛点气速估算",
    "tags": ["吸收", "填料塔", "压降", "泛点"],
    "desc": "测定干填料层与 25 L/h 水淋量下湿填料层的压降 ΔP，绘制 ΔP/Z–u 双对数曲线；"
            "湿层曲线由恒持液量区转为载液/液泛区，用低、高气速两段拟合直线的交点估算泛点气速。",
    "method": [
        "① 由 U 形管压差计读数 Δh 换算 ΔP = ρ水·g·Δh，再除以填料层高度 Z 得 ΔP/Z；",
        "② 由转子流量计读数 V 与塔内径 D 换算空塔气速 u（本表直接采用报告给出的 u）；",
        "③ 在双对数坐标上分别作干、湿填料层的 ΔP/Z–u 曲线；",
        "④ 对湿层低气速段前 n低 点、高气速段末 n高 点分别作 lg(ΔP/Z)–lg u 直线拟合；",
        "⑤ 两拟合直线的交点即为泛点气速估算值，交点纵坐标为泛点压降。",
    ],
    "tables": [
        {"key": "wet", "title": "湿填料层（水淋量 25 L/h）",
         "note": "报告表 8 数据；温度只在实验开始、结束时记录，中间行为“—”。",
         "columns": [
             {"key": "v", "label": "V / (m³/h)", "type": "number"},
             {"key": "dh", "label": "Δh / cm", "type": "number"},
             {"key": "t", "label": "t / ℃", "type": "number"},
             {"key": "dp", "label": "ΔP / Pa", "type": "number"},
             {"key": "dpz", "label": "ΔP/Z / (Pa/m)", "type": "number"},
             {"key": "u", "label": "u / (m/s)", "type": "number"},
         ],
         "rows": WET},
        {"key": "dry", "title": "干填料层",
         "note": "报告表 6 数据；温度只在实验开始、结束时记录，中间行为“—”。",
         "columns": [
             {"key": "v", "label": "V / (m³/h)", "type": "number"},
             {"key": "dh", "label": "Δh / cm", "type": "number"},
             {"key": "t", "label": "t / ℃", "type": "number"},
             {"key": "dp", "label": "ΔP / Pa", "type": "number"},
             {"key": "dpz", "label": "ΔP/Z / (Pa/m)", "type": "number"},
             {"key": "u", "label": "u / (m/s)", "type": "number"},
         ],
         "rows": DRY},
    ],
    "params": [
        {"key": "z", "label": "填料层高度 Z", "type": "number", "default": 0.4, "step": 0.01,
         "hint": "单位 m；仅当 ΔP/Z 列为空时用于复算"},
        {"key": "d", "label": "填料塔内径 D", "type": "number", "default": 0.075, "step": 0.001,
         "hint": "单位 m；仅当 u 列为空时按 V 复算"},
        {"key": "nlow", "label": "低气速段点数", "type": "number", "default": 4, "step": 1,
         "hint": "湿层前几个点作恒持液量区拟合"},
        {"key": "nhigh", "label": "高气速段点数", "type": "number", "default": 3, "step": 1,
         "hint": "湿层最后几个点作液泛区拟合"},
    ],
}


def _prepare(rows, z, d):
    """整理数据：缺 ΔP、ΔP/Z 或 u 时按 Z、D 复算；按 u 升序。"""
    out = []
    for r in rows:
        if len(r) < 6:
            continue
        v = num(r[0])
        dh = num(r[1])
        t = num(r[2])
        dp = num(r[3])
        dpz = num(r[4])
        u = num(r[5])
        if dp is None and dh is not None:
            dp = 1000.0 * 9.80665 * dh / 100.0
        if dpz is None and dp is not None and z > 0:
            dpz = dp / z
        if u is None and v is not None and d > 0:
            u = (v / 3600.0) / (math.pi * d * d / 4.0)
        if u is None or dpz is None or u <= 0 or dpz <= 0:
            continue
        out.append({"v": v, "dh": dh, "t": t, "dp": dp, "dpz": dpz, "u": u})
    out.sort(key=lambda q: q["u"])
    return out


def _logfit(points):
    xs = [math.log10(q["u"]) for q in points]
    ys = [math.log10(q["dpz"]) for q in points]
    return linfit(xs, ys)


def _table(pts):
    rows = []
    for q in pts:
        rows.append([
            round(q["v"], 2) if q["v"] is not None else "—",
            round(q["dh"], 2) if q["dh"] is not None else "—",
            round(q["t"], 1) if q["t"] is not None else "—",
            round(q["dp"], 2) if q["dp"] is not None else "—",
            round(q["dpz"], 1),
            round(q["u"], 4),
        ])
    return rows


def run(data):
    tables = data.get("tables") or {}
    p = data.get("params") or {}
    z = num(p.get("z"), 0.4)
    d = num(p.get("d"), 0.075)
    nlow = int(num(p.get("nlow"), 4))
    nhigh = int(num(p.get("nhigh"), 3))

    if z <= 0:
        raise ValueError("填料层高度 Z 必须大于 0")
    if d <= 0:
        raise ValueError("填料塔内径 D 必须大于 0")
    if nlow < 2 or nhigh < 2:
        raise ValueError("低气速段和高气速段都至少取 2 个点")

    wet = _prepare(tables.get("wet") or [], z, d)
    dry = _prepare(tables.get("dry") or [], z, d)
    if len(wet) < nlow + nhigh:
        raise ValueError(f"湿填料层只有 {len(wet)} 个有效点，少于低段 {nlow} 点 + 高段 {nhigh} 点")
    if len(dry) < 3:
        raise ValueError("干填料层数据不足 3 个点，无法拟合参考斜率")

    low_pts, high_pts = wet[:nlow], wet[-nhigh:]
    if low_pts[-1]["u"] >= high_pts[0]["u"]:
        raise ValueError("低气速段与高气速段重叠，请减小 n低 或 n高")

    f_low = _logfit(low_pts)
    f_high = _logfit(high_pts)
    if abs(f_low["slope"] - f_high["slope"]) < 1e-9:
        raise ValueError("低、高气速段拟合直线平行，无法求交点；请调整分段点数")

    lx, ly = intersect(f_low, f_high)
    uf = 10 ** lx
    dpz_f = 10 ** ly
    if not (math.isfinite(uf) and math.isfinite(dpz_f)) or uf <= 0 or dpz_f <= 0:
        raise ValueError("拟合交点不合理，请检查数据或调整 n低 / n高")

    f_dry = _logfit(dry)
    umin = wet[0]["u"]
    umax = wet[-1]["u"]
    all_u = [q["u"] for q in wet] + [q["u"] for q in dry]

    # ---------------- 图 ----------------
    series = [
        {"name": "湿填料层 25 L/h", "type": "scatter", "color": "#e5533d",
         "points": [[q["u"], q["dpz"]] for q in wet]},
        {"name": "干填料层", "type": "scatter", "color": "#2f6df6",
         "points": [[q["u"], q["dpz"]] for q in dry]},
        {"name": "湿层低气速段拟合", "type": "line", "color": "#e5533d", "dash": True,
         "points": [[umin, 10 ** (f_low["slope"] * math.log10(umin) + f_low["intercept"])],
                    [uf, dpz_f]]},
        {"name": "湿层高气速段拟合", "type": "line", "color": "#c0392b", "dash": True,
         "points": [[uf, dpz_f],
                    [umax, 10 ** (f_high["slope"] * math.log10(umax) + f_high["intercept"])]]},
    ]
    chart = {
        "title": "干、湿填料层 ΔP/Z–u 双对数曲线",
        "xlabel": "空塔气速 u / (m/s)", "ylabel": "ΔP/Z / (Pa/m)",
        "series": series,
        "vlines": [{"x": uf, "label": f"泛点估算 u={uf:.3f} m/s"}],
        "points": [{"x": uf, "y": dpz_f, "label": f"交点 ({uf:.3f}, {dpz_f:.0f})"}],
        "annotations": True,
        "xlog": True, "ylog": True,
        "xrange": [min(all_u) * 0.9, max(all_u) * 1.05],
    }

    warnings = []
    if not (umin <= uf <= umax):
        warnings.append("拟合交点落在实验气速范围之外，泛点数值属于外推，仅供参考")
    if f_low["r2"] < 0.97:
        warnings.append(f"湿层低气速段拟合 R²={f_low['r2']:.4f}，线性一般，可调整低段点数")
    if f_high["r2"] < 0.97:
        warnings.append(f"湿层高气速段拟合 R²={f_high['r2']:.4f}，线性一般，可调整高段点数")
    if len(wet) < 6:
        warnings.append("湿填料层数据点较少，泛点交点对分段点数较敏感")

    return {
        "kpis": [
            {"label": "泛点气速（两段拟合交点）", "value": round(uf, 3), "unit": "m/s",
             "digits": 3, "hint": f"低 {nlow} 点 / 高 {nhigh} 点双对数直线交点"},
            {"label": "泛点压降", "value": round(dpz_f, 1), "unit": "Pa/m", "digits": 0,
             "hint": "交点对应的 ΔP/Z"},
            {"label": "湿层低气速段斜率", "value": round(f_low["slope"], 2), "digits": 2,
             "hint": f"lg(ΔP/Z)–lg u，R²={f_low['r2']:.3f}"},
            {"label": "湿层高气速段斜率", "value": round(f_high["slope"], 2), "digits": 2,
             "hint": f"lg(ΔP/Z)–lg u，R²={f_high['r2']:.3f}"},
            {"label": "干填料层斜率", "value": round(f_dry["slope"], 2), "digits": 2,
             "hint": f"{len(dry)} 点整体拟合，R²={f_dry['r2']:.3f}"},
        ],
        "charts": [chart],
        "tables": [
            {"title": "湿填料层（25 L/h）数据处理", "columns":
             ["V / (m³/h)", "Δh / cm", "t / ℃", "ΔP / Pa", "ΔP/Z / (Pa/m)", "u / (m/s)"],
             "rows": _table(wet)},
            {"title": "干填料层数据处理", "columns":
             ["V / (m³/h)", "Δh / cm", "t / ℃", "ΔP / Pa", "ΔP/Z / (Pa/m)", "u / (m/s)"],
             "rows": _table(dry)},
        ],
        "notes": [
            f"ΔP 由 U 形管读数换算：ΔP = ρ水·g·Δh（Δh 以 cm 计时 ΔP = 98.07·Δh Pa）；ΔP/Z 取 Z={z:g} m。",
            f"空塔气速 u 优先采用表中报告值；若 u 列留空，则按 u = (V/3600)/(πD²/4)、D={d:g} m 复算。",
            f"泛点估算：湿层前 {nlow} 点拟合 lg(ΔP/Z)={f_low['slope']:.3f}·lg u+{f_low['intercept']:.3f}，"
            f"末 {nhigh} 点拟合斜率 {f_high['slope']:.3f}，交点 u={uf:.4f} m/s、ΔP/Z={dpz_f:.1f} Pa/m。",
            "与报告对照：报告表 8（25 L/h）末点 V=17.5 m³/h、u=1.1635 m/s、ΔP/Z=3679.9 Pa/m；"
            "表 6（干）末点 V=20 m³/h、u=1.3010 m/s、ΔP/Z=2266.6 Pa/m，本模块默认数据与之一致。",
            "报告只定性给出“恒持液量区→载液区→液泛区”，未给泛点数值；报告图另用竖线/端点标出载点、泛点，"
            "其中 25 L/h 曲线在 ΔP/Z≈2400 Pa/m 处（u≈0.997 m/s）被标为泛点，可作参考。",
            "报告未给出液相总传质系数 KLa，故本模块不计算该量。",
            "工作簿 Sheet1/Sheet2 为早期记录（u 与报告值相差约 3.4%），模块采用报告表 6/8 所对应的 Sheet3 (2) 复算值。",
        ],
        "warnings": warnings,
    }
