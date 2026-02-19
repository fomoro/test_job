# Ruta base
$basePath = ".\pocs\01_carga-escalabilidad"

# Carpetas
$directories = @(
    $basePath,
    "$basePath\app",
    
    "$basePath\scripts",
    "$basePath\scripts\database",

    "$basePath\resultados",
    
    "$basePath\reflexiones"
)

# Archivos
$files = @(
    "$basePath\app\main.py",
    "$basePath\app\requirements.txt",
    "$basePath\app\.env",
    "$basePath\README.md",


    "$basePath\reflexiones\arquitectura.md",
    "$basePath\reflexiones\bottlenecks_encontrados.md",
    "$basePath\reflexiones\recomendaciones_produccion.md"
)

# Crear carpetas
foreach ($dir in $directories) {
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
}

# Crear archivos vacíos
foreach ($file in $files) {
    New-Item -Path $file -ItemType File -Force | Out-Null
}

Write-Host "Estructura POC creada correctamente en $basePath" -ForegroundColor Green
