# Script para rodar o frontend React
$frontendPath = Join-Path $PSScriptRoot "frontend"
Set-Location $frontendPath
& "C:\Program Files\nodejs\npm.cmd" run dev
