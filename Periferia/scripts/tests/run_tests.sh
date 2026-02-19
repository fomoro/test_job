#!/bin/bash
# scripts/tests/run_tests.sh
# Script para ejecutar todos los tests del proyecto CCS

set -e  # Detener ejecución al primer error

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorios
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTS_DIR="$PROJECT_ROOT/tests"
APP_DIR="$PROJECT_ROOT/app"
REPORTS_DIR="$PROJECT_ROOT/reports/tests"
LOG_FILE="$REPORTS_DIR/test_run_$(date +%Y%m%d_%H%M%S).log"

# Configuración de pytest
PYTEST_OPTS="-v"
COV_OPTS="--cov=$APP_DIR --cov-report=term-missing"

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
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

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
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
    
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    print_info "Python $PYTHON_VERSION detectado"
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip no encontrado"
        exit 1
    fi
    
    # Verificar pytest
    if ! $PYTHON_CMD -m pytest --version &> /dev/null; then
        print_warning "pytest no encontrado, instalando..."
        $PYTHON_CMD -m pip install pytest pytest-asyncio pytest-cov pytest-mock
    else
        print_success "pytest instalado"
    fi
    
    # Crear directorio de reportes
    mkdir -p "$REPORTS_DIR"
    print_success "Directorio de reportes: $REPORTS_DIR"
}

setup_environment() {
    print_header "CONFIGURANDO ENTORNO"
    
    # Verificar que estamos en el directorio correcto
    if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]]; then
        print_warning "requirements.txt no encontrado en $PROJECT_ROOT"
        print_info "Asumiendo que las dependencias ya están instaladas"
    else
        print_info "Instalando dependencias desde requirements.txt..."
        $PYTHON_CMD -m pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
    
    # Instalar dependencias de desarrollo
    if [[ -f "$PROJECT_ROOT/requirements-dev.txt" ]]; then
        print_info "Instalando dependencias de desarrollo..."
        $PYTHON_CMD -m pip install -r "$PROJECT_ROOT/requirements-dev.txt"
    fi
    
    # Configurar PYTHONPATH
    export PYTHONPATH="$APP_DIR:$PYTHONPATH"
    print_success "PYTHONPATH configurado: $PYTHONPATH"
    
    # Limpiar cache de pytest
    print_info "Limpiando cache de pytest..."
    $PYTHON_CMD -m pytest --cache-clear 2>/dev/null || true
}

# ============================================================================
# FUNCIONES DE EJECUCIÓN DE TESTS
# ============================================================================

run_unit_tests() {
    print_header "EJECUTANDO TESTS UNITARIOS"
    
    UNIT_TESTS_DIR="$TESTS_DIR/unit"
    
    if [[ ! -d "$UNIT_TESTS_DIR" ]]; then
        print_error "Directorio de tests unitarios no encontrado: $UNIT_TESTS_DIR"
        return 1
    fi
    
    log_message "Iniciando tests unitarios"
    
    $PYTHON_CMD -m pytest "$UNIT_TESTS_DIR" \
        $PYTEST_OPTS \
        $COV_OPTS \
        --cov-report=html:"$REPORTS_DIR/coverage_unit" \
        -m "unit" \
        2>&1 | tee -a "$LOG_FILE"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Tests unitarios completados exitosamente"
        return 0
    else
        print_error "Tests unitarios fallaron"
        return $exit_code
    fi
}

run_integration_tests() {
    print_header "EJECUTANDO TESTS DE INTEGRACIÓN"
    
    INTEGRATION_TESTS_DIR="$TESTS_DIR/integration"
    
    if [[ ! -d "$INTEGRATION_TESTS_DIR" ]]; then
        print_error "Directorio de tests de integración no encontrado: $INTEGRATION_TESTS_DIR"
        return 1
    fi
    
    log_message "Iniciando tests de integración"
    
    $PYTHON_CMD -m pytest "$INTEGRATION_TESTS_DIR" \
        $PYTEST_OPTS \
        $COV_OPTS \
        --cov-report=html:"$REPORTS_DIR/coverage_integration" \
        -m "integration" \
        --tb=short \
        2>&1 | tee -a "$LOG_FILE"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Tests de integración completados exitosamente"
        return 0
    else
        print_error "Tests de integración fallaron"
        return $exit_code
    fi
}

run_specific_test() {
    local test_path=$1
    
    print_header "EJECUTANDO TEST ESPECÍFICO: $test_path"
    
    if [[ ! -f "$test_path" ]] && [[ ! -d "$test_path" ]]; then
        print_error "Test no encontrado: $test_path"
        return 1
    fi
    
    log_message "Iniciando test específico: $test_path"
    
    $PYTHON_CMD -m pytest "$test_path" \
        $PYTEST_OPTS \
        -v \
        2>&1 | tee -a "$LOG_FILE"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Test específico completado exitosamente"
        return 0
    else
        print_error "Test específico falló"
        return $exit_code
    fi
}

run_all_tests() {
    print_header "EJECUTANDO TODOS LOS TESTS"
    
    log_message "Iniciando ejecución completa de tests"
    
    $PYTHON_CMD -m pytest "$TESTS_DIR" \
        $PYTEST_OPTS \
        $COV_OPTS \
        --cov-report=html:"$REPORTS_DIR/coverage_all" \
        --junitxml="$REPORTS_DIR/junit_report.xml" \
        2>&1 | tee -a "$LOG_FILE"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Todos los tests completados exitosamente"
        
        # Generar resumen
        generate_summary
        return 0
    else
        print_error "Algunos tests fallaron"
        
        # Generar resumen incluso con fallos
        generate_summary
        return $exit_code
    fi
}

run_fast_tests() {
    print_header "EJECUTANDO TESTS RÁPIDOS (sin integración)"
    
    log_message "Iniciando tests rápidos (excluyendo integración)"
    
    $PYTHON_CMD -m pytest "$TESTS_DIR" \
        $PYTEST_OPTS \
        $COV_OPTS \
        --cov-report=html:"$REPORTS_DIR/coverage_fast" \
        -m "not integration and not slow" \
        2>&1 | tee -a "$LOG_FILE"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Tests rápidos completados exitosamente"
        return 0
    else
        print_error "Tests rápidos fallaron"
        return $exit_code
    fi
}

# ============================================================================
# FUNCIONES DE REPORTES
# ============================================================================

generate_summary() {
    print_header "GENERANDO RESUMEN DE EJECUCIÓN"
    
    local log_content=$(cat "$LOG_FILE")
    
    # Extraer estadísticas
    local passed=$(echo "$log_content" | grep -E "passed|PASSED" | wc -l)
    local failed=$(echo "$log_content" | grep -E "failed|FAILED" | wc -l)
    local skipped=$(echo "$log_content" | grep -E "skipped|SKIPPED" | wc -l)
    local errors=$(echo "$log_content" | grep -E "error|ERROR" | wc -l)
    
    # Extraer cobertura si está disponible
    local coverage_line=$(echo "$log_content" | grep -E "TOTAL|TOTAL.*%")
    local coverage="N/A"
    
    if [[ -n "$coverage_line" ]]; then
        coverage=$(echo "$coverage_line" | grep -oE "[0-9]+%")
        if [[ -z "$coverage" ]]; then
            coverage=$(echo "$coverage_line" | grep -oE "[0-9]+\s*%")
        fi
    fi
    
    # Crear archivo de resumen
    local summary_file="$REPORTS_DIR/summary_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$summary_file" << EOF
RESUMEN DE EJECUCIÓN DE TESTS
==============================
Fecha: $(date)
Duración: $(date -d@$SECONDS -u +%H:%M:%S)

ESTADÍSTICAS:
-------------
Tests pasados: $passed
Tests fallados: $failed
Tests saltados: $skipped
Errores: $errors

COBERTURA:
----------
Cobertura total: ${coverage:-N/A}

ARCHIVOS GENERADOS:
-------------------
Log completo: $LOG_FILE
Reporte JUnit: $REPORTS_DIR/junit_report.xml
Reporte HTML: $REPORTS_DIR/coverage_all/index.html
Este resumen: $summary_file

RECOMENDACIONES:
---------------
EOF
    
    # Añadir recomendaciones basadas en resultados
    if [[ $failed -gt 0 ]]; then
        echo "• Revisar tests fallidos en el log" >> "$summary_file"
    fi
    
    if [[ -n "$coverage" ]] && [[ "${coverage%\%}" -lt 50 ]]; then
        echo "• Cobertura inferior al 50%, agregar más tests" >> "$summary_file"
    fi
    
    if [[ $skipped -gt 0 ]]; then
        echo "• $skipped tests fueron saltados, revisar dependencias" >> "$summary_file"
    fi
    
    # Mostrar resumen en consola
    cat "$summary_file"
    
    print_success "Resumen guardado en: $summary_file"
}

open_coverage_report() {
    local report_file="$REPORTS_DIR/coverage_all/index.html"
    
    if [[ -f "$report_file" ]]; then
        print_info "Abriendo reporte de cobertura..."
        
        if command -v xdg-open &> /dev/null; then
            xdg-open "$report_file"
        elif command -v open &> /dev/null; then
            open "$report_file"
        elif command -v start &> /dev/null; then
            start "$report_file"
        else
            print_warning "No se pudo abrir el reporte automáticamente"
            print_info "Abre manualmente: $report_file"
        fi
    else
        print_error "Reporte de cobertura no encontrado"
        print_info "Ejecuta primero los tests: ./scripts/tests/run_tests.sh all"
    fi
}

# ============================================================================
# FUNCIÓN DE AYUDA
# ============================================================================

show_help() {
    cat << EOF
Uso: $0 [OPCIÓN] [ARGUMENTO]

Script para ejecutar tests del proyecto CCS.

Opciones:
  all           Ejecutar todos los tests (default)
  unit          Ejecutar solo tests unitarios
  integration   Ejecutar solo tests de integración
  fast          Ejecutar tests rápidos (sin integration/slow)
  specific FILE Ejecutar test específico o directorio
  coverage      Abrir reporte de cobertura HTML
  help          Mostrar esta ayuda

Ejemplos:
  $0                # Ejecuta todos los tests
  $0 unit           # Solo tests unitarios
  $0 integration    # Solo tests de integración
  $0 fast           # Tests rápidos (para desarrollo)
  $0 specific tests/unit/test_models.py
  $0 coverage       # Abre reporte de cobertura

Variables de entorno:
  PYTEST_OPTS      Opciones adicionales para pytest
  LOG_LEVEL        Nivel de logging (DEBUG, INFO, WARNING, ERROR)

Reportes generados en: $REPORTS_DIR
EOF
}

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

main() {
    local command=${1:-"all"}
    local argument=${2:-""}
    
    # Iniciar temporizador
    SECONDS=0
    
    # Configurar trap para limpieza
    trap 'print_error "Ejecución interrumpida por usuario"; exit 1' INT TERM
    
    # Verificar y configurar entorno
    check_requirements
    setup_environment
    
    case $command in
        "all")
            run_all_tests
            ;;
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "fast")
            run_fast_tests
            ;;
        "specific")
            if [[ -z "$argument" ]]; then
                print_error "Debe especificar un archivo o directorio de test"
                show_help
                exit 1
            fi
            run_specific_test "$argument"
            ;;
        "coverage")
            open_coverage_report
            exit 0
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
    
    # Mostrar tiempo total
    print_info "Tiempo total de ejecución: $(date -d@$SECONDS -u +%H:%M:%S)"
    
    # Mostrar ubicación de reportes
    print_info "Reportes guardados en: $REPORTS_DIR"
    
    exit $exit_code
}

# ============================================================================
# EJECUCIÓN
# ============================================================================

# Solo ejecutar si se llama directamente (no cuando se importa)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi