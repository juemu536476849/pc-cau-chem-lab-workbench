import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np
from docx import Document
from docx.shared import Inches
import os

# 读取Excel文件
file_path = r"F:\大二下\物化实验\A1\A1数据处理.xlsx"
df = pd.read_excel(file_path)

# 提取A列和B列数据
x_values = df['时间'].values
y_values = df.iloc[:, 1].values

#摄取拐点
guaip1 = int(input('拐点1横坐标：'))
guaip2 = int(input('拐点2横坐标：'))
endp = int(input('末尾点横坐标：'))

# 绘制数据点
plt.scatter(x_values, y_values, label='Data Points')

# 线性拟合
slope1, intercept1, r_value1, p_value1, std_err1 = stats.linregress(x_values[(x_values >= 0) & (x_values <= guaip1)], y_values[(x_values >= 0) & (x_values <= guaip1)])
slope2, intercept2, r_value2, p_value2, std_err2 = stats.linregress(x_values[(x_values >= guaip2) & (x_values <= endp)], y_values[(x_values >= guaip2) & (x_values <= endp)])

# 绘制第一条直线的原始部分
plt.plot(x_values[(x_values >= 0) & (x_values <= guaip1)], slope1 * x_values[(x_values >= 0) & (x_values <= guaip1)] + intercept1,
         color='red', label='Line 1')

# 延长第一条直线至 x=guaip2 的位置，并使用虚线表示延长部分
x_extend1 = np.linspace(guaip1, guaip2, 100)  # 创建 guaip1 到 guaip2 之间的 100 个点用于绘制延长线
y_extend1 = slope1 * x_extend1 + intercept1  # 计算对应的 y 值
plt.plot(x_extend1, y_extend1, color='red', linestyle='--')  # 绘制延长线部分，使用虚线

# 绘制第二条直线的原始部分
plt.plot(x_values[(x_values >= guaip2) & (x_values <= endp)],
         slope2 * x_values[(x_values >= guaip2) & (x_values <= endp)] + intercept2, color='blue', label='Line 2')

# 延长第二条直线至 x=guaip1 的位置，并使用虚线表示延长部分
x_extend2 = np.linspace(guaip1, x_values[x_values >= guaip2].min(), 100)  # 创建 guaip1 到第二条直线原始部分的最小 x 值之间的点
y_extend2 = slope2 * x_extend2 + intercept2  # 计算对应的 y 值
plt.plot(x_extend2, y_extend2, color='blue', linestyle='--')  # 绘制延长线部分，使用虚线

# 连接两条线的中点
x_mid = [guaip1, guaip2]
y_mid = [(slope1 * guaip1 + intercept1), (slope2 * guaip2 + intercept2)]
mid_point = [(x_mid[0] + x_mid[1]) / 2, (y_mid[0] + y_mid[1]) / 2]

plt.plot(x_mid, y_mid)
plt.plot(mid_point[0], mid_point[1], 'ro', label='Midpoint')


# 画出关于X轴的垂线，使用虚线表示
plt.axvline(x=mid_point[0], linestyle='--', color='orange', label='Vertical Line')

# 计算交点
x_intersect = mid_point[0]
y_intersect1 = slope1 * x_intersect + intercept1
y_intersect2 = slope2 * x_intersect + intercept2

# 标记交点
plt.scatter(x_intersect, y_intersect1, color='red', marker='x', zorder=3)  # zorder确保交点标记在上方
plt.scatter(x_intersect, y_intersect2, color='blue', marker='x', zorder=3)

# 打印第一条直线的方程和相关系数，并用文字标注
print(f"第一条直线的方程为：y = {slope1:.2f}x + {intercept1:.2f}")
print(f"第一条直线的相关系数r为：{r_value1:.2f}")

# 打印第二条直线的方程和相关系数，并用文字标注
print(f"第二条直线的方程为：y = {slope2:.2f}x + {intercept2:.2f}")
print(f"第二条直线的相关系数r为：{r_value2:.2f}")

# 打印交点坐标
print(f"交点1坐标: ({x_intersect:.2f}, {y_intersect1:.2f})")
print(f"交点2坐标: ({x_intersect:.2f}, {y_intersect2:.2f})")
y_difference = - y_intersect2 + y_intersect1
print(f"两个交点纵坐标的差值为: {y_difference:.2f}")

pltendp = endp + 1
plt.xlim(-1, pltendp)
plt.xlabel('t/min')
plt.ylabel('T/℃')
plt.title('KNO3(1)')
plt.legend()
plt.grid(True)

# 指定文件夹路径
folder_path = r'F:\大二下\物化实验\A1'  # 替换为你的文件夹路径

# 保存Word文档到指定文件夹
doc_path = os.path.join(folder_path, 'A1数据处理1.docx')


# 删除同名文件
if os.path.exists(doc_path):
    os.remove(doc_path)

# 创建一个新的Word文档
doc = Document()


# 设置页面大小为A4
sections = doc.sections
for section in sections:
    section.page_height = Inches(11.69)
    section.page_width = Inches(8.27)

# 保存当前的图到一个临时文件
plt.savefig('temp_plot.png', bbox_inches='tight')

# 将图片插入到文档中
doc.add_picture('temp_plot.png', width=Inches(5.8))

# 添加文字到文档
doc.add_paragraph(f"第一条直线的方程为：y = {slope1:.4f}x + {intercept1:.4f}")
doc.add_paragraph(f"第一条直线的相关系数r为：{r_value1:.4f}")

doc.add_paragraph(f"第二条直线的方程为：y = {slope2:.4f}x + {intercept2:.4f}")
doc.add_paragraph(f"第二条直线的相关系数r为：{r_value2:.4f}")

doc.add_paragraph(f"交点1坐标: ({x_intersect:.2f}, {y_intersect1:.4f})")
doc.add_paragraph(f"交点2坐标: ({x_intersect:.2f}, {y_intersect2:.4f})")
doc.add_paragraph(f"两个交点纵坐标的差值为: {y_difference:.4f}")


# 清理临时文件
os.remove('temp_plot.png')

doc.save(doc_path)

from openpyxl import load_workbook
# 指定Excel文件的完整路径
excel_file_path = os.path.join(folder_path, 'output.xlsx')

# 尝试加载现有的工作簿，如果不存在则创建新的工作簿
try:
    wb = load_workbook(excel_file_path)
    print("工作簿已加载。")
except FileNotFoundError:
    print("工作簿不存在，将创建一个新的工作簿。")
    wb = Workbook()

# 获取活动工作表
ws = wb.active

# 获取Python文件的名称（不包含扩展名）
python_file_name = os.path.splitext(os.path.basename(__file__))[0]

# 将Python文件的名称填充到A1单元格
ws['A1'] = f"KNO3(1)"

# 将y_difference的值填充到B1单元格，并格式化到小数点后四位
ws['B1'] = round(y_difference, 4)  # 直接设置值，并四舍五入到四位小数

# 如果你需要确保在Excel中显示为数字而不是科学计数法，你可以设置单元格的number_format
ws['B1'].number_format = '0.0000'  # 设置单元格格式以显示四位小数

# 保存Excel文件到指定文件夹
excel_file_path = os.path.join(folder_path, 'output.xlsx')
wb.save(excel_file_path)

print(f"Excel文件已保存到：{excel_file_path}")

