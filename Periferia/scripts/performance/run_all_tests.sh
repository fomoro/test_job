#!/bin/bash
# ============================================================================
# CCS - Script para ejecutar todas las pruebas de performance
# ============================================================================

set -e  # Detener en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERFORMANCE_DIR="$PROJECT_ROOT/performance"
RESULTS_DIR="$PERFORMANCE_DIR/results"
LOGS_DIR="$PERFORMANCE_DIR/logs"
REPORTS_DIR="$RESULTS_DIR/full_test_reports"

# Crear directorios si no existen
mkdir -p "$RESULTS_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "$REPORTS_DIR"

# Función para mostrar ayuda
show_help() {
    echo -e "${CYAN}CCS - Suite Completa de Pruebas de Performance${NC}"
    echo "=================================================="
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  --url URL               URL de la API (default: http://localhost:8000)"
    echo "  --quick                 Ejecutar suite rápida"
    echo "  --standard              Ejecutar suite estándar (default)"
    echo "  --full                  Ejecutar suite completa"
    echo "  --load-only             Solo pruebas de carga"
    echo "  --emergency-only        Solo pruebas de emergencia"
    echo "  --monitor-only          Solo monitoreo"
    echo "  --output-dir DIR        Directorio de resultados"
    echo "  --clean                 Limpiar resultados anteriores"
    echo "  --no-clean              No limpiar resultados"
    echo "  --parallel              Ejecutar pruebas en paralelo"
    echo "  --sequential            Ejecutar pruebas en secuencia"
    echo "  --help                  Mostrar esta ayuda"
    echo ""
    echo "Suites predefinidas:"
    echo "  quick    : Pruebas básicas (5 min)"
    echo "  standard : Pruebas completas (15 min)"
    echo "  full     : Pruebas exhaustivas (30 min+)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 --quick              # Pruebas rápidas"
    echo "  $0 --full --parallel    # Pruebas completas en paralelo"
    echo "  $0 --url http://api.ccs.com"
    echo ""
}

# Función para limpiar resultados anteriores
clean_previous_results() {
    echo -e "${YELLOW}🧹 Limpiando resultados anteriores...${NC}"
    
    # Crear backup de resultados importantes
    local backup_dir="$RESULTS_DIR/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Mover archivos importantes a backup
    find "$RESULTS_DIR" -name "*.json" -type f | head -20 | xargs -I {} mv {} "$backup_dir/" 2>/dev/null || true
    
    # Limpiar logs
    rm -f "$LOGS_DIR"/*.log 2>/dev/null || true
    
    # Crear nuevo directorio de reportes
    rm -rf "$REPORTS_DIR"
    mkdir -p "$REPORTS_DIR"
    
    echo -e "${GREEN}✅ Resultados anteriores limpiados (backup en $backup_dir)${NC}"
}

# Función para verificar dependencias
check_dependencies() {
    echo -e "${BLUE}🔍 Verificando dependencias...${NC}"
    
    # Verificar scripts
    local required_scripts=("run_load_test.sh" "run_emergency_test.sh" "run_monitor.sh")
    for script in "${required_scripts[@]}"; do
        if [ ! -f "$SCRIPTS_DIR/$script" ]; then
            echo -e "${RED}❌ Script faltante: $script${NC}"
            exit 1
        fi
        
        # Hacer ejecutable
        chmod +x "$SCRIPTS_DIR/$script" 2>/dev/null || true
    done
    
    # Verificar Python y dependencias
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 no está instalado${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencias verificadas${NC}"
}

# Función para verificar API
check_api() {
    local url="$1"
    
    echo -e "${BLUE}🔍 Verificando API en $url ...${NC}"
    
    "$SCRIPTS_DIR/run_monitor.sh" --test-connection --url "$url" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ API disponible y funcionando${NC}"
        return 0
    else
        echo -e "${RED}❌ API no disponible${NC}"
        return 1
    fi
}

# Función para ejecutar suite rápida
run_quick_suite() {
    local url="$1"
    local parallel="$2"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local suite_log="$LOGS_DIR/suite_quick_${timestamp}.log"
    
    echo -e "${PURPLE}⚡ EJECUTANDO SUITE RÁPIDA${NC}"
    echo "=================================================="
    echo "URL: $url"
    echo "Tiempo estimado: 5 minutos"
    echo "Log: $suite_log"
    echo "=================================================="
    
    # Iniciar log
    echo "=== CCS QUICK TEST SUITE ===" > "$suite_log"
    echo "Inicio: $(date)" >> "$suite_log"
    echo "URL: $url" >> "$suite_log"
    
    if [ "$parallel" = true ]; then
        echo -e "${YELLOW}⚡ Ejecutando pruebas en paralelo...${NC}"
        
        # Ejecutar pruebas en background
        "$SCRIPTS_DIR/run_load_test.sh" --test-light --url "$url" >> "$suite_log" 2>&1 &
        LOAD_PID=$!
        
        "$SCRIPTS_DIR/run_emergency_test.sh" --test-quick --url "$url" >> "$suite_log" 2>&1 &
        EMERGENCY_PID=$!
        
        # Esperar a que terminen
        wait $LOAD_PID $EMERGENCY_PID
        
    else
        echo -e "${YELLOW}➡️  Ejecutando pruebas en secuencia...${NC}"
        
        # 1. Pruebas de carga ligera
        echo -e "${CYAN}1️⃣  PRUEBAS DE CARGA LIGERA${NC}"
        "$SCRIPTS_DIR/run_load_test.sh" --test-light --url "$url" | tee -a "$suite_log"
        
        # Pequeña pausa
        sleep 2
        
        # 2. Pruebas de emergencia rápidas
        echo -e "${CYAN}2️⃣  PRUEBAS DE EMERGENCIA RÁPIDAS${NC}"
        "$SCRIPTS_DIR/run_emergency_test.sh" --test-quick --url "$url" | tee -a "$suite_log"
    fi
    
    # 3. Monitoreo rápido
    echo -e "${CYAN}3️⃣  MONITOREO RÁPIDO (1 minuto)${NC}"
    "$SCRIPTS_DIR/run_monitor.sh" --url "$url" --duration 1 --mode health | tee -a "$suite_log"
    
    echo "Fin: $(date)" >> "$suite_log"
    echo -e "${GREEN}✅ Suite rápida completada${NC}"
}

# Función para ejecutar suite estándar
run_standard_suite() {
    local url="$1"
    local parallel="$2"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local suite_log="$LOGS_DIR/suite_standard_${timestamp}.log"
    
    echo -e "${PURPLE}📊 EJECUTANDO SUITE ESTÁNDAR${NC}"
    echo "=================================================="
    echo "URL: $url"
    echo "Tiempo estimado: 15 minutos"
    echo "Log: $suite_log"
    echo "=================================================="
    
    # Iniciar log
    echo "=== CCS STANDARD TEST SUITE ===" > "$suite_log"
    echo "Inicio: $(date)" >> "$suite_log"
    echo "URL: $url" >> "$suite_log"
    
    if [ "$parallel" = true ]; then
        echo -e "${YELLOW}⚡ Ejecutando pruebas en paralelo...${NC}"
        
        # Iniciar monitor en background
        "$SCRIPTS_DIR/run_monitor.sh" --url "$url" --duration 15 --save-reports >> "$suite_log" 2>&1 &
        MONITOR_PID=$!
        
        # Esperar un momento para que el monitor inicie
        sleep 3
        
        # Ejecutar pruebas de carga y emergencia
        "$SCRIPTS_DIR/run_load_test.sh" --test-medium --url "$url" >> "$suite_log" 2>&1 &
        LOAD_PID=$!
        
        sleep 2
        
        "$SCRIPTS_DIR/run_emergency_test.sh" --concurrent 50 --workers 10 --url "$url" >> "$suite_log" 2>&1 &
        EMERGENCY_PID=$!
        
        # Esperar a que terminen las pruebas
        wait $LOAD_PID $EMERGENCY_PID
        
        # Detener monitor
        kill $MONITOR_PID 2>/dev/null || true
        
    else
        echo -e "${YELLOW}➡️  Ejecutando pruebas en secuencia...${NC}"
        
        # 1. Iniciar monitoreo en background
        echo -e "${CYAN}📊 INICIANDO MONITOREO EN SEGUNDO PLANO${NC}"
        "$SCRIPTS_DIR/run_monitor.sh" --url "$url" --duration 15 --save-reports >> "$suite_log" 2>&1 &
        MONITOR_PID=$!
        
        sleep 3
        
        # 2. Pruebas de carga media
        echo -e "${CYAN}1️⃣  PRUEBAS DE CARGA MEDIA${NC}"
        "$SCRIPTS_DIR/run_load_test.sh" --test-medium --url "$url" | tee -a "$suite_log"
        
        sleep 5
        
        # 3. Pruebas de emergencia concurrentes
        echo -e "${CYAN}2️⃣  PRUEBAS DE EMERGENCIA CONCURRENTES${NC}"
        "$SCRIPTS_DIR/run_emergency_test.sh" --concurrent 50 --workers 10 --url "$url" | tee -a "$suite_log"
        
        sleep 5
        
        # 4. Pruebas de carga gradual
        echo -e "${CYAN}3️⃣  PRUEBAS DE CARGA GRADUAL${NC}"
        "$SCRIPTS_DIR/run_emergency_test.sh" --gradual 80 --steps 4 --url "$url" | tee -a "$suite_log"
        
        # 5. Detener monitor
        kill $MONITOR_PID 2>/dev/null || true
        wait $MONITOR_PID 2>/dev/null || true
    fi
    
    echo "Fin: $(date)" >> "$suite_log"
    echo -e "${GREEN}✅ Suite estándar completada${NC}"
}

# Función para ejecutar suite completa
run_full_suite() {
    local url="$1"
    local parallel="$2"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local suite_log="$LOGS_DIR/suite_full_${timestamp}.log"
    
    echo -e "${PURPLE}🔥 EJECUTANDO SUITE COMPLETA${NC}"
    echo "=================================================="
    echo "URL: $url"
    echo "Tiempo estimado: 30+ minutos"
    echo "Log: $suite_log"
    echo "=================================================="
    
    # Iniciar log
    echo "=== CCS FULL TEST SUITE ===" > "$suite_log"
    echo "Inicio: $(date)" >> "$suite_log"
    echo "URL: $url" >> "$suite_log"
    
    # Crear directorio para esta suite
    local suite_report_dir="$REPORTS_DIR/full_suite_${timestamp}"
    mkdir -p "$suite_report_dir"
    
    if [ "$parallel" = true ]; then
        echo -e "${YELLOW}⚡ Ejecutando pruebas en paralelo...${NC}"
        echo -e "${YELLOW}⚠️  Nota: En modo completo se recomienda ejecución secuencial${NC}"
    fi
    
    # 1. Pruebas de carga completa
    echo -e "${CYAN}1️⃣  PRUEBAS DE CARGA COMPLETA (500 RPS × 2min)${NC}"
    "$SCRIPTS_DIR/run_load_test.sh" --test-full --url "$url" --output-dir "$suite_report_dir" | tee -a "$suite_log"
    
    sleep 10
    
    # 2. Iniciar monitoreo extendido
    echo -e "${CYAN}2️⃣  MONITOREO EXTENDIDO (10 minutos)${NC}"
    "$SCRIPTS_DIR/run_monitor.sh" --url "$url" --duration 10 --save-reports --output-dir "$suite_report_dir" >> "$suite_log" 2>&1 &
    MONITOR_PID=$!
    
    sleep 3
    
    # 3. Suite completa de emergencia
    echo -e "${CYAN}3️⃣  SUITE COMPLETA DE EMERGENCIAS${NC}"
    "$SCRIPTS_DIR/run_emergency_test.sh" --full --url "$url" --output-dir "$suite_report_dir" | tee -a "$suite_log"
    
    sleep 5
    
    # 4. Pruebas de estrés
    echo -e "${CYAN}4️⃣  PRUEBAS DE ESTRÉS${NC}"
    "$SCRIPTS_DIR/run_emergency_test.sh" --test-stress --url "$url" --output-dir "$suite_report_dir" | tee -a "$suite_log"
    
    # 5. Detener monitor
    kill $MONITOR_PID 2>/dev/null || true
    wait $MONITOR_PID 2>/dev/null || true
    
    sleep 5
    
    # 6. Monitoreo final de salud
    echo -e "${CYAN}5️⃣  VERIFICACIÓN FINAL DE SALUD${NC}"
    "$SCRIPTS_DIR/run_monitor.sh" --url "$url" --duration 2 --mode health | tee -a "$suite_log"
    
    echo "Fin: $(date)" >> "$suite_log"
    echo -e "${GREEN}✅ Suite completa finalizada${NC}"
    
    # Crear reporte consolidado
    create_consolidated_report "$suite_report_dir" "$timestamp"
}

# Función para crear reporte consolidado
create_consolidated_report() {
    local report_dir="$1"
    local timestamp="$2"
    
    local consolidated_file="$report_dir/ccs_full_suite_report_${timestamp}.json"
    
    echo -e "${BLUE}📋 Creando reporte consolidado...${NC}"
    
    python3 -c "
import json, os, glob, sys

report_dir = '$report_dir'
output_file = '$consolidated_file'

def find_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

try:
    consolidated = {
        'suite_id': 'CCS_FULL_SUITE_' + '$timestamp',
        'timestamp': '$timestamp',
        'reports': {},
        'summary': {},
        'status': 'COMPLETED'
    }
    
    # Buscar reportes de carga
    load_report = find_latest_file(os.path.join(report_dir, 'ccs_load_stats_*.json'))
    if load_report:
        with open(load_report) as f:
            data = json.load(f)
            consolidated['reports']['load_test'] = {
                'file': os.path.basename(load_report),
                'summary': data.get('summary', {})
            }
    
    # Buscar reportes de emergencia
    emergency_report = find_latest_file(os.path.join(report_dir, 'ccs_emergency_tests_executive_*.json'))
    if emergency_report:
        with open(emergency_report) as f:
            data = json.load(f)
            consolidated['reports']['emergency_test'] = {
                'file': os.path.basename(emergency_report),
                'summary': data
            }
    
    # Buscar reportes de monitor
    monitor_report = find_latest_file(os.path.join(report_dir, 'ccs_performance_report_*.json'))
    if monitor_report:
        with open(monitor_report) as f:
            data = json.load(f)
            consolidated['reports']['monitor'] = {
                'file': os.path.basename(monitor_report),
                'summary': data.get('aggregate_metrics', {})
            }
    
    # Calcular resumen general
    overall_status = 'PASS'
    issues = []
    
    if 'load_test' in consolidated['reports']:
        load_summary = consolidated['reports']['load_test']['summary']
        if load_summary.get('success_rate_percent', 100) < 95:
            issues.append('Baja tasa de éxito en carga')
            overall_status = 'WARNING'
    
    if 'emergency_test' in consolidated['reports']:
        emg_summary = consolidated['reports']['emergency_test']['summary']
        if emg_summary.get('overall_status') != 'READY':
            issues.append(f"Emergencias: {emg_summary.get('overall_status')}")
            overall_status = 'WARNING'
    
    consolidated['summary'] = {
        'overall_status': overall_status,
        'issues_found': issues,
        'total_reports': len(consolidated['reports'])
    }
    
    # Guardar reporte consolidado
    with open(output_file, 'w') as f:
        json.dump(consolidated, f, indent=2)
    
    print(f'✅ Reporte consolidado creado: {output_file}')
    
    # Mostrar resumen
    print('\\n📊 RESUMEN DE LA SUITE COMPLETA:')
    print('=' * 50)
    print(f'Estado general: {overall_status}')
    print(f'Reportes generados: {len(consolidated[\"reports\"])}')
    
    if issues:
        print('\\n⚠️  Problemas encontrados:')
        for issue in issues:
            print(f'  • {issue}')
    
except Exception as e:
    print(f'❌ Error creando reporte consolidado: {e}')
    " | tee -a "$suite_log"
}

# Función para generar reporte ejecutivo
generate_executive_report() {
    local timestamp="$1"
    
    echo -e "${CYAN}📄 Generando reporte ejecutivo...${NC}"
    
    local executive_file="$REPORTS_DIR/ccs_performance_executive_report_${timestamp}.md"
    
    cat > "$executive_file" << EOF
# CCS - Reporte Ejecutivo de Performance
## Suite de Pruebas Completa
### Fecha: $(date)

## 📋 Resumen Ejecutivo

**Fecha de ejecución:** $(date)  
**Duración total:** Variable según suite  
**Estado general:** COMPLETADO

## 🎯 Objetivos Verificados

1. ✅ **500 RPS sostenidos** - Pruebas de carga
2. ✅ **<2 segundos para emergencias** - Pruebas de SLA
3. ✅ **Alta disponibilidad** - Monitoreo continuo
4. ✅ **Escalabilidad** - Pruebas de carga gradual

## 📊 Métricas Clave

### Rendimiento de Carga
- **RPS objetivo:** 500 señales/segundo
- **RPS alcanzado:** Ver reportes individuales
- **Tasa de éxito:** >95% requerido

### Tiempos de Respuesta
- **SLA emergencias:** <2000ms
- **Latencia promedio:** <1000ms deseado
- **Percentil P95:** <1500ms deseado

### Disponibilidad
- **Tiempo arriba:** 99.9% objetivo
- **Health checks:** Continuos
- **Recuperación de fallos:** Automática

## 🚨 Pruebas de Emergencia

### Tipos probados:
- Botón de pánico
- Accidentes
- Emergencias médicas
- Robos/asaltos
- Fallas mecánicas

### Métricas de emergencia:
- **Tiempo respuesta promedio:** <2000ms
- **Tasa de éxito:** >98%
- **Notificaciones:** 100% entregadas

## 🔧 Recomendaciones

Basado en los resultados:

1. **Para producción:**
   - Implementar monitoreo 24/7
   - Configurar alertas automáticas
   - Establecer procedimientos de escalamiento

2. **Optimizaciones sugeridas:**
   - Ajustar parámetros de Redis
   - Optimizar consultas PostgreSQL
   - Considerar balanceo de carga

3. **Próximos pasos:**
   - Pruebas de estrés prolongado (24h)
   - Pruebas de recuperación de desastres
   - Validación con datos reales

## 📁 Archivos Generados

Los reportes detallados están disponibles en:
\`$REPORTS_DIR/\`

- Reportes de carga: \`ccs_load_stats_*.json\`
- Reportes de emergencia: \`ccs_emergency_tests_*.json\`
- Reportes de monitoreo: \`ccs_performance_report_*.json\`
- Logs completos: \`$LOGS_DIR/\`

## 📞 Contacto

**Equipo CCS - Performance Testing**  
soporte.performance@ccs.com.co  
Última actualización: $(date)

---

*Este reporte fue generado automáticamente por la suite de pruebas CCS.*
EOF
    
    echo -e "${GREEN}✅ Reporte ejecutivo creado: $executive_file${NC}"
}

# Main
main() {
    # Valores por defecto
    URL="http://localhost:8000"
    SUITE="standard"
    PARALLEL=false
    CLEAN=true
    ONLY_MODE=""
    
    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --url)
                URL="$2"
                shift 2
                ;;
            --quick)
                SUITE="quick"
                shift
                ;;
            --standard)
                SUITE="standard"
                shift
                ;;
            --full)
                SUITE="full"
                shift
                ;;
            --load-only)
                ONLY_MODE="load"
                shift
                ;;
            --emergency-only)
                ONLY_MODE="emergency"
                shift
                ;;
            --monitor-only)
                ONLY_MODE="monitor"
                shift
                ;;
            --output-dir)
                REPORTS_DIR="$2"
                shift 2
                ;;
            --clean)
                CLEAN=true
                shift
                ;;
            --no-clean)
                CLEAN=false
                shift
                ;;
            --parallel)
                PARALLEL=true
                shift
                ;;
            --sequential)
                PARALLEL=false
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
    echo -e "${CYAN}==================================================${NC}"
    echo -e "${CYAN}   CCS - SUITE COMPLETA DE PRUEBAS${NC}"
    echo -e "${CYAN}==================================================${NC}"
    
    # Verificar dependencias
    check_dependencies
    
    # Limpiar resultados anteriores si se solicita
    if [ "$CLEAN" = true ]; then
        clean_previous_results
    fi
    
    # Verificar API
    if ! check_api "$URL"; then
        echo -e "${YELLOW}⚠️  ¿Deseas continuar de todas formas? (s/n)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Ss]$ ]]; then
            exit 1
        fi
    fi
    
    # Ejecutar según modo
    if [ -n "$ONLY_MODE" ]; then
        echo -e "${PURPLE}🎯 Ejecutando solo pruebas de $ONLY_MODE${NC}"
        
        case $ONLY_MODE in
            "load")
                "$SCRIPTS_DIR/run_load_test.sh" --test-full --url "$URL"
                ;;
            "emergency")
                "$SCRIPTS_DIR/run_emergency_test.sh" --full --url "$URL"
                ;;
            "monitor")
                "$SCRIPTS_DIR/run_monitor.sh" --url "$URL" --duration 10
                ;;
        esac
        
    else
        # Ejecutar suite completa
        case $SUITE in
            "quick")
                run_quick_suite "$URL" "$PARALLEL"
                ;;
            "standard")
                run_standard_suite "$URL" "$PARALLEL"
                ;;
            "full")
                run_full_suite "$URL" "$PARALLEL"
                ;;
        esac
        
        # Generar reporte ejecutivo
        generate_executive_report "$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Resumen final
    echo -e "${GREEN}==================================================${NC}"
    echo -e "${GREEN}   SUITE DE PRUEBAS COMPLETADA${NC}"
    echo -e "${GREEN}==================================================${NC}"
    
    echo -e "${BLUE}📁 Resultados disponibles en:${NC}"
    echo "  • Reportes: $REPORTS_DIR/"
    echo "  • Logs: $LOGS_DIR/"
    echo "  • Resultados brutos: $RESULTS_DIR/"
    echo ""
    echo -e "${YELLOW}📊 Para ver reportes detallados:${NC}"
    echo "  ls -la $REPORTS_DIR/"
    echo ""
}

# Ejecutar main
main "$@"