import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import os
from docx import Document
from docx.shared import Inches

# 输入数据
x_values = [0.000, 0.200, 0.400, 0.600, 0.800, 1.000]
y_values = [0.000, 0.121, 0.235, 0.238, 0.126, 0.000]

# 使用样条插值对数据进行平滑处理
x_smooth = np.linspace(min(x_values), max(x_values), 300)
spl = make_interp_spline(x_values, y_values, k=3)
y_smooth = spl(x_smooth)

# 创建Word文档
doc_path = r"F:\大二下\物化实验"  # 替换为你指定的文件夹路径
doc_name = "A2数据处理1.docx"
full_doc_path = os.path.join(doc_path, doc_name)

# 删除已存在的文档
if os.path.exists(full_doc_path):
    os.remove(full_doc_path)

doc = Document()
doc.add_heading('Data Processing', 0)

# 绘制并保存图片
plt.plot(x_smooth, y_smooth)
plt.scatter(x_values, y_values, color='red')  # 绘制数据点
plt.xlabel('x$_{VN}$/mL')
plt.ylabel('OD$_{527}$')
plt.title('Correction curve of ΔD-x$_V$ (1)')
plt.grid(True)
plt.ylim(-0.025, 0.375)

# 计算第一个切线的斜率（在第二个数据点处）
slope1 = spl.derivative(nu=1)(x_values[1])

# 计算第一个切线的截距
intercept1 = y_values[1] - slope1 * x_values[1]

# 切线方程
x_tangent1 = np.linspace(x_values[1], x_values[3], 100)
y_tangent1 = slope1 * x_tangent1 + intercept1

# 绘制第一个切线
plt.plot(x_tangent1, y_tangent1, linestyle='--', color='blue')

# 计算第二个切线的斜率（在第四个数据点处）
slope2 = spl.derivative(nu=1)(x_values[4])

# 计算第二个切线的截距
intercept2 = y_values[4] - slope2 * x_values[4]

# 第二个切线方程
x_tangent2 = np.linspace(x_values[1], x_values[4], 100)
y_tangent2 = slope2 * x_tangent2 + intercept2

# 绘制第二个切线
plt.plot(x_tangent2, y_tangent2, linestyle='--', color='green')

# 计算两条切线的交点坐标
intersection_x = (intercept2 - intercept1) / (slope1 - slope2)
intersection_y = slope1 * intersection_x + intercept1

# 保存图片
temp_img_path = os.path.join(doc_path, "temp.png")
plt.savefig(temp_img_path)

# 在图片下方写入交点坐标和切线方程
doc.add_picture(temp_img_path, width=Inches(6))
doc.add_paragraph("Equations of two tangents:")
doc.add_paragraph(f"Tangent 1: y = {slope1:.2f}x + {intercept1:.2f}")
doc.add_paragraph(f"Tangent 2: y = {slope2:.2f}x + {intercept2:.2f}")
doc.add_paragraph(f"Intersection point coordinates: ({intersection_x:.3f}, {intersection_y:.3f})")

# 保存Word文档
doc.save(full_doc_path)
plt.show()

# 输入数据
x_values = [0.000, 0.200, 0.400, 0.600, 0.800, 1.000]
y_values = [0.000, 0.256, 0.476, 0.488, 0.249, 0.000]

# 使用样条插值对数据进行平滑处理
x_smooth = np.linspace(min(x_values), max(x_values), 300)
spl = make_interp_spline(x_values, y_values, k=3)
y_smooth = spl(x_smooth)

# 创建Word文档
doc_path = r"F:\大二下\物化实验"  # 替换为你指定的文件夹路径
doc_name = "A2数据处理2.docx"
full_doc_path = os.path.join(doc_path, doc_name)

# 删除已存在的文档
if os.path.exists(full_doc_path):
    os.remove(full_doc_path)

doc = Document()
doc.add_heading('Data Processing', 0)

# 绘制并保存图片
plt.plot(x_smooth, y_smooth)
plt.scatter(x_values, y_values, color='red')  # 绘制数据点
plt.xlabel('x$_{VN}$/mL')
plt.ylabel('OD$_{527}$')
plt.title('Correction curve of ΔD-x$_V$ (2)')
plt.grid(True)
plt.ylim(-0.05, 0.75)

# 计算第一个切线的斜率（在第二个数据点处）
slope1 = spl.derivative(nu=1)(x_values[1])

# 计算第一个切线的截距
intercept1 = y_values[1] - slope1 * x_values[1]

# 切线方程
x_tangent1 = np.linspace(x_values[1], x_values[3], 100)
y_tangent1 = slope1 * x_tangent1 + intercept1

# 绘制第一个切线
plt.plot(x_tangent1, y_tangent1, linestyle='--', color='blue')

# 计算第二个切线的斜率（在第四个数据点处）
slope2 = spl.derivative(nu=1)(x_values[4])

# 计算第二个切线的截距
intercept2 = y_values[4] - slope2 * x_values[4]

# 第二个切线方程
x_tangent2 = np.linspace(x_values[1], x_values[4], 100)
y_tangent2 = slope2 * x_tangent2 + intercept2

# 绘制第二个切线
plt.plot(x_tangent2, y_tangent2, linestyle='--', color='green')

# 计算两条切线的交点坐标
intersection_x = (intercept2 - intercept1) / (slope1 - slope2)
intersection_y = slope1 * intersection_x + intercept1

# 保存图片
temp_img_path = os.path.join(doc_path, "temp.png")
plt.savefig(temp_img_path)

# 在图片下方写入交点坐标和切线方程
doc.add_picture(temp_img_path, width=Inches(6))
doc.add_paragraph("Equations of two tangents:")
doc.add_paragraph(f"Tangent 1: y = {slope1:.2f}x + {intercept1:.2f}")
doc.add_paragraph(f"Tangent 2: y = {slope2:.2f}x + {intercept2:.2f}")
doc.add_paragraph(f"Intersection point coordinates: ({intersection_x:.3f}, {intersection_y:.3f})")

# 保存Word文档
doc.save(full_doc_path)
plt.show()