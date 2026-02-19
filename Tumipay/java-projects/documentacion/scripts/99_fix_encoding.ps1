# ==============================================================================
# SCRIPT: CORRECCIÓN DE CODIFICACIÓN (ELIMINAR BOM)
# ==============================================================================
# Recorre todos los archivos .java y elimina el carácter invisible '\ufeff'
# que PowerShell agrega por defecto en Windows.
# ==============================================================================

$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service\src\main\java"

Write-Host "--- INICIANDO LIMPIEZA DE CARACTERES INVISIBLES (BOM) ---" -ForegroundColor Cyan

if (-not (Test-Path $basePath)) {
    Write-Host "[ERROR] No encuentro la carpeta src/main/java" -ForegroundColor Red
    exit
}

# Obtener todos los archivos .java
$files = Get-ChildItem -Path $basePath -Recurse -Filter "*.java"

$utf8NoBom = New-Object System.Text.UTF8Encoding $false

foreach ($file in $files) {
    # Leer el contenido tal cual está
    $content = Get-Content -Path $file.FullName -Raw

    # Sobreescribir el archivo forzando UTF-8 SIN BOM
    [System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
    
    Write-Host " -> Reparado: $($file.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ ¡Archivos limpiados! Ahora intenta compilar de nuevo." -ForegroundColor Yellow