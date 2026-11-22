import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import os
from docx import Document
from docx.shared import Inches, Cm
import pandas as pd

# 输入数据
x_values = [0.000, 0.040, 0.080, 0.120, 0.160, 0.200]
# y_values = [0.000, 0.121, 0.235, 0.238, 0.126, 0.000]
x_valuesa = [0.000, 0.040, 0.080, 0.120, 0.160, 0.200]
# y_valuesa = [0.000, 0.256, 0.476, 0.488, 0.249, 0.000]

# 获取当前脚本的目录
current_directory = os.path.dirname(os.path.abspath(__file__))

# 拼接文件名得到完整的文件路径
excel_file_path = os.path.join(current_directory, 'A2数据处理(1) - 副本.xlsx')
sheet_name = "Sheet2 (4)"

# 使用pandas读取Excel文件的指定工作表
df = pd.read_excel(excel_file_path, sheet_name=sheet_name)

# 提取B6到G6的数据到y_values
y_values = df.iloc[4, 1:7].tolist()  # 注意索引从0开始，且iloc的行索引从0开始，列索引从1开始（因为B列是第二列）

# 提取H6到M6的数据到y_valuesa
y_valuesa = df.iloc[4, 7:13].tolist()  # 同样注意索引，H列是第八列

# 之后可以对y_values和y_valuesa进行您需要的操作

# 使用样条插值对数据进行平滑处理
x_smooth = np.linspace(min(x_values), max(x_values), 300)
spl = make_interp_spline(x_values, y_values, k=3)
y_smooth = spl(x_smooth)
# 计算第一个切线的斜率（在第二个数据点处）
slope1 = spl.derivative(nu=1)(x_values[1])
# 计算第二个切线的斜率（在第四个数据点处）
slope2 = spl.derivative(nu=1)(x_values[4])

x_smootha = np.linspace(min(x_valuesa), max(x_valuesa), 300)
spl_a = make_interp_spline(x_valuesa, y_valuesa, k=3)
y_smootha = spl_a(x_smootha)

# 创建Word文档
# 使用 os.path.dirname 获取 excel_file_path 所在的文件夹路径
folder_path = os.path.dirname(excel_file_path)

# 构造 Word 文档的路径，假设文档名为 "report.docx"
doc_path = os.path.join(folder_path)
doc_name = "A2数据处理.docx"
full_doc_path = os.path.join(doc_path, doc_name)

# 删除已存在的文档
if os.path.exists(full_doc_path):
    os.remove(full_doc_path)

# 创建新文档
doc = Document()

# 设置页面大小为A5，并设置上下页边距为1厘米
section = doc.sections[0]
section.page_width = Inches(5.83)
section.page_height = Inches(8.27)# A5尺寸（5.83 x 8.27英寸）
section.top_margin = section.bottom_margin = Cm(1)  # 上下页边距为1厘米

# 绘制并保存图片
plt.plot(x_smooth, y_smooth)
plt.scatter(x_values, y_values, color='red')  # 绘制数据点
plt.plot(x_smootha, y_smootha)
plt.scatter(x_valuesa, y_valuesa, color='red')  # 绘制数据点
plt.xlabel('x$_{VN}$/mL')
plt.ylabel('OD$_{527}$')
plt.title('Correction curve of ΔD-x$_V$')
plt.grid(True)
plt.ylim(-0.05, 0.75)




# 计算第一个切线的截距
intercept1 = y_values[1] - slope1 * x_values[1]

# 切线方程
x_tangent1 = np.linspace(x_values[1], x_values[3], 100)
y_tangent1 = slope1 * x_tangent1 + intercept1

# 绘制第一个切线
plt.plot(x_tangent1, y_tangent1, linestyle='--', color='blue')



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

# 计算第一个切线的斜率（在第二个数据点处）
slope1a = spl_a.derivative(nu=1)(x_valuesa[1])

# 计算第一个切线的截距
intercept1a = y_valuesa[1] - slope1a * x_valuesa[1]

# 切线方程
x_tangent1a = np.linspace(x_valuesa[1], x_valuesa[3], 100)
y_tangent1a = slope1a * x_tangent1a + intercept1a

# 绘制第一个切线
plt.plot(x_tangent1a, y_tangent1a, linestyle='--', color='blue')

# 计算第二个切线的斜率（在第四个数据点处）
slope2a = spl_a.derivative(nu=1)(x_valuesa[4])

# 计算第二个切线的截距
intercept2a = y_valuesa[4] - slope2a * x_valuesa[4]

# 第二个切线方程
x_tangent2a = np.linspace(x_valuesa[1], x_valuesa[4], 100)
y_tangent2a = slope2a * x_tangent2a + intercept2a

# 绘制第二个切线
plt.plot(x_tangent2a, y_tangent2a, linestyle='--', color='green')

# 计算两条切线的交点坐标
intersection_xa = (intercept2a - intercept1a) / (slope1a - slope2a)
intersection_ya = slope1a * intersection_xa + intercept1a


# 绘制直线y=0.1 (0<x<0.2)
x_line = np.linspace(0, 0.2, 100)  # 创建x值数组
y_line = 0.1 * np.ones_like(x_line)  # 对应的y值数组

# 绘制图像
plt.plot(x_smooth, y_smooth)
plt.scatter(x_values, y_values, color='red')
plt.plot(x_smootha, y_smootha)
plt.scatter(x_valuesa, y_valuesa, color='red')

# 添加直线y=0.1 (0<x<0.2)
plt.plot(x_line, y_line, linestyle='-', color='orange')  # 绘制直线

from scipy.optimize import fsolve
# 查找交点的函数
def find_intersection(x):
    return spl(x) - 0.1


def find_intersection_a(x):
    return spl_a(x) - 0.1


# 查找第一个交点
x_intersection = fsolve(find_intersection, [0, 0.04])[0]
print(f"Intersection with Curve 1 at x = {x_intersection}")

# 查找第二个交点
x_intersection_a = fsolve(find_intersection_a, [0, 0.04])[0]
print(f"Intersection with Curve 2 at x = {x_intersection_a}")


# 保存图片
temp_img_path = os.path.join(doc_path, "temp.png")
plt.savefig(temp_img_path)

# 在图片下方写入交点坐标和切线方程
doc.add_paragraph("Data Processing")
doc.add_picture(temp_img_path, width=Inches(3.5))
doc.add_paragraph("Equations of two tangents:")
doc.add_paragraph(f"Tangent 1: y = {slope1:.2f}x + {intercept1:.2f}")
doc.add_paragraph(f"Tangent 2: y = {slope2:.2f}x + {intercept2:.2f}")
doc.add_paragraph(f"Intersection point coordinates: ({intersection_x:.3f}, {intersection_y:.3f})")
doc.add_paragraph("Equations of two tangents:")
doc.add_paragraph(f"Tangent 1: y = {slope1a:.2f}x + {intercept1a:.2f}")
doc.add_paragraph(f"Tangent 2: y = {slope2a:.2f}x + {intercept2a:.2f}")
doc.add_paragraph(f"Intersection point coordinates: ({intersection_xa:.3f}, {intersection_ya:.3f})")
doc.add_paragraph(f"x_VN1={x_intersection:.3f}, x_VN2={x_intersection_a:.3f}")

a1 = x_intersection * 0.002
a2 = x_intersection_a * 0.002
b1 = (0.2 - x_intersection) * 0.002
b2 = (0.4 - x_intersection_a) * 0.002
import math
import os
import io
import sys

# 定义要保存输出内容的文件路径
# file_path = r"F:\大二下\物化实验\output.txt"
file_path = os.path.join(folder_path, "output.txt")

# 检查文件是否存在，如果存在则删除
if os.path.exists(file_path):
    os.remove(file_path)

# 创建一个字符串IO对象来捕获print函数的输出
output = io.StringIO()

# 保存原始sys.stdout的引用
original_stdout = sys.stdout

# 将sys.stdout重定向到我们的StringIO对象
sys.stdout = output

# 解方程
denominator = a1 + b1 - a2 - b2
if denominator == 0:
    print("方程无解或有无穷多解，因为分母为零。")
else:
    x_value = (a1 * b1 - a2 * b2) / denominator
    print(f"解出的x值为：{x_value}")

    # 计算k值
    k_value = x_value / ((a1 - x_value) * (b1 - x_value))
    print(f"计算出的k值为：{k_value}")

    # 计算dG值
    T = 20.2 + 273.15  # 温度，单位：开尔文
    R = 8.314  # 气体常数，单位：J/(mol*K)
    dG_value = -R * T * math.log(k_value)
    print(f"计算出的dG值为：{dG_value:.3f} J/mol")  # 保留两位小数

import pandas as pd
import numpy as np


# 使用pandas读取Excel文件
df = pd.read_excel(excel_file_path)

# 提取x轴和y轴的数据（N3到R3为x轴，N4到R4为y轴）
x_data = df.iloc[1, 13:18].values
y_data = df.iloc[2, 13:18].values

# 确保x_data和y_data是float类型
x_data = x_data.astype(float)
y_data = y_data.astype(float)

# 因为我们想要强制纵截距为0，我们可以通过简单的线性代数来计算斜率
# y = mx，其中m是斜率，x是x_data，y是y_data
# 我们可以通过求解线性方程组 Ax = b 来找到斜率m，其中A是x_data组成的矩阵，b是y_data组成的向量
# 但因为x_data是一维数组，我们只需要简单的除法操作即可

# 计算斜率，强制纵截距为0
slope_variable = np.sum(x_data * y_data) / np.sum(x_data ** 2)

xn1 = intersection_y/slope_variable
cn1 = 0.002*xn1
kn1 = cn1/((0.002*intersection_x-cn1)*(0.002*(0.2-intersection_x)-cn1))
dGn1 = -R * T * math.log(kn1)
xn2 = intersection_ya/slope_variable
cn2 = 0.002*xn2
kn2 = cn2/((0.004*intersection_xa-cn2)*(0.004*(0.2-intersection_xa)-cn2))
dGn2 = -R * T * math.log(kn2)
# 分别print这些值
print(f"xn1: {xn1}")
print(f"cn1: {cn1}")
print(f"kn1: {kn1}")
print(f"dGn1: {dGn1:.2f}")  # 保留两位小数
print(f"xn2: {xn2}")
print(f"cn2: {cn2}")
print(f"kn2: {kn2}")
print(f"dGn2: {dGn2:.2f}")  # 保留两位小数

# 将sys.stdout重定向回原始输出
sys.stdout = original_stdout

# 获取保存在StringIO对象中的输出内容
output_content = output.getvalue()

# 将输出内容写入到文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(output_content)

print(f"输出已保存到 {file_path}")


# 保存Word文档
doc.save(full_doc_path)

