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
import pyperclip

# 提示用户复制路径到剪贴板
print("请使用Ctrl+Shift+C复制文件路径到剪贴板，然后按Enter继续。")
input("按Enter继续...")  # 等待用户按下Enter键

# 从剪贴板获取路径
file_path_from_clipboard = pyperclip.paste()

# 删除所有的双引号
file_path = file_path_from_clipboard.replace('"', '')

# 检查路径是否存在
if os.path.exists(file_path):
    print(f"文件路径已获取：{file_path}")
    # 接下来你可以使用这个路径做你想做的事情，比如打开Excel文件等
else:
    print("提供的路径不存在，请检查剪贴板中的路径是否正确。")
sheet_name = 'Sheet1 (2)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 提取数据
x = df['sqr.c'][0:4]
y = df['Am'][0:4]

# 设置matplotlib参数，以支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

# 线性拟合
slope, intercept = np.polyfit(x, y, 1)

# 绘制散点图和拟合直线
plt.scatter(x, y, label='散点数据')
plt.plot(x, slope * x + intercept, 'r-', label=f'拟合直线: y = {slope:.4f}x + {intercept:.4f}')
plt.title('NaCl溶液Λm-sqrt(c) 图')
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
p = doc.add_paragraph('NaCl溶液Λm-sqrt(c) 散点图及线性拟合直线')
p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

# 添加线性拟合直线方程
doc.add_paragraph(f'线性拟合直线方程: y = {slope:.4f}x + {intercept:.4f}')

# 添加相关系数
doc.add_paragraph(f'相关系数: r = {stats.linregress(x, y).rvalue:.4f}')

# 添加一个段落
am_infty_paragraph = doc.add_paragraph()

# 添加A和设置m为下标
run = am_infty_paragraph.add_run('A')
run_m = am_infty_paragraph.add_run('m')
run_m.font.subscript = True  # 设置m为下标

# 添加∞并设置为上标
run_infty = am_infty_paragraph.add_run('∞')
run_infty.font.superscript = True  # 设置∞为上标

# 添加文本和纵截距的值
run = am_infty_paragraph.add_run(f'的值（线性拟合直线方程的纵截距）: {intercept:.4f}')

# 获取Excel文件所在文件夹路径
excel_dir = os.path.dirname(file_path)

# 定义Word文档名称
word_filename = os.path.join(excel_dir, 'A4数据处理1.docx')

# 检查文件是否存在，如果存在则删除
if os.path.exists(word_filename):
    os.remove(word_filename)

# 保存Word文档
doc.save(word_filename)

# 输出提示信息
print(f'Word文档已保存到：{word_filename}')

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
sheet_name = 'Sheet1 (2)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 提取数据
x = df['sqr.c'][4:8]
y = df['Am'][4:8]

# 设置matplotlib参数，以支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

# 线性拟合
slope, intercept = np.polyfit(x, y, 1)

# 绘制散点图和拟合直线
plt.scatter(x, y, label='散点数据')
plt.plot(x, slope * x + intercept, 'r-', label=f'拟合直线: y = {slope:.4f}x + {intercept:.4f}')
plt.title('HCl溶液Λm-sqrt(c) 图')
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
p = doc.add_paragraph('HCl溶液Λm-sqrt(c) 散点图及线性拟合直线')
p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

# 添加线性拟合直线方程
doc.add_paragraph(f'线性拟合直线方程: y = {slope:.4f}x + {intercept:.4f}')

# 添加相关系数
doc.add_paragraph(f'相关系数: r = {stats.linregress(x, y).rvalue:.4f}')

# 添加一个段落
am_infty_paragraph = doc.add_paragraph()

# 添加A和设置m为下标
run = am_infty_paragraph.add_run('A')
run_m = am_infty_paragraph.add_run('m')
run_m.font.subscript = True  # 设置m为下标

# 添加∞并设置为上标
run_infty = am_infty_paragraph.add_run('∞')
run_infty.font.superscript = True  # 设置∞为上标

# 添加文本和纵截距的值
run = am_infty_paragraph.add_run(f'的值（线性拟合直线方程的纵截距）: {intercept:.4f}')

# 获取Excel文件所在文件夹路径
excel_dir = os.path.dirname(file_path)

# 定义Word文档名称
word_filename = os.path.join(excel_dir, 'A4数据处理2.docx')

# 检查文件是否存在，如果存在则删除
if os.path.exists(word_filename):
    os.remove(word_filename)

# 保存Word文档
doc.save(word_filename)

# 输出提示信息
print(f'Word文档已保存到：{word_filename}')

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
sheet_name = 'Sheet1 (2)'
df = pd.read_excel(file_path, sheet_name=sheet_name)

# 提取数据
x = df['sqr.c'][8:12]
y = df['Am'][8:12]

# 设置matplotlib参数，以支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

# 线性拟合
slope, intercept = np.polyfit(x, y, 1)

# 绘制散点图和拟合直线
plt.scatter(x, y, label='散点数据')
plt.plot(x, slope * x + intercept, 'r-', label=f'拟合直线: y = {slope:.4f}x + {intercept:.4f}')
plt.title('NaAc溶液Λm-sqrt(c) 图')
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
p = doc.add_paragraph('NaAc溶液Λm-sqrt(c) 散点图及线性拟合直线')
p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

# 添加线性拟合直线方程
doc.add_paragraph(f'线性拟合直线方程: y = {slope:.4f}x + {intercept:.4f}')

# 添加相关系数
doc.add_paragraph(f'相关系数: r = {stats.linregress(x, y).rvalue:.4f}')

# 添加一个段落
am_infty_paragraph = doc.add_paragraph()

# 添加A和设置m为下标
run = am_infty_paragraph.add_run('A')
run_m = am_infty_paragraph.add_run('m')
run_m.font.subscript = True  # 设置m为下标

# 添加∞并设置为上标
run_infty = am_infty_paragraph.add_run('∞')
run_infty.font.superscript = True  # 设置∞为上标

# 添加文本和纵截距的值
run = am_infty_paragraph.add_run(f'的值（线性拟合直线方程的纵截距）: {intercept:.4f}')

# 获取Excel文件所在文件夹路径
excel_dir = os.path.dirname(file_path)

# 定义Word文档名称
word_filename = os.path.join(excel_dir, 'A4数据处理3.docx')

# 检查文件是否存在，如果存在则删除
if os.path.exists(word_filename):
    os.remove(word_filename)

# 保存Word文档
doc.save(word_filename)

# 输出提示信息
print(f'Word文档已保存到：{word_filename}')

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

from docx import Document
from docxcompose.composer import Composer
from pathlib import Path


def delete_file(file_path):
    file_path = Path(file_path)
    if file_path.exists():
        file_path.unlink()
        print(f"文件 {file_path} 已删除。")
    else:
        print(f"文件 {file_path} 不存在，无需删除。")


def combine_docx_files_in_folder(folder_path, output_file):
    # 转换路径为Path对象
    folder_path = Path(folder_path)
    output_file = Path(output_file)

    # 删除已存在的输出文件
    delete_file(output_file)

    # 创建一个空的Document对象作为主文档
    master_doc = Document()

    # 初始化Composer对象，使用刚才创建的Document对象
    composer = Composer(master_doc)

    # 遍历文件夹中的所有.docx文件
    for filename in folder_path.glob('*.docx'):
        if filename.name != output_file.name:  # 使用文件名而不是完整路径来比较
            # 将文件添加到Composer中
            composer.append(Document(str(filename)))  # 将Path对象转换为字符串路径

    # 保存到输出文件
    composer.save(str(output_file))
    print(f"文件已合并到 {output_file}")


# 调用函数进行文件合并
# excel_dir = r'F:\大二下\物化实验\A4'  # 文件夹路径，从excel_dir变量获取
output_file_path = 'A4数据处理.docx'  # 输出文件路径

combine_docx_files_in_folder(excel_dir, output_file_path)
