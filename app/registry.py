# -*- coding: utf-8 -*-
"""实验模块注册表：自动发现 app/modules/*.py 中的 SPEC / run。"""
import importlib
import os
import re

MODULE_DIR = os.path.join(os.path.dirname(__file__), "modules")

_cache = None


def _natural_key(code):
    m = re.match(r"([A-Za-z]*)(\d+)", code or "")
    if m:
        return (m.group(1), int(m.group(2)))
    return (code or "", 0)


def load_all():
    global _cache
    if _cache is not None:
        return _cache
    mods = {}
    for fn in sorted(os.listdir(MODULE_DIR)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        name = "app.modules." + fn[:-3]
        try:
            m = importlib.import_module(name)
        except Exception as e:  # 单个模块坏掉不影响整体
            print(f"[registry] 跳过 {fn}: {e}")
            continue
        spec = getattr(m, "SPEC", None)
        run = getattr(m, "run", None)
        if not spec or not callable(run):
            print(f"[registry] 跳过 {fn}: 缺少 SPEC 或 run")
            continue
        spec = dict(spec)
        spec.setdefault("tags", [])
        spec.setdefault("method", [])
        spec.setdefault("tables", [])
        spec.setdefault("params", [])
        spec["_module"] = m
        mods[spec["id"]] = spec
    order = {"物化": 0, "化工": 1}
    _cache = dict(sorted(mods.items(),
                         key=lambda kv: (order.get(kv[1].get("group"), 9),
                                         _natural_key(kv[1].get("code")))))
    return _cache


def get(exp_id):
    return load_all().get(exp_id)


def public_spec(spec):
    return {k: v for k, v in spec.items() if not k.startswith("_")}


def all_specs():
    return [public_spec(s) for s in load_all().values()]
