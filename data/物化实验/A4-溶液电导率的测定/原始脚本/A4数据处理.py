import subprocess
import os

# 定义要运行的Python文件列表
python_files = [
    "F:\\大二下\\物化实验\\A4\\A4数据处理1.py",
    "F:\\大二下\\物化实验\\A4\\A4数据处理2.py",
    "F:\\大二下\\物化实验\\A4\\A4数据处理3.py",
    "F:\\大二下\\物化实验\\A4\\A4数据处理4.py"
]

# 依次运行每个Python文件
for file_path in python_files:
    # 检查文件是否存在
    if os.path.isfile(file_path):
        # 使用Python解释器运行文件
        try:
            subprocess.run(["python", file_path], check=True)
            print(f"成功运行：{file_path}")
        except subprocess.CalledProcessError as e:
            print(f"运行失败：{file_path}，错误信息：{e}")
    else:
        print(f"文件不存在：{file_path}")

print("所有文件运行完毕。")

import os
from docx import Document
from docxcompose.composer import Composer


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"文件 {file_path} 已删除。")
    else:
        print(f"文件 {file_path} 不存在，无需删除。")


def combine_docx_files_in_folder(folder_path, output_file):
    # 删除已存在的输出文件
    delete_file(output_file)

    # 创建一个空的Document对象作为主文档
    master_doc = Document()

    # 初始化Composer对象，使用刚才创建的Document对象
    composer = Composer(master_doc)

    # 遍历文件夹中的所有.docx文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.docx') and filename != os.path.basename(output_file):
            file_path = os.path.join(folder_path, filename)
            # 将文件添加到Composer中
            composer.append(Document(file_path))

            # 保存到输出文件
    composer.save(output_file)
    print(f"文件已合并到 {output_file}")


# 调用函数进行文件合并
folder_to_merge = r'F:\大二下\物化实验\A4'  # 文件夹路径
output_file_path = 'A4数据处理.docx'  # 输出文件路径

combine_docx_files_in_folder(folder_to_merge, output_file_path)

# # 打开生成的A4数据处理.docx文件
# if os.path.exists(output_file_path):
#     os.startfile(output_file_path)
# else:
#     print(f"文件 {output_file_path} 不存在，无法打开。")
