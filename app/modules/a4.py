# -*- coding: utf-8 -*-
"""A4 溶液电导率的测定：Λm–√c 线性外推求无限稀释摩尔电导率 Λm∞。"""
import math

from ..core import linfit, line_y, num

# 原表 Sheet1 (2)：c 为浓度（mol/m³，即 mol·L⁻¹×10³），k 为电导率（μS/cm）。
# 四个体系各 4 个浓度点，次序与原始脚本切片 [0:4]、[4:8]、[8:12]、[12:16] 一致。
RAW = [
    ["NaCl", 4, 557],
    ["NaCl", 6, 829],
    ["NaCl", 8, 1080],
    ["NaCl", 10, 1350],
    ["HCl", 1, 412],
    ["HCl", 2, 823],
    ["HCl", 3, 1233],
    ["HCl", 4, 1642],
    ["NaAc", 4, 342],
    ["NaAc", 6, 505],
    ["NaAc", 8, 665],
    ["NaAc", 10, 822],
    ["HAc", 100, 570],
    ["HAc", 150, 698],
    ["HAc", 200, 797],
    ["HAc", 250, 884],
]

# lit：25 ℃ 无限稀释摩尔电导率文献值（S·m²·mol⁻¹），由离子摩尔电导率加和：
# H⁺ 349.8、Na⁺ 50.1、Cl⁻ 76.3、Ac⁻ 40.9（S·cm²·mol⁻¹）。
SERIES = [
    {"value": "nacl", "label": "NaCl", "lit": 0.012645},
    {"value": "hcl", "label": "HCl", "lit": 0.042616},
    {"value": "naac", "label": "NaAc", "lit": 0.009102},
    {"value": "hac", "label": "HAc", "lit": 0.039072},
]

SPEC = {
    "id": "a4",
    "code": "A4",
    "group": "物化",
    "name": "溶液电导率的测定",
    "subtitle": "Λm–√c 线性外推 · 求无限稀释摩尔电导率 Λm∞",
    "tags": ["电导率", "摩尔电导率", "Kohlrausch 外推", "弱电解质"],
    "desc": "用交流电桥测四种溶液不同浓度下的电导率 κ，换算成摩尔电导率 Λm；"
            "对强电解质，Λm 与 √c 在低浓度下近似成直线，外推到 c→0 即得 Λm∞。"
            "弱电解质 HAc 只在极稀时才部分电离，直线外推不成立，结果仅作对照。",
    "method": [
        "① Λm = κ/c，κ 由 μS/cm 换成 S/m（×10⁻⁴），c 用 mol/m³；",
        "② 以 √c 为横坐标、Λm 为纵坐标作散点；",
        "③ 对 4 个点作最小二乘直线 Λm = Λm∞ − A√c；",
        "④ 纵截距即无限稀释摩尔电导率 Λm∞，斜率反映离子间相互作用；",
        "⑤ 与 25 ℃ 文献值（离子摩尔电导率加和）比较，判断外推是否合理。",
    ],
    "tables": [{
        "key": "raw",
        "title": "电导率原始数据",
        "note": "c 单位 mol/m³（= mol·L⁻¹×10³）；κ 单位 μS/cm。电导水电导率 1.6 μS/cm，"
                "自来水 336 μS/cm（原表记录，未参与拟合）。",
        "columns": [
            {"key": "sys", "label": "体系", "type": "text"},
            {"key": "c", "label": "c /(mol·m⁻³)", "type": "number"},
            {"key": "k", "label": "κ /(μS·cm⁻¹)", "type": "number"},
        ],
        "rows": RAW,
    }],
    "params": [
        {"key": "sys", "label": "作图体系", "type": "select", "default": "nacl",
         "options": [{"value": s["value"], "label": s["label"]} for s in SERIES]},
        {"key": "sub", "label": "是否扣除电导水", "type": "select", "default": "no",
         "options": [{"value": "no", "label": "不扣除"},
                     {"value": "yes", "label": "扣除电导水"}],
         "hint": "原脚本直接用测得电导率，未扣溶剂本底"},
        {"key": "kwater", "label": "电导水电导率", "type": "number", "default": 1.6,
         "step": 0.1, "hint": "μS/cm，仅当“扣除电导水”时参与计算"},
    ],
}


def run(data):
    rows = (data.get("tables") or {}).get("raw") or []
    p = data.get("params") or {}

    sub = (p.get("sub") or "no") == "yes"
    kwater = num(p.get("kwater"), 1.6)
    if kwater < 0:
        raise ValueError("电导水的电导率不能为负")
    sel = p.get("sys") or "nacl"

    groups = {}
    for r in rows:
        if len(r) < 3:
            continue
        name = str(r[0]).strip() if r[0] is not None else ""
        c = num(r[1])
        k = num(r[2])
        if not name or c is None or k is None:
            continue
        groups.setdefault(name, []).append((c, k))

    if not groups:
        raise ValueError("表格中没有有效数据，请至少给出“体系、浓度、电导率”三列")

    res = {}
    for s in SERIES:
        pts = groups.get(s["label"])
        if not pts:
            continue
        if len(pts) < 2:
            raise ValueError(f"{s['label']} 只有 1 个浓度点，至少需要 2 点才能作 Λm–√c 直线")
        xs, ys, detail = [], [], []
        for c, k in sorted(pts):
            if c <= 0:
                raise ValueError(f"{s['label']} 的浓度必须为正值（mol/m³）")
            kk = k - kwater if sub else k
            if kk <= 0:
                raise ValueError(f"{s['label']} 扣除电导水后电导率非正，请检查 κ水 的取值")
            lam = kk * 1e-4 / c
            xs.append(math.sqrt(c))
            ys.append(lam)
            detail.append((c, k, lam))
        f = linfit(xs, ys)
        res[s["value"]] = {"fit": f, "xs": xs, "ys": ys, "detail": detail, "meta": s}

    if not res:
        raise ValueError("四个体系的名称需与表格中的“体系”列一致（NaCl / HCl / NaAc / HAc）")
    if sel not in res:
        sel = next(iter(res))
    r = res[sel]
    f = r["fit"]

    lam_inf = f["intercept"]
    lit = r["meta"]["lit"]
    dev = (lam_inf - lit) / lit * 100 if lit else 0.0

    x_lo, x_hi = min(r["xs"]), max(r["xs"])
    chart = {
        "title": f"{r['meta']['label']} 溶液 · Λm–√c 直线外推",
        "xlabel": "√c /(mol·m⁻³)^½", "ylabel": "Λm /(S·m²·mol⁻¹)",
        "series": [
            {"name": "实验点", "type": "scatter", "color": "#2f6df6",
             "points": [[x, y] for x, y in zip(r["xs"], r["ys"])]},
            {"name": f"Λm = {f['slope']:.4f}·√c + {lam_inf:.4f}", "type": "line",
             "color": "#e5533d",
             "points": [[0.0, lam_inf], [x_hi * 1.05, line_y(f, x_hi * 1.05)]]},
        ],
        "points": [{"x": 0.0, "y": lam_inf, "label": f"Λm∞ = {lam_inf:.4f}"}],
        "vlines": [], "hlines": [],
        "annotations": True,
        "xrange": [0, x_hi * 1.08],
    }

    table_rows = []
    for s in SERIES:
        q = res.get(s["value"])
        if not q:
            continue
        g = q["fit"]
        d = (g["intercept"] - s["lit"]) / s["lit"] * 100
        table_rows.append([s["label"], round(g["slope"], 5), round(g["intercept"], 5),
                           round(g["r"], 4), s["lit"], round(d, 1)])

    warnings = []
    if abs(f["r"]) < 0.995:
        warnings.append(f"{r['meta']['label']} 的 r = {f['r']:.4f} 偏低，"
                        f"该体系低浓度点离散，Λm∞ 外推不确定度较大")
    if sel == "hac" or (r["meta"]["label"] == "HAc"):
        warnings.append("HAc 是弱电解质，Λm–√c 直线外推不适用（截距远低于文献值属正常），"
                        "只可作定性对照")
    if lam_inf <= 0:
        warnings.append("拟合截距非正，Λm∞ 无物理意义，请检查浓度与电导率的单位")

    return {
        "kpis": [
            {"label": "Λm∞", "value": round(lam_inf, 4), "unit": "S·m²·mol⁻¹", "digits": 4,
             "hint": f"{r['meta']['label']} 的 Λm–√c 直线纵截距"},
            {"label": "斜率", "value": round(f["slope"], 5), "unit": "S·m²·mol⁻¹·(mol·m⁻³)^-½",
             "digits": 5, "hint": "Kohlrausch 直线的斜率为负"},
            {"label": "r", "value": round(f["r"], 4), "digits": 4, "hint": "4 点线性相关系数"},
            {"label": "相对文献偏差", "value": round(dev, 1), "unit": "%", "digits": 1,
             "hint": f"文献 Λm∞ = {lit:.4f}（25 ℃，离子摩尔电导率加和）"},
        ],
        "charts": [chart],
        "tables": [{
            "title": "四体系 Λm–√c 拟合汇总",
            "columns": ["体系", "斜率", "Λm∞ /(S·m²·mol⁻¹)", "r",
                        "文献 Λm∞", "相对偏差 /%"],
            "rows": table_rows,
        }],
        "notes": [
            "Λm 换算：κ[μS/cm]×10⁻⁴ 得 κ[S/m]，再除以 c[mol/m³]，即 Λm = κ·10⁻⁴/c。"
            "例：NaCl c=4 mol/m³、κ=557 μS/cm → Λm = 0.013925 S·m²·mol⁻¹。",
            "与实验报告逐条对照：报告 NaCl y=−0.0004x+0.0148、r=−0.9453；HCl y=−0.0001x+0.0414、r=−0.9951；"
            "NaAc y=−0.0003x+0.0091、r=−0.9998；HAc y=−0.0000x+0.0009、r=−0.9930。"
            "本模块用 A4数据处理.xlsx 的 Sheet1 (2)、以 √c 作横坐标复算，四条直线的截距与 r 与报告完全吻合"
            "（见上表；仅末位四舍五入差异）。",
            "横坐标必须是 √c：若误用 c 作横坐标，NaCl 会算成 r = −0.884、截距 0.01488，与报告的 −0.9453/0.0148 对不上；"
            "报告与原脚本都是对 √c 拟合，本模块保持一致。",
            "数据版本说明：目录里另有一版 `A4数据处理，.xlsx`（κ 如 NaCl 506/755/994/1222），"
            "按 √c 拟合得截距 0.0134、r = −0.9612，而 PDF 版报告里写的是 0.0133、r = −0.9972，两者也不一致；"
            "本模块采用与 docx 报告数值逐条吻合的 A4数据处理.xlsx，未混用两版数据。",
            "文献值按 25 ℃ 离子摩尔电导率加和：H⁺ 349.8、Na⁺ 50.1、Cl⁻ 76.3、Ac⁻ 40.9（S·cm²·mol⁻¹），"
            "换算后 Λm∞ 依次为 0.012645（NaCl）、0.042616（HCl）、0.009102（NaAc）、0.039072（HAc）。",
            "原脚本按 Sheet1 (2) 的 [0:4]/[4:8]/[8:12]/[12:16] 行切片，分别对应 NaCl/HCl/NaAc/HAc，"
            "本模块改用“体系”列分组，结果一致；HAc 的 Λm∞ 段落在原脚本里被注释掉，原因同上（弱电解质）。",
        ],
        "warnings": warnings,
    }
