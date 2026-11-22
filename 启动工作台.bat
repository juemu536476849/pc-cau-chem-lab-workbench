@echo off
chcp 936 >nul 2>nul
setlocal EnableExtensions
cd /d "%~dp0"
title 物化-化工实验数据处理工作台
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if not exist "app\server.py" (
  echo.
  echo  找不到 app\server.py，请确认整个文件夹是完整拷贝的。
  pause
  exit /b 1
)

set "LOCAL_PY=%~dp0runtime\python\python.exe"

if exist "%LOCAL_PY%" (
  "%LOCAL_PY%" -c "import flask, numpy, pandas, scipy, openpyxl" >nul 2>nul
  if not errorlevel 1 goto launch_local
)

python -c "import flask, numpy, pandas, scipy, openpyxl" >nul 2>nul
if not errorlevel 1 goto launch_sys

echo.
echo  ============================================================
echo   首次运行：正在自动准备运行环境
echo   需要联网下载 Python 与计算库，共约 90 MB，只需一次
echo  ============================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_env.ps1"
if errorlevel 1 goto fail

if exist "%LOCAL_PY%" goto launch_local
goto launch_sys

:launch_local
"%LOCAL_PY%" -m app.server
goto done

:launch_sys
python -m app.server
goto done

:fail
echo.
echo  环境准备没有完成。可以查看 runtime\setup.log，
echo  或手动安装 Python 3.10 以上版本后，再双击本文件。
pause
exit /b 1

:done
if errorlevel 1 (
  echo.
  echo  工作台异常退出，请把上面的提示截图反馈。
  pause
)
endlocal
