import pandas as pd
import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
from matplotlib import font_manager

# 设置matplotlib支持中文
font_path = "C:/Windows/Fonts/simhei.ttf"  # 对于Windows系统，SimHei是常见的中文字体
# font_path = "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"  # Linux中的Arial字体路径
# font_path = "/System/Library/Fonts/STHeiti Light.ttc"  # macOS中的中文字体路径

# 使用字体
font_prop = font_manager.FontProperties(fname=font_path)

# 设置全局字体
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# 读取Excel文件
file_path = '回归插值原始数据.xlsx'  # 请根据实际文件路径修改
df = pd.read_excel(file_path, header=None)

# 获取x轴、y轴和z轴数据
x_values = df.iloc[0, 1:].values  # B1:P1为x轴数据
y_values = df.iloc[1:4, 0].values  # A2:A4为y轴数据
z_values = df.iloc[1:4, 1:].values  # B2:P4为z轴数据

# 创建一个三维散点图
from mpl_toolkits.mplot3d import Axes3D

# 创建一个三维轴对象
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 绘制散点图
for i, y in enumerate(y_values):
    for j, x in enumerate(x_values):
        ax.scatter(x, y, z_values[i, j], c='b', marker='o')
# 设置轴标签
ax.set_xlabel('质量分率 W_A')
ax.set_ylabel('温度 t (℃)')
ax.set_zlabel('折光率 n_D,d')

# 保存图片到当前路径
plt.savefig('散点图.png', dpi = 300)  # 你可以选择其他格式，如 .jpg, .pdf 等

# # 显示图形
# plt.show()

