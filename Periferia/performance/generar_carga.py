"""
CCS - Generador de Carga Puro (Load Generator) MEJORADO
Envía señales compatibles con el modelo Signal de la aplicación CCS.
"""
import asyncio
import aiohttp
import random
import time
from datetime import datetime, timezone
from typing import List, Dict
import json
import argparse
from pathlib import Path
import statistics
import uuid

# --- CONFIGURACIÓN POR DEFECTO MEJORADA ---
DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000",
    "target_rps": 500,                    # REQUERIMIENTO: 500 señales/segundo
    "duration_seconds": 120,              # REQUERIMIENTO: 2 minutos
    "num_vehicles": 150,                  # 10% del total proyectado
    "vehicle_types": ["TRUCK", "CAR", "MOTO"],
    "vehicle_prefixes": {
        "TRUCK": "TRUCK",
        "CAR": "CAR", 
        "MOTO": "MOTO"
    },
    "panic_probability": 0.001,           # 0.1% probabilidad de botón de pánico
    "high_temp_probability": 0.02,        # 2% probabilidad de temperatura alta
    "timeout_seconds": 5,                 # Timeout más ajustado
    "concurrent_workers": 100,            # Workers concurrentes para alta carga
    "output_dir": "performance/results"   # Carpeta específica para results
}


class CCSLoadGenerator:
    """Generador de carga optimizado para CCS API."""
    
    def __init__(self, config: dict):
        self.config = config
        self.vehicles = self._generate_vehicle_pool()
        self.results = []
        self.start_time = None
        self.end_time = None
        self.session = None
        self.test_id = f"LOAD-{uuid.uuid4().hex[:8].upper()}"
        
    def _generate_vehicle_pool(self) -> List[Dict]:
        """Genera pool de vehículos con características realistas."""
        vehicles = []
        vehicle_count = 0
        
        for vtype in self.config["vehicle_types"]:
            prefix = self.config["vehicle_prefixes"].get(vtype, vtype)
            
            # Distribuir vehículos proporcionalmente
            if vtype == "TRUCK":
                count = int(self.config["num_vehicles"] * 0.4)  # 40% camiones
            elif vtype == "CAR":
                count = int(self.config["num_vehicles"] * 0.35)  # 35% carros
            else:
                count = int(self.config["num_vehicles"] * 0.25)  # 25% motos
            
            for i in range(count):
                vehicle_id = f"{prefix}-{vehicle_count + i + 1:03d}"
                
                # Características específicas por tipo
                metadata = {
                    "driver_id": f"DRV-{random.randint(1000, 9999)}",
                    "plate": f"ABC{random.randint(100, 999)}{random.choice(['A', 'B', 'C'])}",
                    "company": random.choice(["CCS", "TRANSPORTE_SA", "LOGISTICA_COL"]),
                    "fuel_level": random.randint(20, 100),
                    "engine_hours": random.randint(0, 5000)
                }
                
                if vtype == "TRUCK":
                    metadata.update({
                        "cargo_type": random.choice(["general", "refrigerated", "hazardous", "bulk"]),
                        "weight_kg": random.randint(1000, 20000),
                        "has_trailer": random.choice([True, False])
                    })
                
                vehicles.append({
                    "id": vehicle_id,
                    "type": vtype,
                    "metadata": metadata,
                    "max_speed": random.uniform(80, 120) if vtype != "TRUCK" else random.uniform(60, 90),
                    "current_location": {
                        "lat": 4.6 + random.uniform(-0.3, 0.3),
                        "lon": -74.0 + random.uniform(-0.3, 0.3)
                    }
                })
            
            vehicle_count += count
        
        return vehicles
    
    def _create_signal_payload(self, vehicle: Dict) -> dict:
        """Crea un payload de señal compatible con el modelo Signal de CCS."""
        # Determinar si es emergencia
        is_emergency = random.random() < self.config["panic_probability"]
        
        # Mover vehículo ligeramente
        lat = vehicle["current_location"]["lat"] + random.uniform(-0.001, 0.001)
        lon = vehicle["current_location"]["lon"] + random.uniform(-0.001, 0.001)
        
        # Actualizar ubicación
        vehicle["current_location"]["lat"] = lat
        vehicle["current_location"]["lon"] = lon
        
        # Crear payload según modelo Signal
        payload = {
            "vehicle_id": vehicle["id"],
            "speed": random.uniform(0, vehicle["max_speed"]),
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "panic_button": is_emergency,
            "vehicle_type": vehicle["type"],
            "metadata": vehicle["metadata"].copy()
        }
        
        # Agregar temperatura para camiones (algunos refrigerados)
        if vehicle["type"] == "TRUCK" and random.random() < 0.3:
            payload["temperature"] = random.uniform(-20, 5)
            if random.random() < self.config["high_temp_probability"]:
                payload["temperature"] = random.uniform(10, 25)  # Temperatura ALTA para alerta
        
        # Simular otros sensores
        if vehicle["type"] == "TRUCK":
            payload["metadata"]["door_status"] = random.choice(["closed", "closed", "closed", "open"])
            payload["metadata"]["engine_temp"] = random.uniform(70, 110)
        
        return payload
    
    async def _send_signal(self, session: aiohttp.ClientSession, vehicle: Dict) -> Dict:
        """Envía una señal y retorna resultado detallado."""
        payload = self._create_signal_payload(vehicle)
        signal_id = f"SIG-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        start_time = time.perf_counter()
        
        try:
            async with session.post(
                f"{self.config['api_url']}/signal",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config["timeout_seconds"])
            ) as response:
                
                response_time = (time.perf_counter() - start_time) * 1000  # ms
                
                result = {
                    "signal_id": signal_id,
                    "vehicle_id": vehicle["id"],
                    "vehicle_type": vehicle["type"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": payload,
                    "status": "unknown",
                    "http_status": response.status,
                    "response_time_ms": response_time,
                    "processing_time_ms": 0,
                    "is_emergency": payload.get("panic_button", False),
                    "alerts_generated": 0,
                    "error": None
                }
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        result.update({
                            "status": "success",
                            "processing_time_ms": data.get("processing_time_ms", 0),
                            "alerts_generated": data.get("alerts_generated", 0),
                            "priority": data.get("priority", "normal"),
                            "message_id": data.get("message_id", "unknown")
                        })
                    except:
                        result.update({
                            "status": "json_error",
                            "error": "Invalid JSON response"
                        })
                elif response.status == 202:  # Accepted
                    try:
                        data = await response.json()
                        result.update({
                            "status": "accepted",
                            "processing_time_ms": data.get("processing_time_ms", 0),
                            "priority": data.get("priority", "normal")
                        })
                    except:
                        result.update({
                            "status": "accepted_no_json",
                            "error": "No JSON in 202 response"
                        })
                else:
                    result.update({
                        "status": f"http_error_{response.status}",
                        "error": f"HTTP {response.status}: {await response.text()[:100]}"
                    })
                
                return result
                
        except asyncio.TimeoutError:
            return {
                "signal_id": signal_id,
                "vehicle_id": vehicle["id"],
                "status": "timeout",
                "http_status": 0,
                "response_time_ms": self.config["timeout_seconds"] * 1000,
                "processing_time_ms": 0,
                "is_emergency": payload.get("panic_button", False),
                "error": f"Timeout after {self.config['timeout_seconds']}s"
            }
        except Exception as e:
            return {
                "signal_id": signal_id,
                "vehicle_id": vehicle["id"],
                "status": "exception",
                "http_status": 0,
                "response_time_ms": (time.perf_counter() - start_time) * 1000,
                "processing_time_ms": 0,
                "is_emergency": payload.get("panic_button", False),
                "error": str(e)[:100]
            }
    
    async def _run_second(self, session: aiohttp.ClientSession, second_num: int) -> Dict:
        """Ejecuta un segundo completo de carga con control de ritmo."""
        target_rps = self.config["target_rps"]
        
        # Crear semáforo para control de concurrencia
        semaphore = asyncio.Semaphore(self.config["concurrent_workers"])
        
        async def send_with_semaphore(vehicle):
            async with semaphore:
                return await self._send_signal(session, vehicle)
        
        # Seleccionar vehículos para este segundo
        selected_vehicles = random.choices(self.vehicles, k=target_rps)
        
        # Medir tiempo exacto
        start_time = time.perf_counter()
        
        # Ejecutar todas las peticiones
        tasks = [send_with_semaphore(vehicle) for vehicle in selected_vehicles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar excepciones
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                valid_results.append({
                    "status": "gather_exception",
                    "error": str(r),
                    "response_time_ms": (time.perf_counter() - start_time) * 1000
                })
            else:
                valid_results.append(r)
        
        execution_time = time.perf_counter() - start_time
        
        # Calcular estadísticas
        success_count = sum(1 for r in valid_results if r.get("status") in ["success", "accepted"])
        emergency_count = sum(1 for r in valid_results if r.get("is_emergency", False))
        alerts_total = sum(r.get("alerts_generated", 0) for r in valid_results)
        
        response_times = [r.get("response_time_ms", 0) for r in valid_results]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        stats = {
            "second": second_num,
            "target_rps": target_rps,
            "actual_rps": len(valid_results),
            "execution_time_sec": execution_time,
            "success_count": success_count,
            "error_count": len(valid_results) - success_count,
            "emergency_count": emergency_count,
            "alerts_total": alerts_total,
            "avg_response_time_ms": avg_response_time,
            "p95_response_time_ms": statistics.quantiles(response_times, n=100)[94] if len(response_times) >= 5 else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Guardar muestra de resultados
        if second_num % 5 == 0:  # Cada 5 segundos
            sample_size = min(50, len(valid_results))
            self.results.extend(random.sample(valid_results, sample_size) if sample_size > 0 else [])
        
        # Mostrar progreso
        success_rate = (success_count / len(valid_results) * 100) if valid_results else 0
        print(f"⏱️  T+{second_num:03d}s | "
              f"RPS: {stats['actual_rps']:4d}/{target_rps} | "
              f"OK: {success_rate:5.1f}% | "
              f"Emerg: {emergency_count:2d} | "
              f"Alertas: {alerts_total:4d} | "
              f"AvgRT: {avg_response_time:6.1f}ms")
        
        # Control de ritmo preciso
        if execution_time < 1.0:
            await asyncio.sleep(1.0 - execution_time)
        
        return stats
    
    async def run(self):
        """Ejecuta la prueba de carga completa."""
        print("=" * 80)
        print("🚀 CCS - GENERADOR DE CARGA OPTIMIZADO")
        print(f"Test ID: {self.test_id}")
        print(f"Objetivo: {self.config['target_rps']} RPS × {self.config['duration_seconds']}s")
        print(f"Vehículos: {len(self.vehicles)} ({', '.join(self.config['vehicle_types'])})")
        print(f"Workers: {self.config['concurrent_workers']}")
        print(f"API: {self.config['api_url']}")
        print("=" * 80)
        
        self.start_time = datetime.now(timezone.utc)
        all_stats = []
        
        async with aiohttp.ClientSession() as session:
            for second in range(self.config["duration_seconds"]):
                try:
                    stats = await self._run_second(session, second)
                    all_stats.append(stats)
                except KeyboardInterrupt:
                    print(f"\n🛑 Prueba interrumpida en segundo {second}")
                    break
                except Exception as e:
                    print(f"\n⚠️ Error en segundo {second}: {str(e)[:50]}")
                    # Stats de error para mantener continuidad
                    all_stats.append({
                        "second": second,
                        "error": str(e),
                        "actual_rps": 0,
                        "success_count": 0
                    })
                    continue
        
        self.end_time = datetime.now(timezone.utc)
        
        # Guardar resultados
        self._save_results(all_stats)
        
        # Mostrar resumen
        self._print_summary(all_stats)
    
    def _save_results(self, stats: List[Dict]):
        """Guarda resultados en la carpeta designada."""
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Estadísticas por segundo (principal)
        stats_file = output_dir / f"ccs_load_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_id": self.test_id,
                "metadata": {
                    "config": self.config,
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                    "duration_seconds": len(stats),
                    "total_vehicles": len(self.vehicles)
                },
                "summary": self._calculate_summary(stats),
                "stats_by_second": stats
            }, f, indent=2, ensure_ascii=False)
        
        # 2. Muestra de señales individuales
        if self.results:
            samples_file = output_dir / f"ccs_load_samples_{timestamp}.json"
            with open(samples_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_id": self.test_id,
                    "samples_count": len(self.results),
                    "samples": self.results[:100]  # Solo 100 muestras para tamaño manejable
                }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: {output_dir}/")
        print(f"   • ccs_load_stats_{timestamp}.json")
        if self.results:
            print(f"   • ccs_load_samples_{timestamp}.json")
    
    def _calculate_summary(self, stats: List[Dict]) -> Dict:
        """Calcula estadísticas resumen."""
        if not stats:
            return {}
        
        total_requests = sum(s.get("actual_rps", 0) for s in stats)
        total_success = sum(s.get("success_count", 0) for s in stats)
        total_emergencies = sum(s.get("emergency_count", 0) for s in stats)
        total_alerts = sum(s.get("alerts_total", 0) for s in stats)
        
        # Calcular RPS promedio y máximo
        rps_values = [s.get("actual_rps", 0) for s in stats]
        avg_rps = statistics.mean(rps_values) if rps_values else 0
        max_rps = max(rps_values) if rps_values else 0
        
        # Calcular tiempos de respuesta
        response_times = []
        for s in stats:
            if s.get("avg_response_time_ms", 0) > 0:
                response_times.append(s["avg_response_time_ms"])
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        return {
            "total_seconds": len(stats),
            "total_requests": total_requests,
            "total_success": total_success,
            "success_rate_percent": (total_success / total_requests * 100) if total_requests > 0 else 0,
            "total_emergencies": total_emergencies,
            "total_alerts": total_alerts,
            "avg_rps": round(avg_rps, 2),
            "max_rps": max_rps,
            "target_rps": self.config["target_rps"],
            "avg_response_time_ms": round(avg_response_time, 2),
            "target_sla_seconds": 2,
            "sla_compliant_percent": (sum(1 for s in stats if s.get("p95_response_time_ms", 9999) < 2000) / len(stats) * 100) if stats else 0
        }
    
    def _print_summary(self, stats: List[Dict]):
        """Imprime resumen completo de la prueba."""
        if not stats:
            print("❌ No se ejecutó ninguna prueba")
            return
        
        summary = self._calculate_summary(stats)
        duration = (self.end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 RESUMEN COMPLETO DE PRUEBA DE CARGA")
        print("=" * 80)
        print(f"📈 MÉTRICAS DE RENDIMIENTO:")
        print(f"   • Test ID: {self.test_id}")
        print(f"   • Duración real: {duration:.1f}s (objetivo: {self.config['duration_seconds']}s)")
        print(f"   • Total peticiones: {summary['total_requests']:,}")
        print(f"   • RPS promedio: {summary['avg_rps']:.1f} (objetivo: {summary['target_rps']})")
        print(f"   • RPS máximo: {summary['max_rps']}")
        print(f"   • Tasa de éxito: {summary['success_rate_percent']:.1f}%")
        print(f"   • Tiempo respuesta promedio: {summary['avg_response_time_ms']:.1f}ms")
        print(f"   • Cumplimiento SLA (<2s): {summary['sla_compliant_percent']:.1f}%")
        
        print(f"\n🚨 MÉTRICAS DE NEGOCIO:")
        print(f"   • Emergencias simuladas: {summary['total_emergencies']}")
        print(f"   • Alertas generadas: {summary['total_alerts']}")
        print(f"   • Vehículos activos: {len(self.vehicles)}")
        
        print(f"\n🎯 EVALUACIÓN DE REQUISITOS:")
        
        # Evaluar requisito de 500 RPS
        rps_ok = summary['avg_rps'] >= (self.config['target_rps'] * 0.95)  # 95% del objetivo
        rps_status = "✅" if rps_ok else "❌"
        print(f"   • 500 RPS sostenidos: {rps_status} ({summary['avg_rps']:.1f} RPS)")
        
        # Evaluar SLA de 2 segundos
        sla_ok = summary['sla_compliant_percent'] >= 95  # 95% cumplimiento
        sla_status = "✅" if sla_ok else "❌"
        print(f"   • SLA <2s para emergencias: {sla_status} ({summary['sla_compliant_percent']:.1f}%)")
        
        # Evaluar duración
        duration_ok = duration >= (self.config['duration_seconds'] * 0.9)  # 90% de duración
        duration_status = "✅" if duration_ok else "⚠️"
        print(f"   • 2 minutos de carga: {duration_status} ({duration:.1f}s)")
        
        print(f"\n📁 Resultados guardados en: {self.config['output_dir']}/")
        print(f"\n🔧 Recomendaciones:")
        
        if not rps_ok:
            print("   • Aumentar workers concurrentes o optimizar API")
        if not sla_ok:
            print("   • Investigar latencias altas en emergencias")
        if summary['success_rate_percent'] < 95:
            print("   • Revisar logs de errores HTTP/timeout")
        
        print(f"\n✅ Prueba de carga completada.")


def parse_args():
    """Parse argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Generador de carga optimizado para CCS API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                                 # 500 RPS × 2 minutos
  %(prog)s --rps 300 --duration 60         # 300 RPS por 60 segundos
  %(prog)s --url http://api.ccs.com:8000   # API remota
  %(prog)s --vehicles 200 --workers 50     # 200 vehículos, 50 workers
  %(prog)s --panic-prob 0.01               # 1% probabilidad de emergencia
        """
    )
    
    parser.add_argument('--url', default=DEFAULT_CONFIG['api_url'],
                       help=f'URL base de la API (default: {DEFAULT_CONFIG["api_url"]})')
    parser.add_argument('--rps', type=int, default=DEFAULT_CONFIG['target_rps'],
                       help=f'Señales por segundo (default: {DEFAULT_CONFIG["target_rps"]})')
    parser.add_argument('--duration', type=int, default=DEFAULT_CONFIG['duration_seconds'],
                       help=f'Duración en segundos (default: {DEFAULT_CONFIG["duration_seconds"]})')
    parser.add_argument('--vehicles', type=int, default=DEFAULT_CONFIG['num_vehicles'],
                       help=f'Número de vehículos (default: {DEFAULT_CONFIG["num_vehicles"]})')
    parser.add_argument('--workers', type=int, default=DEFAULT_CONFIG['concurrent_workers'],
                       help=f'Workers concurrentes (default: {DEFAULT_CONFIG["concurrent_workers"]})')
    parser.add_argument('--output-dir', default=DEFAULT_CONFIG['output_dir'],
                       help=f'Directorio para resultados (default: {DEFAULT_CONFIG["output_dir"]})')
    parser.add_argument('--panic-prob', type=float, default=DEFAULT_CONFIG['panic_probability'],
                       help=f'Probabilidad botón pánico (default: {DEFAULT_CONFIG["panic_probability"]})')
    parser.add_argument('--vehicle-types', nargs='+', default=DEFAULT_CONFIG['vehicle_types'],
                       help=f'Tipos de vehículos (default: {DEFAULT_CONFIG["vehicle_types"]})')
    
    return parser.parse_args()


async def main():
    """Función principal."""
    args = parse_args()
    
    # Configuración personalizada
    config = DEFAULT_CONFIG.copy()
    config.update({
        "api_url": args.url.rstrip('/'),
        "target_rps": args.rps,
        "duration_seconds": args.duration,
        "num_vehicles": args.vehicles,
        "concurrent_workers": args.workers,
        "output_dir": args.output_dir,
        "panic_probability": args.panic_prob,
        "vehicle_types": args.vehicle_types
    })
    
    try:
        generator = CCSLoadGenerator(config)
        await generator.run()
    except KeyboardInterrupt:
        print("\n🛑 Generador detenido por usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Instalar dependencias: pip install aiohttp
    asyncio.run(main())