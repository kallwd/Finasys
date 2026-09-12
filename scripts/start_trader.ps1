$ErrorActionPreference = "Stop"

$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectPath ".venv\Scripts\python.exe"
$runtimePath = Join-Path $projectPath ".runtime"
$healthUrl = "http://127.0.0.1:17888/health"
$homeUrl = "http://127.0.0.1:17888/"

function Show-LauncherError([string]$message) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        $message,
        "Finasys",
        [System.Windows.MessageBoxButton]::OK,
        [System.Windows.MessageBoxImage]::Error
    ) | Out-Null
}

function Test-TraderReady {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 1
        return (
            $health.service -eq "finasys" -and
            $health.status -eq "ok" -and
            $health.trading_enabled -eq $false
        )
    }
    catch {
        return $false
    }
}

try {
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        throw "Project environment not found. Run: uv sync --dev"
    }

    if (-not (Test-TraderReady)) {
        New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
        $stdoutPath = Join-Path $runtimePath "server-output.log"
        $stderrPath = Join-Path $runtimePath "server-error.log"

        Start-Process `
            -FilePath $pythonPath `
            -ArgumentList @(
                "-m", "uvicorn", "trader_api.main:app",
                "--app-dir", "src",
                "--host", "127.0.0.1",
                "--port", "17888"
            ) `
            -WorkingDirectory $projectPath `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath | Out-Null

        $ready = $false
        for ($attempt = 0; $attempt -lt 80; $attempt++) {
            if (Test-TraderReady) {
                $ready = $true
                break
            }
            Start-Sleep -Milliseconds 250
        }

        if (-not $ready) {
            throw "Server did not start within 20 seconds. Check: $stderrPath"
        }
    }

    Start-Process -FilePath $homeUrl | Out-Null
}
catch {
    Show-LauncherError $_.Exception.Message
    exit 1
}
