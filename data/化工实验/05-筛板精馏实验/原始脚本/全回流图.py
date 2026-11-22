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

# 设置x轴和y轴范围
plt.xlim(0, 1)
plt.ylim(0, 1)

# 添加标题和标签
plt.xlabel('X')
plt.ylabel('Y')

# 添加图例
plt.legend()

# 保存图片到当前路径
plt.savefig('平衡操作图.png', dpi = 300)

# 显示图形
plt.grid(True)
plt.show()
