# 实验模块开发契约（给模块作者 / 子代理）

每个实验一个文件：`app/modules/<id>.py`，只依赖标准库 + numpy/scipy（可用 `app.core`），
**不要**读 F: 盘或任何绝对路径，**不要**用 matplotlib / 写文件 / print 调试输出。

## 必须导出

```python
SPEC = {
    "id": "a1",                    # 唯一 id：a1..a8 / b1..b5 / c1..c7
    "code": "A1",                  # 展示编号
    "group": "物化",               # "物化" 或 "化工"
    "name": "积分溶解热的测定",
    "subtitle": "双直线外推 · 温差 ΔT",   # 一行副标题，说清方法
    "tags": ["热化学", "量热"],
    "desc": "两句话说明实验做什么、这个模块算什么。",
    "method": ["① ...", "② ..."],   # 3-6 条计算步骤，写给同学看
    "tables": [
        {"key": "raw", "title": "温度–时间数据",
         "note": "可从 Excel 直接粘贴；空行忽略",
         "columns": [{"key": "t", "label": "t / min", "type": "number"},
                     {"key": "T", "label": "T / K", "type": "number"}],
         "rows": [[1, 300.1], [2, 300.2]]}       # 默认示例数据（务必真实，取自原实验）
    ],
    "params": [
        {"key": "g1", "label": "第一拐点 t", "type": "number", "default": 5,
         "step": 1, "hint": "升温段结束的位置"},
        {"key": "mode", "label": "体系", "type": "select", "default": "nacl",
         "options": [{"value": "nacl", "label": "NaCl"}]}
    ],
}

def run(data):
    """data = {"tables": {key: [[...], ...]}, "params": {key: value}}"""
    return {
        "kpis": [{"label": "ΔT", "value": 1.0063, "unit": "K", "digits": 4,
                  "hint": "两拟合线在中点处的纵差"}],
        "charts": [{
            "title": "温度–时间曲线与双直线外推",
            "xlabel": "t / min", "ylabel": "T / K",
            "series": [
                {"name": "实验点", "type": "scatter", "points": [[1, 300.1]]},
                {"name": "拟合 1", "type": "line", "points": [[0, 300.0], [5, 300.5]]},
                {"name": "延长线", "type": "line", "points": [[5, 300.5], [7.5, 300.9]],
                 "dash": True, "color": "#e5533d"},
            ],
            "vlines": [{"x": 7.5, "label": "中点"}],
            "hlines": [{"y": 0.1, "label": "y = 0.1"}],
            "points": [{"x": 0.101, "y": 0.332, "label": "交点"}],
            "xlog": False, "ylog": False,
        }],
        "tables": [{"title": "拟合结果", "columns": ["体系", "k", "b", "r", "ΔT / K"],
                    "rows": [["KNO₃", -0.0038, -0.0063, -0.9887, 1.0063]]}],
        "notes": ["ΔT 取两拟合直线在 x=(g1+g2)/2 处的纵坐标之差。"],
        "warnings": ["第二段相关系数偏低，建议调整拐点。"],
    }
```

## 规则

1. **忠实移植**：算法、参数、公式与原脚本/报告一致；原脚本用 `input()` 的地方改为 `params`，
   硬编码路径改为表格输入。原脚本里明显是笔误的地方可以修，但要在 `notes` 里说明。
2. **错误友好**：数据不足、除零、拟合失败时 `raise ValueError("中文说明，告诉用户改哪里")`，
   服务端会原样显示。不要静默返回空结果。
3. **数值**：`kpis[].value` 用数字（前端按 `digits` 格式化），不要自己拼字符串；
   表格里的数也用数字，单位写进列名。
4. **图表**：`points` 是 `[[x, y], ...]`；`type` 取 `line` / `scatter` / `step`；
   `dash: true` 虚线；`color` 可省略（自动配色）。一个模块 1–3 张图。
5. **表格**：`columns` 是字符串列表，`rows` 是二维数组，长度与列数一致。
6. `rows` 里允许字符串（如“体系”列）。
7. 不要 import `app.server`，不要读 `data/` 目录。
8. 用 `python -m app.selftest <id>` 自测，必须通过。

## 常用工具（app/core.py）

`num(v, default)`、`column(rows, i)`、`xy(rows, ix, iy)`、`linfit(xs, ys)`、`fit_through_origin`、
`line_y(fit, x)`、`intersect(fit1, fit2)`、`interp(x, xs, ys)`、`trapz`、`spline_points`、
`fmt`、`fmt_sci`。
