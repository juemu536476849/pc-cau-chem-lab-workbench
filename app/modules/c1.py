# -*- coding: utf-8 -*-
"""C1 流体阻力测定：光滑管 λ–Re 与局部阻力系数 ζ。"""
import math

from ..core import num

# 光滑管原始记录：序号、流量 (L/h)、U 型管高度差 (cm)、压差传感器 (kPa)
# 低流量段用 U 型管读数，高流量段用压差传感器读数（传感器示数需减零位 P0）
SMOOTH_RAW = [
    [1, 13, 0.74, None],
    [2, 20, 0.97, None],
    [3, 30, 1.53, None],
    [4, 40, 2.11, None],
    [5, 50, 3.93, None],
    [6, 72, 7.89, None],
    [7, 88, 11.33, None],
    [8, 96, 12.53, None],
    [9, 140, None, 1.1],
    [10, 220, None, 3.6],
    [11, 300, None, 7.1],
    [12, 400, None, 12.5],
    [13, 500, None, 19.3],
    [14, 600, None, 27.6],
    [15, 700, None, 36.9],
    [16, 800, None, 46.0],
    [17, 900, None, 58.7],
    [18, 1000, None, 71.6],
]

# 局部阻力原始记录：序号、流量 (L/h)、近端 U 型管读数 (cm)、远端 U 型管读数 (cm)
LOCAL_RAW = [
    [1, 200, 1.27, 1.42],
    [2, 300, 2.80, 3.14],
    [3, 400, 4.80, 5.40],
    [4, 500, 7.46, 8.31],
    [5, 600, 10.86, 12.18],
    [6, 700, 14.68, 16.38],
]

G = 9.81
D_LOCAL = 0.015     # 局部阻力试验管内径 / m（报告表 2）
L_LOCAL = 1.7       # 局部阻力测压段长度 / m（报告表 2）


def _rho(t):
    """报告式(3)：水密度 kg/m³，t 为 ℃。"""
    return 1000.5 - 5.65e-3 * (t + 12) ** 1.887


def _no(v):
    """序号列：能转数字就取整，否则返回 None。"""
    x = num(v)
    return int(round(x)) if x is not None else None


def _mu(t):
    """报告式(4)：水粘度 Pa·s，t 为 ℃。"""
    return 0.9467215 * (t + 47.05) ** (-1.629311)


SPEC = {
    "id": "c1",
    "code": "C1",
    "group": "化工",
    "name": "流体阻力测定",
    "subtitle": "光滑管 λ–Re 双对数 · 局部阻力 ζ",
    "tags": ["流体力学", "直管阻力", "局部阻力", "Blasius"],
    "desc": "用 U 型管与压差传感器测定光滑管不同流量下的压强降，换算摩擦系数 λ 与雷诺数 Re，"
            "并与 Blasius 经验式 λ=0.3164/Re^0.25 对照；另一组数据用两点压差法求局部阻力系数 ζ。",
    "method": [
        "① 由流量 qv 与管内径 d 求流速 u = qv/(3600·πd²/4)；",
        "② 低流量用 U 型管读数 Δh 换算 ΔP=ρgΔh，高流量用传感器示数减零位 P0；",
        "③ 由 λ = 2dΔP/(ρLū²) 求摩擦系数，Re = duρ/μ；",
        "④ 局部阻力：ΔPf = 2ΔP近 − ΔP远，ζ = 2ΔPf/(ρu²)；",
        "⑤ 在双对数坐标中比较实测 λ–Re 与 Blasius 式，并考察 ζ 是否近似为常数。",
    ],
    "tables": [
        {
            "key": "smooth",
            "title": "光滑管原始数据",
            "note": "前 8 组读 U 型管高度差 Δh，后 10 组读压差传感器；传感器零位 P0 在参数中修正。",
            "columns": [
                {"key": "no", "label": "序号", "type": "number"},
                {"key": "qv", "label": "流量 qv /(L·h⁻¹)", "type": "number"},
                {"key": "dh", "label": "U 型管 Δh /cm", "type": "number"},
                {"key": "dp", "label": "传感器 ΔP /kPa", "type": "number"},
            ],
            "rows": SMOOTH_RAW,
        },
        {
            "key": "local",
            "title": "局部阻力原始数据",
            "note": "近端、远端两只 U 型管的读数，均为 cm 水柱；空白格自动跳过。",
            "columns": [
                {"key": "no", "label": "序号", "type": "number"},
                {"key": "qv", "label": "流量 qv /(L·h⁻¹)", "type": "number"},
                {"key": "hn", "label": "近端 Δh /cm", "type": "number"},
                {"key": "hf", "label": "远端 Δh /cm", "type": "number"},
            ],
            "rows": LOCAL_RAW,
        },
    ],
    "params": [
        {"key": "d", "label": "光滑管内径 d", "type": "number", "default": 0.008,
         "step": 0.001, "hint": "报告表 2：d = 0.008 m"},
        {"key": "L", "label": "光滑管测压段长度 L", "type": "number", "default": 1.68,
         "step": 0.01, "hint": "报告表 2：L = 1.68 m"},
        {"key": "P0", "label": "压差传感器零位 P₀", "type": "number", "default": -0.8,
         "step": 0.1, "hint": "ΔP = 示数 − P₀；报告 P₀ = −0.8 kPa，即示数加 0.8"},
        {"key": "ts", "label": "光滑管平均水温", "type": "number", "default": 22.75,
         "step": 0.05, "hint": "原始记录 T初 22.1 ℃、T末 23.4 ℃，取平均"},
        {"key": "tl", "label": "局部阻力平均水温", "type": "number", "default": 23.65,
         "step": 0.05, "hint": "原始记录 T初 23.5 ℃、T末 23.8 ℃，取平均"},
    ],
}


def run(data):
    tables = data.get("tables") or {}
    p = data.get("params") or {}
    rows_s = tables.get("smooth") or []
    rows_l = tables.get("local") or []

    d = num(p.get("d"), 0.008)
    L = num(p.get("L"), 1.68)
    P0 = num(p.get("P0"), -0.8)
    ts = num(p.get("ts"), 22.75)
    tl = num(p.get("tl"), 23.65)
    if d is None or d <= 0:
        raise ValueError("光滑管内径 d 必须为正数，请检查参数")
    if L is None or L <= 0:
        raise ValueError("测压段长度 L 必须为正数，请检查参数")
    if ts is None or tl is None:
        raise ValueError("水温不能为空，请检查参数")

    rho_s, mu_s = _rho(ts), _mu(ts)
    rho_l, mu_l = _rho(tl), _mu(tl)

    # ---------------- 光滑管 ----------------
    smooth = []
    for r in rows_s:
        if len(r) < 4:
            continue
        no = _no(r[0])
        qv = num(r[1])
        dh = num(r[2])
        dps = num(r[3])
        if qv is None or qv <= 0:
            continue
        if dh is None and dps is None:
            continue
        u = qv * 1e-3 / 3600 / (math.pi * d * d / 4)
        if dh is not None and dh > 0:
            dP = rho_s * G * dh * 0.01 / 1000      # kPa
        else:
            dP = dps - P0                          # kPa
        if dP <= 0:
            raise ValueError(f"第 {no if no is not None else '?'} 组光滑管压差不为正，请检查 U 型管读数或传感器零位 P₀")
        lam = 2 * d * dP * 1000 / (rho_s * L * u * u)
        Re = d * u * rho_s / mu_s
        smooth.append({"no": no, "qv": qv, "u": u, "dP": dP, "lam": lam, "Re": Re,
                       "bl": 0.3164 / Re ** 0.25})

    if len(smooth) < 3:
        raise ValueError("光滑管数据不足（至少 3 组）：请检查流量、U 型管高度差与传感器读数")

    # ---------------- 局部阻力 ----------------
    local = []
    for r in rows_l:
        if len(r) < 4:
            continue
        no = _no(r[0])
        qv = num(r[1])
        hn = num(r[2])
        hf = num(r[3])
        if qv is None or qv <= 0 or hn is None or hf is None:
            continue
        u = qv * 1e-3 / 3600 / (math.pi * D_LOCAL * D_LOCAL / 4)
        pn = rho_l * G * hn * 0.01 / 1000          # kPa
        pf = rho_l * G * hf * 0.01 / 1000          # kPa
        dpf = 2 * pn - pf
        if dpf <= 0:
            raise ValueError(f"第 {no if no is not None else '?'} 组局部阻力压差不为正，请检查近端/远端读数是否接反")
        zeta = 2 * dpf * 1000 / (rho_l * u * u)
        local.append({"no": no, "qv": qv, "u": u, "pn": pn, "pf": pf, "dpf": dpf, "zeta": zeta})

    if len(local) < 2:
        raise ValueError("局部阻力数据不足（至少 2 组）：请检查近端/远端 U 型管读数，或两列是否填反")

    # ---------------- 统计 ----------------
    turb = [x for x in smooth if x["Re"] >= 4000]
    if not turb:
        raise ValueError("光滑管数据没有 Re ≥ 4×10³ 的湍流点，无法与 Blasius 式对照，请检查流量或内径参数")
    lam_turb = sum(x["lam"] for x in turb) / len(turb)
    dev_turb = sum((x["lam"] - x["bl"]) / x["bl"] * 100 for x in turb) / len(turb)
    dev_abs = sum(abs((x["lam"] - x["bl"]) / x["bl"] * 100) for x in turb) / len(turb)
    lam_min = min(x["lam"] for x in smooth)
    lam_max = max(x["lam"] for x in smooth)
    re_min = min(x["Re"] for x in smooth)
    re_max = max(x["Re"] for x in smooth)

    lam_lam = [x for x in smooth if x["Re"] < 2320]
    lamRe = (sum(x["lam"] * x["Re"] for x in lam_lam) / len(lam_lam)) if lam_lam else float("nan")

    zmean = sum(x["zeta"] for x in local) / len(local) if local else float("nan")
    zsd = (math.sqrt(sum((x["zeta"] - zmean) ** 2 for x in local) / (len(local) - 1))
           if len(local) > 1 else 0.0)
    zrsd = zsd / zmean * 100 if zmean else float("nan")

    charts = []
    # λ–Re 双对数
    series = [{"name": "光滑管实测", "type": "scatter",
               "points": [[x["Re"], x["lam"]] for x in smooth]}]
    if re_max > 4000:
        lo = max(4000.0, re_min)
        n = 24
        pts = []
        for i in range(n):
            re = lo * (re_max * 1.05 / lo) ** (i / (n - 1))
            pts.append([re, 0.3164 / re ** 0.25])
        series.append({"name": "Blasius λ=0.3164/Re^0.25", "type": "line",
                       "color": "#2f6df6", "points": pts, "dash": True})
    if re_min < 2320:
        lo = max(re_min * 0.95, 100.0)
        hi = min(2320.0, re_max)
        if hi > lo:
            n = 24
            pts = []
            for i in range(n):
                re = lo * (hi / lo) ** (i / (n - 1))
                pts.append([re, 64.0 / re])
            series.append({"name": "层流 λ=64/Re", "type": "line",
                           "color": "#8a94a6", "points": pts, "dash": True})
    charts.append({
        "title": "光滑管 λ–Re 双对数关系",
        "xlabel": "Re", "ylabel": "λ",
        "series": series,
        "xlog": True, "ylog": True,
        "annotations": True,
    })

    if local:
        charts.append({
            "title": "局部阻力系数 ζ 随流量的变化",
            "xlabel": "qv /(L·h⁻¹)", "ylabel": "ζ",
            "series": [{"name": "局部阻力实测", "type": "scatter",
                        "points": [[x["qv"], x["zeta"]] for x in local]}],
            "hlines": [{"y": zmean, "label": f"平均 ζ = {zmean:.3f}"}],
            "xrange": [0, max(x["qv"] for x in local) * 1.12],
            "annotations": True,
        })

    # ---------------- 结果表 ----------------
    t_smooth = []
    for x in smooth:
        turb_ok = x["Re"] >= 4000
        t_smooth.append([
            x["no"], x["qv"], round(x["u"], 4), round(x["dP"], 4), round(x["Re"]),
            round(x["lam"], 4),
            round(x["bl"], 4) if turb_ok else "—",
            round((x["lam"] - x["bl"]) / x["bl"] * 100, 1) if turb_ok else "—",
        ])

    t_local = []
    for x in local:
        t_local.append([x["no"], x["qv"], round(x["u"], 4), round(x["pn"], 4),
                        round(x["pf"], 4), round(x["dpf"], 4), round(x["zeta"], 3)])
    if local:
        t_local.append(["平均", "—", "—", "—", "—", "—", round(zmean, 3)])

    table_out = [{
        "title": "光滑管 λ–Re 计算表",
        "columns": ["序号", "qv /(L·h⁻¹)", "u /(m·s⁻¹)", "ΔP /kPa", "Re", "λ",
                    "λ_Blasius", "相对偏差 /%"],
        "rows": t_smooth,
    }]
    if local:
        table_out.append({
            "title": "局部阻力 ζ 计算表",
            "columns": ["序号", "qv /(L·h⁻¹)", "u /(m·s⁻¹)", "ΔP近 /kPa", "ΔP远 /kPa",
                        "ΔPf /kPa", "ζ"],
            "rows": t_local,
        })

    warnings = []
    trans = [x for x in smooth if 2320 <= x["Re"] < 4000]
    if trans:
        warnings.append(
            "Re = " + "、".join(f"{x['Re']:.0f}" for x in trans) +
            " 位于 2320–4000 过渡区，λ 本身波动较大，Blasius 式不适用。")
    if turb:
        bad = [x for x in turb if abs((x["lam"] - x["bl"]) / x["bl"]) > 0.20]
        if bad:
            warnings.append(
                "第 " + "、".join(str(x["no"]) for x in bad) +
                " 组 λ 与 Blasius 偏差超过 20%，可检查该点压差读数或是否漏减 P₀。")
    if local and zrsd > 5:
        warnings.append(f"局部阻力 ζ 的 RSD = {zrsd:.1f}%，分散偏大，建议检查近端/远端读数是否稳定。")

    notes = [
        f"物性按报告式(3)(4)由水温计算：ρ = 1000.5 − 5.65×10⁻³(t+12)^1.887 kg/m³，"
        f"μ = 0.9467215(t+47.05)^(−1.629311) Pa·s；光滑管 t = {ts:g} ℃ → ρ = {rho_s:.2f} kg/m³、"
        f"μ = {mu_s * 1e3:.3f} mPa·s。",
        f"光滑管：u = qv/(3600A)，ΔP = ρgΔh（U 型管）或 ΔP = 示数 − P₀，λ = 2dΔP/(ρLu²)，"
        f"Re = duρ/μ；本模块 d = {d:g} m、L = {L:g} m、P₀ = {P0:g} kPa。",
        f"结果：λ = {lam_min:.3f}–{lam_max:.3f}，Re = {re_min:.0f}–{re_max:.0f}，"
        f"湍流段（Re ≥ 4×10³，{len(turb)} 点）平均 λ = {lam_turb:.4f}，"
        f"相对 Blasius 平均偏差 {dev_turb:+.1f}%（平均绝对偏差 {dev_abs:.1f}%）。",
        "与报告对照：报告表 7 的 λ = 0.022–0.180、Re = 446–44596（原始记录为 10–98 L/h、水温 20.3/20.8 ℃）；"
        "本表采用实验 1 数据处理.xlsx 的原始记录（13–96 L/h、水温 22.1/23.4 ℃），故低 Re 端 λ 与报告不同，"
        "但“λ 随 Re 增大而减小、高 Re 端趋于 0.022–0.023”的规律一致。",
        "报告表 7 的高流量段有的点直接用了传感器示数（如 300 L/h 记 7.6 kPa，未加 0.8 kPa 零位修正），"
        "例如 Re≈1.34×10⁴ 处 λ=0.026，比 Blasius 值低约 12%；本模块统一按 ΔP = 示数 + 0.8 kPa 修正后，"
        "该点 λ≈0.0275，偏差缩小到 −5%。",
        *([f"层流段（Re < 2320，{len(lam_lam)} 点）λ·Re 平均 = {lamRe:.1f}，理论值 64；"
           "实测偏高与报告“层流段实测 λ 高于 64/Re”的结论一致，说明低流量下 U 型管读数偏大或存在附加压降。"]
          if lam_lam else []),
        "局部阻力：d = 0.015 m、测压段 1.7 m（报告表 2），ΔPf = 2ΔP近 − ΔP远，ζ = 2ΔPf/(ρu²)；"
        f"本表 {len(local)} 组 ζ = " + "、".join(f"{x['zeta']:.2f}" for x in local) +
        f"，平均 {zmean:.3f}，RSD {zrsd:.2f}%。",
        "与报告对照：报告局部阻力数据表的 ζ = 1.99、2.06、2.01、1.94、2.03、2.08（平均 2.018）；"
        f"xlsx 版读数算得平均 {zmean:.3f}，两者相差约 {abs(zmean - 2.018) / 2.018 * 100:.1f}%，"
        "属两版原始记录（近端/远端读数差 0.2–0.5 cm）造成的差异，ζ 近似为常数的结论不变。",
    ]

    kpis = [
        {"label": "湍流段平均 λ", "value": round(lam_turb, 4), "digits": 4,
         "hint": f"Re ≥ 4×10³ 共 {len(turb)} 点，理论 Blasius 随 Re 变化"},
        {"label": "与 Blasius 平均绝对偏差", "value": round(dev_abs, 1), "unit": "%", "digits": 1,
         "hint": "实测 λ 相对 0.3164/Re^0.25 的平均绝对偏差"},
        {"label": "平均局部阻力系数 ζ", "value": round(zmean, 3), "digits": 3,
         "hint": f"{len(local)} 组算术平均，报告值约 2.02"},
        {"label": "ζ 的 RSD", "value": round(zrsd, 2), "unit": "%", "digits": 2,
         "hint": "样本标准差 / 平均值"},
        *([{"label": "层流段 λ·Re", "value": round(lamRe, 1), "digits": 1,
            "hint": "理论值 64，实测偏高"}] if lam_lam else []),
    ]

    return {"kpis": kpis, "charts": charts, "tables": table_out,
            "notes": notes, "warnings": warnings}
