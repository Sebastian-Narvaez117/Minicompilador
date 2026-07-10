$ErrorActionPreference = "Stop"
.\build.ps1
Write-Host "[RUN] Iniciando servidor semántico Java en puerto 8090..." -ForegroundColor Cyan
java -cp "out;lib\gson.jar" semantic.SemanticServer
