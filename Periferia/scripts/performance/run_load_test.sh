#!/bin/bash
# ============================================================================
# CCS - Script para ejecutar pruebas de carga
# ============================================================================

set -e  # Detener en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PERFORMANCE_DIR="$PROJECT_ROOT/performance"
RESULTS_DIR="$PROJECT_ROOT/performance/results"
LOGS_DIR="$PROJECT_ROOT/performance/logs"
CONFIG_FILE="$PERFORMANCE_DIR/config.json"

# Crear directorios si no existen
mkdir -p "$RESULTS_DIR"
mkdir -p "$LOGS_DIR"

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}CCS - Script de Pruebas de Carga${NC}"
    echo "========================================"
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  --rps N           Señales por segundo (default: 500)"
    echo "  --duration N      Duración en segundos (default: 120)"
    echo "  --vehicles N      Número de vehículos (default: 150)"
    echo "  --url URL         URL de la API (default: http://localhost:8000)"
    echo "  --workers N       Workers concurrentes (default: 100)"
    echo "  --panic-prob F    Probabilidad de emergencia (default: 0.001)"
    echo "  --output-dir DIR  Directorio de resultados"
    echo "  --test-light      Ejecutar prueba liviana (50 RPS × 30s)"
    echo "  --test-medium     Ejecutar prueba media (200 RPS × 60s)"
    echo "  --test-full       Ejecutar prueba completa (500 RPS × 120s)"
    echo "  --help            Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 --test-light          # Prueba rápida"
    echo "  $0 --rps 300 --duration 60"
    echo "  $0 --url http://api.ccs.com --rps 100"
    echo ""
}

# Función para verificar dependencias
check_dependencies() {
    echo -e "${BLUE}🔍 Verificando dependencias...${NC}"
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 no está instalado${NC}"
        exit 1
    fi
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${YELLOW}⚠️  pip3 no encontrado, intentando instalar...${NC}"
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        else
            echo -e "${RED}❌ No se pudo instalar pip3${NC}"
            exit 1
        fi
    fi
    
    # Verificar módulos Python necesarios
    REQUIRED_MODULES=("aiohttp" "requests" "psutil")
    for module in "${REQUIRED_MODULES[@]}"; do
        if ! python3 -c "import $module" &> /dev/null; then
            echo -e "${YELLOW}⚠️  Instalando módulo $module...${NC}"
            pip3 install "$module"
        fi
    done
    
    echo -e "${GREEN}✅ Dependencias verificadas${NC}"
}

# Función para verificar que la API está corriendo
check_api() {
    local url="$1"
    echo -e "${BLUE}🔍 Verificando conexión con API...${NC}"
    
    if ! command -v curl &> /dev/null; then
        echo -e "${YELLOW}⚠️  curl no instalado, usando python...${NC}"
        if python3 -c "import requests; r = requests.get('$url/health', timeout=5); print('OK' if r.status_code == 200 else 'FAIL')" 2>/dev/null | grep -q "OK"; then
            echo -e "${GREEN}✅ API disponible en $url${NC}"
            return 0
        else
            echo -e "${RED}❌ No se puede conectar a $url${NC}"
            return 1
        fi
    else
        if curl -s --max-time 5 "$url/health" | grep -q '"status":"healthy"'; then
            echo -e "${GREEN}✅ API disponible en $url${NC}"
            return 0
        else
            echo -e "${RED}❌ No se puede conectar a $url${NC}"
            return 1
        fi
    fi
}

# Función para ejecutar prueba de carga
run_load_test() {
    local rps="$1"
    local duration="$2"
    local vehicles="$3"
    local url="$4"
    local workers="$5"
    local panic_prob="$6"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_file="$LOGS_DIR/load_test_${timestamp}.log"
    
    echo -e "${BLUE}🚀 Iniciando prueba de carga...${NC}"
    echo "========================================"
    echo "RPS objetivo: $rps señales/segundo"
    echo "Duración: $duration segundos"
    echo "Vehículos: $vehicles"
    echo "Workers: $workers"
    echo "URL API: $url"
    echo "Prob. emergencia: $panic_prob"
    echo "Log: $log_file"
    echo "========================================"
    
    # Ejecutar generador de carga
    cd "$PERFORMANCE_DIR"
    python3 generar_carga.py \
        --url "$url" \
        --rps "$rps" \
        --duration "$duration" \
        --vehicles "$vehicles" \
        --workers "$workers" \
        --panic-prob "$panic_prob" \
        --output-dir "$RESULTS_DIR" 2>&1 | tee "$log_file"
    
    # Verificar resultado
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Prueba de carga completada exitosamente${NC}"
        
        # Encontrar archivo de resultados más reciente
        latest_result=$(find "$RESULTS_DIR" -name "ccs_load_stats_*.json" -type f | sort -r | head -1)
        if [ -n "$latest_result" ]; then
            echo -e "${BLUE}📊 Resultados guardados en: $latest_result${NC}"
            
            # Mostrar resumen
            python3 -c "
import json, sys
try:
    with open('$latest_result') as f:
        data = json.load(f)
    summary = data.get('summary', {})
    print('\\n📈 RESUMEN DE PRUEBA:')
    print(f'  • RPS promedio: {summary.get(\"avg_rps\", 0):.1f}')
    print(f'  • Tasa de éxito: {summary.get(\"success_rate_percent\", 0):.1f}%')
    print(f'  • Latencia promedio: {summary.get(\"avg_response_time_ms\", 0):.1f}ms')
    print(f'  • Cumplimiento SLA: {summary.get(\"sla_compliant_percent\", 0):.1f}%')
except Exception as e:
    print(f'Error leyendo resultados: {e}')
            "
        fi
    else
        echo -e "${RED}❌ Error en la prueba de carga${NC}"
        return 1
    fi
}

# Función para ejecutar prueba predefinida
run_preset_test() {
    local preset="$1"
    
    case $preset in
        "light")
            echo -e "${BLUE}🧪 Ejecutando prueba LIGERA (50 RPS × 30s)${NC}"
            run_load_test 50 30 50 "http://localhost:8000" 20 0.001
            ;;
        "medium")
            echo -e "${BLUE}🧪 Ejecutando prueba MEDIA (200 RPS × 60s)${NC}"
            run_load_test 200 60 100 "http://localhost:8000" 50 0.002
            ;;
        "full")
            echo -e "${BLUE}🧪 Ejecutando prueba COMPLETA (500 RPS × 120s)${NC}"
            run_load_test 500 120 150 "http://localhost:8000" 100 0.001
            ;;
    esac
}

# Main
main() {
    # Valores por defecto
    RPS=500
    DURATION=120
    VEHICLES=150
    URL="http://localhost:8000"
    WORKERS=100
    PANIC_PROB=0.001
    PRESET=""
    
    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --rps)
                RPS="$2"
                shift 2
                ;;
            --duration)
                DURATION="$2"
                shift 2
                ;;
            --vehicles)
                VEHICLES="$2"
                shift 2
                ;;
            --url)
                URL="$2"
                shift 2
                ;;
            --workers)
                WORKERS="$2"
                shift 2
                ;;
            --panic-prob)
                PANIC_PROB="$2"
                shift 2
                ;;
            --output-dir)
                RESULTS_DIR="$2"
                shift 2
                ;;
            --test-light)
                PRESET="light"
                shift
                ;;
            --test-medium)
                PRESET="medium"
                shift
                ;;
            --test-full)
                PRESET="full"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Opción desconocida: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Banner
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}   CCS - PRUEBAS DE CARGA${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Verificar dependencias
    check_dependencies
    
    # Verificar API
    if ! check_api "$URL"; then
        echo -e "${YELLOW}⚠️  ¿Deseas continuar de todas formas? (s/n)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Ss]$ ]]; then
            exit 1
        fi
    fi
    
    # Ejecutar prueba
    if [ -n "$PRESET" ]; then
        run_preset_test "$PRESET"
    else
        run_load_test "$RPS" "$DURATION" "$VEHICLES" "$URL" "$WORKERS" "$PANIC_PROB"
    fi
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   PRUEBA FINALIZADA${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Ejecutar main
main "$@"