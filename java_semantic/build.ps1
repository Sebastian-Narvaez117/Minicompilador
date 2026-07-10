$ErrorActionPreference = "Stop"

Write-Host "[BUILD] Compilando proyecto Java Semantic..." -ForegroundColor Cyan

$srcDir = "src"
$outDir = "out"
$libDir = "lib"
$gsonJar = "$libDir\gson.jar"

if (!(Test-Path $gsonJar)) {
    Write-Host "[BUILD] Descargando Gson..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar" -OutFile $gsonJar
}

if (Test-Path $outDir) {
    Remove-Item -Recurse -Force $outDir
}
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$files = Get-ChildItem -Path $srcDir -Recurse -Filter "*.java" | ForEach-Object { $_.FullName }

javac -cp $gsonJar -d $outDir $files

Write-Host "[BUILD] Compilación exitosa." -ForegroundColor Green
Write-Host "[BUILD] Salida: $outDir" -ForegroundColor Green
