import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from docx import Document
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from io import BytesIO
import os

# 读取Excel文件
file_path = 'F:\大二下\物化实验\A4\A4数据处理.xlsx'
sheet_name = 'Sheet1 (2)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 提取数据
x = df['sqr.c'][12:16]
y = df['Am'][12:16]

# 设置matplotlib参数，以支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

# 线性拟合
slope, intercept = np.polyfit(x, y, 1)

# 绘制散点图和拟合直线
plt.scatter(x, y, label='散点数据')
plt.plot(x, slope * x + intercept, 'r-', label=f'拟合直线: y = {slope:.4f}x + {intercept:.4f}')
plt.title('HAc溶液Λm-sqrt(c) 图')
plt.xlabel('sqrt(c)')
plt.ylabel('Λm')
plt.legend()
plt.grid(True)

# 保存图表到BytesIO对象
buf = BytesIO()
plt.savefig(buf, format='png')
plt.close()
buf.seek(0)


# 转换毫米到点（假设96 DPI）
def mm_to_points(mm):
    # 每英寸点数
    DPI = 96
    # 每毫米点数
    POINTS_PER_MM = DPI / 25.4
    # 转换毫米到点并四舍五入到最接近的整数
    return round(mm * POINTS_PER_MM)


# 创建Word文档并设置默认字体
doc = Document()
doc.styles['Normal'].font.name = '宋体'
doc.styles['Normal'].font.size = Pt(12)  # 小四号字体通常对应12磅

# 获取第一个section对象
section = doc.sections[0]

# 设置页面大小（148mm×210mm），转换为点并四舍五入到整数
section.page_width = Pt(mm_to_points(148))
section.page_height = Pt(mm_to_points(210))

# 设置页边距（假设页边距也是以毫米为单位，并转换为点）
section.top_margin = Pt(mm_to_points(19.05))  # 假设页边距为19.05mm
section.bottom_margin = Pt(mm_to_points(19.05))
section.left_margin = Pt(mm_to_points(19.05))
section.right_margin = Pt(mm_to_points(19.05))

# 读取图片到Word文档
doc = Document()
doc.add_picture(buf, width=Inches(3.5))

# 添加图片题注并居中
p = doc.add_paragraph('HAc溶液Λm-sqrt(c) 散点图及线性拟合直线')
p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

# 添加线性拟合直线方程
doc.add_paragraph(f'线性拟合直线方程: y = {slope:.4f}x + {intercept:.4f}')

# 添加相关系数
doc.add_paragraph(f'相关系数: r = {stats.linregress(x, y).rvalue:.4f}')

# # 添加一个段落
# am_infty_paragraph = doc.add_paragraph()
#
# # 添加A和设置m为下标
# run = am_infty_paragraph.add_run('A')
# run_m = am_infty_paragraph.add_run('m')
# run_m.font.subscript = True  # 设置m为下标
#
# # 添加∞并设置为上标
# run_infty = am_infty_paragraph.add_run('∞')
# run_infty.font.superscript = True  # 设置∞为上标
#
# # 添加文本和纵截距的值
# run = am_infty_paragraph.add_run(f'的值（线性拟合直线方程的纵截距）: {intercept:.4f}')

# 获取Excel文件所在文件夹路径
excel_dir = os.path.dirname(file_path)

# 定义Word文档名称
word_filename = os.path.join(excel_dir, 'A4数据处理4.docx')

# 检查文件是否存在，如果存在则删除
if os.path.exists(word_filename):
    os.remove(word_filename)

# 保存Word文档
doc.save(word_filename)

# 输出提示信息
print(f'Word文档已保存到：{word_filename}')