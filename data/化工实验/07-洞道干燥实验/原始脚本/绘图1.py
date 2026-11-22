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
t = df.iloc[0, :].values  # 获取第一行数据
xi = df.iloc[3, :].values  # 获取第四行数据

# 创建图形
plt.figure(figsize=(10, 6))
plt.plot(t, xi, color='black', linewidth=2, label='实验曲线')

# 定义填充区域
tb1 = np.linspace(0, 80, 100)
tb2 = np.linspace(80, 100, 100)
tb3 = np.linspace(100, 160, 100)

# 填充不同区域的颜色：小于80，80到100，大于100
plt.fill_between(tb1, 0, 1.25, color='lightblue', label='恒速干燥阶段', alpha=0.5)
plt.fill_between(tb2, 0, 1.25, color='lightgreen', label='降速第一阶段', alpha=0.5)
plt.fill_between(tb3, 0, 1.25, color='lightcoral', label='降速第二阶段', alpha=0.5)

# 添加散点和文本
spx = [80, 100]
spy = [0.38, 0.224]
plt.scatter(spx, spy, s=100, color='red', edgecolor='black', zorder=5)  # 散点更突出

# 添加文本
for i in range(2):
    plt.text(spx[i], spy[i], f'({spx[i]}, {spy[i]:.3f})', fontsize=18, ha='right', va='bottom', color='black', fontweight='bold')

# 添加标签和标题
plt.xlabel('t(min)', fontsize=14, fontweight='bold')
plt.ylabel('X_i', fontsize=14, fontweight='bold')
plt.xlim(0, 160)
plt.ylim(0, 1.25)

# 显示图例
plt.legend(fontsize=12, loc='upper right')

# 自动调整布局，避免标签被遮挡
plt.tight_layout()
plt.savefig('图1.svg', format='svg')

# 显示图表
plt.show()
