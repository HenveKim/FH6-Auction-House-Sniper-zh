param(
    [string]$PythonExe = "python",
    [switch]$RecreateVenv,
    [switch]$SourceSelfTest
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

function Test-TkinterRuntime {
    & $Python -c "import tkinter as tk; root=tk.Tk(); root.withdraw(); root.update_idletasks(); root.destroy(); print('tkinter runtime ok')"
    if ($LASTEXITCODE -ne 0) {
        throw "Build Python cannot start Tkinter. Use a clean official Python with Tcl/Tk, then run: .\scripts\build.ps1 -PythonExe C:\Path\To\python.exe -RecreateVenv"
    }
}

$Venv = Join-Path $Root ".venv-build"
$Python = Join-Path $Venv "Scripts\python.exe"

if ($RecreateVenv -and (Test-Path $Venv)) {
    Remove-Item -LiteralPath $Venv -Recurse -Force
}

if (-not (Test-Path $Python)) {
    Invoke-Native { & $PythonExe -m venv $Venv }
}

Invoke-Native { & $Python -m pip install --upgrade pip }
Invoke-Native { & $Python -m pip install -r requirements.md }
Test-TkinterRuntime

if ($SourceSelfTest) {
    Invoke-Native { & $Python -m fh6_sniper.main --self-test }
}

Invoke-Native { & $Python -m PyInstaller --clean --noconfirm packaging\FH6-Sniper.spec }

$Exe = Join-Path $Root "dist\FH6-Sniper\FH6-Sniper.exe"
$ExeDir = Split-Path -Parent $Exe
$SelfTestRequest = Join-Path $ExeDir "self-test.request"
$SelfTestLog = Join-Path $ExeDir "logs\self-test.log"
if (Test-Path $SelfTestLog) {
    Remove-Item -LiteralPath $SelfTestLog -Force
}
Set-Content -LiteralPath $SelfTestRequest -Value "1" -Encoding ASCII
$OldSelfTest = [Environment]::GetEnvironmentVariable(
    "FH6_SNIPER_SELF_TEST", "Process")
[Environment]::SetEnvironmentVariable("FH6_SNIPER_SELF_TEST", "1", "Process")
try {
    $Process = Start-Process -FilePath $Exe -ArgumentList "--self-test" -PassThru
    if (-not $Process.WaitForExit(30000)) {
        Stop-Process -Id $Process.Id -Force
        throw "Packaged self-test timed out"
    }
} finally {
    [Environment]::SetEnvironmentVariable(
        "FH6_SNIPER_SELF_TEST", $OldSelfTest, "Process")
    if (Test-Path $SelfTestRequest) {
        Remove-Item -LiteralPath $SelfTestRequest -Force
    }
}
Get-Content $SelfTestLog
if ($Process.ExitCode -ne 0) {
    exit $Process.ExitCode
}

Write-Host "Build ready: $Exe"
