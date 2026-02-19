# POC OVERVIEW - Validación Arquitectura CCS

## 🎯 1. CONTEXTO Y OBJETIVOS

### Contexto del Reto Técnico:
- CCS: 9,000+ vehículos monitoreados (20% crecimiento anual)
- Requisitos: 500 señales/seg × 2 min, SLA <2s emergencias
- Necesidad: Central que procese, analice y notifique en tiempo real

### Objetivos del POC:
1. **Validar rendimiento**: 500 RPS sostenidos durante 2 minutos
2. **Garantizar SLA**: <2 segundos para señales de emergencia
3. **Probar escalabilidad**: Cache Redis + PostgreSQL particionado
4. **Verificar funcionalidad**: Alertas, persistencia, actualización reglas

## 📊 3. MÉTRICAS DE VALIDACIÓN

### Métricas Clave a Medir:
| Métrica | Objetivo | Cómo se mide |
|---------|----------|--------------|
| **Throughput** | 500 RPS promedio | Script `generar_carga.py` |
| **Latencia P95** | < 2000 ms | Percentil 95 tiempos respuesta |
| **Disponibilidad** | > 99.9% | Health checks continuos |
| **Cache Hit Rate** | > 80% | `cache_status` en respuestas |
| **Persistencia** | 100% alertas guardadas | Consultas SQL a `alerts` |

### Criterios de Éxito:
- ✅ RPS ≥ 475 sostenidos × 120 segundos
- ✅ P95 latencia < 2000 ms
- ✅ 0% pérdida de datos (alertas persistentes)
- ✅ Cache funcionando (miss → hit pattern)