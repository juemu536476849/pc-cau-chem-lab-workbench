import subprocess
import shutil
import os

# 定义源文件和目标路径
source_script = 'A4数据处理0.py'
target_dir = 'F:\\大二下\\物化实验\\A4\\'
dist_dir = os.path.join(target_dir, 'dist')
build_dir = os.path.join(target_dir, 'build')
exe_name = os.path.splitext(source_script)[0] + '.exe'
exe_path = os.path.join(dist_dir, exe_name)
spec_path = os.path.join(target_dir, 'A4数据处理0.spec')  # 定义spec文件路径

# 执行PyInstaller命令
subprocess.run(['pyinstaller', '--onefile', source_script], check=True)

# 复制生成的exe文件到目标目录（在删除之前）
if os.path.exists(exe_path):
    shutil.copy(exe_path, target_dir)
    print(f"The executable file has been copied to {target_dir}")
else:
    print("Executable file not found. Please check PyInstaller output.")


# # 删除目标目录中的build和dist文件夹
# def delete_directory(directory):
#     if os.path.exists(directory):
#         shutil.rmtree(directory)
#         print(f"The directory {directory} has been deleted.")
#     else:
#         print(f"The directory {directory} does not exist.")
#
#     # 删除指定的文件
#
#
# def delete_file(file_path):
#     if os.path.exists(file_path):
#         os.remove(file_path)
#         print(f"The file {file_path} has been deleted.")
#     else:
#         print(f"The file {file_path} does not exist.")
#
#     # 删除build和dist目录
#
#
# delete_directory(build_dir)
# delete_directory(dist_dir)
#
# # 删除A4数据处理0.spec文件
# delete_file(spec_path)