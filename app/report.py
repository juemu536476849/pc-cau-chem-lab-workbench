# -*- coding: utf-8 -*-
"""把一次计算结果排成 Word 实验报告（python-docx）。

输入：spec（模块 SPEC）、data（tables/params）、result（run() 的返回）、
      images（[{"title": 图题, "png": PNG 字节}]）。
输出：bytes，即 .docx 文件内容。

文字里的上下标：`_{}` / `^{}` 记号（模块里的 Unicode 上下标已由 app.text 统一转换）
渲染成 Word 真正的下标/上标；`$...$` 行内公式、`$$...$$` 独立公式渲染成 OMML 公式对象。
"""

import io
import time

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app import text as T

INK = RGBColor(0x1F, 0x29, 0x37)
MUTED = RGBColor(0x6B, 0x72, 0x80)

LATIN = "Times New Roman"
CJK = "宋体"


def _set_font(run, name=CJK, size=None, bold=None, color=None):
    """西文用 Times New Roman，中文用宋体（Word 里分别走 ascii 与 eastAsia）。"""
    run.font.name = LATIN
    rf = run._element.rPr.rFonts
    rf.set(qn("w:ascii"), LATIN)
    rf.set(qn("w:hAnsi"), LATIN)
    rf.set(qn("w:eastAsia"), CJK)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def _para(doc, text="", size=10.5, bold=False, color=INK, align=None,
          space_before=0, space_after=4, indent=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.45
    if indent:
        pf.first_line_indent = Pt(size * 2)
    setter = lambda r: _set_font(r, size=size, bold=bold, color=color)  # noqa: E731
    T.add_rich(p, str(text), font_setter=setter)
    return p


def _formula(doc, tex, size=11):
    """独立公式：居中 OMML，前后留一点空隙。"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(4)
    try:
        p._p.append(T.omml(tex))
    except Exception:
        r = p.add_run(tex)
        _set_font(r, size=size)
    return p


_SEQ = ["一", "二", "三", "四", "五", "六", "七", "八"]


def _section(doc, text, idx):
    """带中文序号的小节标题，序号按实际出现顺序编号。"""
    return _heading(doc, "%s、%s" % (_SEQ[idx], text))


def _heading(doc, text, size=12, space_before=10, space_after=4):
    p = _para(doc, text, size=size, bold=True, color=INK,
              space_before=space_before, space_after=space_after)
    p.paragraph_format.keep_with_next = True
    return p


def _table(doc, columns, rows, widths=None, font_size=9.5):
    cols = [str(c) for c in columns]
    n = max(1, len(cols))
    t = doc.add_table(rows=1, cols=n)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    def fill(cell, txt, bold=False):
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        T.add_rich(p, str(txt), font_setter=lambda r: _set_font(r, size=font_size, bold=bold))

    for i, c in enumerate(cols):
        fill(t.rows[0].cells[i], c, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i in range(n):
            v = row[i] if i < len(row) else ""
            fill(cells[i], "" if v is None else v)

    # 行不跨页断开（cantSplit 必须排在 tblHeader 之前，符合 OOXML 顺序）
    for row in t.rows:
        rp = row._tr.get_or_add_trPr()
        el = OxmlElement("w:cantSplit")
        el.set(qn("w:val"), "true")
        rp.append(el)
    # 表头行跨页重复
    hdr_pr = t.rows[0]._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    hdr_pr.append(el)

    if widths:
        for i, w in enumerate(widths[:n]):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    return t


def _fmt_value(kpi):
    """把 KPI 数值按 digits 格式化，保留有效信息。"""
    v = kpi.get("value")
    if isinstance(v, str):
        return v
    try:
        num = float(v)
    except Exception:
        return str(v)
    digits = kpi.get("digits")
    if isinstance(digits, int) and digits >= 0:
        return f"{num:.{digits}f}"
    return f"{num:.4g}"


def build(spec, data, result, images=None, note=True):
    images = images or []
    doc = Document()

    # 页面：A4，左右 2.4 cm
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.4)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)

    style = doc.styles["Normal"]
    style.font.name = LATIN
    style.font.size = Pt(10.5)
    rf = style.element.rPr.rFonts
    rf.set(qn("w:ascii"), LATIN)
    rf.set(qn("w:hAnsi"), LATIN)
    rf.set(qn("w:eastAsia"), CJK)

    # 标题
    _para(doc, f"{spec.get('code', '')}　{spec.get('name', '')}", size=18, bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    sub = spec.get("subtitle", "")
    if sub:
        _para(doc, sub, size=10, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

    today = time.strftime("%Y 年 %m 月 %d 日")
    _para(doc, f"数据处理日期：{today}", size=9, color=MUTED,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    # 一、实验原理与数据处理
    n = 0
    desc = (spec.get("desc") or "").strip()
    method = spec.get("method") or []
    formulas = spec.get("formulas") or []
    if desc or method or formulas:
        _section(doc, "实验原理与数据处理", n); n += 1
        if desc:
            _para(doc, desc, size=10, indent=True, space_after=4)
        for i, m in enumerate(method, 1):
            _para(doc, str(m), size=10, space_after=2)
        for f in formulas:
            _formula(doc, f)
        if formulas:
            _para(doc, "", size=5, space_after=2)

    kpis = result.get("kpis") or []
    if kpis:
        _section(doc, "主要结果", n); n += 1
        rows = [[k.get("label", ""), _fmt_value(k), k.get("unit", "") or "—"] for k in kpis]
        _table(doc, ["指标", "结果", "单位"], rows, widths=[7.0, 5.6, 3.0])

    # 二、关系图
    if images:
        _section(doc, "关系图", n); n += 1
        for img in images:
            png = img.get("png")
            if not png:
                continue
            doc.add_picture(io.BytesIO(png), width=Cm(15.4))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.paragraphs[-1].paragraph_format.space_after = Pt(8)

    # 三、计算结果表
    rtables = result.get("tables") or []
    if rtables:
        _section(doc, "计算结果表", n); n += 1
        for t in rtables:
            _table(doc, t.get("columns", []), t.get("rows", []), font_size=9)
            _para(doc, "", size=6, space_before=0, space_after=2)

    # 四、原始数据
    in_tables = spec.get("tables") or []
    shown = 0
    for tdef in in_tables:
        rows = (data.get("tables") or {}).get(tdef.get("key")) or []
        cols = tdef.get("columns") or []
        if not rows and not cols:
            continue
        if shown == 0:
            _section(doc, "原始数据", n); n += 1
        shown += 1
        _table(doc, [c.get("label", c.get("key")) for c in cols], rows, font_size=8.5)
        _para(doc, "", size=6, space_before=0, space_after=2)

    # 五、计算参数
    params = spec.get("params") or []
    if params:
        _section(doc, "计算参数", n); n += 1
        vals = data.get("params") or {}
        rows = []
        for p in params:
            v = vals.get(p.get("key"), p.get("default"))
            label = p.get("label", p.get("key"))
            if isinstance(v, bool):
                v = "是" if v else "否"
            if p.get("type") == "select" and p.get("options"):
                for o in p["options"]:
                    if str(o.get("value")) == str(v):
                        v = o.get("label", v)
                        break
            rows.append([label, v, p.get("unit", "") or ""])
        _table(doc, ["参数", "取值", "单位"], rows, widths=[7.4, 5.6, 2.6])

    if note:
        warns = result.get("warnings") or []
        notes = result.get("notes") or []
        if warns or notes:
            _section(doc, "说明", n); n += 1
            for w in warns:
                _para(doc, "· " + str(w), size=9.5, color=RGBColor(0x9A, 0x5B, 0x00),
                      space_after=2)
            for item in notes:
                _para(doc, "· " + str(item), size=9.5, color=MUTED, space_after=2)

    # 样式表里残留的其他字体（如 Macro Text 的 Courier）也统一掉
    for st in doc.styles:
        try:
            rf = st.element.get_or_add_rPr().get_or_add_rFonts()
        except Exception:
            continue
        rf.set(qn("w:ascii"), LATIN)
        rf.set(qn("w:hAnsi"), LATIN)
        rf.set(qn("w:eastAsia"), CJK)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
