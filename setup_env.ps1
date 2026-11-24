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
$pyReady = Test-Path $pyExe
if ($pyReady) {
    # 有 python.exe 也可能是解压中断留下的半截目录，先确认它跑得起来。
    # 注意：Windows PowerShell 5.1 在 Stop 模式下会把原生命令的 stderr 当成终止错误，所以要 try 住
    try {
        & $pyExe -c "import sys" 2>$null
        if ($LASTEXITCODE -ne 0) { $pyReady = $false }
    } catch { $pyReady = $false }
    if (-not $pyReady) { Note "已有 python.exe 但无法运行，重新解压一份。" }
}

if (-not $pyReady) {
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
} else {
    Ok ("已存在便携 Python：" + $pyExe)
}

# ---------- 3. 安装 pip ----------
# get-pip.py 必须放在 runtime\python\ 里，和 python.exe 同目录并在该目录下运行：
# 便携版的库搜索路径由 python312._pth 固定在 exe 旁边，放错目录会装不上 pip。
# 这一步不放在「是否新下载 Python」分支里，否则 python 在、pip 坏了时重跑脚本会直接跳过。
Step "检查 pip"
# 用文件判断，不调 python：5.1 下 `python -m pip --version` 失败时会往 stderr 写一行，
# 被重定向后变成终止错误，脚本会直接崩在探测这一步。
$pipDir = Join-Path $pyDir "Lib\site-packages\pip"
$pipOk = Test-Path (Join-Path $pipDir "__init__.py")
if ($pipOk) {
    Ok "pip 已就绪"
} else {
    Step "安装 pip（只需一次）"
    $getpip = Join-Path $pyDir "get-pip.py"
    # 旧版本把 get-pip.py 错放在 runtime\ 里，顺手清理掉
    Remove-Item (Join-Path $runtime "get-pip.py") -Force -ErrorAction SilentlyContinue
    $pipUrls = @(
        "https://bootstrap.pypa.io/get-pip.py",
        "https://mirrors.aliyun.com/pypi/get-pip.py"
    )
    $gotPip = $false
    foreach ($u in $pipUrls) {
        Note ("下载：" + $u)
        if (Get-File $u $getpip 100000) { $gotPip = $true; break }
        Note "该地址不可用，换下一个。"
    }
    if (-not $gotPip) {
        Fail "pip 安装包下载失败，请检查网络。"
        exit 1
    }

    $pipIndexes = @(
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "https://mirrors.aliyun.com/pypi/simple",
        "https://pypi.org/simple"
    )
    foreach ($idx in $pipIndexes) {
        Push-Location $pyDir
        & $pyExe "get-pip.py" --no-warn-script-location -i $idx
        $code = $LASTEXITCODE
        Pop-Location
        if ($code -eq 0) { break }
        Note "这个镜像没装上，换下一个。"
    }

    if (-not (Test-Path (Join-Path $pipDir "__init__.py"))) {
        Fail "pip 没装上。请手动执行下面两行（get-pip.py 就在该目录里）："
        Write-Host ("  cd /d " + $pyDir) -ForegroundColor Yellow
        Write-Host "  python.exe get-pip.py" -ForegroundColor Yellow
        exit 1
    }
    Remove-Item $getpip -Force -ErrorAction SilentlyContinue
    Ok "pip 就绪"
}

# ---------- 4. 安装依赖库 ----------
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

# ---------- 5. 自检 ----------
Step "自检"
Push-Location $root
# 这两步都把输出写文件；5.1 下 stderr 被重定向时会变成终止错误，所以统一 try 住按退出码判断
$impLog = Join-Path $runtime "import.log"
$impCode = 0
try {
    & $pyExe -c "import flask, numpy, pandas, scipy, openpyxl" *> $impLog
    $impCode = $LASTEXITCODE
} catch {
    $impCode = 1
    try { $_ | Out-String | Add-Content -Path $impLog -Encoding UTF8 } catch {}
}
if ($impCode -ne 0) {
    Pop-Location
    Fail ("依赖导入失败，详见 " + $impLog)
    exit 1
}
$stamp = Join-Path $runtime "selftest.log"
$code = 0
try {
    & $pyExe -m app.selftest *> $stamp
    $code = $LASTEXITCODE
} catch {
    $code = 1
    try { $_ | Out-String | Add-Content -Path $stamp -Encoding UTF8 } catch {}
}
Pop-Location
if ($code -ne 0) {
    Fail ("自检未通过，详见 " + $stamp)
    exit 1
}
Ok "自检通过（19 个实验模块全部可算）"
Ok "环境准备完成，下次启动无需再下载"
exit 0
