import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy import linalg

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

# 构建数据矩阵
X, Y = np.meshgrid(x_values, y_values)
Z = z_values

# 将数据展平以便进行拟合
X_flat = X.flatten()
Y_flat = Y.flatten()
Z_flat = Z.flatten()

# 构建最小二乘问题的设计矩阵
A = np.vstack([X_flat, Y_flat, np.ones_like(X_flat)]).T

# 使用最小二乘法拟合平面
params, resids, rank, s = linalg.lstsq(A, Z_flat)

# 提取平面参数
A_coeff, B_coeff, C_coeff = params

# 拟合平面方程（以6位小数输出）
print(f"拟合平面方程：")
print(f"W_A = {A_coeff:.6f}x_A + {B_coeff:.6f}t + {C_coeff:.6f}")

# 转换为 x_A = At + Bw_A + C 的形式
if A_coeff != 0:
    x_A_eq = f"x_A = {(-B_coeff / A_coeff):.6f}t + {(1 / A_coeff):.6f}W_A + {(-C_coeff / A_coeff):.6f}"
else:
    x_A_eq = "A_coeff is zero, cannot solve for x_A in terms of t and W_A."

# 打印方程的三种形式
print(f"\n平面方程的形式 x_A = At + Bw_A + C 为：")
print(x_A_eq)

# 计算拟合值
W_A_fitted = A.dot(params)

# 计算R平方
ss_total = np.sum((Z_flat - np.mean(Z_flat))**2)
ss_residual = np.sum((Z_flat - W_A_fitted)**2)
r_squared = 1 - (ss_residual / ss_total)

print(f"\nR平方值: {r_squared:.6f}")

# 创建一个三维图形
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 绘制原始散点图
ax.scatter(X_flat, Y_flat, Z_flat, c='b', marker='o', label='原始数据')

# 绘制拟合平面
X_plane, Y_plane = np.meshgrid(x_values, y_values)
Z_plane = A_coeff * X_plane + B_coeff * Y_plane + C_coeff
ax.plot_surface(X_plane, Y_plane, Z_plane, color='r', alpha=0.5, label='拟合平面')

# 设置轴标签
ax.set_xlabel('质量分率 W_A')
ax.set_ylabel('温度 t (℃)')
ax.set_zlabel('折光率 n_D,d')

# # 显示图形
# plt.show()

# 保存图片到当前路径
plt.savefig('拟合平面.png', dpi = 300)  # 你可以选择其他格式，如 .jpg, .pdf 等
