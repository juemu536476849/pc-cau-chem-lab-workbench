# -*- coding: utf-8 -*-
"""B2 循环伏安法测定电极反应：峰电流–扫描速率关系（ip ∝ √v）与抗坏血酸工作曲线。

体系：[Fe(CN)6]³⁻/[Fe(CN)6]⁴⁻，2 mol/L KNO₃ 支持电解质，玻碳电极 / 铂丝 / 饱和甘汞电极。
原始记录只有峰电流，没有峰电位，故不计算 ΔEp（见 warnings）。
"""
import math

from ..core import num, linfit, line_y

# 峰电流随扫描速率变化（xlsx Sheet1：两平行样，单位 µA；负号为阴极峰 ipa，正号为阳极峰 ipc）
CV = [
    [0.005, -1.326753, -1.310078, 1.596711, 1.572194],
    [0.010, -1.463163, -1.455721, 1.957940, 1.949728],
    [0.020, -1.649636, -1.626165, 2.638836, 2.633857],
    [0.050, -1.930412, -1.885159, 3.855735, 3.824696],
]

# 抗坏血酸工作曲线（xlsx Sheet2：c/(mol/L)、两平行峰电流 µA）；最后一行的 c 为空，即未知样
AA = [
    [0.0002, -0.5189909, -0.506593],
    [0.0003, -1.467044, -1.223471],
    [0.0004, -1.972312, -1.771123],
    [0.0005, -2.606543, -2.463536],
    [0.0006, -3.161857, -2.962409],
    [None, -2.61942, -2.356286],
]

SPEC = {
    "id": "b2",
    "code": "B2",
    "group": "物化",
    "name": "循环伏安法测定电极反应",
    "subtitle": "峰电流–√v 判扩散控制 · 工作曲线测抗坏血酸",
    "tags": ["电化学", "循环伏安", "扩散控制", "工作曲线"],
    "desc": "以三角波电压扫描铁氰化钾体系，记录峰电流 ip。ip 与扫描速率平方根 √v 成正比说明电极反应受扩散控制"
            "（Randles–Ševčík）；再用峰电流对抗坏血酸浓度作工作曲线，反算未知样含量。",
    "method": [
        "① 在 2 mol/L KNO₃ 支持电解质中，对 1.00×10⁻² mol/L K₃Fe(CN)₆ 做 5–50 mV/s 的循环伏安扫描；",
        "② 读出每个扫描速率下的阴极峰电流 ipa 与阳极峰电流 ipc（各测两平行样取平均）；",
        "③ 作 ip–√v 图，线性关系说明扩散控制，斜率即 Randles–Ševčík 式中的比例常数；",
        "④ 改变抗坏血酸浓度测峰电流，作 ip–c 工作曲线（线性）；",
        "⑤ 未知样测峰电流后反算浓度，再按 c·V·稀释倍数·M 换算质量。",
    ],
    "tables": [
        {
            "key": "cv",
            "title": "峰电流–扫描速率",
            "note": "两平行样各一列（µA）。负号为阴极峰 ipa，正号为阳极峰 ipc；√v 由程序计算。",
            "columns": [
                {"key": "v", "label": "v / (V/s)", "type": "number"},
                {"key": "a1", "label": "ipa① / µA", "type": "number"},
                {"key": "a2", "label": "ipa② / µA", "type": "number"},
                {"key": "c1", "label": "ipc① / µA", "type": "number"},
                {"key": "c2", "label": "ipc② / µA", "type": "number"},
            ],
            "rows": CV,
        },
        {
            "key": "aa",
            "title": "抗坏血酸工作曲线",
            "note": "前 5 行为标准系列（c 与两平行峰电流）；最后一行 c 留空表示未知样，只填峰电流。",
            "columns": [
                {"key": "c", "label": "c / (mol/L)", "type": "number"},
                {"key": "i1", "label": "ip① / µA", "type": "number"},
                {"key": "i2", "label": "ip② / µA", "type": "number"},
            ],
            "rows": AA,
        },
    ],
    "params": [
        {"key": "mode", "label": "平行样取值", "type": "select", "default": "mean",
         "options": [{"value": "mean", "label": "两平行平均"}, {"value": "r1", "label": "只取第 1 次"},
                     {"value": "r2", "label": "只取第 2 次"}],
         "hint": "与处理表一致时选“两平行平均”"},
        {"key": "vol", "label": "取样体积 / L", "type": "number", "default": 0.1, "step": 0.01,
         "hint": "未知样定容体积，处理表按 100 mL 计算"},
        {"key": "dil", "label": "稀释倍数", "type": "number", "default": 10, "step": 1,
         "hint": "测定液由原液稀释而来时填稀释倍数（处理表乘 10）"},
        {"key": "mm", "label": "摩尔质量 / (g/mol)", "type": "number", "default": 176.12, "step": 0.01,
         "hint": "抗坏血酸 C₆H₈O₆ = 176.12 g/mol"},
    ],
}


def _pick(v1, v2, mode):
    if v1 is not None and v2 is not None:
        if mode == "r1":
            return v1
        if mode == "r2":
            return v2
        return (v1 + v2) / 2.0
    return v1 if v1 is not None else v2


def run(data):
    tb = data.get("tables") or {}
    cv_rows = tb.get("cv") or []
    aa_rows = tb.get("aa") or []
    p = data.get("params") or {}
    mode = str(p.get("mode") or "mean")
    vol = num(p.get("vol"), 0.1)
    dil = num(p.get("dil"), 10.0)
    mm = num(p.get("mm"), 176.12)
    if vol <= 0 or mm <= 0:
        raise ValueError("取样体积与摩尔质量必须大于 0")
    if dil <= 0:
        raise ValueError("稀释倍数必须大于 0（未稀释填 1）")

    # ---------- 峰电流–√v ----------
    vv, sv, ipa, ipc = [], [], [], []
    for r in cv_rows:
        if len(r) < 5:
            continue
        v = num(r[0])
        a = _pick(num(r[1]), num(r[2]), mode)
        c = _pick(num(r[3]), num(r[4]), mode)
        if v is None or a is None or c is None:
            continue
        if v <= 0:
            raise ValueError(f"扫描速率 v = {v:g} 不是正数：√v 无定义，请检查第一张表第 1 列")
        vv.append(v)
        sv.append(math.sqrt(v))
        ipa.append(a)
        ipc.append(c)
    if len(vv) < 3:
        raise ValueError("峰电流表至少需要 3 个不同扫描速率：请检查第一张表")

    fa = linfit(sv, ipa)
    fc = linfit(sv, ipc)
    vmax = max(vv)
    imax_a = ipa[vv.index(vmax)]
    imax_c = ipc[vv.index(vmax)]
    ratio = abs(imax_a / imax_c) if imax_c else float("nan")

    # ---------- 抗坏血酸工作曲线 ----------
    cs, ips, unk_ip = [], [], None
    for r in aa_rows:
        if len(r) < 2:
            continue
        c = num(r[0])
        i = _pick(num(r[1]), num(r[2]) if len(r) > 2 else None, mode)
        if i is None:
            continue
        if c is None or c <= 0:
            if unk_ip is None:
                unk_ip = i
            continue
        cs.append(c)
        ips.append(i)
    if len(cs) < 3:
        raise ValueError("抗坏血酸标准系列至少需要 3 个浓度点：请检查第二张表的 c 列")
    if unk_ip is None:
        raise ValueError("第二张表缺少未知样：把未知样那一行的 c 留空、只填峰电流")

    fcal = linfit(cs, ips)
    if abs(fcal["slope"]) < 1e-12:
        raise ValueError("工作曲线斜率接近 0：峰电流与浓度无线性关系，请检查数据是否填反")
    c_unk = (unk_ip - fcal["intercept"]) / fcal["slope"]
    if c_unk <= 0:
        raise ValueError(f"反算浓度 c = {c_unk:.3g} ≤ 0：未知样峰电流可能超出工作曲线范围")
    c_orig = c_unk * dil
    mass = c_orig * vol * mm

    # ---------- 图表 ----------
    x0, x1 = min(sv), max(sv)
    chart1 = {
        "title": "峰电流–扫描速率平方根（铁氰化钾）",
        "xlabel": "√v / (V/s)^0.5", "ylabel": "ip / µA",
        "series": [
            {"name": "ipa（阴极峰）", "type": "scatter", "points": [[x, y] for x, y in zip(sv, ipa)]},
            {"name": "ipc（阳极峰）", "type": "scatter", "points": [[x, y] for x, y in zip(sv, ipc)]},
            {"name": f"ipa 拟合  k={fa['slope']:.3g}", "type": "line", "color": "#2f6df6",
             "points": [[x0, line_y(fa, x0)], [x1, line_y(fa, x1)]]},
            {"name": f"ipc 拟合  k={fc['slope']:.3g}", "type": "line", "color": "#e5533d",
             "points": [[x0, line_y(fc, x0)], [x1, line_y(fc, x1)]]},
        ],
        "annotations": True,
        "xrange": [x0 - 0.02, x1 + 0.02],
    }

    c0, c1 = min(cs), max(cs)
    chart2 = {
        "title": "峰电流–抗坏血酸浓度工作曲线",
        "xlabel": "c / (mol/L)", "ylabel": "ip / µA",
        "series": [
            {"name": "标准系列", "type": "scatter", "points": [[x, y] for x, y in zip(cs, ips)]},
            {"name": f"ip = {fcal['slope']:.4g}·c + {fcal['intercept']:.4g}", "type": "line",
             "color": "#2f6df6", "points": [[c0, line_y(fcal, c0)], [c1, line_y(fcal, c1)]]},
        ],
        "points": [{"x": c_unk, "y": unk_ip, "label": f"未知样 c={c_unk:.3g} mol/L"}],
        "vlines": [{"x": c_unk, "label": "未知样浓度"}],
        "hlines": [{"y": unk_ip, "label": "未知样峰电流"}],
        "annotations": True,
    }

    # ---------- 表 ----------
    t1 = []
    for i, v in enumerate(vv):
        t1.append([v, round(sv[i], 5), round(ipa[i], 4), round(ipc[i], 4),
                   round(abs(ipa[i] / ipc[i]), 3) if ipc[i] else "—",
                   round(ipa[i] / sv[i], 3), round(ipc[i] / sv[i], 3)])
    t2 = []
    for c, i in zip(cs, ips):
        fit_i = line_y(fcal, c)
        t2.append([c, round(i, 4), round(fit_i, 4), round(i - fit_i, 4)])
    t2.append(["未知样", round(unk_ip, 4), round(line_y(fcal, c_unk), 4), "—"])

    warnings = [
        "原始记录只有峰电流、没有峰电位，因此未计算 ΔEp 与可逆性判据（25 ℃ 时理论 ΔEp ≈ 59/n mV）；"
        "若要判定体系可逆性，需在第一张表补 Epa、Epc 两列。",
    ]
    if abs(ratio - 1) > 0.15:
        warnings.append(f"最大扫描速率下 |ipa/ipc| = {ratio:.2f}，明显偏离 1，说明该体系在玻碳电极上不是理想可逆过程"
                        f"（或两次峰电流的读法不一致），不能直接用 ipa/ipc 判断可逆性。")
    if abs(fcal["r2"]) < 0.995:
        warnings.append(f"抗坏血酸工作曲线 r² = {fcal['r2']:.4f}，线性一般，可检查哪个标准点离群。")
    if abs(fa["r2"]) < 0.98 or abs(fc["r2"]) < 0.98:
        warnings.append(f"ip–√v 拟合 r²（ipa {fa['r2']:.4f} / ipc {fc['r2']:.4f}）偏低，"
                        f"可能受电容电流或电极表面状态影响。")

    return {
        "kpis": [
            {"label": "ipa", "value": round(imax_a, 4), "unit": "µA", "digits": 4,
             "hint": f"v = {vmax:g} V/s 的阴极峰电流"},
            {"label": "ipc", "value": round(imax_c, 4), "unit": "µA", "digits": 4,
             "hint": f"v = {vmax:g} V/s 的阳极峰电流"},
            {"label": "|ipa/ipc|", "value": round(ratio, 3), "digits": 3,
             "hint": "理想可逆体系应为 1"},
            {"label": "ipc–√v 斜率", "value": round(fc["slope"], 3), "unit": "µA/(V/s)^0.5",
             "digits": 3, "hint": f"r² = {fc['r2']:.4f}；ipa 斜率 {fa['slope']:.3f}"},
            {"label": "未知样 c", "value": round(c_unk, 6), "unit": "mol/L", "digits": 6,
             "hint": f"原液 c = {c_orig:.3g} mol/L，{vol * 1000:g} mL 中含 {mass:.4f} g"},
        ],
        "charts": [chart1, chart2],
        "tables": [
            {"title": "峰电流与扫描速率",
             "columns": ["v / (V/s)", "√v / (V/s)^0.5", "ipa / µA", "ipc / µA", "|ipa/ipc|",
                         "ipa/√v", "ipc/√v"],
             "rows": t1},
            {"title": "抗坏血酸工作曲线", "columns": ["c / (mol/L)", "ip / µA", "拟合 ip / µA", "残差 / µA"],
             "rows": t2},
        ],
        "notes": [
            "体系为 [Fe(CN)6]³⁻/[Fe(CN)6]⁴⁻，φ° = 0.36 V，2 mol/L KNO₃ 作支持电解质，玻碳电极 / 铂丝 / 饱和甘汞电极"
            "（据参考资料 B2 讲义）。",
            "ip 与 √v 成正比说明电极反应由溶液中反应物向电极表面的扩散控制（Randles–Ševčík：ip = 2.69×10⁵·n^1.5·A·D^0.5·c·v^0.5），"
            "若 ip–v 成正比则为吸附控制；本组 ipc 斜率明显大于 ipa，说明两峰受扩散控制的程度不同。",
            "处理表反算：未知样峰电流 −2.488 µA，代入 I = −6.29×10⁻³·c + 6.50×10⁻⁷（A）得 c = 4.99×10⁻⁴ mol/L，"
            "再乘 100 mL × 10 倍稀释 × 176.12 g/mol 得 0.0879 g；本模块结果与之相差 < 1%。",
            "峰电流符号沿用原始记录：ipa 记负、ipc 记正（扫描方向与工作站的电流方向约定相关），比值取绝对值。",
        ],
        "warnings": warnings,
    }
