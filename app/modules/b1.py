# -*- coding: utf-8 -*-
"""B1 氧弹燃烧热：雷诺(Reynolds)温度校正求 ΔT → 水当量标定 → 萘的恒容/恒压燃烧热。

计算方法取自实验指导书（第二章 2-6 节）：
    (m/M)·Q_V + L·Q_L + (m_水·C_水 + C_计)·ΔT = 0
其中 Q_L = −290 J/m（引燃铁丝单位长度燃烧热），苯甲酸氧弹燃烧热 −26460 J/g。
"""
import math

from ..core import num, linfit, line_y, interp

# 温度–时间原始记录（xlsx：B1数据处理.xlsx Sheet1 苯甲酸 / Sheet2 萘，共 30 个时间点）
RAW = [
    [60, 20.638, 22.732],
    [120, 20.648, 22.738],
    [180, 20.660, 22.742],
    [240, 20.670, 22.744],
    [300, 20.682, 22.747],
    [315, 20.691, 22.749],
    [330, 20.776, 22.773],
    [345, 20.956, 22.842],
    [360, 21.171, 22.952],
    [375, 21.391, 23.072],
    [390, 21.593, 23.185],
    [405, 21.764, 23.378],
    [420, 21.909, 23.531],
    [435, 22.026, 23.674],
    [450, 22.124, 23.769],
    [465, 22.195, 23.857],
    [480, 22.254, 23.932],
    [495, 22.308, 23.987],
    [510, 22.349, 24.034],
    [525, 22.384, 24.073],
    [540, 22.419, 24.108],
    [555, 22.447, 24.140],
    [570, 22.473, 24.169],
    [585, 22.496, 24.194],
    [600, 22.515, 24.220],
    [660, 22.582, 24.308],
    [720, 22.629, 24.378],
    [780, 22.664, 24.437],
    [840, 22.691, 24.485],
    [900, 22.712, 24.522],
]

# 其它数据（实验报告“其它数据”表）：两列分别是苯甲酸、萘
AUX = [
    ["样品质量 / g", 1.0106, 0.6204],
    ["点火丝长度(点火前) / cm", 12.1, 12.5],
    ["点火丝长度(燃烧后) / cm", 4.3, 4.1],
    ["铁桶内水的质量 / g", 2685.0, 2675.0],
]

C_WATER = 4.184      # J/(g·K)
M_NAPH = 128.17      # g/mol，萘 C10H8
M_BENZ = 122.12      # g/mol，苯甲酸 C7H6O2
T0 = 298.15          # K
R_GAS = 8.314        # J/(mol·K)
H_NAPH_LIT = -5153.9  # kJ/mol，萘的恒压燃烧热文献值

SPEC = {
    "id": "b1",
    "code": "B1",
    "group": "物化",
    "name": "氧弹燃烧热",
    "subtitle": "雷诺温度校正 · 水当量标定 · 求摩尔燃烧热",
    "tags": ["热化学", "量热", "氧弹", "雷诺校正"],
    "desc": "先用已知燃烧热的苯甲酸标定量热计的水当量 W = m水·C水 + C计，再用同一台量热计测萘的温升。"
            "温度曲线的上升段与后期段分别外推到中间温度，得到扣除热交换后的真实 ΔT。",
    "method": [
        "① 每 15–60 s 读一次内筒水温，得到燃烧前后的温度–时间曲线；",
        "② 取前后原始温度的平均值 T_m = [T(t₁)+T(t₂)]/2，在最接近 T_m 的实测点 t_m 处作竖直线；",
        "③ 把前期直线 ab 与后期直线 cd 延长到该竖线，交点纵坐标差即 ΔT = EF（雷诺校正）；",
        "④ 由苯甲酸：W = (m₁·26460 + L₁·2.90) / ΔT₁，其中 L 为烧掉的铁丝长度（cm）；",
        "⑤ 由萘：Q_V = −(W·ΔT₂ + L₂·2.90)·M₂/m₂，再换算恒压燃烧热 Q_p = Q_V + Δn·RT（萘 Δn = −2）。",
    ],
    "tables": [
        {
            "key": "raw",
            "title": "温度–时间记录（苯甲酸 / 萘）",
            "note": "直接粘贴 Excel 三列即可。原始记录为 15–60 s 一个点，燃烧段温度突升；空白行自动跳过。",
            "columns": [
                {"key": "t", "label": "t / s", "type": "number"},
                {"key": "tb", "label": "T(苯甲酸) / ℃", "type": "number"},
                {"key": "tn", "label": "T(萘) / ℃", "type": "number"},
            ],
            "rows": RAW,
        },
        {
            "key": "aux",
            "title": "样品与量热计数据",
            "note": "两列分别为苯甲酸、萘。点火丝长度为点火前/燃烧后，差值即实际燃烧长度。",
            "columns": [
                {"key": "item", "label": "项目", "type": "text"},
                {"key": "ba", "label": "苯甲酸", "type": "number"},
                {"key": "na", "label": "萘", "type": "number"},
            ],
            "rows": AUX,
        },
    ],
    "params": [
        {"key": "t1", "label": "前期末点 t₁ / s", "type": "number", "default": 300, "step": 15,
         "hint": "燃烧前温度缓慢上升段的最后一个点（本组 300 s）"},
        {"key": "t2", "label": "后期起点 t₂ / s", "type": "number", "default": 660, "step": 15,
         "hint": "温度基本稳定、进入缓慢冷却段的第一个点（本组 660 s）"},
        {"key": "ql", "label": "点火丝燃烧热 / (J/cm)", "type": "number", "default": 2.90,
         "step": 0.01, "hint": "指导书给 −290 J/m，即 2.90 J/cm"},
        {"key": "hba", "label": "苯甲酸氧弹燃烧热 / (J/g)", "type": "number", "default": 26460,
         "step": 10, "hint": "指导书给 −26460 J·g⁻¹，用于标定水当量"},
    ],
}


def _cell(rows, i, j):
    if i < len(rows) and len(rows[i]) > j:
        return num(rows[i][j])
    return None


def _reynolds(ts, Ts, t1, t2):
    """雷诺校正：返回前期/后期拟合线与中间温度处的 ΔT。"""
    T1 = interp(t1, ts, Ts)
    T2 = interp(t2, ts, Ts)
    t_target = (T1 + T2) / 2.0
    idx = min(range(len(ts)), key=lambda i: abs(Ts[i] - t_target))
    tm = ts[idx]
    pre = [(t, T) for t, T in zip(ts, Ts) if t <= t1]
    post = [(t, T) for t, T in zip(ts, Ts) if t >= t2]
    if len(pre) < 2:
        raise ValueError(f"前期段点数不足：t₁ = {t1:g} s 之前至少要有 2 个数据点")
    if len(post) < 2:
        raise ValueError(f"后期段点数不足：t₂ = {t2:g} s 之后至少要有 2 个数据点")
    f1 = linfit([a for a, _ in pre], [b for _, b in pre])
    f2 = linfit([a for a, _ in post], [b for _, b in post])
    y1, y2 = line_y(f1, tm), line_y(f2, tm)
    return {"T1": T1, "T2": T2, "tm": tm, "t_target": t_target, "f1": f1, "f2": f2,
            "y1": y1, "y2": y2, "dT": y2 - y1, "ts": ts, "Ts": Ts}


def run(data):
    tb = data.get("tables") or {}
    rows = tb.get("raw") or []
    aux = tb.get("aux") or []
    p = data.get("params") or {}
    t1 = num(p.get("t1"), 300.0)
    t2 = num(p.get("t2"), 660.0)
    ql = num(p.get("ql"), 2.90)
    hba = num(p.get("hba"), 26460.0)
    if t1 >= t2:
        raise ValueError("前期末点 t₁ 必须小于后期起点 t₂")

    pairs = []
    for r in rows:
        if len(r) < 3:
            continue
        t, a, b = num(r[0]), num(r[1]), num(r[2])
        if t is None or a is None or b is None:
            continue
        pairs.append((t, a, b))
    if len(pairs) < 6:
        raise ValueError("数据不足：请检查第一张表的时间与两条温度列是否填全")
    pairs.sort(key=lambda q: q[0])
    ts = [q[0] for q in pairs]
    tba = [q[1] for q in pairs]
    tnaph = [q[2] for q in pairs]

    m1, m2 = _cell(aux, 0, 1), _cell(aux, 0, 2)
    la0, lb0 = _cell(aux, 1, 1), _cell(aux, 2, 1)   # 苯甲酸：点火前、燃烧后
    la1, lb1 = _cell(aux, 1, 2), _cell(aux, 2, 2)   # 萘
    w1, w2 = _cell(aux, 3, 1), _cell(aux, 3, 2)
    for name, v in (("苯甲酸质量", m1), ("萘质量", m2), ("苯甲酸点火丝长度", la0),
                    ("萘点火丝长度", la1), ("苯甲酸水量", w1), ("萘水量", w2)):
        if v is None:
            raise ValueError(f"第二张表缺少{name}：请按 4 行（质量/点火丝前/点火丝后/水量）×2 列填写")
    L1 = la0 - lb0
    L2 = la1 - lb1
    if L1 <= 0 or L2 <= 0:
        raise ValueError("点火丝燃烧后长度应小于点火前：请检查第二张表第 2、3 行的前后顺序")

    rba = _reynolds(ts, tba, t1, t2)
    rna = _reynolds(ts, tnaph, t1, t2)
    if rba["dT"] <= 0 or rna["dT"] <= 0:
        raise ValueError("ΔT ≤ 0：前期/后期段划分可能反了，请检查 t₁、t₂")

    q_wire1 = L1 * ql
    W = (m1 * hba + q_wire1) / rba["dT"]          # J/K，水当量
    W_water = w1 * C_WATER
    c_cal = W - W_water                            # J/K，仪器（氧弹+搅拌器+温度计）热容
    q_wire2 = L2 * ql
    qv = -(W * rna["dT"] + q_wire2) * M_NAPH / m2  # J/mol，恒容燃烧热（放热为负）
    dn = -2.0                                      # C10H8(s)+12O2 → 10CO2+4H2O(l)
    qp = qv / 1000.0 + dn * R_GAS * T0 / 1000.0     # kJ/mol，恒压燃烧热
    rel = (qp - H_NAPH_LIT) / H_NAPH_LIT * 100.0

    # ---------------- 图 ----------------
    def _chart(title, rr, ylabel):
        ts_, Ts_ = rr["ts"], rr["Ts"]
        tm = rr["tm"]
        f1, f2 = rr["f1"], rr["f2"]
        x0, x1 = ts_[0], ts_[-1]
        series = [
            {"name": "实测温度", "type": "scatter", "points": [[x, y] for x, y in zip(ts_, Ts_)]},
            {"name": "前期拟合", "type": "line", "color": "#e5533d",
             "points": [[x0, line_y(f1, x0)], [t1, line_y(f1, t1)]]},
            {"name": "前期外推", "type": "line", "color": "#e5533d", "dash": True,
             "points": [[t1, line_y(f1, t1)], [tm, line_y(f1, tm)]]},
            {"name": "后期拟合", "type": "line", "color": "#2f6df6",
             "points": [[t2, line_y(f2, t2)], [x1, line_y(f2, x1)]]},
            {"name": "后期外推", "type": "line", "color": "#2f6df6", "dash": True,
             "points": [[tm, line_y(f2, tm)], [t2, line_y(f2, t2)]]},
        ]
        return {
            "title": title, "xlabel": "t / s", "ylabel": ylabel, "series": series,
            "vlines": [{"x": tm, "label": f"t_m = {tm:g} s"}],
            "points": [{"x": tm, "y": (rr["y1"] + rr["y2"]) / 2,
                        "label": f"ΔT = {rr['dT']:.4f} K"}],
            "annotations": True,
            "xrange": [x0 - 40, x1 + 40],
        }

    chart1 = _chart("苯甲酸 · 温度–时间曲线与雷诺校正", rba, "T / ℃")
    chart2 = _chart("萘 · 温度–时间曲线与雷诺校正", rna, "T / ℃")

    t_reyn = [
        ["前期末点 t₁ / s", t1, t1],
        ["后期起点 t₂ / s", t2, t2],
        ["T(t₁) / ℃", round(rba["T1"], 3), round(rna["T1"], 3)],
        ["T(t₂) / ℃", round(rba["T2"], 3), round(rna["T2"], 3)],
        ["中间温度 T_m / ℃", round(rba["t_target"], 3), round(rna["t_target"], 3)],
        ["校正点 t_m / s", rba["tm"], rna["tm"]],
        ["前期斜率 / (K/s)", round(rba["f1"]["slope"], 6), round(rna["f1"]["slope"], 6)],
        ["前期 r", round(rba["f1"]["r"], 4), round(rna["f1"]["r"], 4)],
        ["后期斜率 / (K/s)", round(rba["f2"]["slope"], 6), round(rna["f2"]["slope"], 6)],
        ["后期 r", round(rba["f2"]["r"], 4), round(rna["f2"]["r"], 4)],
        ["前期线在 t_m 处 / ℃", round(rba["y1"], 3), round(rna["y1"], 3)],
        ["后期线在 t_m 处 / ℃", round(rba["y2"], 3), round(rna["y2"], 3)],
        ["ΔT / K", round(rba["dT"], 4), round(rna["dT"], 4)],
    ]

    t_q = [
        ["样品质量 m / g", m1, round(m2, 4)],
        ["点火丝燃烧长度 L / cm", round(L1, 2), round(L2, 2)],
        ["点火丝放热 L·Q_L / J", round(q_wire1, 2), round(q_wire2, 2)],
        ["水的质量 m_水 / g", w1, w2],
        ["水的热容 m_水·C_水 / (J/K)", round(W_water, 1), round(w2 * C_WATER, 1)],
        ["水当量 W / (J/K)", round(W, 1), "—"],
        ["仪器热容 C_计 / (J/K)", round(c_cal, 1), "—"],
        ["ΔT / K", round(rba["dT"], 4), round(rna["dT"], 4)],
        ["Q_V / (kJ/mol)", round(-hba * M_BENZ / 1000.0, 2), round(qv / 1000.0, 2)],
        ["Δn·RT / (kJ/mol)", "—", round(dn * R_GAS * T0 / 1000.0, 3)],
        ["Q_p / (kJ/mol)", "—", round(qp, 2)],
        ["文献值 / (kJ/mol)", "—", H_NAPH_LIT],
        ["相对误差 / %", "—", round(rel, 2)],
    ]

    warnings = []
    if c_cal / W > 0.2:
        warnings.append(f"水当量 W = {W / 1000:.2f} kJ/K，扣掉 {w1:g} g 水的 {W_water / 1000:.2f} kJ/K 后，"
                        f"仪器热容 C_计 = {c_cal / 1000:.2f} kJ/K（占 {c_cal / W * 100:.0f}%），明显偏大；"
                        f"常见氧弹量热计 C_计 只有 0.5–1.5 kJ/K，请复核铁桶内水量与样品质量。")
    if abs(rel) > 5:
        warnings.append(f"萘的恒压燃烧热 {qp:.1f} kJ/mol 与文献 {H_NAPH_LIT} kJ/mol 相差 {rel:+.1f}%，"
                        f"超出可接受范围：本组温度曲线的雷诺校正 ΔT 明显小于实测温升"
                        f"（{rna['dT']:.3f} K vs {max(tnaph) - min(tnaph):.3f} K），"
                        f"或样品未完全燃烧，建议复核 t₂ 的取点与样品是否燃尽。")
    warnings.append("实验报告 PDF 中“ΔT 表”把两条曲线的样品名写反了：报告标“苯甲酸”的 ΔT = 1.354 K 实际来自萘（22.732 ℃ 起）"
                    "那条曲线，标“萘”的 1.727 K 来自苯甲酸（20.638 ℃ 起）那条；本模块按报告图线与 xlsx 工作表标题"
                    "（Sheet1 苯甲酸 / Sheet2 萘）配对，故 ΔT 与报告表相反。")

    return {
        "kpis": [
            {"label": "ΔT(苯甲酸)", "value": round(rba["dT"], 4), "unit": "K", "digits": 4,
             "hint": f"t_m = {rba['tm']:g} s 处两线差（报告表记 1.727 K）"},
            {"label": "ΔT(萘)", "value": round(rna["dT"], 4), "unit": "K", "digits": 4,
             "hint": f"t_m = {rna['tm']:g} s 处两线差（报告表记 1.354 K）"},
            {"label": "水当量 W", "value": round(W / 1000.0, 3), "unit": "kJ/K", "digits": 3,
             "hint": "m水·C水 + C_计，由苯甲酸标定"},
            {"label": "ΔH_c(萘)", "value": round(qp, 1), "unit": "kJ/mol", "digits": 1,
             "hint": "恒压燃烧热 Q_p = Q_V + Δn·RT"},
            {"label": "相对误差", "value": round(rel, 1), "unit": "%", "digits": 1,
             "hint": f"相对文献值 {H_NAPH_LIT} kJ/mol"},
        ],
        "charts": [chart1, chart2],
        "tables": [
            {"title": "雷诺温度校正", "columns": ["项目", "苯甲酸", "萘"], "rows": t_reyn},
            {"title": "水当量与燃烧热计算", "columns": ["项目", "苯甲酸", "萘"], "rows": t_q},
        ],
        "notes": [
            "雷诺校正：在 T_m = [T(t₁)+T(t₂)]/2 对应的竖直线处，把前期（ab）与后期（cd）直线延长，"
            "两交点纵坐标差即扣除热交换后的真实温升 ΔT。",
            "量热方程 (m/M)·Q_V + L·Q_L + (m水·C水 + C计)·ΔT = 0，故 W = (m₁·26460 + L₁·Q_L)/ΔT₁；"
            "Q_L = 2.90 J/cm（指导书 −290 J/m）、苯甲酸 −26460 J/g 均来自实验指导书。",
            "复算对照：苯甲酸 ΔT = 1.748 K（报告表 1.727 K）、萘 ΔT = 1.350 K（报告表 1.354 K），"
            "差异来自报告用 Origin 手绘延长线，本模块用最小二乘，两者相差 < 1.3%。",
            "萘的 Δn = 10 − 12 = −2（C₁₀H₈(s) + 12O₂ → 10CO₂ + 4H₂O(l)），故 Q_p = Q_V − 4.96 kJ/mol。",
            "报告里没有给出最终的 Q_V / Q_p，本模块按同一套公式补全；若 W 与 C_计 不合理，"
            "优先怀疑第二张表的水量与点火丝长度。",
        ],
        "warnings": warnings,
    }
