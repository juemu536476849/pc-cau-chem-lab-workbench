import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
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


# 定义幂函数模型
def power_law(x, a):
    return x ** a


# 使用curve_fit拟合幂函数
popt, _ = curve_fit(power_law, x, y)

# 拟合得到的a值
a_fit = popt[0]

# 计算预测值
y_pred = power_law(x, a_fit)

# 创建x值的细分区间用于绘制拟合曲线
x_smooth = np.linspace(x.min(), x.max(), 500)
y_smooth = power_law(x_smooth, a_fit)

# 创建图形
plt.figure(figsize=(8, 6))

# 绘制幂函数拟合的平衡线
plt.plot(x_smooth, y_smooth, color='red', label=f'平衡线 (y = x^{a_fit:.2f})')

# 绘制操作线
plt.plot([0, 1], [0, 1], color='blue', label='操作线')

# 定义射线追踪的起点和目标x1, x2
x1 = 0.2282
x2 = 0.6791
y2 = power_law(x2, a_fit)

# 存储射线的路径
ray_x = [x2]
ray_y = [y2]

# 设置射线方向变量，True表示平行于x轴，False表示平行于y轴
horizontal_ray = True

# 执行射线追踪，直到x达到x1
while ray_x[-1] > x1:
    if horizontal_ray:
        # 计算当前x坐标对应的y值，沿x轴向左射线
        x_current = ray_x[-1]
        y_current = power_law(x_current, a_fit)

        # 确定射线与平衡线的交点
        if y_current < ray_y[-1]:
            # 交点时，沿y轴射线向下
            ray_y.append(y_current)
            ray_x.append(x_current)
        else:
            # 交点时，沿x轴射线向左
            ray_x.append(x_current - 0.01)  # 每次往左移动0.01
            ray_y.append(power_law(ray_x[-1], a_fit))
    else:
        # 继续沿y轴方向追踪
        pass

    # 更改射线方向
    horizontal_ray = not horizontal_ray

# 绘制射线路径
plt.plot(ray_x, ray_y, 'green', label='射线路径')

# 填充区域
plt.fill_between(np.linspace(x1, x2, 500), 0, 1, color='yellow', alpha=0.2)

# 设置x轴和y轴范围
plt.xlim(0, 1)
plt.ylim(0, 1)

# 添加标题和标签
plt.xlabel('X')
plt.ylabel('Y')

# 添加图例
plt.legend()

# 保存图片到当前路径
plt.savefig('射线追踪.png', dpi=300)

# 显示图形
plt.grid(True)
plt.show()
