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

if ($SourceSelfTest) {
    Invoke-Native { & $Python -m fh6_sniper.main --self-test }
}

Invoke-Native { & $Python -m PyInstaller --clean --noconfirm packaging\FH6-Sniper.spec }

$Exe = Join-Path $Root "dist\FH6-Sniper\FH6-Sniper.exe"
$Process = Start-Process -FilePath $Exe -ArgumentList "--self-test" -Wait -PassThru
Get-Content (Join-Path $Root "dist\FH6-Sniper\logs\self-test.log")
if ($Process.ExitCode -ne 0) {
    exit $Process.ExitCode
}

Write-Host "Build ready: $Exe"
