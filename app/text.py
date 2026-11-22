"""上下标与公式的统一处理。

约定（模块里可以任选一种写法，导出时都会被正确渲染）：
1. Unicode 上下标，如 Λm∞、kg·m⁻³、H₂O —— 自动转成 `_{}` / `^{}` 记号；
2. 显式记号 `_{...}` 下标、`^{...}` 上标；
3. 行内公式 `$...$`、独立成行公式 `$$...$$`，支持 LaTeX 子集。

前端把它渲染成 <sub>/<sup>（公式用 <span class="frac"> 等），
Word 里生成真正的下标/上标格式，`$...$` 用 OMML 公式对象。
"""

import re
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

# ---------------------------------------------------------------- 上下标字符

_SUB_MAP = {
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7",
    "₈": "8", "₉": "9", "₊": "+", "₋": "-", "₌": "=", "₍": "(", "₎": ")",
    "ₐ": "a", "ₑ": "e", "ₕ": "h", "ᵢ": "i", "ⱼ": "j", "ₖ": "k", "ₗ": "l", "ₘ": "m",
    "ₙ": "n", "ₒ": "o", "ₚ": "p", "ᵣ": "r", "ₛ": "s", "ₜ": "t", "ᵤ": "u", "ᵥ": "v", "ₓ": "x",
}
_SUP_MAP = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7",
    "⁸": "8", "⁹": "9", "⁺": "+", "⁻": "-", "⁼": "=", "⁽": "(", "⁾": ")", "ⁿ": "n",
}

_GREEK = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\Delta": "Δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η", r"\theta": "θ",
    r"\Theta": "Θ", r"\kappa": "κ", r"\lambda": "λ", r"\Lambda": "Λ", r"\mu": "μ",
    r"\nu": "ν", r"\xi": "ξ", r"\pi": "π", r"\Pi": "Π", r"\rho": "ρ", r"\sigma": "σ",
    r"\Sigma": "Σ", r"\tau": "τ", r"\phi": "φ", r"\varphi": "φ", r"\chi": "χ",
    r"\psi": "ψ", r"\Psi": "Ψ", r"\omega": "ω", r"\Omega": "Ω",
}
_SYMBOL = {
    r"\times": "×", r"\cdot": "·", r"\pm": "±", r"\mp": "∓", r"\infty": "∞",
    r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥", r"\ne": "≠", r"\neq": "≠",
    r"\approx": "≈", r"\sim": "~", r"\propto": "∝", r"\degree": "°", r"\prime": "′",
    r"\angle": "∠", r"\to": "→", r"\rightarrow": "→", r"\leftarrow": "←",
    r"\sum": "∑", r"\int": "∫", r"\partial": "∂", r"\nabla": "∇",
    r"\,": "\u2009", r"\;": "\u2009", r"\ ": " ", r"\%": "%",
}
_FUNC = {"ln", "lg", "log", "exp", "sin", "cos", "tan", "lim", "max", "min", "mol", "cal"}


_ASCII_SUB = re.compile(r"(?<=[^\s{_}])_(?:([A-Za-z][A-Za-z0-9]{0,11})|([0-9]{1,2})|([\u4e00-\u9fff]{1,4})|(\u221e))(?![A-Za-z0-9{])")
_ASCII_SUP = re.compile(r"\^([A-Za-z0-9.\-\u221e]{1,6})(?![A-Za-z0-9{])")


def to_markup(s):
    """Unicode 上下标 / ASCII 下划线写法 -> `_{}` / `^{}` 记号（幂等）。"""
    if not isinstance(s, str) or not s:
        return s
    if any(c in _SUB_MAP or c in _SUP_MAP for c in s):
        s = _markup(s)
    if "_" in s:
        s = _ASCII_SUB.sub(lambda m: "_{" + next(g for g in m.groups() if g) + "}", s)
    if "^" in s:
        s = _ASCII_SUP.sub(lambda m: "^{" + m.group(1) + "}", s)
    return s


def _markup(s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch in _SUB_MAP or ch in _SUP_MAP:
            table = _SUB_MAP if ch in _SUB_MAP else _SUP_MAP
            marker = "_{" if ch in _SUB_MAP else "^{"
            j = i
            buf = []
            while j < n and s[j] in table:
                buf.append(table[s[j]])
                j += 1
            out.append(marker + "".join(buf) + "}")
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def walk(obj, fn=to_markup):
    """递归处理 dict/list/str（保留其它类型）。"""
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, dict):
        return {k: walk(v, fn) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [walk(v, fn) for v in obj]
    return obj


# ---------------------------------------------------------------- LaTeX 子集解析

def _read_group(s, i):
    """读取 { ... } 分组，返回 (内容, 新位置)。也支持单个字符。"""
    while i < len(s) and s[i] == " ":
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        depth = 0
        j = i
        while j < len(s):
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
                if depth == 0:
                    return s[i + 1:j], j + 1
            j += 1
        return s[i + 1:], len(s)
    if s[i] == "\\":
        m = re.match(r"\\[A-Za-z]+", s[i:])
        if m:
            return m.group(0), i + m.end()
    return s[i], i + 1


def parse_math(tex):
    """把 LaTeX 子集解析成节点树，供 HTML / OMML 两种后端渲染。"""
    nodes, i = _parse_seq(tex, 0, None)
    return nodes


def _parse_seq(s, i, stop):
    nodes = []
    while i < len(s):
        ch = s[i]
        if stop and ch == stop:
            return nodes, i + 1
        if ch == "{":
            inner, i = _read_group(s, i)
            nodes.append({"t": "group", "body": _parse_seq(inner, 0, None)[0]})
            continue
        if ch == "^" or ch == "_":
            arg, i = _read_group(s, i + 1)
            body = _parse_seq(arg, 0, None)[0]
            nodes.append({"t": "sup" if ch == "^" else "sub", "body": body})
            continue
        if ch == "\\":
            m = re.match(r"\\([A-Za-z]+)", s[i:])
            name = m.group(0) if m else s[i:i + 2]
            i += len(name)
            if name == r"\frac":
                a, i = _read_group(s, i)
                b, i = _read_group(s, i)
                nodes.append({"t": "frac", "a": _parse_seq(a, 0, None)[0], "b": _parse_seq(b, 0, None)[0]})
                continue
            if name == r"\sqrt":
                a, i = _read_group(s, i)
                nodes.append({"t": "sqrt", "body": _parse_seq(a, 0, None)[0]})
                continue
            if name in (r"\text", r"\mathrm", r"\mathit"):
                a, i = _read_group(s, i)
                nodes.append({"t": "text", "body": a})
                continue
            if name in (r"\left", r"\right"):
                continue
            if name in _GREEK:
                nodes.append({"t": "text", "body": _GREEK[name]})
                continue
            if name in _SYMBOL:
                nodes.append({"t": "text", "body": _SYMBOL[name]})
                continue
            nodes.append({"t": "text", "body": name[1:]})
            continue
        if ch == " ":
            nodes.append({"t": "space"})
            i += 1
            continue
        # 普通字符：吸到下一个 ^ _ \ { 之前
        m = re.match(r"[^\\^_{} ]+", s[i:])
        if m:
            txt = m.group(0)
            nodes.append({"t": "text", "body": txt, "italic": txt.isalpha() and txt not in _FUNC})
            i += len(txt)
            continue
        nodes.append({"t": "text", "body": ch})
        i += 1
    return nodes, i


# ---------------------------------------------------------------- OMML（Word 公式）

_M_NS = nsdecls("m", "w")


def _omath_run(text, italic=False):
    """单个 m:r，可选斜体（Word 公式里变量用 Cambria Math 斜体）。"""
    rpr = ""
    if italic:
        rpr = "<m:rPr><m:sty m:val=\"i\"/></m:rPr>"
    return f"<m:r>{rpr}<m:t xml:space=\"preserve\">{_xml_escape(text)}</m:t></m:r>"


def _xml_escape(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _omml_nodes(nodes):
    out = []
    for n in nodes:
        t = n["t"]
        if t == "text":
            out.append(_omath_run(n["body"], n.get("italic", False)))
        elif t == "space":
            out.append(_omath_run("\u2009"))
        elif t == "group":
            out.append(_omml_nodes(n["body"]))
        elif t == "sup":
            out.append("<m:sSup><m:e><m:r><m:t>\u200b</m:t></m:r></m:e><m:sup>"
                       + _body(n["body"]) + "</m:sup></m:sSup>")
        elif t == "sub":
            out.append("<m:sSub><m:e><m:r><m:t>\u200b</m:t></m:r></m:e><m:sub>"
                       + _body(n["body"]) + "</m:sub></m:sSub>")
        elif t == "frac":
            out.append("<m:f><m:num>" + _body(n["a"]) + "</m:num><m:den>"
                       + _body(n["b"]) + "</m:den></m:f>")
        elif t == "sqrt":
            out.append("<m:rad><m:radPr><m:degHide m:val=\"1\"/></m:radPr><m:deg/>"
                       "<m:e>" + _body(n["body"]) + "</m:e></m:rad>")
    return "".join(out)


def _body(nodes):
    """渲染一组节点（内部先做上下标合并，保证分数里也能正确挂到底数上）。"""
    return _merge_scripts(nodes)


def omml(tex):
    """LaTeX 子集 -> m:oMath 元素。上下标需要依附前一个字符，这里做一次合并。"""
    nodes = parse_math(tex)
    xml = f"<m:oMath {_M_NS}>" + _merge_scripts(nodes) + "</m:oMath>"
    return parse_xml(xml)


def _merge_scripts(nodes):
    """把 `x` 后面的 ^/_ 合并成 Word 的 sSup / sSub（底数 = 前一个节点）。"""
    merged = []
    for n in nodes:
        if n["t"] in ("sup", "sub") and merged:
            base = merged.pop()
            merged.append({"t": n["t"], "base": base, "body": n["body"]})
        else:
            merged.append(n)
    out = []
    for n in merged:
        if n["t"] in ("sup", "sub") and "base" in n:
            tag = "m:sSup" if n["t"] == "sup" else "m:sSub"
            part = "m:sup" if n["t"] == "sup" else "m:sub"
            out.append(f"<{tag}><m:e>{_omml_nodes([n['base']])}</m:e>"
                       f"<{part}>{_body(n['body'])}</{part}></{tag}>")
        else:
            out.append(_omml_nodes([n]))
    return "".join(out)


# ---------------------------------------------------------------- Word 富文本

_TOK = re.compile(r"(\$[^$]+\$|\$\$[^$]+\$\$|_\{[^{}]*\}|\^\{[^{}]*\})")


def rich_runs(text, font_setter=None):
    """把带记号/公式的字符串切成 [(kind, content)]，kind ∈ text/sub/sup/math。"""
    parts = []
    text = to_markup(text or "")
    for chunk in _TOK.split(text):
        if not chunk:
            continue
        if chunk.startswith("$$") and chunk.endswith("$$") and len(chunk) > 4:
            parts.append(("math", chunk[2:-2]))
        elif chunk.startswith("$") and chunk.endswith("$") and len(chunk) > 2:
            parts.append(("math", chunk[1:-1]))
        elif chunk.startswith("_{") and chunk.endswith("}"):
            parts.append(("sub", chunk[2:-1]))
        elif chunk.startswith("^{") and chunk.endswith("}"):
            parts.append(("sup", chunk[2:-1]))
        else:
            parts.append(("text", chunk))
    return parts


def add_rich(paragraph, text, size=None, bold=None, font_setter=None):
    """向段落写入富文本：真正的下标/上标 + 行内 OMML 公式。"""
    from docx.shared import Pt

    for kind, content in rich_runs(text):
        if kind == "math":
            try:
                paragraph._p.append(omml(content))
            except Exception:
                r = paragraph.add_run(content)
                _style(r, size, bold, font_setter)
            continue
        r = paragraph.add_run(content)
        if kind == "sub":
            r.font.subscript = True
        elif kind == "sup":
            r.font.superscript = True
        _style(r, size, bold, font_setter)
    return paragraph


def _style(run, size, bold, font_setter):
    from docx.shared import Pt

    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if font_setter:
        font_setter(run)


# ---------------------------------------------------------------- 前端用：LaTeX -> HTML

def math_html(tex):
    """后端只需要给前端一个可读的兜底（前端自己也会解析）。"""
    return tex
