#!/bin/bash
# ============================================================================
# CCS - Script para ejecutar monitor de métricas
# ============================================================================

set -e  # Detener en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PERFORMANCE_DIR="$PROJECT_ROOT/performance"
RESULTS_DIR="$PROJECT_ROOT/performance/results"
LOGS_DIR="$PERFORMANCE_DIR/logs"
CONFIG_DIR="$PERFORMANCE_DIR/config"

# Crear directorios si no existen
mkdir -p "$RESULTS_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "$CONFIG_DIR"

# Función para mostrar ayuda
show_help() {
    echo -e "${CYAN}CCS - Script de Monitoreo de Métricas${NC}"
    echo "=========================================="
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  --url URL           URL de la API (default: http://localhost:8000)"
    echo "  --interval N        Intervalo en segundos (default: 2)"
    echo "  --duration N        Duración en minutos (0 = infinito)"
    echo "  --width N           Ancho de terminal (default: 100)"
    echo "  --output-dir DIR    Directorio de resultados"
    echo "  --log-level LEVEL   Nivel de log (info, debug, error)"
    echo "  --save-reports      Guardar reportes periódicos"
    echo "  --test-connection   Solo probar conexión y salir"
    echo "  --dashboard-only    Solo mostrar dashboard, no guardar"
    echo "  --help              Mostrar esta ayuda"
    echo ""
    echo "Modos especiales:"
    echo "  --mode health       Solo monitoreo de salud"
    echo "  --mode performance  Solo métricas de rendimiento"
    echo "  --mode business     Solo métricas de negocio"
    echo "  --mode full         Todas las métricas (default)"
    echo ""
    echo "Ejemplos:"
    echo "  $0                             # Monitoreo completo"
    echo "  $0 --url http://api.ccs.com    # API remota"
    echo "  $0 --interval 5 --width 120    # Actualizar cada 5s, ancho 120"
    echo "  $0 --duration 10               # Monitorear por 10 minutos"
    echo "  $0 --test-connection           # Probar conexión"
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

# Función para verificar conexión
test_connection() {
    local url="$1"
    
    echo -e "${BLUE}🔍 Probando conexión con $url ...${NC}"
    
    cd "$PERFORMANCE_DIR"
    python3 -c "
import requests, sys, json
try:
    # Probando endpoint de health
    resp = requests.get('$url/health', timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        print('✅ HEALTH CHECK:')
        print(f'  Status: {data.get(\"status\", \"unknown\")}')
        print(f'  Uptime: {data.get(\"uptime_seconds\", 0):.0f}s')
        
        services = data.get('services', {})
        for service, status in services.items():
            icon = '✅' if status == 'healthy' else '❌'
            print(f'  {service}: {icon} {status}')
    else:
        print(f'❌ HTTP {resp.status_code}')
        sys.exit(1)
        
    # Probando endpoint de metrics
    resp = requests.get('$url/metrics', timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        print('\\n📊 SYSTEM METRICS:')
        
        processing = data.get('processing', {})
        if processing:
            print(f'  Señales procesadas: {processing.get(\"signals_processed\", 0)}')
            print(f'  Emergencias: {processing.get(\"emergencies_processed\", 0)}')
            print(f'  Alertas: {processing.get(\"alerts_generated\", 0)}')
        
        db = data.get('database', {})
        if db:
            print(f'  Vehículos activos: {db.get(\"total_vehicles\", 0)}')
        
    else:
        print(f'⚠️  No se pudo obtener metrics (HTTP {resp.status_code})')
        
except requests.exceptions.ConnectionError:
    print('❌ No se puede conectar a la API')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
    "
    
    return $?
}

# Función para ejecutar monitor
run_monitor() {
    local url="$1"
    local interval="$2"
    local width="$3"
    local duration="$4"
    local mode="$5"
    local save_reports="$6"
    local log_level="$7"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_file="$LOGS_DIR/monitor_${timestamp}.log"
    local config_file="$CONFIG_DIR/monitor_config_${timestamp}.json"
    
    # Crear archivo de configuración
    cat > "$config_file" << EOF
{
    "api_url": "$url",
    "interval_seconds": $interval,
    "terminal_width": $width,
    "duration_minutes": $duration,
    "monitoring_mode": "$mode",
    "save_reports": $save_reports,
    "log_level": "$log_level",
    "start_time": "$(date -Iseconds)",
    "output_dir": "$RESULTS_DIR"
}
EOF
    
    echo -e "${CYAN}📊 Iniciando monitor CCS...${NC}"
    echo "=========================================="
    echo "URL API: $url"
    echo "Intervalo: ${interval}s"
    echo "Ancho terminal: $width"
    echo "Duración: ${duration} min (0 = infinito)"
    echo "Modo: $mode"
    echo "Guardar reportes: $save_reports"
    echo "Log: $log_file"
    echo "Config: $(basename "$config_file")"
    echo "=========================================="
    
    # Comando base
    cmd="cd '$PERFORMANCE_DIR' && python3 monitor_metrics.py --url '$url' --interval $interval --width $width --output-dir '$RESULTS_DIR'"
    
    # Agregar parámetros según modo
    case $mode in
        "health")
            echo -e "${BLUE}🧬 Modo: Solo monitoreo de salud${NC}"
            ;;
        "performance")
            echo -e "${BLUE}⚡ Modo: Solo métricas de rendimiento${NC}"
            ;;
        "business")
            echo -e "${BLUE}🏢 Modo: Solo métricas de negocio${NC}"
            ;;
        "full")
            echo -e "${BLUE}📈 Modo: Monitoreo completo${NC}"
            ;;
    esac
    
    # Ejecutar con timeout si se especificó duración
    if [ "$duration" -gt 0 ]; then
        echo -e "${YELLOW}⏰ Ejecutando por $duration minutos...${NC}"
        timeout "${duration}m" bash -c "$cmd" 2>&1 | tee "$log_file"
        
        # Verificar si fue terminado por timeout
        if [ $? -eq 124 ]; then
            echo -e "${YELLOW}⏰ Monitor detenido después de $duration minutos${NC}"
        fi
    else
        echo -e "${YELLOW}♾️  Ejecutando indefinidamente (Ctrl+C para detener)${NC}"
        bash -c "$cmd" 2>&1 | tee "$log_file"
    fi
    
    # Verificar resultado
    if [ $? -eq 0 ] || [ $? -eq 124 ]; then  # 124 es código de timeout
        echo -e "${GREEN}✅ Monitor finalizado${NC}"
        
        # Buscar reportes generados
        latest_report=$(find "$RESULTS_DIR" -name "ccs_performance_report_*.json" -type f | sort -r | head -1)
        if [ -n "$latest_report" ] && [ "$save_reports" = "true" ]; then
            echo -e "${BLUE}📄 Reporte guardado en: $(basename "$latest_report")${NC}"
            
            # Mostrar resumen del reporte
            python3 -c "
import json, sys, os
try:
    with open('$latest_report') as f:
        data = json.load(f)
    
    meta = data.get('metadata', {})
    print('\\n📋 RESUMEN DEL MONITOREO:')
    print('=' * 40)
    print(f'Duración: {meta.get(\"duration_seconds\", 0):.0f}s')
    print(f'Muestras: {meta.get(\"samples_collected\", 0)}')
    
    agg = data.get('aggregate_metrics', {})
    if 'rps' in agg:
        rps = agg['rps']
        print(f'\\n📈 RENDIMIENTO:')
        print(f'  • RPS promedio: {rps.get(\"avg\", 0):.1f}')
        print(f'  • RPS máximo: {rps.get(\"max\", 0):.1f}')
    
    if 'emergency_latency' in agg:
        emg = agg['emergency_latency']
        print(f'\\n🚨 EMERGENCIAS:')
        print(f'  • P95 promedio: {emg.get(\"p95_avg\", 0):.1f}ms')
        print(f'  • Cumplimiento SLA: {emg.get(\"sla_compliance_percentage\", 0):.1f}%')
    
    health = data.get('health_summary', {})
    if health:
        print(f'\\n🧬 SALUD DEL SISTEMA:')
        print(f'  • Tiempo saludable: {health.get(\"healthy_percentage\", 0):.1f}%')
    
except Exception as e:
    print(f'Error leyendo reporte: {e}')
            "
        fi
    else
        echo -e "${RED}❌ Error en el monitor${NC}"
        return 1
    fi
}

# Función para limpiar logs antiguos
clean_old_logs() {
    local days_to_keep=7
    
    echo -e "${YELLOW}🧹 Limpiando logs antiguos (>${days_to_keep} días)...${NC}"
    
    # Limpiar logs
    find "$LOGS_DIR" -name "*.log" -type f -mtime +$days_to_keep -delete 2>/dev/null || true
    
    # Limpiar configs antiguos
    find "$CONFIG_DIR" -name "*.json" -type f -mtime +$days_to_keep -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Limpieza completada${NC}"
}

# Main
main() {
    # Valores por defecto
    URL="http://localhost:8000"
    INTERVAL=2
    WIDTH=100
    DURATION=0  # 0 = infinito
    MODE="full"
    SAVE_REPORTS="true"
    LOG_LEVEL="info"
    TEST_CONNECTION_ONLY=false
    DASHBOARD_ONLY=false
    
    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --url)
                URL="$2"
                shift 2
                ;;
            --interval)
                INTERVAL="$2"
                shift 2
                ;;
            --width)
                WIDTH="$2"
                shift 2
                ;;
            --duration)
                DURATION="$2"
                shift 2
                ;;
            --mode)
                MODE="$2"
                shift 2
                ;;
            --output-dir)
                RESULTS_DIR="$2"
                shift 2
                ;;
            --log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            --save-reports)
                SAVE_REPORTS="true"
                shift
                ;;
            --no-save-reports)
                SAVE_REPORTS="false"
                shift
                ;;
            --test-connection)
                TEST_CONNECTION_ONLY=true
                shift
                ;;
            --dashboard-only)
                DASHBOARD_ONLY=true
                SAVE_REPORTS="false"
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
    echo -e "${CYAN}==========================================${NC}"
    echo -e "${CYAN}   CCS - MONITOR DE MÉTRICAS${NC}"
    echo -e "${CYAN}==========================================${NC}"
    
    # Verificar dependencias
    check_dependencies
    
    # Limpiar logs antiguos
    clean_old_logs
    
    # Probar conexión si se solicitó
    if [ "$TEST_CONNECTION_ONLY" = true ]; then
        test_connection "$URL"
        exit $?
    fi
    
    # Verificar API
    if ! test_connection "$URL"; then
        echo -e "${YELLOW}⚠️  ¿Deseas continuar de todas formas? (s/n)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Ss]$ ]]; then
            exit 1
        fi
    fi
    
    # Modo solo dashboard
    if [ "$DASHBOARD_ONLY" = true ]; then
        echo -e "${YELLOW}👁️  Modo solo dashboard - no se guardarán reportes${NC}"
        SAVE_REPORTS="false"
    fi
    
    # Ejecutar monitor
    run_monitor "$URL" "$INTERVAL" "$WIDTH" "$DURATION" "$MODE" "$SAVE_REPORTS" "$LOG_LEVEL"
    
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}   MONITOR FINALIZADO${NC}"
    echo -e "${GREEN}==========================================${NC}"
}

# Ejecutar main
main "$@"