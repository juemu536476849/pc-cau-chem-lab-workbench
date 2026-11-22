# -*- coding: utf-8 -*-
"""模块自测：python -m app.selftest [id ...]

用每个模块 SPEC 里的默认数据与默认参数跑一遍 run()，检查返回值结构。
"""
import json
import math
import sys
import traceback

from . import registry


def _finite(v):
    return isinstance(v, (int, float)) and math.isfinite(v)


def check(exp_id, spec, verbose=True):
    for f in ("id", "code", "name", "subtitle", "desc", "method"):
        assert spec.get(f), f"SPEC 缺少 {f}"
    assert spec.get("group") in ("物化", "化工"), f"group 不合法：{spec.get('group')}"
    data = {
        "tables": {t["key"]: [list(r) for r in t.get("rows", [])] for t in spec.get("tables", [])},
        "params": {p["key"]: p.get("default") for p in spec.get("params", [])},
    }
    res = spec["_module"].run(data)
    assert isinstance(res, dict), "run 必须返回 dict"
    for k in ("kpis", "charts", "tables"):
        assert isinstance(res.get(k, []), list), f"{k} 必须是列表"
    for k in res.get("kpis", []):
        assert k.get("label"), "KPI 缺少 label"
        v = k.get("value")
        assert isinstance(v, str) or _finite(v), f"KPI {k.get('label')} 的值异常：{v}"
    for c in res.get("charts", []):
        assert "series" in c and c["series"], "chart 缺少 series"
        assert c.get("xlabel") and c.get("ylabel"), f"图表 {c.get('title')} 缺少轴标题"
        for s in c["series"]:
            assert s.get("points"), f"series {s.get('name')} 没有 points"
            for pt in s["points"]:
                assert len(pt) == 2, f"points 必须是 [x, y]：{pt}"
                x, y = float(pt[0]), float(pt[1])
                assert math.isfinite(x) and math.isfinite(y), f"series {s.get('name')} 含非有限值：{pt}"
                if c.get("xlog"):
                    assert x > 0, f"对数横轴上出现非正值：{pt}"
                if c.get("ylog"):
                    assert y > 0, f"对数纵轴上出现非正值：{pt}"
    for t in res.get("tables", []):
        n = len(t.get("columns", []))
        for row in t.get("rows", []):
            assert len(row) == n, f"表格 {t.get('title')} 有一行列数不匹配：{row}"
    if verbose:
        kpis = ", ".join(f"{k['label']}={k.get('value')}" for k in res.get("kpis", []))
        print(f"  [OK] {exp_id:>3} {spec['name']}  |  {kpis}  "
              f"| 图 {len(res.get('charts', []))} 表 {len(res.get('tables', []))}")
    return res


def main(argv):
    wanted = argv[1:]
    specs = registry.load_all()
    if not specs:
        print("没有发现任何实验模块")
        return 1
    bad = 0
    for exp_id, spec in specs.items():
        if wanted and exp_id not in wanted and spec.get("code") not in wanted:
            continue
        try:
            check(exp_id, spec)
        except Exception as e:
            bad += 1
            print(f"  [FAIL] {exp_id:>3} {spec.get('name')}: {type(e).__name__}: {e}")
            traceback.print_exc(limit=4)
    print(f"\n共 {len(specs)} 个模块，失败 {bad} 个")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
