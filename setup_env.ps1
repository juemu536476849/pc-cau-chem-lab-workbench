param([switch]$Force)
$ErrorActionPreference = "Stop"
# 子进程统一 UTF-8；自检输出写文件，避免控制台代码页把中文弄乱
$env:PYTHONIOENCODING = "utf-8"
$ProgressPreference = "SilentlyContinue"

$root    = $PSScriptRoot
$runtime = Join-Path $root "runtime"
$pyDir   = Join-Path $runtime "python"
$pyExe   = Join-Path $pyDir "python.exe"
$logFile = Join-Path $runtime "setup.log"
$reqFile = Join-Path $root "requirements.txt"
$version = "3.12.8"

New-Item -ItemType Directory -Force -Path $runtime | Out-Null

# pip 需要一个可写的临时目录；有些启动方式下 TMP 会被设成无效路径
$env:TMP  = [System.IO.Path]::GetTempPath()
$env:TEMP = $env:TMP
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"

function Log([string]$text) {
    try { Add-Content -Path $logFile -Value $text -Encoding UTF8 } catch {}
}
function Step([string]$text) {
    Write-Host ""
    Write-Host ("==> " + $text) -ForegroundColor Cyan
    Log ("==> " + $text)
}
function Ok([string]$text) {
    Write-Host ("  [OK] " + $text) -ForegroundColor Green
    Log ("  [OK] " + $text)
}
function Note([string]$text) {
    Write-Host ("  " + $text) -ForegroundColor Gray
    Log ("  " + $text)
}
function Fail([string]$text) {
    Write-Host ("  " + $text) -ForegroundColor Red
    Log ("  [FAIL] " + $text)
}

function Test-Python([string]$exe) {
    if (-not $exe -or -not (Test-Path $exe)) { return $false }
    try {
        & $exe -c "import sys; assert sys.version_info >= (3,10)" 2>$null
        if ($LASTEXITCODE -ne 0) { return $false }
        & $exe -c "import flask, numpy, pandas, scipy, openpyxl" 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Get-File([string]$url, [string]$out, [int]$minBytes) {
    if (-not $minBytes) { $minBytes = 100000 }
    try { if (Test-Path $out) { Remove-Item $out -Force } } catch {}
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curl) {
        & $curl.Source -L --retry 3 --retry-delay 2 --silent --show-error -o $out $url 2>$null
        if ($LASTEXITCODE -eq 0 -and (Test-Path $out) -and ((Get-Item $out).Length -gt $minBytes)) { return $true }
        Note ("curl 返回 " + $LASTEXITCODE)
    }
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -TimeoutSec 180
        if ((Test-Path $out) -and ((Get-Item $out).Length -gt $minBytes)) { return $true }
    } catch {
        Note ("下载异常：" + $_.Exception.Message)
    }
    return $false
}

Write-Host ""
Write-Host "  物化 / 化工实验数据处理工作台 - 运行环境准备" -ForegroundColor White
Write-Host "  ----------------------------------------------------" -ForegroundColor DarkGray

# ---------- 1. 已有可用的 Python 就直接用 ----------
Step "检查这台电脑上可用的 Python"
$candidates = @()
$candidates += $pyExe
$sysCmd = Get-Command python -ErrorAction SilentlyContinue
if ($sysCmd) { $candidates += $sysCmd.Source }
$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pyCmd) {
    try { $candidates += (& $pyCmd.Source -3 -c "import sys; print(sys.executable)" 2>$null) } catch {}
}

if (-not $Force) {
    foreach ($c in $candidates) {
        if (Test-Python $c) {
            Ok ("已找到可用的 Python：" + $c)
            Note "依赖齐全，无需下载安装。"
            exit 0
        } elseif ($c -and (Test-Path $c)) {
            Note ("发现 Python，但缺少依赖：" + $c)
        }
    }
}

# ---------- 2. 下载便携版 Python（免安装、不需要管理员权限） ----------
if (-not (Test-Path $pyExe)) {
    Step ("下载 Python " + $version + " 便携版（约 11 MB，只需一次）")
    $zip = Join-Path $runtime "python-embed.zip"
    $zipUrls = @(
        "https://mirrors.huaweicloud.com/python/$version/python-$version-embed-amd64.zip",
        "https://registry.npmmirror.com/-/binary/python/$version/python-$version-embed-amd64.zip",
        "https://www.python.org/ftp/python/$version/python-$version-embed-amd64.zip"
    )
    $got = $false
    foreach ($u in $zipUrls) {
        Note ("下载：" + $u)
        if (Get-File $u $zip 5000000) { $got = $true; break }
        Note "该地址不可用，换下一个。"
    }
    if (-not $got) {
        Fail "下载失败。请检查网络后重试，或手动安装 Python 3.10+ 再双击启动脚本。"
        exit 1
    }
    Ok "下载完成"

    Step "解压到项目目录"
    if (Test-Path $pyDir) { Remove-Item $pyDir -Recurse -Force -ErrorAction SilentlyContinue }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $pyDir)
    Remove-Item $zip -Force -ErrorAction SilentlyContinue

    # 让便携版能加载 site-packages（默认被 _pth 屏蔽）
    $pth = Get-ChildItem $pyDir -Filter "python*._pth" | Select-Object -First 1
    if ($pth) {
        $lines = @(Get-Content $pth.FullName)
        $lines = $lines | Where-Object { $_ -notmatch '^\s*#?\s*import site\s*$' -and $_ -notmatch 'site-packages' }
        $lines += "Lib\site-packages","..\..","import site"
        Set-Content -Path $pth.FullName -Value $lines -Encoding ASCII
    }
    Ok ("Python 已就绪：" + $pyExe)

    Step "安装 pip"
    $getpip = Join-Path $runtime "get-pip.py"
    $pipUrls = @(
        "https://bootstrap.pypa.io/get-pip.py",
        "https://mirrors.aliyun.com/pypi/get-pip.py"
    )
    $okPip = $false
    foreach ($u in $pipUrls) {
        if (Get-File $u $getpip 100000) { $okPip = $true; break }
    }
    if (-not $okPip) { Fail "pip 安装包下载失败，请检查网络。"; exit 1 }
    & $pyExe $getpip --no-warn-script-location -i https://pypi.tuna.tsinghua.edu.cn/simple
    Remove-Item $getpip -Force -ErrorAction SilentlyContinue
    Ok "pip 就绪"
} else {
    Ok "已存在便携 Python"
}

# ---------- 3. 安装依赖库 ----------
Step "安装计算所需的库（numpy / pandas / scipy / flask / openpyxl，约 60 MB）"
$indexes = @(
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.org/simple"
)
$ok = $false
foreach ($idx in $indexes) {
    Note ("使用镜像：" + $idx)
    & $pyExe -m pip install --disable-pip-version-check --no-cache-dir --no-warn-script-location -i $idx -r $reqFile
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Note "这个镜像不行，换下一个。"
}
if (-not $ok) {
    Fail "依赖安装失败。请检查网络，或手动执行下面这条命令："
    Write-Host ("  " + $pyExe + " -m pip install -r requirements.txt") -ForegroundColor Yellow
    exit 1
}
Ok "依赖安装完成"

# ---------- 4. 自检 ----------
Step "自检"
Push-Location $root
& $pyExe -c "import flask, numpy, pandas, scipy, openpyxl" *> (Join-Path $runtime "import.log")
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Fail ("依赖导入失败，详见 " + (Join-Path $runtime "import.log"))
    exit 1
}
$stamp = Join-Path $runtime "selftest.log"
& $pyExe -m app.selftest *> $stamp
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) {
    Fail ("自检未通过，详见 " + $stamp)
    exit 1
}
Ok "自检通过（19 个实验模块全部可算）"
Ok "环境准备完成，下次启动无需再下载"
exit 0
