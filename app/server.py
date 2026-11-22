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


@app.route("/api/import", methods=["POST"])
def api_import():
    """读取上传的 xlsx / csv，返回二维数组，供前端填入数据表。"""
    f = request.files.get("file")
    if not f:
        return jsonify({"ok": False, "error": "没有收到文件"}), 400
    name = f.filename or "data"
    try:
        import pandas as pd
        bio = io.BytesIO(f.read())
        if name.lower().endswith((".xlsx", ".xls", ".xlsm")):
            df = pd.read_excel(bio, header=None, sheet_name=0)
        else:
            df = pd.read_csv(bio, header=None, sep=None, engine="python")
        df = df.where(pd.notnull(df), None)
        rows = []
        for r in df.values.tolist()[:3000]:
            row = []
            for v in r:
                if v is None:
                    row.append("")
                elif isinstance(v, float):
                    row.append(round(v, 8))
                else:
                    row.append(v)
            rows.append(row)
        return jsonify({"ok": True, "rows": rows, "name": name,
                        "shape": [len(rows), len(rows[0]) if rows else 0]})
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 400


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
