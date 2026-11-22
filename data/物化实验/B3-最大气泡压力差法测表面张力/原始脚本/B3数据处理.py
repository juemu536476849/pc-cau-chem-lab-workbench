import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# 定义拟合函数 y = a - b * ln(1 + c * x)，使用 np.log1p(x) 等价于 np.log(1 + x)
def model_func(x, a, b, c):
    return a - b * np.log1p(c * x)

# 读取 Excel 文件，并假设没有列名
file_path = 'B3数据处理.xlsx'
data = pd.read_excel(file_path, header=None)

# 选择指定范围的数据，并将其转换为 numpy 数组，确保所有数据是数值类型
x_data = np.array(pd.to_numeric(data.iloc[11:19, 0].values, errors='coerce'))  # A12:A19，对应第1列
y_data = np.array(pd.to_numeric(data.iloc[11:19, 2].values, errors='coerce'))  # C12:C19，对应第3列

# 去除任何可能的 NaN 值
x_data = x_data[~np.isnan(x_data)]
y_data = y_data[~np.isnan(y_data)]

# 绘制散点图
plt.scatter(x_data, y_data, color='blue')

# 拟合曲线
initial_guess = [1, 1, 1]  # 初始猜测值 [a, b, c]
params, covariance = curve_fit(model_func, x_data, y_data, p0=initial_guess)

# 获取拟合参数 a, b, c
a, b, c = params

# 计算拟合的 y 值
y_fit = model_func(x_data, a, b, c)

# 计算 R^2 值
ss_res = np.sum((y_data - y_fit) ** 2)  # 残差平方和
ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)  # 总平方和
r_squared = 1 - (ss_res / ss_tot)

# 绘制拟合曲线
x_fit = np.linspace(min(x_data), max(x_data), 100)
y_fit_curve = model_func(x_fit, a, b, c)
plt.plot(x_fit, y_fit_curve, label=f'Fitted Curve\ny = {a:.4f} - {b:.4f} ln(1 + {c:.4f}x)', color='red')

# 添加标题和标签
plt.title('Scatter and Fitted Curve Plot')
plt.xlabel('concentration(mol/L)')
plt.ylabel('σ(N/m)')
plt.legend()

# 打印拟合参数和 R^2 值
print(f"拟合参数: a = {a:.4f}, b = {b:.4f}, c = {c:.4f}")
print(f"R^2 = {r_squared:.4f}")
print(f"拟合曲线方程: y = {a:.4f} - {b:.4f} ln(1 + {c:.4f}x)")

# 显示图形
plt.show()


