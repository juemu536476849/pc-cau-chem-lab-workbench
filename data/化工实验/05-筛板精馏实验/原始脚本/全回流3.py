import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from matplotlib import font_manager

# 设置matplotlib支持中文
font_path = "C:/Windows/Fonts/simhei.ttf"  # 对于Windows系统，SimHei是常见的中文字体

# 使用字体
font_prop = font_manager.FontProperties(fname=font_path)

# 设置全局字体
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 读取Excel数据
df = pd.read_excel('全回流图.xlsx', header=None)

# 提取A1:K1为x轴，A2:K2为y轴
x = df.iloc[0, :11].values  # A1:K1
y = df.iloc[1, :11].values  # A2:K2

# 创建平滑曲线
spl = make_interp_spline(x, y, k=3)  # k=3表示三次样条插值
x_smooth = np.linspace(x.min(), x.max(), 500)  # 创建更多的x值用于平滑曲线
y_smooth = spl(x_smooth)  # 计算平滑曲线的y值

# 创建图形
plt.figure(figsize=(8, 6))

# 绘制平滑曲线
plt.plot(x_smooth, y_smooth, color='red', label='平衡线')

# 绘制y=x直线
plt.plot([0, 1], [0, 1], color='blue', label='操作线')

# 绘制精馏段操作线
x_rich = np.linspace(0, 0.2839, 500)
y_rich = 0.8 * x_rich + 0.1167
plt.plot(x_rich, y_rich, 'g--')

# 绘制精馏段操作线
x_rich = np.linspace(0.2839, 0.5835, 500)
y_rich = 0.8 * x_rich + 0.1167
plt.plot(x_rich, y_rich, 'g-', label='精馏段操作线')

# 绘制提馏段操作线
x_stripping = np.linspace(0.1176, 0.2839, 500)
y_stripping = 1.3605 * x_stripping - 0.0424
plt.plot(x_stripping, y_stripping, 'm-', label='提馏段操作线')

# 绘制q线
x_q = np.linspace(0.2687, 0.2839, 500)
y_q = 4.9643 * x_q - 1.0653
plt.plot(x_q, y_q, 'c-', label='q线')

# x1 和 x2 的值
x1 = 0.1176
x2 = 0.5835

# 你需要确保x_smooth中包含这两个x值
x_fill = np.linspace(x1, x2, 500)
y_fill = 1  # 对应的y值

# 填充区域
plt.fill_between(x_fill, y_fill, color='yellow', alpha=0.2)

# 标注 x = x1 和 x = x2
plt.axvline(x=x1, color='green', linestyle='--', label=f'塔底摩尔分率')
plt.axvline(x=x2, color='purple', linestyle='--', label=f'塔顶摩尔分率')

# 添加文字标注
plt.text(x1, 0.05, f'塔底摩尔分率\nx={x1}', color='green', ha='center', va='top', fontsize=12)
plt.text(x2, 0.05, f'塔顶摩尔分率\nx={x2}', color='purple', ha='center', va='top', fontsize=12)

xa, ya = 0.5835, 0.5835  # 点A
xb, yb = 0, 0.1167  # 点B
xe, ye = 0.2687, 0.2687  # 点E
xc, yc = 0.1176, 0.1176  # 点C
xd, yd = 0.2839, 0.3438  # 点D

# 绘制点A、B、C、D、E
plt.scatter([xa], [ya], color='black', zorder=5)
plt.scatter([xb], [yb], color='black', zorder=5)
plt.scatter([xc], [yc], color='black', zorder=5)
plt.scatter([xd], [yd], color='black', zorder=5)
plt.scatter([xe], [ye], color='black', zorder=5)

# 添加文字标注
plt.text(xa, ya, 'A', fontsize=12, ha='right')
plt.text(xb, yb, 'B', fontsize=12, ha='right')
plt.text(xc, yc, 'C', fontsize=12, ha='right')
plt.text(xd, yd, 'D', fontsize=12, ha='right')
plt.text(xe, ye, 'E', fontsize=12, ha='right')

# 设置x轴和y轴范围
plt.xlim(0, 1)
plt.ylim(0, 1)

# 添加标题和标签
plt.xlabel('X')
plt.ylabel('Y')

# 添加图例
plt.legend()

# 保存图片到当前路径
plt.savefig('部分回流求解.png', dpi=300)

# 显示图形
plt.grid(True)
plt.show()