$ErrorActionPreference = 'Stop'
$pythonExe = Join-Path $PSScriptRoot 'runtime\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}
& $pythonExe (Join-Path $PSScriptRoot 'serve_local.py') --open
