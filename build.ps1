param(
    [string]$PythonExe = "python",
    [switch]$RecreateVenv
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Venv = Join-Path $Root ".venv-build"
$Python = Join-Path $Venv "Scripts\python.exe"

if ($RecreateVenv -and (Test-Path $Venv)) {
    Remove-Item -LiteralPath $Venv -Recurse -Force
}

if (-not (Test-Path $Python)) {
    & $PythonExe -m venv $Venv
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
& $Python -m pip install -r requirements-build.txt
& $Python -m fh6_sniper.main --self-test
& $Python -m PyInstaller --clean --noconfirm FH6-Sniper.spec

$Exe = Join-Path $Root "dist\FH6-Sniper\FH6-Sniper.exe"
$Process = Start-Process -FilePath $Exe -ArgumentList "--self-test" -Wait -PassThru
Get-Content (Join-Path $Root "dist\FH6-Sniper\logs\self-test.log")
if ($Process.ExitCode -ne 0) {
    exit $Process.ExitCode
}

Write-Host "Build ready: $Exe"
