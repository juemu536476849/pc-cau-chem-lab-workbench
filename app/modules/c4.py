# -*- coding: utf-8 -*-
"""C4 传热综合实验：套管加强管给热系数 α、Nu–Re 关联式与列管总传热系数 K0。"""
import math

from ..core import num, linfit

# 60 ℃ 干空气物性（与实验报告取值一致）
CP_AIR = 1005.0      # J/(kg·K)，报告记作 1.005 kJ/(kg·K)
LAM_AIR = 0.0283     # W/(m·K)
MU_AIR = 1.96e-5     # Pa·s
RHO_AIR = 1.060      # kg/m³
RHO_T1 = 1.165       # kg/m³，进气温度下空气密度，用于普通管孔板流量换算
N_TUBE = 6           # 列管根数

# 列管（普通管）：孔板压差/kPa、空气入口/出口温度/℃、蒸汽壁温/℃
PLAIN = [
    [0.56, 32.4, 77.6, 99.7],
    [0.86, 33.8, 77.5, 99.7],
    [1.22, 36.4, 77.7, 99.7],
    [1.60, 38.5, 77.8, 99.7],
    [1.90, 39.3, 77.2, 99.7],
]

# 套管（加强管）：孔板压差/kPa、空气入口/出口温度/℃、套管壁温/℃
ENHANCED = [
    [0.34, 33.6, 88.3, 98.1],
    [0.43, 38.3, 88.5, 97.9],
    [0.68, 39.5, 87.8, 97.4],
    [0.86, 40.1, 87.3, 97.2],
    [1.07, 40.1, 86.9, 97.0],
    [1.19, 36.9, 85.8, 96.5],
]

SPEC = {
    "id": "c4",
    "code": "C4",
    "group": "化工",
    "name": "传热综合实验",
    "subtitle": "给热系数 α · Nu–Re 关联式 · 总传热系数 K₀ 与强化对比",
    "tags": ["传热", "对流给热", "准数关联", "强化传热"],
    "desc": "饱和水蒸气加热管内冷空气，测孔板压差与进出口气温、壁温，"
            "算出传热速率 Q、对流传热系数 α、Nu/Re，拟合 Nu = A·Re^m 关联式，"
            "并对比普通列管与套管加强管的总传热系数 K₀，评价强化传热效果。",
    "method": [
        "① 孔板流量 V = C₀·A₀·3600·√(2Δp/ρ)，A₀ = πd₀²/4（Δp 用 Pa，V 得 m³/h）；",
        "② 质量流量 W = Vρ/3600，传热速率 Q = W·Cp·(t₂ − t₁)；",
        "③ 温差 Δtm = tw − (t₁+t₂)/2，给热系数 α = Q/(S₁·Δtm)，S₁ = πd₁L₁；",
        "④ 流速 u = V/(3600A₀)，Nu = αd₁/λ，Re = uρd₁/μ，Pr = Cpμ/λ；",
        "⑤ 双对数拟合 lnNu = lnA + m·lnRe 得关联式 Nu = A·Re^m；",
        "⑥ 列管总传热系数 K₀ = Q/(S₂·ΔTm)，S₂ = 6πd₂L₂，ΔTm 取逆流对数平均温差。",
    ],
    "tables": [
        {
            "key": "plain",
            "title": "列管（普通管）原始数据",
            "note": "孔板压差用 kPa，温度为 ℃；可直接从 Excel 粘贴四列。空白行自动跳过。",
            "columns": [
                {"key": "dp", "label": "孔板压差 / kPa", "type": "number"},
                {"key": "t1", "label": "空气入口 t₁ / ℃", "type": "number"},
                {"key": "t2", "label": "空气出口 t₂ / ℃", "type": "number"},
                {"key": "tw", "label": "壁温 tw / ℃", "type": "number"},
            ],
            "rows": PLAIN,
        },
        {
            "key": "enhanced",
            "title": "套管（加强管）原始数据",
            "note": "套管为强化传热管，壁温 tw 指套管外壁平均温度；其余与普通管相同。",
            "columns": [
                {"key": "dp", "label": "孔板压差 / kPa", "type": "number"},
                {"key": "t1", "label": "空气入口 t₁ / ℃", "type": "number"},
                {"key": "t2", "label": "空气出口 t₂ / ℃", "type": "number"},
                {"key": "tw", "label": "壁温 tw / ℃", "type": "number"},
            ],
            "rows": ENHANCED,
        },
    ],
    "params": [
        {"key": "d1", "label": "套管内径 d₁", "type": "number", "default": 0.019, "step": 0.001,
         "hint": "管内换热面积 S₁ = πd₁L₁ 用，单位 m；报告正文写 0.02，但实际计算取 0.019"},
        {"key": "L1", "label": "套管长度 L₁", "type": "number", "default": 1.2, "step": 0.1,
         "hint": "换热管有效长度，单位 m"},
        {"key": "d0", "label": "孔板内径 d₀", "type": "number", "default": 0.017, "step": 0.001,
         "hint": "孔板流量计内径，A₀ = πd₀²/4，单位 m"},
        {"key": "C0", "label": "孔板系数 C₀", "type": "number", "default": 0.65, "step": 0.01,
         "hint": "孔板流量计流量系数，本实验台 0.65"},
        {"key": "rho", "label": "空气密度 ρ", "type": "number", "default": 1.060, "step": 0.005,
         "hint": "按平均温度 60 ℃ 查干空气物性表，kg/m³"},
    ],
}


def _calc(rows, kind, d1, L1, d0, C0, rho):
    """逐组计算一根管的传热参数。kind = plain / enhanced。"""
    a0 = math.pi * d0 ** 2 / 4.0
    s1 = math.pi * d1 * L1
    s2 = N_TUBE * s1
    out, skipped = [], []
    for i, r in enumerate(rows):
        dp = num(r[0]) if len(r) > 0 else None
        t1 = num(r[1]) if len(r) > 1 else None
        t2 = num(r[2]) if len(r) > 2 else None
        tw = num(r[3]) if len(r) > 3 else None
        if dp is None or t1 is None or t2 is None or tw is None:
            skipped.append((i + 1, "缺孔板压差或温度"))
            continue
        if dp <= 0:
            skipped.append((i + 1, "孔板压差 ≤ 0"))
            continue
        if t2 <= t1:
            skipped.append((i + 1, "出口温度不高于进口温度"))
            continue

        t = (t1 + t2) / 2.0
        if kind == "plain":
            # 普通管：孔板按进气温度密度 1.165 算体积流量，再换算到平均温度
            v_t1 = C0 * a0 * 3600.0 * math.sqrt(2.0 * dp * 1000.0 / RHO_T1)
            V = v_t1 * (273.15 + t) / (273.15 + t1)
        else:
            # 加强管：报告直接用 60 ℃ 密度算体积流量
            V = C0 * a0 * 3600.0 * math.sqrt(2.0 * dp * 1000.0 / rho)
            v_t1 = None
        W = V * rho / 3600.0                 # kg/s
        Q = W * CP_AIR * (t2 - t1)           # W

        dtm = tw - t
        if dtm <= 0:
            raise ValueError("壁温 tw 必须高于空气平均温度 t，请检查第 {} 行数据".format(i + 1))
        alpha = Q / (s1 * dtm)

        u = V / (3600.0 * a0)
        Nu = alpha * d1 / LAM_AIR
        Re = u * rho * d1 / MU_AIR

        dt1 = tw - t1
        dt2 = tw - t2
        if dt1 <= 0 or dt2 <= 0:
            raise ValueError("壁温 tw 必须高于空气进出口温度，请检查第 {} 行数据".format(i + 1))
        lmtd = dt1 if abs(dt1 - dt2) < 1e-9 else (dt1 - dt2) / math.log(dt1 / dt2)
        K0 = Q / (s2 * lmtd)

        out.append({"row": i + 1, "dp": dp, "t1": t1, "t2": t2, "tw": tw, "t": t,
                    "dtm": dtm, "V": V, "v_t1": v_t1, "W": W * 1000.0, "Q": Q,
                    "alpha": alpha, "u": u, "Nu": Nu, "Re": Re, "K0": K0,
                    "dt1": dt1, "dt2": dt2, "lmtd": lmtd})
    return out, skipped, s1, s2


def _fit(pts, name):
    if len(pts) < 2:
        raise ValueError(f"{name} 有效数据不足 2 组，无法拟合 Nu–Re 关联式")
    xs = [math.log(d["Re"]) for d in pts]
    ys = [math.log(d["Nu"]) for d in pts]
    fit = linfit(xs, ys)
    return {"m": fit["slope"], "b": fit["intercept"], "A": math.exp(fit["intercept"]),
            "r2": fit["r2"], "r": fit["r"], "n": fit["n"]}


def run(data):
    tabs = data.get("tables") or {}
    p = data.get("params") or {}
    d1 = num(p.get("d1"), 0.019)
    L1 = num(p.get("L1"), 1.2)
    d0 = num(p.get("d0"), 0.017)
    C0 = num(p.get("C0"), 0.65)
    rho = num(p.get("rho"), RHO_AIR)

    for label, v in (("套管内径 d₁", d1), ("套管长度 L₁", L1),
                     ("孔板内径 d₀", d0), ("孔板系数 C₀", C0), ("空气密度 ρ", rho)):
        if v is None or v <= 0:
            raise ValueError(f"{label} 必须大于 0，请检查参数设置")

    plain_rows = tabs.get("plain")
    enh_rows = tabs.get("enhanced")
    if plain_rows is None:
        plain_rows = PLAIN
    if enh_rows is None:
        enh_rows = ENHANCED

    plain, skip_p, s1, s2 = _calc(plain_rows, "plain", d1, L1, d0, C0, rho)
    enh, skip_e, _, _ = _calc(enh_rows, "enhanced", d1, L1, d0, C0, rho)

    if not plain:
        raise ValueError("普通管没有有效数据：请检查孔板压差与进出口温度四列")
    if not enh:
        raise ValueError("加强管没有有效数据：请检查孔板压差与进出口温度四列")

    fit_p = _fit(plain, "普通管")
    fit_e = _fit(enh, "加强管")

    re_ref = 25000.0
    nu_p_ref = fit_p["A"] * re_ref ** fit_p["m"]
    nu_e_ref = fit_e["A"] * re_ref ** fit_e["m"]
    ratio = nu_e_ref / nu_p_ref

    re_p = [d["Re"] for d in plain]
    re_e = [d["Re"] for d in enh]
    nu_p = [d["Nu"] for d in plain]
    nu_e = [d["Nu"] for d in enh]

    def fit_line(fit, lo, hi):
        return [[lo, fit["A"] * lo ** fit["m"]], [hi, fit["A"] * hi ** fit["m"]]]

    chart_nu = {
        "title": "Nu–Re 双对数图（普通管 vs 加强管）",
        "xlabel": "Re", "ylabel": "Nu",
        "series": [
            {"name": "普通管实测", "type": "scatter", "color": "#2f6df6",
             "points": [[x, y] for x, y in zip(re_p, nu_p)]},
            {"name": "加强管实测", "type": "scatter", "color": "#e5533d",
             "points": [[x, y] for x, y in zip(re_e, nu_e)]},
            {"name": f"普通管拟合 Nu={fit_p['A']:.4g}Re^{fit_p['m']:.3f}", "type": "line",
             "color": "#2f6df6", "dash": True,
             "points": fit_line(fit_p, min(re_p) * 0.9, max(re_p) * 1.1)},
            {"name": f"加强管拟合 Nu={fit_e['A']:.4g}Re^{fit_e['m']:.3f}", "type": "line",
             "color": "#e5533d", "dash": True,
             "points": fit_line(fit_e, min(re_e) * 0.9, max(re_e) * 1.1)},
        ],
        "points": [{"x": re_ref, "y": (nu_p_ref + nu_e_ref) / 2,
                    "label": f"Re={re_ref:.0f} 处 Nu 比 = {ratio:.2f}"}],
        "annotations": True,
        "xlog": True, "ylog": True,
    }

    chart_alpha = {
        "title": "给热系数 α 随 Re 的变化",
        "xlabel": "Re", "ylabel": "α / (W·m⁻²·℃⁻¹)",
        "series": [
            {"name": "普通管", "type": "scatter", "color": "#2f6df6",
             "points": [[x, d["alpha"]] for x, d in zip(re_p, plain)]},
            {"name": "加强管", "type": "scatter", "color": "#e5533d",
             "points": [[x, d["alpha"]] for x, d in zip(re_e, enh)]},
        ],
        "annotations": True,
    }

    detail_rows = []
    for tag, pts in (("列管（普通管）", plain), ("套管（加强管）", enh)):
        for k, d in enumerate(pts, start=1):
            detail_rows.append([
                tag, k, round(d["dp"], 2), round(d["t1"], 1), round(d["t2"], 1), round(d["tw"], 1),
                round(d["t"], 2), round(d["dtm"], 2), round(d["lmtd"], 2),
                round(d["V"], 2), round(d["W"], 3),
                round(d["Q"], 1), round(d["alpha"], 2), round(d["u"], 2),
                round(d["Nu"], 2), int(round(d["Re"])), round(d["K0"], 2),
            ])

    alpha_p_mean = sum(d["alpha"] for d in plain) / len(plain)
    alpha_e_mean = sum(d["alpha"] for d in enh) / len(enh)
    k0_p_mean = sum(d["K0"] for d in plain) / len(plain)
    k0_e_mean = sum(d["K0"] for d in enh) / len(enh)

    compare_rows = [
        ["列管（普通管）", len(plain),
         f"{min(re_p):.0f}~{max(re_p):.0f}", f"{min(nu_p):.1f}~{max(nu_p):.1f}",
         round(alpha_p_mean, 2), round(k0_p_mean, 2),
         f"Nu = {fit_p['A']:.4g}·Re^{fit_p['m']:.3f}", round(fit_p["r2"], 4)],
        ["套管（加强管）", len(enh),
         f"{min(re_e):.0f}~{max(re_e):.0f}", f"{min(nu_e):.1f}~{max(nu_e):.1f}",
         round(alpha_e_mean, 2), round(k0_e_mean, 2),
         f"Nu = {fit_e['A']:.4g}·Re^{fit_e['m']:.3f}", round(fit_e["r2"], 4)],
    ]

    warnings = []
    if skip_p:
        warnings.append("；".join(f"普通管第 {n} 行已跳过：{why}" for n, why in skip_p))
    if skip_e:
        warnings.append("；".join(f"加强管第 {n} 行已跳过：{why}" for n, why in skip_e))
    if abs(fit_e["m"] - 0.8) > 0.1:
        warnings.append(
            f"加强管拟合指数 m = {fit_e['m']:.3f}，与常用湍流关联式的 m ≈ 0.8 偏差较大，"
            "与物性取固定值（60 ℃）及壁温/压差读数误差有关，报告中也提到需与 m = 0.8 比较后修正 A")

    return {
        "kpis": [
            {"label": "加强管 m", "value": round(fit_e["m"], 4), "digits": 3,
             "hint": f"Nu = A·Re^m 的指数，R² = {fit_e['r2']:.4f}"},
            {"label": "加强管 A", "value": round(fit_e["A"], 5), "digits": 5,
             "hint": "Nu = A·Re^m 的系数（拟合截距取指数）"},
            {"label": "普通管 K0 均值", "value": round(k0_p_mean, 2), "unit": "W/(m²·K)", "digits": 2,
             "hint": f"{len(plain)} 组按 S₂ = 6πd₂L₂ 计算"},
            {"label": "强化比 Nu强/Nu普", "value": round(ratio, 3), "digits": 3,
             "hint": "Re = 25000 处按两条拟合式外推的 Nu 之比"},
        ],
        "charts": [chart_nu, chart_alpha],
        "tables": [
            {
                "title": "两管逐组传热参数（S₁ = πd₁L₁，S₂ = 6πd₂L₂）",
                "columns": ["管型", "序号", "Δp / kPa", "t₁ / ℃", "t₂ / ℃", "tw / ℃", "t / ℃",
                            "Δtm / ℃", "ΔTm / ℃", "V / (m³/h)", "W / (g/s)", "Q / W",
                            "α / (W·m⁻²·℃⁻¹)", "u / (m/s)", "Nu", "Re", "K₀ / (W·m⁻²·K⁻¹)"],
                "rows": detail_rows,
            },
            {
                "title": "普通管与加强管对比",
                "columns": ["管型", "组数", "Re 范围", "Nu 范围", "α 均值 / (W·m⁻²·℃⁻¹)",
                            "K₀ 均值 / (W·m⁻²·K⁻¹)", "拟合关联式", "R²"],
                "rows": compare_rows,
            },
        ],
        "notes": [
            f"几何参数按报告取值：d₁ = d₂ = {d1:g} m、L₁ = L₂ = {L1:g} m、d₀ = {d0:g} m、C₀ = {C0:g}，"
            f"列管 {N_TUBE} 根，S₁ = πd₁L₁ = {s1:.5f} m²、S₂ = 6πd₂L₂ = {s2:.5f} m²。",
            "物性取平均温度约 60 ℃ 的干空气常数：ρ = 1.060 kg/m³、Cp = 1.005 kJ/(kg·K)、"
            "λ = 0.0283 W/(m·K)、μ = 1.96×10⁻⁵ Pa·s，故 Pr = Cpμ/λ = 0.696，与报告一致。",
            "与报告表 5 对照（加强管第 3 组 Δp = 0.68 kPa）：V = 19.02 m³/h、W = 5.60 g/s、"
            "Q = 271.9 W、α = 112.5 W/(m²·℃)、u = 23.28 m/s、Nu = 75.5、Re = 23924，"
            "报告为 19.02 / 5.602 / 271.9 / 112.48 / 23.28 / 75.52 / 23924，逐项一致，"
            "差别仅在报告表格的末位舍入。",
            "与报告表 7 对照（普通管第 3 组 Δp = 1.22 kPa）：V = 25.93 m³/h、W = 7.63 g/s、"
            "K₀ = 18.9 W/(m²·K)，报告为 25.93 / 7.63 / 18.87，一致；"
            "普通管表 7 的 V 是先把孔板流量按进气温度密度 1.165 kg/m³ 算成 V_t1，"
            "再按 V = V_t1(273.15+t)/(273.15+t₁) 换算到平均温度，本模块照此实现。",
            "报告正文写 S₁ = 0.0754 m²（相当于 d₁ = 0.02 m），但由报告 α 反算实际用的是 0.07163 m²"
            "（d₁ = 0.019 m）。本模块按 d₁ = 0.019 计算；若把 d₁ 改成 0.02，α 会偏低约 5%（如 112.5 → 106.9）。",
            "加强管在第 3 组给的是 α 的计算举例，普通管只给 K₀（以 6 根管的外表面积 S₂ 为基准）；"
            "两管的 α、Nu 均按报告公式 α = Q/(S₁·Δtm)、Nu = αd₁/λ 计算，保证同一基准可比。",
            "实验数据说明：本模块用报告表 3/表 4 的原始数据（普通管 Δp 0.56~1.90 kPa）；"
            "「实验4数据处理.xlsx」里是另一组数据（Δp 0.64~2.11 kPa，且用 d₃ = 0.022 m 的 S₀ = 0.0829 m² 算 K₀），"
            "结果 α 偏小、K₀ 偏大，不要与本页数值混用。",
            "拟合关联式形如 Nu = A·Re^m（报告式 17/18）；若按 Nu/Pr^0.4 = A′·Re^m 的写法，"
            f"系数应为 A′ = A/Pr^0.4 = {fit_e['A'] / 0.696 ** 0.4:.5g}（加强管）。",
        ],
        "warnings": warnings,
    }
