# -*- coding: utf-8 -*-
"""C3 离心泵性能测定：由流量、表压、电机功率换算扬程 H、轴功率 N 与效率 η。"""
import math

from ..core import num, spline_points

G = 9.81

# 定速（50 Hz）实测数据：Q(m³/h)、压力表(MPa)、真空表(MPa)、电机功率(kW)
# 取自「实验3数据处理.xlsx」sheet「实验」D2:G22，与实验报告表 5 同源
RAW = [
    [-0.04, 0.186, 0.00000, 0.41],
    [0.16, 0.201, 0.00000, 0.42],
    [0.44, 0.200, 0.00000, 0.43],
    [0.99, 0.196, 0.00000, 0.46],
    [1.44, 0.194, 0.00000, 0.48],
    [2.38, 0.185, 0.00048, 0.54],
    [2.82, 0.180, 0.00120, 0.56],
    [3.27, 0.177, 0.00240, 0.59],
    [4.05, 0.169, 0.00420, 0.63],
    [4.87, 0.158, 0.00636, 0.67],
    [5.38, 0.152, 0.00780, 0.69],
    [5.67, 0.148, 0.00936, 0.70],
    [6.04, 0.142, 0.01050, 0.72],
    [6.58, 0.133, 0.01220, 0.74],
    [7.04, 0.125, 0.01400, 0.75],
    [7.56, 0.115, 0.01600, 0.76],
    [8.11, 0.104, 0.01810, 0.77],
    [8.69, 0.092, 0.02180, 0.78],
    [9.05, 0.084, 0.02200, 0.78],
    [9.53, 0.067, 0.02420, 0.77],
    [10.00, 0.035, 0.02650, 0.73],
]

SPEC = {
    "id": "c3",
    "code": "C3",
    "group": "化工",
    "name": "离心泵性能测定",
    "subtitle": "H–Q / N–Q / η–Q 特性曲线 · 找最高效率点",
    "tags": ["流体输送", "离心泵", "特性曲线", "化工原理"],
    "desc": "在恒定转速下逐点开大出口阀，记录流量、压力表与真空表读数、电机功率，"
            "换算泵的扬程 H、轴功率 N 和效率 η，绘出 H–Q、N–Q、η–Q 三条特性曲线并确定高效工作点。",
    "method": [
        "① 扬程 H = h₀ + (p表 + p真)/(ρg) + (u出² − u入²)/(2g)，压力单位取 Pa；",
        "② 管内流速 u = 4Q/(3600·πd²)，Q 用 m³/h、d 用 m，故除以 3600 换算成 m/s；",
        "③ 轴功率 N = η₀·P电，电机效率 η₀ 取 0.6；有效功率 Ne = ρgQH（Q 用 m³/s）；",
        "④ 泵效率 η = Ne/N，以 Q 为横坐标作 H–Q、N–Q、η–Q 三条曲线；",
        "⑤ η 最大处即高效工作点，其流量记为 Q_opt，用于选泵与管路特性匹配。",
    ],
    "tables": [{
        "key": "raw",
        "title": "离心泵性能实测数据",
        "note": "直接粘贴 Excel 四列（流量、压力表、真空表、电机功率）即可；空白或非数字单元格自动跳过。"
                "第 1 行 Q = −0.04 m³/h 为出口阀全关时的异常记录，程序会自动剔除并给出提示。",
        "columns": [
            {"key": "q", "label": "Q / (m³/h)", "type": "number"},
            {"key": "pout", "label": "压力表 / MPa", "type": "number"},
            {"key": "pin", "label": "真空表 / MPa", "type": "number"},
            {"key": "pe", "label": "电机功率 / kW", "type": "number"},
        ],
        "rows": RAW,
    }],
    "params": [
        {"key": "h0", "label": "两表位差 h₀", "type": "number", "default": 0.26, "step": 0.01,
         "hint": "压力表与真空表安装高度差，单位 m"},
        {"key": "d_in", "label": "入口管内径 d入", "type": "number", "default": 0.036, "step": 0.001,
         "hint": "泵入口管径，用于计算入口动能项，单位 m"},
        {"key": "d_out", "label": "出口管内径 d出", "type": "number", "default": 0.042, "step": 0.001,
         "hint": "泵出口管径，用于计算出口动能项，单位 m"},
        {"key": "rho", "label": "水的密度 ρ", "type": "number", "default": 996.5, "step": 0.5,
         "hint": "实验水温 20.6~22.0 ℃，取 996.5 kg/m³"},
        {"key": "eta0", "label": "电机效率 η₀", "type": "number", "default": 0.6, "step": 0.01,
         "hint": "轴功率 N = η₀·P电，本实验台取 0.6"},
    ],
}


def run(data):
    rows = (data.get("tables") or {}).get("raw") or []
    p = data.get("params") or {}
    h0 = num(p.get("h0"), 0.26)
    d_in = num(p.get("d_in"), 0.036)
    d_out = num(p.get("d_out"), 0.042)
    rho = num(p.get("rho"), 996.5)
    eta0 = num(p.get("eta0"), 0.6)

    if d_in is None or d_in <= 0 or d_out is None or d_out <= 0:
        raise ValueError("进口/出口管内径必须大于 0，请检查 d入、d出 两个参数")
    if rho is None or rho <= 0:
        raise ValueError("水的密度必须大于 0 kg/m³，请检查 ρ 参数")
    if eta0 is None or not 0 < eta0 <= 1:
        raise ValueError("电机效率 η₀ 应在 (0, 1] 之间，本实验台取 0.6")

    pts, skipped = [], []
    for i, r in enumerate(rows):
        q = num(r[0]) if len(r) > 0 else None
        p_out = num(r[1]) if len(r) > 1 else None
        p_in = num(r[2], 0.0) if len(r) > 2 else 0.0
        pe = num(r[3]) if len(r) > 3 else None
        if q is None or p_out is None or pe is None:
            skipped.append((i + 1, "缺流量 / 压力表 / 电机功率"))
            continue
        if p_in is None:
            p_in = 0.0
        if q <= 0:
            skipped.append((i + 1, f"流量 Q = {q:g} m³/h ≤ 0（阀门全关）"))
            continue
        if pe <= 0:
            skipped.append((i + 1, "电机功率 ≤ 0"))
            continue

        q_s = q / 3600.0
        u_out = 4.0 * q_s / (math.pi * d_out ** 2)
        u_in = 4.0 * q_s / (math.pi * d_in ** 2)
        H = h0 + (p_out + p_in) * 1e6 / (rho * G) + (u_out ** 2 - u_in ** 2) / (2.0 * G)
        N = eta0 * pe
        Ne = rho * G * q_s * H / 1000.0
        eta = Ne / N
        pts.append({"row": i + 1, "q": q, "p_out": p_out, "p_in": p_in, "pe": pe,
                    "H": H, "N": N, "Ne": Ne, "eta": eta})

    if not pts:
        raise ValueError("没有可用数据：请检查「流量」「压力表」「电机功率」三列是否填了数字")
    if len(pts) < 3:
        raise ValueError("有效数据不足 3 组，无法绘出泵特性曲线，请补测几个流量点")

    pts.sort(key=lambda d: d["q"])
    best = max(pts, key=lambda d: d["eta"])
    hmax = max(pts, key=lambda d: d["H"])
    qmax = max(d["q"] for d in pts)
    qmax_pt = max(pts, key=lambda d: d["q"])

    qs = [d["q"] for d in pts]
    Hs = [d["H"] for d in pts]
    Ns = [d["N"] for d in pts]
    etas = [d["eta"] for d in pts]

    sx_h, sy_h = spline_points(qs, Hs, 200)
    sx_e, sy_e = spline_points(qs, etas, 200)
    sx_n, sy_n = spline_points(qs, Ns, 200)

    chart_h = {
        "title": "H–Q 特性曲线（转速恒定）",
        "xlabel": "Q / (m³/h)", "ylabel": "H / m",
        "series": [
            {"name": "实测点", "type": "scatter", "color": "#2f6df6",
             "points": [[q, H] for q, H in zip(qs, Hs)]},
            {"name": "H–Q 曲线", "type": "line", "color": "#2f6df6",
             "points": [[x, y] for x, y in zip(sx_h, sy_h)]},
        ],
        "vlines": [{"x": best["q"], "label": f"Q_opt = {best['q']:.2f}"}],
        "points": [{"x": best["q"], "y": best["H"],
                    "label": f"最高效率点 η = {best['eta']:.3f}"}],
        "annotations": True,
        "xrange": [0.0, qmax * 1.05],
    }

    chart_e = {
        "title": "η–Q 与 N–Q 曲线",
        "xlabel": "Q / (m³/h)", "ylabel": "η（—）/ N（kW）",
        "series": [
            {"name": "η–Q 实测点", "type": "scatter", "color": "#e5533d",
             "points": [[q, e] for q, e in zip(qs, etas)]},
            {"name": "η–Q 曲线", "type": "line", "color": "#e5533d",
             "points": [[x, y] for x, y in zip(sx_e, sy_e)]},
            {"name": "N–Q 实测点", "type": "scatter", "color": "#12a150",
             "points": [[q, n] for q, n in zip(qs, Ns)]},
            {"name": "N–Q 曲线", "type": "line", "color": "#12a150",
             "points": [[x, y] for x, y in zip(sx_n, sy_n)]},
        ],
        "points": [{"x": best["q"], "y": best["eta"],
                    "label": f"η_max = {best['eta']:.3f}"}],
        "annotations": True,
        "xrange": [0.0, qmax * 1.05],
    }

    detail_rows = []
    for d in pts:
        detail_rows.append([round(d["q"], 2), round(d["p_out"], 4), round(d["p_in"], 5),
                            round(d["pe"], 2), round(d["H"], 3), round(d["N"], 3),
                            round(d["Ne"], 4), round(d["eta"], 4)])

    feature_rows = [
        ["最高扬程点", round(hmax["q"], 2), round(hmax["H"], 3), round(hmax["N"], 3),
         round(hmax["eta"], 4), "出口阀近全关，流量最小"],
        ["最高效率点", round(best["q"], 2), round(best["H"], 3), round(best["N"], 3),
         round(best["eta"], 4), "高效工作点，选泵依据"],
        ["最大流量点", round(qmax_pt["q"], 2), round(qmax_pt["H"], 3), round(qmax_pt["N"], 3),
         round(qmax_pt["eta"], 4), "出口阀全开"],
    ]

    warnings = []
    if skipped:
        msg = "；".join(f"第 {n} 行：{why}" for n, why in skipped)
        warnings.append(f"已跳过 {len(skipped)} 行无效记录（{msg}）")
    if best["eta"] < 0.3:
        warnings.append("最高效率偏低（< 0.3），请检查 η₀、密度的取值或表压/真空度是否填反")
    if len(pts) < 8:
        warnings.append("有效数据少于 8 组，H–Q 与 η–Q 曲线可能不够光滑")

    return {
        "kpis": [
            {"label": "最高效率 η_max", "value": round(best["eta"], 4), "digits": 3,
             "hint": f"出现在 Q = {best['q']:.2f} m³/h，H = {best['H']:.2f} m"},
            {"label": "高效点流量 Q_opt", "value": round(best["q"], 2), "unit": "m³/h", "digits": 2,
             "hint": "η 最大处的流量"},
            {"label": "最高扬程 H_max", "value": round(hmax["H"], 3), "unit": "m", "digits": 3,
             "hint": f"Q = {hmax['q']:.2f} m³/h 时（阀门近全关）"},
            {"label": "最大流量 Q_max", "value": round(qmax, 2), "unit": "m³/h", "digits": 2,
             "hint": f"对应扬程 H = {qmax_pt['H']:.2f} m"},
        ],
        "charts": [chart_h, chart_e],
        "tables": [
            {
                "title": "泵性能参数表（逐点复算）",
                "columns": ["Q / (m³/h)", "压力表 / MPa", "真空表 / MPa", "P电 / kW",
                            "H / m", "N / kW", "Ne / kW", "η"],
                "rows": detail_rows,
            },
            {
                "title": "特性曲线特征点",
                "columns": ["特征点", "Q / (m³/h)", "H / m", "N / kW", "η", "说明"],
                "rows": feature_rows,
            },
        ],
        "notes": [
            "扬程 H = h₀ + (p表 + p真)·10⁶/(ρg) + (u出² − u入²)/(2g)，真空表读数按正数代入，"
            f"ρ = {rho:g} kg/m³、h₀ = {h0:g} m；动能项在 Q < 2 m³/h 时不足 0.01 m，高流量时约 −0.17 m。",
            "轴功率 N = η₀·P电（η₀ = 0.6），有效功率 Ne = ρgQH，η = Ne/N。"
            "原 Excel 用 η = ρQH/(102·N) 换算，102 ≈ 1000/g，两者相差 < 0.1%，末位可能差 1 个单位。",
            "与实验报告表 5 对照：Q = 0.16 m³/h → H = 20.821 m、N = 0.252 kW、η = 0.036；"
            "Q = 7.04 m³/h → H = 14.392 m、η = 0.611（全表最高）；Q = 10.00 m³/h → H = 6.376 m。"
            "本模块逐行复算的 H、N、η 与报告表 5 完全一致（H 差 < 0.002 m，η 差 < 0.001）。",
            "报告所用泵为 WB70/055 型离心泵；实验记录首行 Q = −0.04 m³/h 是出口阀全关时真空表与压力表"
            "读数引起的异常点，报告表 5 中也未采用，本程序自动剔除。",
            "原表另有 16 组变频（50→20 Hz）数据，用于验证相似定律 H ∝ n²、Q ∝ n，本模块只处理定速数据；"
            "报告图 1 中还画了管路特性曲线 H = h₀ + KQ²，需要管路阻力系数，本模块未包含。",
            "水温实测 20.6~22.0 ℃，水密度按 996.5 kg/m³ 取值；若改用其他温度，请在参数里改 ρ。",
        ],
        "warnings": warnings,
    }
