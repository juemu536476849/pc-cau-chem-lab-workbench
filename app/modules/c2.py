# -*- coding: utf-8 -*-
"""C2 流量计性能测定：孔板流量计流量系数 C 与 Re 的关系。"""
import math

from ..core import linfit, num

# 原始记录：序号、U 型管高度差 Δh (cm)、压差传感器 ΔPᵢ (kPa)、10 s 液面上升高度 ΔH (cm)
# 第 1–8 组用 U 型管测压差，第 9–17 组用压差传感器
RAW = [
    [1, 2.54, None, 1.03],
    [2, 5.87, None, 1.36],
    [3, 10.45, None, 1.77],
    [4, 15.43, None, 2.18],
    [5, 20.12, None, 2.59],
    [6, 30.27, None, 3.12],
    [7, 39.74, None, 3.54],
    [8, 49.99, None, 4.03],
    [9, None, 5.80, 4.56],
    [10, None, 7.00, 4.94],
    [11, None, 8.50, 5.33],
    [12, None, 9.60, 5.64],
    [13, None, 11.10, 5.95],
    [14, None, 13.70, 6.74],
    [15, None, 16.40, 7.38],
    [16, None, 19.00, 7.83],
    [17, None, 21.20, 8.66],
]

G = 9.81
T_MEASURE = 10.0     # 计量时间 / s


def _rho(t):
    """报告式(3)：水密度 kg/m³，t 为 ℃。"""
    return 1000.5 - 5.65e-3 * (t + 12) ** 1.887


def _mu(t):
    """报告式(4)：水粘度 Pa·s，t 为 ℃。"""
    return 0.9467215 * (t + 47.05) ** (-1.629311)


def _no(v):
    """序号列：能转数字就取整，否则返回 None。"""
    x = num(v)
    return int(round(x)) if x is not None else None


SPEC = {
    "id": "c2",
    "code": "C2",
    "group": "化工",
    "name": "流量计性能测定",
    "subtitle": "孔板流量计 C–Re 标定 · Vs–ΔP 双对数",
    "tags": ["流体力学", "流量计", "孔板", "流量系数"],
    "desc": "用体积法测孔板流量计的体积流量 Vs，同时读取孔板前后压差 ΔP，"
            "由孔板流量方程反算流量系数 C，考察 C 随 Re 的变化，并对 Vs–ΔP 作双对数拟合。",
    "method": [
        "① 由计量桶截面积 A1 与 10 s 内液面上升高度 ΔH 求 Vs = A1·ΔH（L/s）；",
        "② 低流量段 ΔP = ρgΔh，高流量段 ΔP = 传感器示数 + 零位 ΔP₀；",
        "③ 由 C = Vs/(A₀√(2ΔP/ρ)) 逐点求流量系数；",
        "④ 由 u = Vs/A、Re = duρ/μ 求管流速与雷诺数；",
        "⑤ 对 lnVs–lnΔP 作最小二乘拟合，检查斜率是否接近理论值 0.5。",
    ],
    "tables": [
        {
            "key": "raw",
            "title": "孔板流量计原始数据",
            "note": "前 8 组读 U 型管高度差 Δh，第 9 组起读压差传感器；空白格自动跳过。",
            "columns": [
                {"key": "no", "label": "序号", "type": "number"},
                {"key": "dh", "label": "U 型管 Δh /cm", "type": "number"},
                {"key": "dpi", "label": "传感器 ΔPᵢ /kPa", "type": "number"},
                {"key": "dH", "label": "10 s 液面上升 ΔH /cm", "type": "number"},
            ],
            "rows": RAW,
        },
    ],
    "params": [
        {"key": "A1", "label": "计量桶截面积 A₁", "type": "number", "default": 0.1106,
         "step": 0.0001, "hint": "报告：A₁ = 0.1106 m²"},
        {"key": "d0", "label": "孔板孔径 d₀", "type": "number", "default": 0.015,
         "step": 0.001, "hint": "报告：d₀ = 0.015 m，A₀ = 1.77×10⁻⁴ m²"},
        {"key": "d", "label": "试验管内径 d", "type": "number", "default": 0.026,
         "step": 0.001, "hint": "报告：d = 0.026 m，A = 5.31×10⁻⁴ m²"},
        {"key": "P0", "label": "传感器零点 ΔP₀", "type": "number", "default": -0.3,
         "step": 0.1, "hint": "按报告：ΔP = ΔPᵢ + ΔP₀（5.80 → 5.50 kPa）"},
        {"key": "t", "label": "平均水温", "type": "number", "default": 21.05,
         "step": 0.05, "hint": "报告 T初 21.7 ℃、T末 20.4 ℃，取平均"},
    ],
}


def run(data):
    rows = (data.get("tables") or {}).get("raw") or []
    p = data.get("params") or {}

    A1 = num(p.get("A1"), 0.1106)
    d0 = num(p.get("d0"), 0.015)
    d = num(p.get("d"), 0.026)
    P0 = num(p.get("P0"), -0.3)
    t = num(p.get("t"), 21.05)
    if A1 is None or A1 <= 0:
        raise ValueError("计量桶截面积 A₁ 必须为正数，请检查参数")
    if d0 is None or d0 <= 0:
        raise ValueError("孔板孔径 d₀ 必须为正数，请检查参数")
    if d is None or d <= 0:
        raise ValueError("试验管内径 d 必须为正数，请检查参数")
    if d <= d0:
        raise ValueError("试验管内径 d 必须大于孔板孔径 d₀，请检查参数")
    if t is None:
        raise ValueError("平均水温不能为空，请检查参数")

    rho, mu = _rho(t), _mu(t)
    A0 = math.pi * d0 * d0 / 4
    A = math.pi * d * d / 4

    pts = []
    for r in rows:
        if len(r) < 4:
            continue
        no = _no(r[0])
        dh = num(r[1])
        dpi = num(r[2])
        dH = num(r[3])
        if dH is None or dH <= 0:
            continue
        if dh is None and dpi is None:
            continue
        if dh is not None and dh > 0:
            dP = rho * G * dh * 0.01 / 1000       # kPa
        else:
            dP = dpi + P0                          # kPa，报告按此处理
        if dP <= 0:
            raise ValueError(f"第 {no if no is not None else '?'} 组孔板压差不为正，请检查 U 型管读数或传感器零点 ΔP₀")
        Vs = A1 * dH                               # L/s
        u = Vs * 1e-3 / A
        C = Vs * 1e-3 / (A0 * math.sqrt(2 * dP * 1000 / rho))
        Re = d * u * rho / mu
        pts.append({"no": no, "dh": dh, "dpi": dpi, "dP": dP, "Vs": Vs,
                    "u": u, "C": C, "Re": Re})

    if len(pts) < 3:
        raise ValueError("数据不足（至少 3 组）：请检查 ΔH 列以及 Δh/ΔPᵢ 是否至少填了一列")

    n = len(pts)
    Cmean = sum(x["C"] for x in pts) / n
    Csd = math.sqrt(sum((x["C"] - Cmean) ** 2 for x in pts) / (n - 1)) if n > 1 else 0.0
    Crsd = Csd / Cmean * 100 if Cmean else float("nan")

    # ln Vs – ln ΔP 拟合
    lx = [math.log(x["dP"]) for x in pts]
    ly = [math.log(x["Vs"]) for x in pts]
    fit = linfit(lx, ly)

    # ---------------- 图 ----------------
    charts = [{
        "title": "孔板流量计 C–Re 标定曲线",
        "xlabel": "Re", "ylabel": "流量系数 C",
        "series": [{"name": "实测 C", "type": "scatter",
                    "points": [[x["Re"], x["C"]] for x in pts]}],
        "hlines": [{"y": Cmean, "label": f"平均 C = {Cmean:.4f}"}],
        "xlog": True,
        "annotations": True,
    }]

    x1, x2 = min(lx), max(lx)
    fit_pts = [[math.exp(x1), math.exp(fit["slope"] * x1 + fit["intercept"])],
               [math.exp(x2), math.exp(fit["slope"] * x2 + fit["intercept"])]]
    charts.append({
        "title": f"Vs–ΔP 双对数（拟合指数 n = {fit['slope']:.3f}）",
        "xlabel": "ΔP /kPa", "ylabel": "Vs /(L·s⁻¹)",
        "series": [
            {"name": "实测点", "type": "scatter",
             "points": [[x["dP"], x["Vs"]] for x in pts]},
            {"name": "最小二乘拟合", "type": "line", "color": "#e5533d",
             "points": fit_pts, "dash": True},
        ],
        "xlog": True, "ylog": True,
        "annotations": True,
    })

    # ---------------- 结果表 ----------------
    calc_rows = []
    for x in pts:
        calc_rows.append([x["no"], round(x["dP"], 4), round(x["Vs"], 4),
                          round(x["u"], 4), round(x["C"], 4), round(x["Re"])])

    summary_rows = [
        ["数据点数", n, "报告表 5 共 17 组"],
        ["平均流量系数 C", round(Cmean, 4), "报告 0.817"],
        ["样本标准差 σ_C", round(Csd, 4), "17 组样本标准差"],
        ["C 的 RSD", f"{Crsd:.2f} %", "报告称 3.28%（疑为 σ_C×100）"],
        ["lnVs–lnΔP 斜率 n", round(fit["slope"], 4), "理论 0.5，报告约 0.48"],
        ["拟合截距", round(fit["intercept"], 4), "ln(Vs/(L·s⁻¹))"],
        ["拟合 R²", round(fit["r2"], 4), "报告 0.9969"],
    ]

    warnings = []
    if n > 1:
        dev = [(x["C"] - Cmean) / Cmean * 100 for x in pts]
        i = max(range(n), key=lambda k: abs(dev[k]))
        if abs(dev[i]) > 10:
            no = pts[i]["no"]
            no_txt = f"{no:g}" if isinstance(no, (int, float)) else "?"
            warnings.append(
                f"第 {no_txt} 组 C = {pts[i]['C']:.3f}，偏离均值 {dev[i]:+.1f}%；"
                "小流量下 U 型管读数相对误差较大，可复测该点。")
    if abs(fit["slope"] - 0.5) > 0.05:
        warnings.append(f"Vs–ΔP 双对数斜率 n = {fit['slope']:.3f}，与理论值 0.5 相差较大，建议检查压差单位或是否漏减零点。")

    notes = [
        f"物性按报告式(3)(4)由水温计算：ρ = 1000.5 − 5.65×10⁻³(t+12)^1.887 kg/m³，"
        f"μ = 0.9467215(t+47.05)^(−1.629311) Pa·s；t = {t:g} ℃ → ρ = {rho:.2f} kg/m³、"
        f"μ = {mu * 1e3:.3f} mPa·s。",
        f"体积法：Vs = A₁·ΔH（A₁ = {A1:g} m²，ΔH 用 cm，10 s 计量，故数值上 Vs[L/s] = A₁·ΔH）；"
        f"A₀ = πd₀²/4 = {A0:.4g} m²，A = πd²/4 = {A:.4g} m²，u = Vs×10⁻³/A。",
        "孔板流量方程：C = Vs/(A₀√(2ΔP/ρ))，其中 Vs 用 m³/s、ΔP 用 Pa；"
        f"低流量段 ΔP = ρgΔh，高流量段按报告取 ΔP = ΔPᵢ + ΔP₀（ΔP₀ = {P0:g} kPa）。",
        f"结果：C = {min(x['C'] for x in pts):.3f}–{max(x['C'] for x in pts):.3f}，"
        f"平均 C = {Cmean:.4f}，σ_C = {Csd:.4f}，RSD = {Crsd:.2f}%；"
        f"Re = {min(x['Re'] for x in pts):.0f}–{max(x['Re'] for x in pts):.0f}。",
        "与报告对照：报告表 5 的 C 逐点值（0.913、0.793、0.774 … 0.800、0.837）与本表一致到小数点后三位，"
        f"平均 C 报告 0.817、本模块 {Cmean:.4f}；lnVs–lnΔP 斜率报告约 0.48、R² = 0.9969，"
        f"本模块 n = {fit['slope']:.4f}、R² = {fit['r2']:.4f}。",
        "关于 RSD：报告正文写“RSD = 3.28%”，但 17 组 C 的样本标准差 σ_C = "
        f"{Csd:.4f}（即 3.28 个百分点），按 RSD = σ_C/C̄ 应为 {Crsd:.2f}%；"
        "报告很可能把 σ_C×100 直接当成了百分数。",
        "C 在 0.77–0.91、平均约 0.82，低于教科书孔板的 0.98–0.99：实际孔板取压方式、孔径比 d₀/d = 0.577、"
        "入口边缘加工与安装条件都与教科书标定条件不同，且低流量段 U 型管读数分辨率有限；"
        "报告也得到同样偏低的 C，说明是装置系统特性而非计算错误。",
        "第 1 组 C = 0.913 明显偏高：Δh 仅 2.54 cm，读数误差 0.05 cm 就会带来约 2% 的 ΔP 误差"
        "（约 1% 的 C 误差），故低流量端 C 的分散度更大；报告在统计时也曾考虑“去除第一个点”。",
    ]

    kpis = [
        {"label": "平均流量系数 C", "value": round(Cmean, 4), "digits": 4,
         "hint": f"{n} 组算术平均，报告 0.817"},
        {"label": "C 的 RSD", "value": round(Crsd, 2), "unit": "%", "digits": 2,
         "hint": f"σ_C = {Csd:.4f}；报告 3.28% 疑为 σ_C×100"},
        {"label": "Vs–ΔP 拟合指数 n", "value": round(fit["slope"], 4), "digits": 4,
         "hint": "理论 0.5，双对数坐标下为直线斜率"},
        {"label": "拟合 R²", "value": round(fit["r2"], 4), "digits": 4,
         "hint": "lnVs 对 lnΔP 的线性拟合"},
    ]

    return {
        "kpis": kpis,
        "charts": charts,
        "tables": [
            {"title": "孔板流量计逐点计算结果",
             "columns": ["序号", "ΔP /kPa", "Vs /(L·s⁻¹)", "u /(m·s⁻¹)", "C", "Re"],
             "rows": calc_rows},
            {"title": "流量系数统计与 Vs–ΔP 拟合",
             "columns": ["统计量", "数值", "对照 / 说明"],
             "rows": summary_rows},
        ],
        "notes": notes,
        "warnings": warnings,
    }
