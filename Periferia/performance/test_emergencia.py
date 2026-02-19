"""
CCS - Pruebas de Emergencia Mejoradas
Pruebas especializadas para validar el procesamiento de emergencias (<2s SLA).
"""

import asyncio
import aiohttp
import time
import random
import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json
import argparse
from pathlib import Path
import uuid
import sys

# ============================================================================
# 1. CONFIGURACIÓN Y MODELOS
# ============================================================================

DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000",
    "timeout_seconds": 10,
    "concurrent_workers": 20,
    "output_dir": "performance/results",
    "sla_threshold_ms": 2000,  # REQUERIMIENTO: <2 segundos
    "max_emergency_duration_ms": 5000,  # Máximo tiempo permitido
    "vehicle_pool_size": 50,
    "location_spread_km": 0.1,
    "emergency_types": [
        "panic_button", "accident", "robbery", "medical", 
        "mechanical", "fire", "hijacking", "assault"
    ]
}

class EmergencyTestResult:
    """Resultado de una prueba de emergencia individual."""
    
    def __init__(self, test_id: str = None):
        self.test_id = test_id or f"EMG-{uuid.uuid4().hex[:8].upper()}"
        self.start_time = None
        self.end_time = None
        self.success = False
        self.sla_compliant = False
        self.http_status = 0
        self.total_latency_ms = 0
        self.api_processing_ms = 0
        self.api_response_time_ms = 0
        self.is_emergency = False
        self.vehicle_id = ""
        self.emergency_type = ""
        self.location = {"lat": 0, "lon": 0}
        self.api_message_id = ""
        self.api_priority = ""
        self.alerts_generated = 0
        self.error_message = ""
        self.retry_count = 0
        self.payload = {}
        self.api_response = {}
        
    def to_dict(self) -> Dict:
        """Convierte a diccionario serializable."""
        return {
            "test_id": self.test_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": self.success,
            "sla_compliant": self.sla_compliant,
            "http_status": self.http_status,
            "total_latency_ms": self.total_latency_ms,
            "api_processing_ms": self.api_processing_ms,
            "api_response_time_ms": self.api_response_time_ms,
            "is_emergency": self.is_emergency,
            "vehicle_id": self.vehicle_id,
            "emergency_type": self.emergency_type,
            "location": self.location,
            "api_message_id": self.api_message_id,
            "api_priority": self.api_priority,
            "alerts_generated": self.alerts_generated,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "execution_duration_ms": (self.end_time - self.start_time).total_seconds() * 1000 
                                     if self.start_time and self.end_time else 0
        }

class EmergencyTestSuite:
    """Suite completa de pruebas de emergencia."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results: List[EmergencyTestResult] = []
        self.vehicles = self._generate_vehicle_pool()
        self.locations = self._generate_locations_pool()
        self.session = None
        self.start_time = None
        self.end_time = None
        self.suite_id = f"EMG-SUITE-{uuid.uuid4().hex[:8].upper()}"
        
    def _generate_vehicle_pool(self) -> List[Dict]:
        """Genera pool de vehículos para pruebas."""
        vehicles = []
        vehicle_count = self.config["vehicle_pool_size"]
        
        # Distribución realista
        types_distribution = [
            ("TRUCK", int(vehicle_count * 0.4)),
            ("CAR", int(vehicle_count * 0.35)),
            ("MOTO", int(vehicle_count * 0.25))
        ]
        
        count = 0
        for vtype, type_count in types_distribution:
            for i in range(type_count):
                vehicle_id = f"{vtype}-EMG-{count + i + 1:03d}"
                vehicles.append({
                    "id": vehicle_id,
                    "type": vtype,
                    "max_speed": random.uniform(60, 120) if vtype != "TRUCK" else random.uniform(50, 90),
                    "has_panic_button": True,
                    "has_temperature_sensor": vtype == "TRUCK",
                    "has_door_sensor": vtype == "TRUCK",
                    "metadata": {
                        "driver_id": f"DRV-EMG-{random.randint(1000, 9999)}",
                        "plate": f"EMG{random.randint(100, 999)}{random.choice(['A', 'B', 'C'])}",
                        "company": "CCS_EMERGENCY_TEST",
                        "emergency_contact": f"+57300{random.randint(1000000, 9999999)}"
                    }
                })
            count += type_count
        
        return vehicles
    
    def _generate_locations_pool(self) -> List[Dict]:
        """Genera ubicaciones realistas para Bogotá."""
        base_locations = [
            {"name": "Centro", "lat": 4.598056, "lon": -74.075833},
            {"name": "Chapinero", "lat": 4.648611, "lon": -74.062778},
            {"name": "Usaquén", "lat": 4.6975, "lon": -74.034167},
            {"name": "Fontibón", "lat": 4.675833, "lon": -74.141667},
            {"name": "Kennedy", "lat": 4.63, "lon": -74.15},
            {"name": "Suba", "lat": 4.75, "lon": -74.083333},
            {"name": "Engativá", "lat": 4.7, "lon": -74.116667},
            {"name": "Bosa", "lat": 4.61, "lon": -74.19}
        ]
        
        locations = []
        spread = self.config["location_spread_km"] / 111.0  # Convertir km a grados
        
        for loc in base_locations:
            # Crear variaciones alrededor de cada ubicación base
            for i in range(5):
                locations.append({
                    "name": f"{loc['name']}_{i}",
                    "lat": loc["lat"] + random.uniform(-spread, spread),
                    "lon": loc["lon"] + random.uniform(-spread, spread),
                    "base": loc["name"]
                })
        
        return locations
    
    def _create_emergency_payload(self, vehicle: Dict, emergency_type: str) -> Dict:
        """Crea payload de emergencia realista."""
        location = random.choice(self.locations)
        
        payload = {
            "vehicle_id": vehicle["id"],
            "speed": random.uniform(0, vehicle["max_speed"]),
            "latitude": location["lat"],
            "longitude": location["lon"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "panic_button": True,  # Siempre True para emergencias
            "vehicle_type": vehicle["type"],
            "metadata": vehicle["metadata"].copy()
        }
        
        # Agregar información específica de la emergencia
        payload["metadata"].update({
            "emergency_type": emergency_type,
            "emergency_timestamp": datetime.now(timezone.utc).isoformat(),
            "location_name": location["name"],
            "test_scenario": True,
            "severity": random.choice(["low", "medium", "high", "critical"]),
            "description": self._get_emergency_description(emergency_type, vehicle["type"])
        })
        
        # Agregar sensores según tipo de vehículo
        if vehicle["has_temperature_sensor"]:
            payload["temperature"] = random.uniform(-20, 40)
        
        if vehicle["has_door_sensor"]:
            payload["metadata"]["door_status"] = random.choice(["open", "closed"])
        
        return payload
    
    def _get_emergency_description(self, emergency_type: str, vehicle_type: str) -> str:
        """Genera descripción realista de la emergencia."""
        descriptions = {
            "panic_button": [
                f"Botón de pánico activado en {vehicle_type}",
                f"Emergencia no especificada - botón de pánico",
                f"Solicitud de ayuda inmediata"
            ],
            "accident": [
                f"Accidente de tránsito involucrando {vehicle_type}",
                f"Colisión reportada",
                f"Vehiculo accidentado requiere asistencia"
            ],
            "robbery": [
                f"Posible robo en {vehicle_type}",
                f"Conductor reporta asalto",
                f"Situación de seguridad en vehículo"
            ],
            "medical": [
                f"Emergencia médica en {vehicle_type}",
                f"Conductor/pasajero requiere atención médica",
                f"Problema de salud reportado"
            ],
            "mechanical": [
                f"Falla mecánica en {vehicle_type}",
                f"Vehiculo inmovilizado por falla",
                f"Problema mecánico crítico"
            ],
            "fire": [
                f"Incendio reportado en {vehicle_type}",
                f"Fuego en vehículo",
                f"Humo o llamas visibles"
            ],
            "hijacking": [
                f"Posible secuestro de {vehicle_type}",
                f"Vehiculo desviado de ruta",
                f"Situación de toma de control"
            ],
            "assault": [
                f"Agresión reportada en {vehicle_type}",
                f"Violencia contra conductor/pasajeros",
                f"Situación de peligro personal"
            ]
        }
        
        return random.choice(descriptions.get(emergency_type, ["Emergencia reportada"]))

# ============================================================================
# 2. PRUEBAS INDIVIDUALES MEJORADAS
# ============================================================================

class EmergencyTester:
    """Tester especializado en emergencias CCS."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = None
        self.test_suite = EmergencyTestSuite(config)
        self.stats = {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "sla_compliant_tests": 0,
            "total_latency_ms": 0,
            "emergencies_by_type": {},
            "vehicles_tested": set(),
            "concurrent_tests": 0,
            "max_concurrent": 0
        }
    
    async def initialize(self):
        """Inicializa el tester."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config["timeout_seconds"])
        )
        print(f"🚀 Inicializando Emergency Tester")
        print(f"📡 API: {self.config['api_url']}")
        print(f"⏱️  SLA: <{self.config['sla_threshold_ms']}ms")
        print(f"🚗 Vehículos: {len(self.test_suite.vehicles)}")
        print(f"📍 Ubicaciones: {len(self.test_suite.locations)}")
        print("=" * 80)
    
    async def close(self):
        """Cierra el tester."""
        if self.session:
            await self.session.close()
    
    async def test_single_emergency(self, 
                                   emergency_type: str = None,
                                   vehicle: Dict = None,
                                   validate_response: bool = True) -> EmergencyTestResult:
        """Ejecuta prueba individual de emergencia."""
        result = EmergencyTestResult()
        result.start_time = datetime.now(timezone.utc)
        
        # Seleccionar vehículo si no se proporciona
        if not vehicle:
            vehicle = random.choice(self.test_suite.vehicles)
        
        # Seleccionar tipo de emergencia si no se proporciona
        if not emergency_type:
            emergency_type = random.choice(self.config["emergency_types"])
        
        result.vehicle_id = vehicle["id"]
        result.emergency_type = emergency_type
        result.is_emergency = True
        
        # Seleccionar ubicación
        location = random.choice(self.test_suite.locations)
        result.location = {"lat": location["lat"], "lon": location["lon"]}
        
        # Crear payload
        payload = self.test_suite._create_emergency_payload(vehicle, emergency_type)
        result.payload = payload.copy()  # Guardar copia para análisis
        
        # Enviar emergencia
        try:
            send_start = time.perf_counter()
            
            async with self.session.post(
                f"{self.config['api_url']}/signal",
                json=payload,
                headers={"X-Emergency-Test": "true"}
            ) as response:
                
                result.api_response_time_ms = (time.perf_counter() - send_start) * 1000
                result.http_status = response.status
                
                if response.status == 200:
                    # Éxito HTTP
                    response_data = await response.json()
                    result.api_response = response_data
                    
                    # Extraer datos de respuesta
                    result.api_processing_ms = response_data.get("processing_time_ms", 0)
                    result.api_message_id = response_data.get("message_id", "")
                    result.api_priority = response_data.get("priority", "")
                    
                    # Validar que sea emergencia
                    if result.api_priority == "emergency":
                        result.success = True
                        
                        # Calcular latencia total (envío + procesamiento reportado)
                        result.total_latency_ms = result.api_response_time_ms + result.api_processing_ms
                        
                        # Verificar SLA
                        result.sla_compliant = result.total_latency_ms < self.config["sla_threshold_ms"]
                        
                        if validate_response:
                            # Validaciones adicionales
                            await self._validate_emergency_response(result, response_data)
                    
                    else:
                        result.success = False
                        result.error_message = f"Prioridad incorrecta: {result.api_priority}"
                
                elif response.status == 202:  # Accepted
                    result.success = True
                    result.api_priority = "emergency"  # Asumir emergencia
                    result.total_latency_ms = result.api_response_time_ms
                    result.sla_compliant = result.total_latency_ms < self.config["sla_threshold_ms"]
                    
                else:
                    result.success = False
                    result.error_message = f"HTTP {response.status}: {await response.text()[:100]}"
        
        except asyncio.TimeoutError:
            result.success = False
            result.error_message = f"Timeout after {self.config['timeout_seconds']}s"
            result.total_latency_ms = self.config["timeout_seconds"] * 1000
        
        except Exception as e:
            result.success = False
            result.error_message = str(e)[:100]
            result.total_latency_ms = (time.perf_counter() - send_start) * 1000
        
        finally:
            result.end_time = datetime.now(timezone.utc)
            
            # Actualizar estadísticas
            self._update_stats(result)
            
            # Mostrar resultado
            self._print_single_result(result)
            
            # Guardar en suite
            self.test_suite.results.append(result)
            
            return result
    
    async def _validate_emergency_response(self, result: EmergencyTestResult, response_data: Dict):
        """Realiza validaciones adicionales de la respuesta."""
        try:
            # Verificar que la respuesta incluya campos esperados
            required_fields = ["status", "vehicle_id", "priority"]
            for field in required_fields:
                if field not in response_data:
                    result.success = False
                    result.error_message = f"Campo faltante: {field}"
                    return
            
            # Verificar que vehicle_id coincida
            if response_data.get("vehicle_id") != result.vehicle_id:
                result.success = False
                result.error_message = f"Vehicle ID mismatch: {response_data.get('vehicle_id')} != {result.vehicle_id}"
                return
            
            # Verificar prioridad de emergencia
            if response_data.get("priority") != "emergency":
                result.success = False
                result.error_message = f"Prioridad no es emergencia: {response_data.get('priority')}"
                return
            
            # Verificar tiempo de procesamiento razonable
            processing_time = response_data.get("processing_time_ms", 0)
            if processing_time > self.config["max_emergency_duration_ms"]:
                result.success = False
                result.error_message = f"Tiempo de procesamiento excesivo: {processing_time}ms"
                return
            
            # Si hay alertas generadas, verificar estructura
            if "alerts_generated" in response_data:
                result.alerts_generated = response_data["alerts_generated"]
            
        except Exception as e:
            result.success = False
            result.error_message = f"Error en validación: {str(e)[:50]}"
    
    def _update_stats(self, result: EmergencyTestResult):
        """Actualiza estadísticas del test."""
        self.stats["total_tests"] += 1
        
        if result.success:
            self.stats["successful_tests"] += 1
            if result.sla_compliant:
                self.stats["sla_compliant_tests"] += 1
        else:
            self.stats["failed_tests"] += 1
        
        self.stats["total_latency_ms"] += result.total_latency_ms
        
        # Contar por tipo de emergencia
        emergency_type = result.emergency_type
        if emergency_type not in self.stats["emergencies_by_type"]:
            self.stats["emergencies_by_type"][emergency_type] = {
                "total": 0, "success": 0, "sla_compliant": 0
            }
        
        self.stats["emergencies_by_type"][emergency_type]["total"] += 1
        if result.success:
            self.stats["emergencies_by_type"][emergency_type]["success"] += 1
        if result.sla_compliant:
            self.stats["emergencies_by_type"][emergency_type]["sla_compliant"] += 1
        
        # Registrar vehículo
        self.stats["vehicles_tested"].add(result.vehicle_id)
    
    def _print_single_result(self, result: EmergencyTestResult):
        """Imprime resultado individual formateado."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if result.success:
            status_icon = "✅" if result.sla_compliant else "⚠️"
            sla_status = "COMPLIES" if result.sla_compliant else "VIOLATES"
            color = "\033[92m" if result.sla_compliant else "\033[93m"
            reset = "\033[0m"
            
            print(f"{timestamp} {status_icon} {color}{result.emergency_type.upper():12}{reset} | "
                  f"🚗 {result.vehicle_id:12} | "
                  f"⏱️  {result.total_latency_ms:6.1f}ms ({sla_status}) | "
                  f"📡 {result.api_response_time_ms:5.1f}ms + ⚙️ {result.api_processing_ms:5.1f}ms")
        else:
            print(f"{timestamp} ❌ {result.emergency_type.upper():12} | "
                  f"🚗 {result.vehicle_id:12} | "
                  f"⏱️  {result.total_latency_ms:6.1f}ms | "
                  f"📡 ERROR: {result.error_message[:40]}")

# ============================================================================
# 3. PRUEBAS CONCURRENTES MEJORADAS
# ============================================================================

    async def test_concurrent_emergencies(self, 
                                         num_emergencies: int = 50,
                                         max_concurrency: int = 20,
                                         emergency_types: List[str] = None) -> List[EmergencyTestResult]:
        """Ejecuta pruebas concurrentes de emergencias."""
        print(f"\n{'=' * 80}")
        print(f"🚨🚨🚨 PRUEBAS CONCURRENTES DE EMERGENCIA")
        print(f"{'=' * 80}")
        print(f"Cantidad: {num_emergencies} emergencias")
        print(f"Concurrencia máxima: {max_concurrency}")
        print(f"Tipos: {emergency_types or self.config['emergency_types']}")
        print(f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'=' * 80}\n")
        
        self.stats["concurrent_tests"] = num_emergencies
        self.stats["max_concurrent"] = max_concurrency
        
        # Crear lista de emergencias a probar
        emergencies_to_test = []
        for i in range(num_emergencies):
            vehicle = random.choice(self.test_suite.vehicles)
            emergency_type = random.choice(emergency_types or self.config["emergency_types"])
            emergencies_to_test.append({
                "id": f"CONC-{i+1:04d}",
                "vehicle": vehicle,
                "emergency_type": emergency_type
            })
        
        # Semaforo para control de concurrencia
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def test_with_semaphore(emergency_data: Dict) -> EmergencyTestResult:
            async with semaphore:
                return await self.test_single_emergency(
                    emergency_type=emergency_data["emergency_type"],
                    vehicle=emergency_data["vehicle"],
                    validate_response=True
                )
        
        # Ejecutar todas las pruebas
        start_time = time.perf_counter()
        tasks = [test_with_semaphore(emg) for emg in emergencies_to_test]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        valid_results = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                # Crear resultado de error
                error_result = EmergencyTestResult()
                error_result.test_id = f"ERROR-{i}"
                error_result.success = False
                error_result.error_message = str(r)[:100]
                error_result.start_time = datetime.now(timezone.utc)
                error_result.end_time = datetime.now(timezone.utc)
                valid_results.append(error_result)
                
                # Actualizar stats
                self.stats["total_tests"] += 1
                self.stats["failed_tests"] += 1
            else:
                valid_results.append(r)
        
        total_time = time.perf_counter() - start_time
        
        # Imprimir resumen concurrente
        self._print_concurrent_summary(valid_results, total_time)
        
        return valid_results
    
    def _print_concurrent_summary(self, results: List[EmergencyTestResult], total_time: float):
        """Imprime resumen de pruebas concurrentes."""
        successful = [r for r in results if r.success]
        sla_compliant = [r for r in successful if r.sla_compliant]
        
        latencies = [r.total_latency_ms for r in successful]
        processing_times = [r.api_processing_ms for r in successful]
        response_times = [r.api_response_time_ms for r in successful]
        
        print(f"\n{'=' * 80}")
        print(f"📊 RESUMEN DE PRUEBAS CONCURRENTES")
        print(f"{'=' * 80}")
        
        # Estadísticas generales
        success_rate = (len(successful) / len(results) * 100) if results else 0
        sla_rate = (len(sla_compliant) / len(successful) * 100) if successful else 0
        
        print(f"📈 ESTADÍSTICAS GENERALES:")
        print(f"   • Total pruebas: {len(results)}")
        print(f"   • Éxitos: {len(successful)} ({success_rate:.1f}%)")
        print(f"   • Fallos: {len(results) - len(successful)}")
        print(f"   • Cumplen SLA: {len(sla_compliant)} ({sla_rate:.1f}% de éxitos)")
        print(f"   • Tiempo total: {total_time:.2f} segundos")
        print(f"   • Throughput: {len(results)/total_time:.1f} emergencias/seg")
        
        # Estadísticas de latencia
        if latencies:
            print(f"\n⏱️  ESTADÍSTICAS DE LATENCIA (ms):")
            print(f"   • Mínimo: {min(latencies):.1f}")
            print(f"   • Máximo: {max(latencies):.1f}")
            print(f"   • Promedio: {statistics.mean(latencies):.1f}")
            print(f"   • Mediana: {statistics.median(latencies):.1f}")
            
            if len(latencies) >= 5:
                p95 = statistics.quantiles(latencies, n=100)[94]
                p99 = statistics.quantiles(latencies, n=100)[98]
                print(f"   • P95: {p95:.1f}")
                print(f"   • P99: {p99:.1f}")
        
        # Estadísticas por tipo de emergencia
        if self.stats["emergencies_by_type"]:
            print(f"\n🚨 ESTADÍSTICAS POR TIPO DE EMERGENCIA:")
            print(f"   {'TIPO':15} {'TOTAL':6} {'ÉXITOS':7} {'SLA OK':7} {'% ÉXITO':8} {'% SLA':7}")
            print(f"   {'-'*15} {'-'*6} {'-'*7} {'-'*7} {'-'*8} {'-'*7}")
            
            for etype, data in sorted(self.stats["emergencies_by_type"].items()):
                total = data["total"]
                success = data["success"]
                sla = data["sla_compliant"]
                
                success_pct = (success / total * 100) if total > 0 else 0
                sla_pct = (sla / success * 100) if success > 0 else 0
                
                print(f"   {etype:15} {total:6d} {success:7d} {sla:7d} "
                      f"{success_pct:7.1f}% {sla_pct:7.1f}%")
        
        # Evaluación de requisitos
        print(f"\n🎯 EVALUACIÓN DE REQUISITOS:")
        
        # Requisito: <2s para emergencias
        sla_requirement_met = sla_rate >= 95  # 95% deben cumplir SLA
        sla_status = "✅ CUMPLE" if sla_requirement_met else "❌ NO CUMPLE"
        print(f"   • SLA <2s: {sla_status} ({sla_rate:.1f}% cumplimiento)")
        
        # Requisito: alta tasa de éxito
        success_requirement_met = success_rate >= 98  # 98% éxito
        success_status = "✅ CUMPLE" if success_requirement_met else "❌ NO CUMPLE"
        print(f"   • Tasa éxito: {success_status} ({success_rate:.1f}% éxito)")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        if success_rate < 95:
            print(f"   • Investigar errores HTTP/timeout")
        
        if sla_rate < 95:
            print(f"   • Optimizar tiempos de respuesta para emergencias")
        
        if len(results) / total_time < 10:  # Menos de 10 emergencias/seg
            print(f"   • Considerar escalar capacidad de procesamiento")
        
        print(f"{'=' * 80}")

# ============================================================================
# 4. PRUEBAS DE CARGA GRADUAL Y ESTRÉS
# ============================================================================

    async def test_gradual_load(self, 
                               max_emergencies: int = 100,
                               steps: int = 5,
                               concurrency_per_step: int = 10):
        """Prueba de carga gradual para identificar límites."""
        print(f"\n{'=' * 80}")
        print(f"📈 PRUEBA DE CARGA GRADUAL DE EMERGENCIAS")
        print(f"{'=' * 80}")
        
        step_size = max_emergencies // steps
        all_results = []
        step_metrics = []
        
        for step in range(1, steps + 1):
            emergencies_in_step = step * step_size
            print(f"\n🎯 PASO {step}/{steps}: {emergencies_in_step} emergencias")
            print(f"{'-' * 60}")
            
            # Ejecutar pruebas concurrentes para este paso
            start_time = time.perf_counter()
            results = await self.test_concurrent_emergencies(
                num_emergencies=emergencies_in_step,
                max_concurrency=min(concurrency_per_step * step, 50),
                emergency_types=["panic_button", "accident", "medical"]
            )
            step_time = time.perf_counter() - start_time
            
            # Calcular métricas del paso
            successful = [r for r in results if r.success]
            sla_compliant = [r for r in successful if r.sla_compliant]
            
            success_rate = (len(successful) / len(results) * 100) if results else 0
            sla_rate = (len(sla_compliant) / len(successful) * 100) if successful else 0
            
            step_metrics.append({
                "step": step,
                "emergencies": emergencies_in_step,
                "concurrency": min(concurrency_per_step * step, 50),
                "success_rate": success_rate,
                "sla_rate": sla_rate,
                "time_seconds": step_time,
                "throughput": len(results) / step_time if step_time > 0 else 0,
                "avg_latency": statistics.mean([r.total_latency_ms for r in successful]) if successful else 0
            })
            
            all_results.extend(results)
            
            # Pausa entre pasos si no es el último
            if step < steps:
                print(f"\n⏸️  Pausa de 3 segundos antes del siguiente paso...")
                await asyncio.sleep(3)
        
        # Análisis de carga gradual
        self._analyze_gradual_load(step_metrics)
        
        return all_results
    
    def _analyze_gradual_load(self, step_metrics: List[Dict]):
        """Analiza resultados de carga gradual."""
        print(f"\n{'=' * 80}")
        print(f"📊 ANÁLISIS DE CARGA GRADUAL")
        print(f"{'=' * 80}")
        
        print(f"PASO | EMERGENCIAS | CONCURRENCIA | ÉXITO % | SLA % | THROUGHPUT | LATENCIA AVG")
        print(f"{'-' * 90}")
        
        for metrics in step_metrics:
            print(f"{metrics['step']:4d} | "
                  f"{metrics['emergencies']:11d} | "
                  f"{metrics['concurrency']:12d} | "
                  f"{metrics['success_rate']:7.1f}% | "
                  f"{metrics['sla_rate']:6.1f}% | "
                  f"{metrics['throughput']:10.1f}/s | "
                  f"{metrics['avg_latency']:11.1f} ms")
        
        print(f"{'-' * 90}")
        
        # Identificar punto de quiebre
        breaking_point = None
        for i in range(1, len(step_metrics)):
            current = step_metrics[i]
            previous = step_metrics[i-1]
            
            # Definir quiebre como caída >10% en éxito o SLA
            success_drop = previous["success_rate"] - current["success_rate"]
            sla_drop = previous["sla_rate"] - current["sla_rate"]
            
            if success_drop > 10 or sla_drop > 15:
                breaking_point = current["emergencies"]
                break
        
        if breaking_point:
            print(f"\n⚠️  PUNTO DE QUIEBRE DETECTADO: {breaking_point} emergencias")
            print(f"   El sistema comienza a degradarse después de este punto")
            
            # Recomendaciones específicas
            breaking_step = next(m for m in step_metrics if m["emergencies"] == breaking_point)
            print(f"\n💡 RECOMENDACIONES PARA {breaking_point} EMERGENCIAS:")
            print(f"   • Optimizar procesamiento de colas Redis")
            print(f"   • Aumentar workers de emergencia")
            print(f"   • Revisar configuración de PostgreSQL")
        else:
            print(f"\n✅ No se detectó punto de quiebre en el rango probado")
            print(f"   El sistema maneja bien la carga incremental")
        
        print(f"{'=' * 80}")

# ============================================================================
# 5. SUITE COMPLETA DE PRUEBAS
# ============================================================================

    async def run_comprehensive_suite(self):
        """Ejecuta suite completa de pruebas de emergencia."""
        print(f"{'=' * 80}")
        print(f"🔥 SUITE COMPLETA DE PRUEBAS DE EMERGENCIA CCS")
        print(f"{'=' * 80}")
        
        self.test_suite.start_time = datetime.now(timezone.utc)
        
        # 1. Verificar conexión con API
        print(f"\n🔍 VERIFICANDO CONEXIÓN CON API...")
        try:
            async with self.session.get(f"{self.config['api_url']}/health") as resp:
                if resp.status == 200:
                    health_data = await resp.json()
                    print(f"   ✅ API saludable: {health_data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ API no responde correctamente: HTTP {resp.status}")
                    return
        except Exception as e:
            print(f"   ❌ No se puede conectar a la API: {e}")
            return
        
        # 2. Pruebas individuales por tipo de vehículo
        print(f"\n🚗 PRUEBAS INDIVIDUALES POR TIPO DE VEHÍCULO")
        print(f"{'-' * 60}")
        
        test_cases = [
            {"type": "TRUCK", "emergency": "panic_button"},
            {"type": "TRUCK", "emergency": "accident"},
            {"type": "CAR", "emergency": "robbery"},
            {"type": "CAR", "emergency": "medical"},
            {"type": "MOTO", "emergency": "assault"},
            {"type": "MOTO", "emergency": "mechanical"}
        ]
        
        individual_results = []
        for test_case in test_cases:
            vehicle = next((v for v in self.test_suite.vehicles 
                          if v["type"] == test_case["type"]), None)
            
            if vehicle:
                result = await self.test_single_emergency(
                    emergency_type=test_case["emergency"],
                    vehicle=vehicle,
                    validate_response=True
                )
                individual_results.append(result)
                await asyncio.sleep(0.5)  # Pequeña pausa
        
        # 3. Prueba de emergencias concurrentes (carga media)
        print(f"\n⚡ PRUEBA DE EMERGENCIAS CONCURRENTES (carga media)")
        concurrent_results = await self.test_concurrent_emergencies(
            num_emergencies=30,
            max_concurrency=10,
            emergency_types=["panic_button", "accident", "medical"]
        )
        
        # 4. Prueba de carga gradual (si el sistema está estable)
        gradual_results = []
        successful_concurrent = sum(1 for r in concurrent_results if r.success)
        
        if successful_concurrent >= 25:  # Al menos 25/30 exitosas
            print(f"\n📈 PRUEBA DE CARGA GRADUAL (identificar límites)")
            gradual_results = await self.test_gradual_load(
                max_emergencies=80,
                steps=4,
                concurrency_per_step=5
            )
        else:
            print(f"\n⚠️  Omitting carga gradual - sistema no está lo suficientemente estable")
            print(f"   (solo {successful_concurrent}/30 emergencias concurrentes exitosas)")
        
        # 5. Prueba de estrés final (opcional)
        all_results = individual_results + concurrent_results + gradual_results
        
        # 6. Generar reporte final
        self.test_suite.end_time = datetime.now(timezone.utc)
        await self._generate_final_report(all_results)
        
        # 7. Resumen final
        self._print_final_summary(all_results)
    
    async def _generate_final_report(self, all_results: List[EmergencyTestResult]):
        """Genera reporte final detallado."""
        if not all_results:
            return
        
        # Crear directorio de salida
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Reporte detallado de todas las pruebas
        detailed_report = {
            "metadata": {
                "suite_id": self.test_suite.suite_id,
                "start_time": self.test_suite.start_time.isoformat(),
                "end_time": self.test_suite.end_time.isoformat(),
                "duration_seconds": (self.test_suite.end_time - self.test_suite.start_time).total_seconds(),
                "config": self.config,
                "total_tests": len(all_results)
            },
            "summary": self._calculate_summary_stats(all_results),
            "test_cases": [r.to_dict() for r in all_results],
            "recommendations": self._generate_recommendations(all_results)
        }
        
        detailed_file = output_dir / f"ccs_emergency_tests_detailed_{timestamp}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, indent=2, ensure_ascii=False)
        
        # 2. Reporte ejecutivo (resumido)
        executive_report = {
            "suite_id": self.test_suite.suite_id,
            "timestamp": timestamp,
            "overall_status": self._get_overall_status(all_results),
            "key_metrics": self._get_key_metrics(all_results),
            "sla_compliance": self._get_sla_compliance(all_results),
            "recommendations": self._generate_executive_recommendations(all_results)
        }
        
        executive_file = output_dir / f"ccs_emergency_tests_executive_{timestamp}.json"
        with open(executive_file, 'w', encoding='utf-8') as f:
            json.dump(executive_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reportes guardados en: {output_dir}/")
        print(f"   • {detailed_file.name}")
        print(f"   • {executive_file.name}")
    
    def _calculate_summary_stats(self, results: List[EmergencyTestResult]) -> Dict:
        """Calcula estadísticas resumen."""
        successful = [r for r in results if r.success]
        sla_compliant = [r for r in successful if r.sla_compliant]
        
        latencies = [r.total_latency_ms for r in successful]
        
        return {
            "total_tests": len(results),
            "successful_tests": len(successful),
            "failed_tests": len(results) - len(successful),
            "sla_compliant_tests": len(sla_compliant),
            "success_rate": (len(successful) / len(results) * 100) if results else 0,
            "sla_compliance_rate": (len(sla_compliant) / len(successful) * 100) if successful else 0,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "p95_latency_ms": statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 5 else 0,
            "p99_latency_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 5 else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0
        }
    
    def _get_overall_status(self, results: List[EmergencyTestResult]) -> str:
        """Determina estado general del sistema."""
        successful = [r for r in results if r.success]
        sla_compliant = [r for r in successful if r.sla_compliant]
        
        success_rate = (len(successful) / len(results) * 100) if results else 0
        sla_rate = (len(sla_compliant) / len(successful) * 100) if successful else 0
        
        if success_rate >= 95 and sla_rate >= 95:
            return "READY"
        elif success_rate >= 80 and sla_rate >= 80:
            return "LIMITED"
        elif success_rate >= 60:
            return "DEGRADED"
        else:
            return "CRITICAL"
    
    def _get_key_metrics(self, results: List[EmergencyTestResult]) -> Dict:
        """Obtiene métricas clave para reporte ejecutivo."""
        summary = self._calculate_summary_stats(results)
        
        return {
            "success_rate_percent": summary["success_rate"],
            "sla_compliance_percent": summary["sla_compliance_rate"],
            "avg_response_time_ms": summary["avg_latency_ms"],
            "p95_response_time_ms": summary["p95_latency_ms"],
            "max_response_time_ms": summary["max_latency_ms"],
            "tests_executed": summary["total_tests"],
            "sla_threshold_ms": self.config["sla_threshold_ms"]
        }
    
    def _get_sla_compliance(self, results: List[EmergencyTestResult]) -> Dict:
        """Obtiene análisis detallado de cumplimiento SLA."""
        successful = [r for r in results if r.success]
        latencies = [r.total_latency_ms for r in successful]
        
        if not latencies:
            return {}
        
        within_1s = sum(1 for l in latencies if l < 1000)
        within_2s = sum(1 for l in latencies if l < 2000)
        within_3s = sum(1 for l in latencies if l < 3000)
        over_3s = sum(1 for l in latencies if l >= 3000)
        
        return {
            "within_1s_percent": (within_1s / len(latencies) * 100),
            "within_2s_percent": (within_2s / len(latencies) * 100),
            "within_3s_percent": (within_3s / len(latencies) * 100),
            "over_3s_percent": (over_3s / len(latencies) * 100),
            "sla_violations": len(latencies) - within_2s
        }
    
    def _generate_recommendations(self, results: List[EmergencyTestResult]) -> List[str]:
        """Genera recomendaciones técnicas detalladas."""
        recommendations = []
        summary = self._calculate_summary_stats(results)
        
        if summary["success_rate"] < 95:
            recommendations.append("Investigar y corregir causas de fallos en emergencias")
        
        if summary["sla_compliance_rate"] < 95:
            recommendations.append("Optimizar tiempos de respuesta para procesamiento de emergencias")
        
        if summary["p95_latency_ms"] > 1500:
            recommendations.append("Revisar bottlenecks en procesamiento de streams de emergencia")
        
        if summary["max_latency_ms"] > 5000:
            recommendations.append("Implementar circuit breakers para emergencias que exceden tiempo máximo")
        
        return recommendations
    
    def _generate_executive_recommendations(self, results: List[EmergencyTestResult]) -> List[str]:
        """Genera recomendaciones ejecutivas."""
        status = self._get_overall_status(results)
        
        if status == "READY":
            return ["Sistema listo para producción", "Monitorear continuamente tiempos de respuesta"]
        elif status == "LIMITED":
            return ["Optimizar sistema antes de despliegue completo", "Realizar pruebas de carga adicionales"]
        elif status == "DEGRADED":
            return ["Requeridas mejoras significativas", "No recomendar despliegue en estado actual"]
        else:  # CRITICAL
            return ["Revisión arquitectónica necesaria", "No apto para producción"]
    
    def _print_final_summary(self, all_results: List[EmergencyTestResult]):
        """Imprime resumen final de todas las pruebas."""
        print(f"\n{'=' * 80}")
        print(f"📋 RESUMEN FINAL DE PRUEBAS DE EMERGENCIA")
        print(f"{'=' * 80}")
        
        summary = self._calculate_summary_stats(all_results)
        overall_status = self._get_overall_status(all_results)
        
        print(f"\n📊 ESTADÍSTICAS GENERALES:")
        print(f"   • Total pruebas ejecutadas: {summary['total_tests']}")
        print(f"   • Pruebas exitosas: {summary['successful_tests']} ({summary['success_rate']:.1f}%)")
        print(f"   • Pruebas fallidas: {summary['failed_tests']}")
        print(f"   • Cumplen SLA (<2s): {summary['sla_compliant_tests']} ({summary['sla_compliance_rate']:.1f}%)")
        
        print(f"\n⏱️  MÉTRICAS DE TIEMPO DE RESPUESTA (ms):")
        print(f"   • Promedio: {summary['avg_latency_ms']:.1f}")
        print(f"   • P95: {summary['p95_latency_ms']:.1f}")
        print(f"   • P99: {summary['p99_latency_ms']:.1f}")
        print(f"   • Mínimo: {summary['min_latency_ms']:.1f}")
        print(f"   • Máximo: {summary['max_latency_ms']:.1f}")
        
        print(f"\n🎯 EVALUACIÓN FINAL DEL SISTEMA:")
        print(f"   • Estado general: {overall_status}")
        
        if overall_status == "READY":
            print(f"   • ✅ SISTEMA LISTO PARA EMERGENCIAS REALES")
            print(f"      - Alta tasa de éxito ({summary['success_rate']:.1f}%)")
            print(f"      - Buen cumplimiento SLA ({summary['sla_compliance_rate']:.1f}%)")
            print(f"      - Tiempos de respuesta dentro de límites")
        elif overall_status == "LIMITED":
            print(f"   • ⚠️  SISTEMA FUNCIONAL CON LIMITACIONES")
            print(f"      - Tasa de éxito aceptable ({summary['success_rate']:.1f}%)")
            print(f"      - Cumplimiento SLA limitado ({summary['sla_compliance_rate']:.1f}%)")
            print(f"      - Requiere optimizaciones antes de producción completa")
        elif overall_status == "DEGRADED":
            print(f"   • ⚠️  SISTEMA DEGRADADO")
            print(f"      - Tasa de éxito baja ({summary['success_rate']:.1f}%)")
            print(f"      - Múltiples violaciones SLA")
            print(f"      - No recomendado para producción")
        else:
            print(f"   • ❌ SISTEMA NO PREPARADO PARA EMERGENCIAS")
            print(f"      - Fallas críticas detectadas")
            print(f"      - Tiempos de respuesta inaceptables")
            print(f"      - Requiere revisión arquitectónica")
        
        sla_compliance = self._get_sla_compliance(all_results)
        if sla_compliance:
            print(f"\n📈 DISTRIBUCIÓN DE TIEMPOS DE RESPUESTA:")
            print(f"   • <1 segundo: {sla_compliance['within_1s_percent']:.1f}%")
            print(f"   • <2 segundos: {sla_compliance['within_2s_percent']:.1f}%")
            print(f"   • <3 segundos: {sla_compliance['within_3s_percent']:.1f}%")
            print(f"   • >3 segundos: {sla_compliance['over_3s_percent']:.1f}%")
            print(f"   • Violaciones SLA: {sla_compliance['sla_violations']}")
        
        print(f"\n💡 RECOMENDACIONES ESTRATÉGICAS:")
        recommendations = self._generate_executive_recommendations(all_results)
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📁 Reportes detallados guardados en: {self.config['output_dir']}/")
        print(f"{'=' * 80}")

# ============================================================================
# 6. PUNTO DE ENTRADA PRINCIPAL
# ============================================================================

async def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='CCS Emergency Tester - Pruebas especializadas para emergencias',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s --single                    # Prueba individual de emergencia
  %(prog)s --concurrent 50 --workers 10 # 50 emergencias con 10 workers
  %(prog)s --gradual 100 --steps 5     # Carga gradual hasta 100 emergencias
  %(prog)s --full                      # Suite completa de pruebas
  %(prog)s --url http://api.ccs.com    # API remota
  %(prog)s --vehicle TRUCK-001         # Vehículo específico
  %(prog)s --type accident             # Tipo específico de emergencia
        """
    )
    
    parser.add_argument('--url', default=DEFAULT_CONFIG['api_url'],
                       help=f'URL de la API CCS (default: {DEFAULT_CONFIG["api_url"]})')
    
    parser.add_argument('--single', action='store_true',
                       help='Ejecutar prueba individual de emergencia')
    
    parser.add_argument('--vehicle', default=None,
                       help='ID del vehículo para prueba individual')
    
    parser.add_argument('--type', default=None,
                       choices=DEFAULT_CONFIG['emergency_types'],
                       help='Tipo de emergencia para prueba individual')
    
    parser.add_argument('--concurrent', type=int, metavar='N',
                       help='Ejecutar N emergencias concurrentes')
    
    parser.add_argument('--workers', type=int, default=DEFAULT_CONFIG['concurrent_workers'],
                       help=f'Número máximo de workers concurrentes (default: {DEFAULT_CONFIG["concurrent_workers"]})')
    
    parser.add_argument('--gradual', type=int, metavar='MAX',
                       help='Prueba de carga gradual hasta MAX emergencias')
    
    parser.add_argument('--steps', type=int, default=5,
                       help='Pasos para carga gradual (default: 5)')
    
    parser.add_argument('--full', action='store_true',
                       help='Ejecutar suite completa de pruebas')
    
    parser.add_argument('--output-dir', default=DEFAULT_CONFIG['output_dir'],
                       help=f'Directorio para reportes (default: {DEFAULT_CONFIG["output_dir"]})')
    
    parser.add_argument('--sla-threshold', type=int, default=DEFAULT_CONFIG['sla_threshold_ms'],
                       help=f'Umbral SLA en ms (default: {DEFAULT_CONFIG["sla_threshold_ms"]})')
    
    args = parser.parse_args()
    
    # Configuración personalizada
    config = DEFAULT_CONFIG.copy()
    config.update({
        "api_url": args.url.rstrip('/'),
        "concurrent_workers": args.workers,
        "output_dir": args.output_dir,
        "sla_threshold_ms": args.sla_threshold
    })
    
    # Crear tester
    tester = EmergencyTester(config)
    
    try:
        # Inicializar
        await tester.initialize()
        
        # Ejecutar pruebas según argumentos
        if args.full:
            await tester.run_comprehensive_suite()
        elif args.concurrent:
            await tester.test_concurrent_emergencies(
                num_emergencies=args.concurrent,
                max_concurrency=args.workers
            )
        elif args.gradual:
            await tester.test_gradual_load(
                max_emergencies=args.gradual,
                steps=args.steps,
                concurrency_per_step=args.workers // 2
            )
        else:
            # Prueba individual
            vehicle = None
            if args.vehicle:
                # Buscar vehículo en el pool
                vehicle = next((v for v in tester.test_suite.vehicles 
                              if v["id"] == args.vehicle), None)
            
            emergency_type = args.type or random.choice(config["emergency_types"])
            
            await tester.test_single_emergency(
                emergency_type=emergency_type,
                vehicle=vehicle,
                validate_response=True
            )
    
    except KeyboardInterrupt:
        print("\n\n🛑 Pruebas interrumpidas por usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.close()

if __name__ == "__main__":
    # Ejecutar: pip install aiohttp
    asyncio.run(main())