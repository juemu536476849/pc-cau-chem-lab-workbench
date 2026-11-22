import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei']  # 或者 'Microsoft YaHei'
rcParams['axes.unicode_minus'] = False  # 处理负号显示问题

# 读取数据
df = pd.read_excel('s7.xlsx', index_col=0)

# 获取数据列，使用 .iloc 进行位置索引
xav = df.iloc[-2, :].values
u = df.iloc[-1, :].values

# 创建图形
plt.figure(figsize=(10, 6))
plt.plot(xav, u, color='black', linewidth=2, label='实验曲线')

b1 = 0.390
b2 = 0.218

# 定义填充区域
tb1 = np.linspace(b1, 1.4, 100)
tb2 = np.linspace(b2, b1, 100)
tb3 = np.linspace(0, b2, 100)

# 填充不同区域的颜色：小于80，80到100，大于100
plt.fill_between(tb1, 0, 1.25, color='lightblue', label='恒速干燥阶段', alpha=0.5)
plt.fill_between(tb2, 0, 1.25, color='lightgreen', label='降速第一阶段', alpha=0.5)
plt.fill_between(tb3, 0, 1.25, color='lightcoral', label='降速第二阶段', alpha=0.5)

# 添加散点和文本
spx = [b1, b2]
spy = [0.000157, 0.00009421]
plt.scatter(spx, spy, s=100, color='red', edgecolor='black', zorder=5)  # 散点更突出

# 调整文本位置，增加两个文本标签之间的距离
plt.text(spx[0], spy[0] + 0.000015, f'({spx[0]}, {spy[0]})', fontsize=18, ha='right', va='bottom', color='black', fontweight='bold')
plt.text(spx[1], spy[1] - 0.000015, f'({spx[1]}, {spy[1]})', fontsize=18, ha='left', va='top', color='black', fontweight='bold')

# 添加标签和标题
plt.xlabel('X_Av', fontsize=14, fontweight='bold')
plt.ylabel('U(kg/m^2*s)', fontsize=14, fontweight='bold')
plt.xlim(0, 1.3)
plt.ylim(0, 0.0002)

# 显示图例
plt.legend(fontsize=12)

# 自动调整布局，避免标签被遮挡
plt.tight_layout()
plt.savefig('图2.svg', format='svg')

# 显示图表
plt.show()
