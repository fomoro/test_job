#!/bin/bash
# scripts/tests/run_coverage.sh
# Script para análisis detallado de cobertura de código

set -e  # Detener ejecución al primer error

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorios
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="$PROJECT_ROOT/app"
TESTS_DIR="$PROJECT_ROOT/tests"
REPORTS_DIR="$PROJECT_ROOT/reports/coverage"
COVERAGE_DATA="$REPORTS_DIR/.coverage"

# Configuración
MIN_COVERAGE=50  # Cobertura mínima requerida (ajustar según necesidades)
PYTHON_PATHS="$APP_DIR"

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_requirements() {
    print_header "VERIFICANDO REQUISITOS"
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python no encontrado"
        exit 1
    fi
    
    # Verificar coverage.py
    if ! $PYTHON_CMD -m coverage --version &> /dev/null; then
        print_warning "coverage.py no encontrado, instalando..."
        $PYTHON_CMD -m pip install coverage
    fi
    
    # Crear directorio de reportes
    mkdir -p "$REPORTS_DIR"
    print_success "Directorio de reportes: $REPORTS_DIR"
}

# ============================================================================
# FUNCIONES DE COBERTURA
# ============================================================================

run_tests_with_coverage() {
    print_header "EJECUTANDO TESTS CON COBERTURA"
    
    if [[ ! -d "$TESTS_DIR" ]]; then
        print_error "Directorio de tests no encontrado: $TESTS_DIR"
        exit 1
    fi
    
    # Limpiar datos anteriores
    $PYTHON_CMD -m coverage erase
    
    # Ejecutar tests con cobertura
    $PYTHON_CMD -m coverage run \
        --source="$PYTHON_PATHS" \
        --branch \
        -m pytest "$TESTS_DIR" \
        -v \
        --tb=short \
        2>&1 | tee "$REPORTS_DIR/test_output.log"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Tests ejecutados con cobertura"
    else
        print_warning "Algunos tests fallaron, pero continuando con análisis de cobertura"
    fi
    
    # Guardar datos de cobertura
    if [[ -f ".coverage" ]]; then
        mv ".coverage" "$COVERAGE_DATA"
    fi
    
    return $exit_code
}

generate_coverage_reports() {
    print_header "GENERANDO REPORTES DE COBERTURA"
    
    if [[ ! -f "$COVERAGE_DATA" ]]; then
        print_error "Datos de cobertura no encontrados: $COVERAGE_DATA"
        print_info "Ejecuta primero los tests: $0 run"
        exit 1
    fi
    
    # Copiar datos a ubicación temporal
    cp "$COVERAGE_DATA" ".coverage"
    
    # 1. Reporte de consola (detallado)
    print_info "Generando reporte de consola..."
    $PYTHON_CMD -m coverage report \
        --show-missing \
        --skip-covered \
        --fail-under=$MIN_COVERAGE \
        2>&1 | tee "$REPORTS_DIR/console_report.txt"
    
    # 2. Reporte HTML (interactivo)
    print_info "Generando reporte HTML..."
    $PYTHON_CMD -m coverage html \
        --directory="$REPORTS_DIR/html" \
        --title="CCS - Cobertura de Tests"
    
    # 3. Reporte XML (para CI/CD)
    print_info "Generando reporte XML..."
    $PYTHON_CMD -m coverage xml \
        -o "$REPORTS_DIR/coverage.xml"
    
    # 4. Reporte JSON (para análisis programático)
    print_info "Generando reporte JSON..."
    $PYTHON_CMD -m coverage json \
        -o "$REPORTS_DIR/coverage.json"
    
    # 5. Reporte por módulo
    print_info "Generando reporte por módulo..."
    $PYTHON_CMD -m coverage report \
        --format=markdown \
        2>&1 | tee "$REPORTS_DIR/module_report.md"
    
    # 6. Análisis de líneas faltantes
    print_info "Analizando líneas sin cobertura..."
    $PYTHON_CMD -m coverage report \
        --show-missing \
        2>&1 | grep -E "(Missing|%)" | head -20 > "$REPORTS_DIR/missing_lines.txt"
    
    # Limpiar archivo temporal
    rm -f ".coverage"
    
    print_success "Reportes generados en: $REPORTS_DIR/"
}

analyze_coverage_by_module() {
    print_header "ANÁLISIS DE COBERTURA POR MÓDULO"
    
    if [[ ! -f "$COVERAGE_DATA" ]]; then
        print_error "Datos de cobertura no encontrados"
        return 1
    fi
    
    cp "$COVERAGE_DATA" ".coverage"
    
    # Obtener lista de módulos
    local modules=$($PYTHON_CMD -m coverage report --format=total | grep -E "^app/" | cut -d' ' -f1 || true)
    
    if [[ -z "$modules" ]]; then
        print_warning "No se encontraron módulos para analizar"
        return 0
    fi
    
    # Crear archivo de análisis
    local analysis_file="$REPORTS_DIR/module_analysis.md"
    
    cat > "$analysis_file" << EOF
# Análisis de Cobertura por Módulo

Fecha: $(date)
Cobertura mínima requerida: ${MIN_COVERAGE}%

## Resumen por Módulo

| Módulo | Cobertura | Estado | Líneas Totales | Líneas Cubiertas | Líneas Faltantes |
|--------|-----------|--------|----------------|------------------|------------------|
EOF
    
    # Analizar cada módulo
    for module in $modules; do
        local module_report=$($PYTHON_CMD -m coverage report --include="$module" 2>/dev/null || true)
        
        if [[ -n "$module_report" ]]; then
            # Extraer estadísticas
            local stats=$(echo "$module_report" | tail -1)
            local coverage_percent=$(echo "$stats" | awk '{print $4}' | sed 's/%//')
            local total_lines=$(echo "$stats" | awk '{print $2}')
            local covered_lines=$(echo "$stats" | awk '{print $3}')
            local missing_lines=$((total_lines - covered_lines))
            
            # Determinar estado
            local status="✅ OK"
            if [[ $coverage_percent -lt $MIN_COVERAGE ]]; then
                status="❌ BAJA"
            elif [[ $coverage_percent -lt 80 ]]; then
                status="⚠️  MEDIA"
            fi
            
            # Añadir a la tabla
            echo "| \`$module\` | $coverage_percent% | $status | $total_lines | $covered_lines | $missing_lines |" >> "$analysis_file"
        fi
    done
    
    # Añadir recomendaciones
    cat >> "$analysis_file" << EOF

## Recomendaciones

### Módulos con cobertura excelente (>90%)
- Mantener y agregar tests de regresión

### Módulos con cobertura buena (70-90%)
- Considerar agregar tests para casos borde

### Módulos con cobertura baja (<$MIN_COVERAGE%)
- **Prioridad alta**: Agregar tests inmediatamente
- Revisar si el código es crítico para el sistema
- Considerar refactorización si es muy complejo de testear

### Módulos sin cobertura
- Investigar si son módulos obsoletos
- Si son necesarios, agregar tests como prioridad
EOF
    
    # Mostrar tabla en consola
    echo -e "\n${CYAN}COBERTURA POR MÓDULO:${NC}"
    tail -n +9 "$analysis_file" | head -n $(($(echo "$modules" | wc -l) + 1))
    
    print_success "Análisis por módulo guardado en: $analysis_file"
    
    rm -f ".coverage"
}

check_coverage_threshold() {
    print_header "VERIFICANDO UMBRAL DE COBERTURA"
    
    if [[ ! -f "$COVERAGE_DATA" ]]; then
        print_error "Datos de cobertura no encontrados"
        return 1
    fi
    
    cp "$COVERAGE_DATA" ".coverage"
    
    # Obtener cobertura total
    local total_coverage=$($PYTHON_CMD -m coverage report --format=total 2>/dev/null | grep "^TOTAL" | awk '{print $4}' | sed 's/%//' || echo "0")
    
    print_info "Cobertura total: ${total_coverage}%"
    print_info "Cobertura mínima requerida: ${MIN_COVERAGE}%"
    
    if [[ $(echo "$total_coverage >= $MIN_COVERAGE" | bc) -eq 1 ]]; then
        print_success "✅ Cobertura SATISFACTORIA (${total_coverage}% >= ${MIN_COVERAGE}%)"
        return 0
    else
        print_error "❌ Cobertura INSUFICIENTE (${total_coverage}% < ${MIN_COVERAGE}%)"
        
        # Mostrar módulos con baja cobertura
        echo -e "\n${YELLOW}Módulos con cobertura < ${MIN_COVERAGE}%:${NC}"
        $PYTHON_CMD -m coverage report --fail-under=$MIN_COVERAGE 2>&1 | grep -E "^app/.*%.*[0-9]{1,2}%" || true
        
        return 1
    fi
    
    rm -f ".coverage"
}

generate_badge() {
    print_header "GENERANDO BADGE DE COBERTURA"
    
    if [[ ! -f "$COVERAGE_DATA" ]]; then
        print_error "Datos de cobertura no encontrados"
        return 1
    fi
    
    cp "$COVERAGE_DATA" ".coverage"
    
    # Obtener cobertura total
    local total_coverage=$($PYTHON_CMD -m coverage report --format=total 2>/dev/null | grep "^TOTAL" | awk '{print $4}' | sed 's/%//' || echo "0")
    
    # Determinar color del badge
    local color="red"
    if [[ $total_coverage -ge 90 ]]; then
        color="brightgreen"
    elif [[ $total_coverage -ge 80 ]]; then
        color="green"
    elif [[ $total_coverage -ge 70 ]]; then
        color="yellowgreen"
    elif [[ $total_coverage -ge 60 ]]; then
        color="yellow"
    elif [[ $total_coverage -ge 50 ]]; then
        color="orange"
    fi
    
    # Crear badge SVG
    local badge_file="$REPORTS_DIR/coverage_badge.svg"
    
    cat > "$badge_file" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="130" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="130" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <rect width="80" height="20" fill="#555"/>
    <rect x="80" width="50" height="20" fill="#$color"/>
    <rect width="130" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="40" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="40" y="14">coverage</text>
    <text x="104" y="15" fill="#010101" fill-opacity=".3">${total_coverage}%</text>
    <text x="104" y="14">${total_coverage}%</text>
  </g>
</svg>
EOF
    
    # También crear badge en formato simple para README
    local readme_badge="$REPORTS_DIR/badge.md"
    
    cat > "$readme_badge" << EOF
![Coverage](https://img.shields.io/badge/coverage-${total_coverage}%25-${color})
EOF
    
    print_success "Badge generado: $badge_file"
    print_info "Para README.md: ![Coverage](https://img.shields.io/badge/coverage-${total_coverage}%25-${color})"
    
    rm -f ".coverage"
}

open_html_report() {
    local html_report="$REPORTS_DIR/html/index.html"
    
    if [[ -f "$html_report" ]]; then
        print_info "Abriendo reporte HTML de cobertura..."
        
        if command -v xdg-open &> /dev/null; then
            xdg-open "$html_report"
        elif command -v open &> /dev/null; then
            open "$html_report"
        elif command -v start &> /dev/null; then
            start "$html_report"
        else
            print_warning "No se pudo abrir el reporte automáticamente"
            print_info "Abre manualmente: $html_report"
        fi
    else
        print_error "Reporte HTML no encontrado"
        print_info "Genera primero los reportes: $0 report"
    fi
}

show_coverage_summary() {
    print_header "RESUMEN DE COBERTURA"
    
    if [[ ! -f "$COVERAGE_DATA" ]] && [[ ! -f "$REPORTS_DIR/coverage.json" ]]; then
        print_error "No hay datos de cobertura disponibles"
        print_info "Ejecuta: $0 run"
        return 1
    fi
    
    # Usar JSON si existe, sino los datos crudos
    if [[ -f "$REPORTS_DIR/coverage.json" ]]; then
        local total_coverage=$(python3 -c "
import json
with open('$REPORTS_DIR/coverage.json') as f:
    data = json.load(f)
print(f\"{data['totals']['percent_covered']:.1f}%\")
")
        
        local total_lines=$(python3 -c "
import json
with open('$REPORTS_DIR/coverage.json') as f:
    data = json.load(f)
print(data['totals']['covered_lines'], '/', data['totals']['num_statements'])
")
        
        echo -e "📊 ${CYAN}Cobertura Total:${NC} $total_coverage"
        echo -e "📝 ${CYAN}Líneas Cubiertas:${NC} $total_lines"
        
    elif [[ -f "$COVERAGE_DATA" ]]; then
        cp "$COVERAGE_DATA" ".coverage"
        
        local summary=$($PYTHON_CMD -m coverage report --format=total 2>/dev/null | grep "^TOTAL" || echo "TOTAL 0 0 0%")
        
        echo -e "📊 ${CYAN}Cobertura Total:${NC} $(echo $summary | awk '{print $4}')"
        echo -e "📝 ${CYAN}Líneas Cubiertas:${NC} $(echo $summary | awk '{print $3}')/$(echo $summary | awk '{print $2}')"
        
        rm -f ".coverage"
    fi
    
    # Mostrar archivos con mejor/peor cobertura
    if [[ -f "$REPORTS_DIR/console_report.txt" ]]; then
        echo -e "\n🏆 ${CYAN}Mejor cobertura:${NC}"
        grep -E "^app/.*%.*9[0-9]%|^app/.*%.*100%" "$REPORTS_DIR/console_report.txt" | head -5 || echo "  No hay módulos con >90% cobertura"
        
        echo -e "\n📉 ${CYAN}Peor cobertura:${NC}"
        grep -E "^app/.*%.*[0-9]%|^app/.*%.*[0-9][0-9]%" "$REPORTS_DIR/console_report.txt" | tail -5 | grep -v "100%" || echo "  Todos los módulos tienen buena cobertura"
    fi
    
    print_info "\nReportes disponibles en: $REPORTS_DIR/"
}

# ============================================================================
# FUNCIÓN DE AYUDA
# ============================================================================

show_help() {
    cat << EOF
Uso: $0 [COMANDO]

Script para análisis de cobertura de código del proyecto CCS.

Comandos:
  run         Ejecutar tests y recolectar datos de cobertura
  report      Generar todos los reportes de cobertura
  analyze     Análisis detallado por módulo
  check       Verificar umbral mínimo de cobertura
  badge       Generar badge de cobertura para README
  summary     Mostrar resumen de cobertura
  open        Abrir reporte HTML en navegador
  all         Ejecutar todos los pasos (run, report, analyze, check, badge)
  help        Mostrar esta ayuda

Ejemplos:
  $0 run               # Solo ejecutar tests con cobertura
  $0 report            # Solo generar reportes
  $0 all               # Ejecutar todo el pipeline
  $0 check             # Verificar si cumple cobertura mínima
  $0 badge             # Generar badge para README

Umbral mínimo configurado: ${MIN_COVERAGE}%

Reportes generados en: $REPORTS_DIR
EOF
}

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

main() {
    local command=${1:-"help"}
    
    # Iniciar temporizador
    SECONDS=0
    
    # Verificar requisitos
    check_requirements
    
    case $command in
        "run")
            run_tests_with_coverage
            ;;
        "report")
            generate_coverage_reports
            ;;
        "analyze")
            analyze_coverage_by_module
            ;;
        "check")
            check_coverage_threshold
            ;;
        "badge")
            generate_badge
            ;;
        "summary")
            show_coverage_summary
            ;;
        "open")
            open_html_report
            ;;
        "all")
            print_header "EJECUTANDO PIPELINE COMPLETO DE COBERTURA"
            run_tests_with_coverage
            generate_coverage_reports
            analyze_coverage_by_module
            check_coverage_threshold
            generate_badge
            show_coverage_summary
            print_info "\n📈 Pipeline completo ejecutado en $(date -d@$SECONDS -u +%H:%M:%S)"
            ;;
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        *)
            print_error "Comando desconocido: $command"
            show_help
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    # Mostrar tiempo de ejecución
    if [[ $command != "help" ]]; then
        print_info "Tiempo de ejecución: $(date -d@$SECONDS -u +%H:%M:%S)"
    fi
    
    exit $exit_code
}

# ============================================================================
# EJECUCIÓN
# ============================================================================

# Solo ejecutar si se llama directamente (no cuando se importa)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi