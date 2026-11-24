# -*- coding: utf-8 -*-
"""物化 / 化工实验数据处理工作台 —— 本地 Flask 服务。"""
import base64
import io
import json
import os
import re
import socket
import subprocess
import sys
import time
import traceback
import webbrowser

from flask import Flask, jsonify, request, send_file, send_from_directory

from . import registry

# 预热数值库：这些库首次导入要 1–3 s，提前加载避免第一次点开实验时卡顿
try:
    import numpy  # noqa: F401
    import scipy.interpolate  # noqa: F401
    import scipy.optimize  # noqa: F401
    import scipy.stats  # noqa: F401
except Exception:  # 缺依赖时按需再报错
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "outputs")
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
os.makedirs(OUT, exist_ok=True)

app = Flask(__name__, static_folder=None)


@app.after_request
def _no_cache(resp):
    """本地单机工具：页面/脚本永远取最新，避免改完前端还看到旧界面。"""
    if not request.path.startswith("/api/material"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------- 静态页面
@app.route("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.route("/<path:fn>")
def static_files(fn):
    return send_from_directory(WEB, fn)


# ---------------------------------------------------------------- API
@app.route("/api/experiments")
def api_experiments():
    return jsonify([registry.public_spec(s) for s in registry.load_all().values()])


def _material_root(exp_id):
    spec = registry.get(exp_id)
    if not spec:
        return None
    code = spec.get("code", "")
    group_dir = "物化实验" if spec.get("group") == "物化" else "化工实验"
    root = os.path.join(DATA, group_dir)
    if not os.path.isdir(root):
        return None
    # 化工实验目录按两位编号命名：C1 → 01-流体阻力测定
    prefixes = [code + "-", code + "_"]
    m = re.match(r"^[A-Za-z]+(\d+)$", code or "")
    if m:
        prefixes.append("%02d-" % int(m.group(1)))
    for name in sorted(os.listdir(root)):
        if any(name.startswith(p) for p in prefixes):
            return os.path.join(root, name)
    return None


def _rel_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for f in filenames:
            if f.startswith("~$") or f.lower().endswith(".pyc"):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root).replace("\\", "/")
            out.append({"name": f, "rel": rel, "size": os.path.getsize(full)})
    out.sort(key=lambda x: (x["rel"].count("/"), x["rel"]))
    return out


@app.route("/api/materials")
def api_materials():
    exp_id = request.args.get("id", "")
    root = _material_root(exp_id)
    if not root:
        return jsonify({"files": [], "dir": ""})
    return jsonify({"files": _rel_files(root), "dir": os.path.basename(root)})


@app.route("/api/material")
def api_material():
    """按相对路径读取实验资料文件（预览 / 下载）。"""
    exp_id = request.args.get("id", "")
    rel = request.args.get("path", "")
    root = _material_root(exp_id)
    if not root:
        return "not found", 404
    full = os.path.realpath(os.path.join(root, rel))
    if not full.startswith(os.path.realpath(root) + os.sep) or not os.path.isfile(full):
        return "forbidden", 403
    inline = request.args.get("inline") == "1"
    return send_file(full, as_attachment=not inline, download_name=os.path.basename(full))


@app.route("/api/open-folder")
def api_open_folder():
    exp_id = request.args.get("id", "")
    root = _material_root(exp_id)
    if not root or not os.path.isdir(root):
        return jsonify({"ok": False, "msg": "未找到资料目录"})
    try:
        if sys.platform.startswith("win"):
            os.startfile(root)  # noqa: S606
        else:
            subprocess.Popen(["xdg-open", root])
        return jsonify({"ok": True, "dir": root})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


def _with_defaults(spec, params):
    """把 SPEC 里的参数默认值补进来：前端/接口只传改动项时也能算对。"""
    out = {p.get("key"): p.get("default") for p in (spec.get("params") or []) if p.get("key")}
    out.update(params or {})
    return out


@app.route("/api/run", methods=["POST"])
def api_run():
    payload = request.get_json(force=True, silent=True) or {}
    exp_id = payload.get("id", "")
    spec = registry.get(exp_id)
    if not spec:
        return jsonify({"ok": False, "error": f"未知实验：{exp_id}"}), 404
    data = {"tables": payload.get("tables") or {}, "params": _with_defaults(spec, payload.get("params"))}
    t0 = time.time()
    try:
        result = spec["_module"].run(data)
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}",
                        "trace": tb.splitlines()[-14:]})
    result = result or {}
    result["ok"] = True
    result["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
    result.setdefault("kpis", [])
    result.setdefault("charts", [])
    result.setdefault("tables", [])
    result.setdefault("notes", [])
    result.setdefault("warnings", [])
    from app.text import walk
    result = walk(result)
    return jsonify(result)


@app.route("/api/export", methods=["POST"])
def api_export():
    """把当前参数、数据与结果写入 outputs/*.xlsx。"""
    payload = request.get_json(force=True, silent=True) or {}
    exp_id = payload.get("id", "")
    spec = registry.get(exp_id)
    if not spec:
        return jsonify({"ok": False, "error": "未知实验"}), 404
    tables = payload.get("tables") or {}
    for t in spec.get("tables", []):
        if tables.get(t.get("key")) is None:
            tables[t["key"]] = [list(r) for r in (t.get("rows") or [])]
    data = {"tables": tables, "params": _with_defaults(spec, payload.get("params"))}
    try:
        result = spec["_module"].run(data)
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 400

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "结果"
    head_fill = PatternFill("solid", fgColor="1F3A5F")
    head_font = Font(color="FFFFFF", bold=True, size=11)

    def style_header(sheet, row=1):
        for c in sheet[row]:
            c.fill = head_fill
            c.font = head_font
            c.alignment = Alignment(horizontal="center", vertical="center")

    ws.append([spec.get("code", ""), spec.get("name", "")])
    ws["A1"].font = Font(bold=True, size=14)
    ws.merge_cells("A1:D1")
    ws.append([])
    ws.append(["关键结果", "数值", "单位", "说明"])
    style_header(ws, 3)
    for k in (result.get("kpis") or []):
        val = k.get("value")
        ws.append([k.get("label", ""), val, k.get("unit", ""), k.get("hint", "")])
    r0 = ws.max_row + 2
    for t in (result.get("tables") or []):
        ws.cell(row=r0, column=1, value=t.get("title", "结果表")).font = Font(bold=True, size=12)
        r0 += 1
        cols = t.get("columns", [])
        for j, c in enumerate(cols, 1):
            cell = ws.cell(row=r0, column=j, value=c)
            cell.fill = head_fill
            cell.font = head_font
            cell.alignment = Alignment(horizontal="center")
        r0 += 1
        for row in t.get("rows", []):
            for j, v in enumerate(row, 1):
                ws.cell(row=r0, column=j, value=v)
            r0 += 1
        r0 += 2
    for i, w in enumerate([26, 18, 12, 46], 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # 输入参数
    wp = wb.create_sheet("输入参数")
    wp.append(["参数", "取值"])
    style_header(wp)
    for p in spec.get("params", []):
        wp.append([p.get("label", p.get("key")), (data.get("params") or {}).get(p.get("key"), p.get("default"))])
    wp.column_dimensions["A"].width = 30
    wp.column_dimensions["B"].width = 20

    # 输入数据
    for tdef in spec.get("tables", []):
        key = tdef.get("key")
        rows = (data.get("tables") or {}).get(key) or []
        if not rows and not tdef.get("columns"):
            continue
        wt = wb.create_sheet("数据-" + str(tdef.get("title", key))[:20])
        wt.append([c.get("label", c.get("key")) for c in tdef.get("columns", [])])
        style_header(wt)
        for row in rows:
            wt.append([_cell_value(v) for v in row])
        wt.freeze_panes = "A2"

    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe = f"{spec.get('code', 'exp')}-{spec.get('name', '')}".replace("/", "_")
    fn = f"{safe}-{stamp}.xlsx"
    path = os.path.join(OUT, fn)
    wb.save(path)
    return jsonify({"ok": True, "file": fn, "path": path})


@app.route("/api/report-docx", methods=["POST"])
def api_report_docx():
    """生成 Word 版实验报告，直接以文件流返回（前端选择保存位置）。"""
    payload = request.get_json(force=True, silent=True) or {}
    spec = registry.get(payload.get("id", ""))
    if not spec:
        return jsonify({"ok": False, "error": "未知实验"}), 404

    tables = payload.get("tables") or {}
    for t in spec.get("tables", []):
        if tables.get(t.get("key")) is None:
            tables[t["key"]] = [list(r) for r in (t.get("rows") or [])]
    data = {"tables": tables, "params": _with_defaults(spec, payload.get("params"))}
    try:
        result = spec["_module"].run(data)
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 400

    images = []
    for img in payload.get("images") or []:
        b64 = img.get("png") or ""
        if not b64:
            continue
        if "," in b64[:64]:
            b64 = b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(b64)
        except Exception:
            continue
        if len(raw) > 256:
            images.append({"title": img.get("title", ""), "png": raw})

    from . import report

    try:
        blob = report.build(spec, data, result, images=images)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": f"生成报告失败：{type(e).__name__}: {e}"}), 500

    safe = f"{spec.get('code', 'exp')}-{spec.get('name', '')}".replace("/", "_")
    name = f"{safe}-实验报告.docx"
    return send_file(
        io.BytesIO(blob),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=name,
    )


def _cell_value(v):
    if isinstance(v, (int, float)) or v is None:
        return v
    try:
        if str(v).strip() == "":
            return None
        return float(v)
    except Exception:
        return v


# ---------------------------------------------------------------- 导入解析
# /api/import 专用工具：把上传的 Excel / CSV 尽量宽容地解析成二维表。
# 旧前端只认 ok/rows/name/shape，新增的 header/notes/dropped_index_col 都是附加字段。
_IMPORT_MAX_ROWS = 3000
_IMPORT_EXCEL_EXT = (".xlsx", ".xls", ".xlsm")
_IMPORT_INDEX_HEADER_RE = re.compile(r"^(序\s*号|编号|no\.?|#|id)$", re.IGNORECASE)


def _import_is_missing(v):
    """空值判断：None / NaN / NaT / pd.NA。常见类型先走快路径。"""
    if v is None:
        return True
    if isinstance(v, float):
        return v != v
    if isinstance(v, (int, str, bool)):
        return False
    try:
        import pandas as pd
        return bool(pd.isna(v))
    except Exception:
        return False


def _import_is_empty(v):
    """单元格是否算“空”：None/NaN 或纯空白字符串。"""
    if _import_is_missing(v):
        return True
    if isinstance(v, str):
        return not v.strip()
    return False


def _import_number(v):
    """把单元格转成 float；布尔、文本、空值返回 None（仅用于判断“像不像数字”）。"""
    if isinstance(v, bool) or _import_is_missing(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except Exception:
            return None
    return None


def _import_is_number(v):
    return _import_number(v) is not None


def _import_cell(v):
    """单元格 → JSON 安全值：空值 ""、浮点保留 8 位、日期时间转字符串。"""
    if _import_is_missing(v):
        return ""
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if v in (float("inf"), float("-inf")):
            return ""
        return round(v, 8)
    if isinstance(v, str):
        return v
    item = getattr(v, "item", None)  # numpy 标量
    if callable(item):
        try:
            return _import_cell(item())
        except Exception:
            pass
    import datetime
    if isinstance(v, datetime.datetime):
        return v.isoformat(sep=" ")
    if isinstance(v, (datetime.date, datetime.time)):
        return v.isoformat()
    return str(v)


def _import_decode_text(raw):
    """CSV 字节解码：先 utf-8-sig，再 gb18030；都失败给出可读错误。"""
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(
        "CSV 编码既不是 UTF-8 也不是 GBK，请用 Excel 另存为“CSV UTF-8”或 GBK 编码后重试"
    )


def _import_guess_csv_sep(text):
    """猜 CSV 分隔符。

    不能直接把 sep=None 交给 pandas：它的嗅探器在单列/中文文件上可能把 “.” 或数字
    当成分隔符且不报错，正是“导入后列错位”的根因。这里只在常见分隔符里嗅探，
    没有常见分隔符时默认单列；只有每行空白分列数一致且 ≥2 才按空白解析。
    """
    import csv
    sample = text[:8192]
    if any(ch in sample for ch in (",", ";", "\t", "|")):
        try:
            return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except Exception:
            return ","
    counts = set()
    for line in sample.splitlines():
        if line.strip():
            counts.add(len(line.split()))
    if len(counts) == 1 and counts.pop() >= 2:
        return r"\s+"
    return ","


def _import_coerce_csv_text(s):
    """csv 模块兜底解析出的字符串 → 尽量还原成数字（与 pandas 的推断保持一致）。"""
    if not isinstance(s, str):
        return s
    t = s.strip()
    if not t:
        return ""
    try:
        if re.fullmatch(r"[+-]?\d+", t):
            return int(t)
        f = float(t)
        if f != f or f in (float("inf"), float("-inf")):
            return s
        return round(f, 8)
    except Exception:
        return s


def _import_coerce_numeric_cells(rows):
    """表头被判掉后，数据列常因混入表头文字而整列变成字符串；这里把数字文本还原。"""
    for r in rows:
        for i, v in enumerate(r):
            if isinstance(v, str) and v.strip():
                r[i] = _import_coerce_csv_text(v)


def _import_read_csv(raw):
    """读取 CSV/TXT：处理编码、分隔符嗅探，并容忍标题行与数据行列数不一致。"""
    import csv
    import pandas as pd

    text, _enc = _import_decode_text(raw)
    if not text.strip():
        raise ValueError("文件里没有可读取的数据（内容为空）")
    sep = _import_guess_csv_sep(text)
    try:
        df = pd.read_csv(io.StringIO(text), header=None, sep=sep,
                         engine="python", skip_blank_lines=True)
        if df.shape[1] == 0:
            raise ValueError("CSV 里没有解析出任何列")
        return df
    except Exception:
        pass
    # 兜底：标题行只有 1 个字段、数据行有 2 个字段时 pandas 会报 ParserError，
    # 用 csv 模块逐行读，容忍每行字段数不一致。
    table = []
    if sep == r"\s+":
        for line in text.splitlines():
            if line.strip():
                table.append(line.split())
    else:
        for r in csv.reader(io.StringIO(text), delimiter=sep):
            if any(str(c).strip() for c in r):
                table.append([_import_coerce_csv_text(c) for c in r])
    if not table:
        raise ValueError("CSV 解析失败：文件里没有可读取的数据行")
    return pd.DataFrame(table)


def _import_read_excel(raw):
    import pandas as pd

    try:
        return pd.read_excel(io.BytesIO(raw), header=None, sheet_name=0)
    except ImportError as e:
        raise ValueError("无法读取 Excel 文件：缺少读取 .xls 所需的 xlrd 库，请用 Excel 另存为 .xlsx 再导入（%s）" % e)
    except Exception as e:
        raise ValueError("无法读取 Excel 文件（文件可能已损坏，或不是真正的 Excel）：%s: %s" % (type(e).__name__, e))


def _import_frame_rows(df):
    """DataFrame → 二维 list（空值 ""，浮点 8 位，最多 3000 行）。"""
    df = df.head(_IMPORT_MAX_ROWS)
    try:
        df = df.astype(object).where(df.notna(), None)
    except Exception:
        pass
    rows = []
    for r in df.values.tolist():
        rows.append([_import_cell(v) for v in r])
    return rows


def _import_header_text(v):
    if _import_is_empty(v):
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(_import_cell(v))


def _import_first_col_is_sequence(data):
    """第一列是否恰好是 1..N 的连续整数（用于无表头时识别多余的序号列）。"""
    if len(data) < 2:
        return False
    for i, row in enumerate(data, 1):
        if not row:
            return False
        n = _import_number(row[0])
        if n is None or not float(n).is_integer() or int(n) != i:
            return False
    return True


def _import_promote_integral_floats(rows):
    """整列都是整数值的浮点（如 1.0）转成 int，前端输入框显示更干净。"""
    width = max((len(r) for r in rows), default=0)
    for c in range(width):
        vals = [r[c] for r in rows if c < len(r) and not _import_is_empty(r[c])]
        if not vals:
            continue
        nums = [_import_number(v) for v in vals]
        if any(n is None for n in nums) or not all(float(n).is_integer() for n in nums):
            continue
        for r in rows:
            if c < len(r) and isinstance(r[c], float) and not isinstance(r[c], bool):
                if r[c].is_integer():
                    r[c] = int(r[c])


def _import_parse_cols(value, notes):
    """解析前端传来的 cols（字符串整数）；非法值忽略并记 note。"""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        n = int(float(s))
    except Exception:
        notes.append("cols 参数不是整数，已忽略")
        return None
    if n <= 0:
        notes.append("cols 参数不是正整数，已忽略")
        return None
    return n


def _import_normalize(rows, cols, notes):
    """整理二维表：去空行/空列、跳过标题、剔除表头与多余序号列、按 cols 对齐。"""
    # 1) 去掉全空行，并把每行补到同一宽度
    rows = [list(r) for r in rows if any(not _import_is_empty(v) for v in r)]
    width = max((len(r) for r in rows), default=0)
    rows = [r + [""] * (width - len(r)) for r in rows]
    # 2) 去掉末尾的全空列
    while width > 0 and all(_import_is_empty(r[width - 1]) for r in rows):
        width -= 1
    rows = [r[:width] for r in rows]

    # 3) 跳过开头的标题行：从第一行起找第一行“像数据”的行
    #    （≥2 个非空且其中 ≥1 个数字；整张表只有一列时放宽为 ≥1 个数字）
    need = 1 if width <= 1 else 2
    start = None
    for i, r in enumerate(rows):
        nonempty = sum(1 for v in r if not _import_is_empty(v))
        if nonempty >= need and any(_import_is_number(v) for v in r):
            start = i
            break
    if start is None:
        start = 0  # 整张表没有数字：不丢任何行，交给前端提示

    # 4) 紧邻数据行的上一行若含“非空且非数字”的单元格，视为表头并剔除
    header = []
    title_count = start
    if start > 0:
        prev = rows[start - 1]
        if any((not _import_is_empty(v)) and (not _import_is_number(v)) for v in prev):
            header = [_import_header_text(v) for v in prev]
            title_count = start - 1
    if title_count > 0:
        notes.append("已跳过 %d 行标题" % title_count)
    data = rows[start:]

    # 5) 请求带 cols 时，剔除多余的序号列（仅当宽度恰好多一列）
    dropped_index = False
    if cols and data and width == cols + 1:
        head0 = header[0].strip() if header else ""
        hit_header = bool(head0) and bool(_IMPORT_INDEX_HEADER_RE.match(head0))
        hit_seq = (not header) and _import_first_col_is_sequence(data)
        if hit_header or hit_seq:
            data = [r[1:] for r in data]
            if header:
                header = header[1:]
            width -= 1
            dropped_index = True
            notes.append("已忽略多余的序号列")

    # 6) 按 cols 裁列，不足补 ""
    if cols:
        data = [r[:cols] + [""] * max(0, cols - len(r)) for r in data]
        if header:
            header = header[:cols] + [""] * max(0, cols - len(header))

    # 7) 数字文本还原成数字；整列都是整数值的浮点转 int
    _import_coerce_numeric_cells(data)
    _import_promote_integral_floats(data)

    return {
        "rows": data,
        "shape": [len(data), len(data[0]) if data else 0],
        "header": header,
        "notes": notes,
        "dropped_index_col": dropped_index,
    }


@app.route("/api/import", methods=["POST"])
def api_import():
    """读取上传的 xlsx / csv，返回二维数组，供前端填入数据表。

    兼容旧前端：始终返回 ok / rows / name / shape；新增 header / notes /
    dropped_index_col 供新前端做列对齐和提示。任何异常都返回 400 JSON，不抛 500。
    """
    try:
        f = request.files.get("file")
        if not f:
            return jsonify({"ok": False, "error": "没有收到文件（请用 multipart 的 file 字段上传）"}), 400
        name = f.filename or "data"
        raw = f.read()
        if not raw:
            return jsonify({"ok": False, "error": "文件是空的（0 字节），请检查后重新上传"}), 400
        low = name.lower()
        if low.endswith(_IMPORT_EXCEL_EXT):
            df = _import_read_excel(raw)
        else:
            # 文本/未知扩展名都按 CSV 试；含 NUL 字节的二进制文件直接拒绝，
            # 否则 gb18030 几乎能解码任意字节，会把图片当表格返回。
            if b"\x00" in raw[:65536]:
                return jsonify({"ok": False, "error": "文件包含二进制内容（或 UTF-16 编码），无法按 CSV 解析；请上传 .csv/.txt 或 Excel 文件"}), 400
            df = _import_read_csv(raw)
        rows = _import_frame_rows(df)
        notes = []
        cols = _import_parse_cols(request.form.get("cols", request.args.get("cols")), notes)
        result = _import_normalize(rows, cols, notes)
        result["ok"] = True
        result["name"] = name
        return jsonify(result)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": f"导入失败：{type(e).__name__}: {e}"}), 400


@app.route("/api/download")
def api_download():
    fn = request.args.get("file", "")
    full = os.path.realpath(os.path.join(OUT, fn))
    if not full.startswith(os.path.realpath(OUT) + os.sep) or not os.path.isfile(full):
        return "forbidden", 403
    return send_file(full, as_attachment=True, download_name=os.path.basename(full))


@app.route("/api/ping")
def api_ping():
    return jsonify({"ok": True, "n": len(registry.load_all())})


def _port_busy(port):
    """端口上是否已经有程序在监听（Windows 上 SO_REUSEADDR 会让 bind 假成功，必须实测连接）。"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.35):
            return True
    except OSError:
        return False


def _is_our_server(port):
    """端口上跑的是不是本工作台（避免把别的程序当自己）。"""
    import urllib.request

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=0.6) as r:
            return b'"ok"' in r.read(200)
    except Exception:
        return False


def _pick_port(start=8765, tries=30):
    for p in range(start, start + tries):
        if not _port_busy(p):
            return p
    return start


def main():
    want = int(os.environ.get("LAB_PORT", "0") or 0)
    port = want or _pick_port()
    # 双击了两次 bat：直接复用已在运行的那个工作台，不要再起一个进程抢端口
    if _port_busy(port) and _is_our_server(port):
        print(f"工作台已经在运行：http://127.0.0.1:{port}")
        if "--no-browser" not in sys.argv:
            try:
                webbrowser.open(f"http://127.0.0.1:{port}")
            except Exception:
                pass
        return
    if _port_busy(port):
        port = _pick_port(port + 1 if want else 8765)
    url = f"http://127.0.0.1:{port}"
    print("=" * 58)
    print("  物化 / 化工实验数据处理工作台")
    print(f"  实验模块：{len(registry.load_all())} 个")
    print(f"  打开浏览器：{url}")
    print("  关闭此窗口即退出工作台")
    print("=" * 58)
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
