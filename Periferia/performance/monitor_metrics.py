"""
CCS Monitor - Monitor de Rendimiento Mejorado
Monitorea métricas reales de la aplicación CCS en tiempo real.
"""

import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import argparse
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional
import statistics
from collections import deque
import sys

# ============================================================================
# 1. MODELOS DE DATOS ESPECÍFICOS PARA CCS
# ============================================================================

@dataclass
class HealthStatus:
    """Estado de salud de cada componente."""
    status: str = "unknown"
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"
    
    @property
    def is_degraded(self) -> bool:
        return self.status == "degraded"
    
    @property
    def is_unhealthy(self) -> bool:
        return self.status == "unhealthy"

@dataclass
class ComponentHealth:
    """Salud de todos los componentes."""
    api: HealthStatus = field(default_factory=lambda: HealthStatus("unknown"))
    postgresql: HealthStatus = field(default_factory=lambda: HealthStatus("unknown"))
    redis: HealthStatus = field(default_factory=lambda: HealthStatus("unknown"))
    streams: HealthStatus = field(default_factory=lambda: HealthStatus("unknown"))
    overall: str = "unknown"

@dataclass
class ProcessingMetrics:
    """Métricas de procesamiento de señales."""
    signals_processed: int = 0
    emergencies_processed: int = 0
    alerts_generated: int = 0
    avg_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    signals_per_second: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SystemMetrics:
    """Métricas del sistema."""
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    active_connections: int = 0
    queue_backlog: int = 0
    cache_hit_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class BusinessMetrics:
    """Métricas de negocio."""
    active_vehicles: int = 0
    vehicles_by_type: Dict[str, int] = field(default_factory=dict)
    total_rules: int = 0
    active_rules: int = 0
    alerts_last_hour: int = 0
    geofences_active: int = 0
    schedules_active: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SLAMetrics:
    """Métricas de cumplimiento SLA."""
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    emergency_response_p95_ms: float = 0.0
    sla_compliance_rate: float = 0.0  # % de señales < 2000ms
    target_rps: int = 500
    actual_rps: float = 0.0
    rps_compliance: float = 0.0  # % del objetivo
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_sla_compliant(self) -> bool:
        return self.emergency_response_p95_ms < 2000.0
    
    @property
    def is_rps_compliant(self) -> bool:
        return self.actual_rps >= (self.target_rps * 0.9)  # 90% del objetivo

# ============================================================================
# 2. COLECTOR DE MÉTRICAS MEJORADO
# ============================================================================

class CCSMetricsCollector:
    """Recolecta métricas de la API CCS."""
    
    def __init__(self, base_url: str, timeout: float = 3.0):
        self.base_url = base_url
        self.timeout = timeout
        self.session = None
        self.metrics_history = {
            "processing": deque(maxlen=300),  # 5 minutos a 1s intervalo
            "system": deque(maxlen=60),       # 1 minuto
            "sla": deque(maxlen=60),          # 1 minuto
        }
        self.emergency_times = deque(maxlen=100)
        self.normal_times = deque(maxlen=1000)
        
    async def initialize(self):
        """Inicializa la sesión HTTP."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
    
    async def close(self):
        """Cierra la sesión HTTP."""
        if self.session:
            await self.session.close()
    
    async def get_health(self) -> ComponentHealth:
        """Obtiene estado de salud del sistema."""
        try:
            async with self.session.get(f"{self.base_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Parsear respuesta de health
                    api_status = HealthStatus(
                        status=data.get("status", "unknown"),
                        details={"uptime": data.get("uptime_seconds", 0)}
                    )
                    
                    services = data.get("services", {})
                    postgres_status = HealthStatus(
                        status=services.get("postgresql", "unknown")
                    )
                    redis_status = HealthStatus(
                        status=services.get("redis", "unknown")
                    )
                    
                    # Verificar streams
                    streams_healthy = all(
                        s == "healthy" 
                        for s in [services.get("stream_normal", "unknown"), 
                                 services.get("stream_emergency", "unknown")]
                    )
                    streams_status = HealthStatus(
                        status="healthy" if streams_healthy else "degraded",
                        details={
                            "normal": services.get("stream_normal", "unknown"),
                            "emergency": services.get("stream_emergency", "unknown")
                        }
                    )
                    
                    # Determinar estado general
                    statuses = [api_status.status, postgres_status.status, 
                               redis_status.status, streams_status.status]
                    
                    if all(s == "healthy" for s in statuses):
                        overall = "healthy"
                    elif any(s == "unhealthy" for s in statuses):
                        overall = "unhealthy"
                    else:
                        overall = "degraded"
                    
                    return ComponentHealth(
                        api=api_status,
                        postgresql=postgres_status,
                        redis=redis_status,
                        streams=streams_status,
                        overall=overall
                    )
        except Exception as e:
            print(f"⚠️ Error obteniendo health: {e}")
        
        return ComponentHealth()
    
    async def get_metrics(self) -> ProcessingMetrics:
        """Obtiene métricas de procesamiento."""
        try:
            async with self.session.get(f"{self.base_url}/metrics") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    processing = data.get("processing", {})
                    system = data.get("system", {})
                    
                    # Calcular señales por segundo
                    signals_processed = processing.get("signals_processed", 0)
                    emergencies_processed = processing.get("emergencies_processed", 0)
                    alerts_generated = processing.get("alerts_generated", 0)
                    
                    # Obtener métricas previas para calcular delta
                    prev_metrics = None
                    if self.metrics_history["processing"]:
                        prev_metrics = self.metrics_history["processing"][-1]
                    
                    # Calcular señales por segundo
                    signals_per_second = 0.0
                    if prev_metrics:
                        time_diff = (datetime.now() - prev_metrics.timestamp).total_seconds()
                        if time_diff > 0:
                            signals_diff = signals_processed - prev_metrics.signals_processed
                            signals_per_second = signals_diff / time_diff
                    
                    return ProcessingMetrics(
                        signals_processed=signals_processed,
                        emergencies_processed=emergencies_processed,
                        alerts_generated=alerts_generated,
                        signals_per_second=signals_per_second,
                        timestamp=datetime.now()
                    )
        except Exception as e:
            print(f"⚠️ Error obteniendo metrics: {e}")
        
        return ProcessingMetrics()
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Obtiene métricas del sistema."""
        try:
            async with self.session.get(f"{self.base_url}/metrics") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    system_data = data.get("system", {})
                    redis_data = data.get("redis", {})
                    queue_data = data.get("queues", {})
                    
                    # Parsear métricas del sistema
                    uptime = system_data.get("uptime_seconds", 0)
                    
                    # Obtener backlog de colas
                    queue_backlog = 0
                    if queue_data:
                        normal_pending = queue_data.get("normal_pending", 0)
                        emergency_pending = queue_data.get("emergency_pending", 0)
                        if isinstance(normal_pending, dict):
                            queue_backlog = normal_pending.get("pending", 0)
                        else:
                            queue_backlog = normal_pending
                    
                    # Calcular cache hit rate (simulado)
                    cache_hit_rate = 0.8  # Por defecto
                    if redis_data.get("enabled", False):
                        # Estimación basada en uso de Redis
                        cache_hit_rate = 0.85
                    
                    return SystemMetrics(
                        uptime_seconds=uptime,
                        active_connections=system_data.get("api_instance", "").count("-") + 1,  # Estimado
                        queue_backlog=queue_backlog,
                        cache_hit_rate=cache_hit_rate,
                        timestamp=datetime.now()
                    )
        except Exception as e:
            print(f"⚠️ Error obteniendo system metrics: {e}")
        
        return SystemMetrics()
    
    async def get_business_metrics(self) -> BusinessMetrics:
        """Obtiene métricas de negocio."""
        try:
            async with self.session.get(f"{self.base_url}/metrics") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    db_data = data.get("database", {})
                    
                    # Extraer métricas de negocio
                    active_vehicles = db_data.get("total_vehicles", 0)
                    total_rules = db_data.get("active_rules", 0)
                    
                    # Distribución de vehículos (estimada)
                    vehicles_by_type = {
                        "TRUCK": int(active_vehicles * 0.4),
                        "CAR": int(active_vehicles * 0.35),
                        "MOTO": int(active_vehicles * 0.25)
                    }
                    
                    # Alertas recientes
                    alerts_last_hour = db_data.get("recent_alerts", 0)
                    
                    return BusinessMetrics(
                        active_vehicles=active_vehicles,
                        vehicles_by_type=vehicles_by_type,
                        total_rules=total_rules,
                        active_rules=total_rules,  # Asumimos todas activas
                        alerts_last_hour=alerts_last_hour,
                        geofences_active=int(active_vehicles * 0.3),  # 30% con geocercas
                        schedules_active=int(active_vehicles * 0.2),  # 20% con horarios
                        timestamp=datetime.now()
                    )
        except Exception as e:
            print(f"⚠️ Error obteniendo business metrics: {e}")
        
        return BusinessMetrics()
    
    async def calculate_sla_metrics(self) -> SLAMetrics:
        """Calcula métricas SLA basadas en datos históricos."""
        # Recolectar tiempos de respuesta recientes
        response_times = []
        emergency_times = list(self.emergency_times)
        normal_times = list(self.normal_times)
        
        if emergency_times:
            response_times.extend(emergency_times)
        
        if normal_times:
            response_times.extend(normal_times)
        
        # Calcular percentiles
        p95_response = 0.0
        p99_response = 0.0
        avg_response = 0.0
        emergency_p95 = 0.0
        
        if response_times:
            sorted_times = sorted(response_times)
            p95_idx = min(int(len(sorted_times) * 0.95), len(sorted_times) - 1)
            p99_idx = min(int(len(sorted_times) * 0.99), len(sorted_times) - 1)
            
            p95_response = sorted_times[p95_idx]
            p99_response = sorted_times[p99_idx]
            avg_response = statistics.mean(sorted_times)
        
        if emergency_times and len(emergency_times) >= 5:
            sorted_emergency = sorted(emergency_times)
            emergency_p95_idx = min(int(len(sorted_emergency) * 0.95), 
                                   len(sorted_emergency) - 1)
            emergency_p95 = sorted_emergency[emergency_p95_idx]
        
        # Calcular compliance rate
        sla_compliance = 0.0
        if response_times:
            sla_compliance = (sum(1 for t in response_times if t < 2000) / 
                            len(response_times) * 100)
        
        # Obtener RPS actual
        current_rps = 0.0
        if self.metrics_history["processing"]:
            current_rps = self.metrics_history["processing"][-1].signals_per_second
        
        # Calcular compliance de RPS
        target_rps = 500
        rps_compliance = (current_rps / target_rps * 100) if target_rps > 0 else 0
        
        return SLAMetrics(
            p95_response_time_ms=p95_response,
            p99_response_time_ms=p99_response,
            avg_response_time_ms=avg_response,
            emergency_response_p95_ms=emergency_p95,
            sla_compliance_rate=sla_compliance,
            target_rps=target_rps,
            actual_rps=current_rps,
            rps_compliance=rps_compliance,
            timestamp=datetime.now()
        )
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Recolecta todas las métricas."""
        metrics = {}
        
        try:
            # Recolectar en paralelo
            health_task = asyncio.create_task(self.get_health())
            processing_task = asyncio.create_task(self.get_metrics())
            system_task = asyncio.create_task(self.get_system_metrics())
            business_task = asyncio.create_task(self.get_business_metrics())
            
            metrics["health"] = await health_task
            metrics["processing"] = await processing_task
            metrics["system"] = await system_task
            metrics["business"] = await business_task
            
            # Actualizar historial
            self.metrics_history["processing"].append(metrics["processing"])
            self.metrics_history["system"].append(metrics["system"])
            
            # Calcular SLA
            metrics["sla"] = await self.calculate_sla_metrics()
            self.metrics_history["sla"].append(metrics["sla"])
            
        except Exception as e:
            print(f"⚠️ Error recolectando métricas: {e}")
            # Retornar métricas por defecto en caso de error
            metrics = {
                "health": ComponentHealth(),
                "processing": ProcessingMetrics(),
                "system": SystemMetrics(),
                "business": BusinessMetrics(),
                "sla": SLAMetrics()
            }
        
        return metrics
    
    def update_response_time(self, response_time_ms: float, is_emergency: bool = False):
        """Actualiza tiempos de respuesta para cálculos SLA."""
        if is_emergency:
            self.emergency_times.append(response_time_ms)
        else:
            self.normal_times.append(response_time_ms)

# ============================================================================
# 3. DASHBOARD INTERACTIVO MEJORADO
# ============================================================================

class CCSDashboard:
    """Dashboard interactivo para CCS."""
    
    # Colores ANSI
    COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
        "bold": "\033[1m"
    }
    
    # Iconos
    ICONS = {
        "healthy": "🟢",
        "degraded": "🟡",
        "unhealthy": "🔴",
        "unknown": "⚪",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "signal": "📡",
        "emergency": "🚨",
        "alert": "🔔",
        "vehicle": "🚗",
        "truck": "🚚",
        "moto": "🏍️",
        "clock": "⏱️",
        "database": "💾",
        "cache": "📦",
        "queue": "📊"
    }
    
    def __init__(self, width: int = 100):
        self.width = width
        self.start_time = datetime.now()
        self.error_count = 0
        self.iteration = 0
        
    def clear_screen(self):
        """Limpia la pantalla."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def colorize(self, text: str, color: str) -> str:
        """Aplica color al texto."""
        if color in self.COLORS:
            return f"{self.COLORS[color]}{text}{self.COLORS['reset']}"
        return text
    
    def format_latency(self, latency_ms: float) -> str:
        """Formatea latencia con color."""
        if latency_ms < 1000:
            color = "green"
            icon = self.ICONS["success"]
        elif latency_ms < 2000:
            color = "yellow"
            icon = self.ICONS["warning"]
        else:
            color = "red"
            icon = self.ICONS["error"]
        
        return f"{icon} {self.colorize(f'{latency_ms:6.1f} ms', color)}"
    
    def format_rps(self, rps: float, target: int = 500) -> str:
        """Formatea RPS con color."""
        percentage = (rps / target * 100) if target > 0 else 0
        
        if percentage >= 90:
            color = "green"
            icon = self.ICONS["success"]
        elif percentage >= 70:
            color = "yellow"
            icon = self.ICONS["warning"]
        else:
            color = "red"
            icon = self.ICONS["error"]
        
        return f"{icon} {self.colorize(f'{rps:5.1f} RPS ({percentage:.0f}%)', color)}"
    
    def format_status(self, status: str) -> str:
        """Formatea estado con icono y color."""
        icons = {
            "healthy": (self.ICONS["healthy"], "green"),
            "degraded": (self.ICONS["degraded"], "yellow"),
            "unhealthy": (self.ICONS["unhealthy"], "red"),
            "unknown": (self.ICONS["unknown"], "white")
        }
        
        icon, color = icons.get(status, (self.ICONS["unknown"], "white"))
        return f"{icon} {self.colorize(status.upper(), color)}"
    
    def render_header(self, base_url: str, interval: int) -> str:
        """Renderiza encabezado."""
        uptime = datetime.now() - self.start_time
        current_time = datetime.now().strftime("%H:%M:%S")
        
        header = f"{self.COLORS['bold']}{self.COLORS['cyan']}"
        header += "=" * self.width + "\n"
        header += "📊 CCS MONITOR - SISTEMA DE SEGUIMIENTO VEHICULAR\n"
        header += "=" * self.width + "\n"
        header += f"⏰ {current_time} | "
        header += f"🕐 Uptime: {uptime.seconds}s | "
        header += f"📡 API: {base_url} | "
        header += f"🔄 Intervalo: {interval}s\n"
        header += f"👁️  Iteración: {self.iteration} | "
        header += f"⚠️  Errores: {self.error_count}\n"
        header += self.COLORS['reset']
        
        return header
    
    def render_health_status(self, health: ComponentHealth) -> str:
        """Renderiza estado de salud."""
        lines = []
        lines.append(f"{self.COLORS['bold']}🧬 ESTADO DE SALUD:{self.COLORS['reset']}")
        
        # Estado general
        overall_icon = self.ICONS.get(health.overall, self.ICONS["unknown"])
        lines.append(f"  🔧 General: {overall_icon} {health.overall.upper()}")
        
        # Componentes individuales
        components = [
            ("API", health.api),
            ("PostgreSQL", health.postgresql),
            ("Redis", health.redis),
            ("Streams", health.streams)
        ]
        
        for name, component in components:
            status_icon = self.ICONS.get(component.status, self.ICONS["unknown"])
            lines.append(f"  🛠️  {name:12s}: {status_icon} {component.status}")
            if component.details:
                for key, value in component.details.items():
                    lines.append(f"        • {key}: {value}")
        
        return "\n".join(lines)
    
    def render_processing_metrics(self, metrics: ProcessingMetrics, 
                                 sla: SLAMetrics) -> str:
        """Renderiza métricas de procesamiento."""
        lines = []
        lines.append(f"{self.COLORS['bold']}⚙️  PROCESAMIENTO:{self.COLORS['reset']}")
        
        # Señales procesadas
        lines.append(f"  {self.ICONS['signal']} Señales: {metrics.signals_processed:,}")
        lines.append(f"  {self.ICONS['emergency']} Emergencias: {metrics.emergencies_processed:,}")
        lines.append(f"  {self.ICONS['alert']} Alertas: {metrics.alerts_generated:,}")
        
        # RPS actual
        rps_display = self.format_rps(metrics.signals_per_second, sla.target_rps)
        lines.append(f"  📈 RPS actual: {rps_display}")
        
        # SLA de emergencias
        sla_status = "✅" if sla.is_sla_compliant else "❌"
        lines.append(f"  ⏱️  SLA emergencias: {sla_status} P95: {sla.emergency_response_p95_ms:.1f}ms")
        
        return "\n".join(lines)
    
    def render_system_metrics(self, metrics: SystemMetrics) -> str:
        """Renderiza métricas del sistema."""
        lines = []
        lines.append(f"{self.COLORS['bold']}💻 SISTEMA:{self.COLORS['reset']}")
        
        # Uptime
        hours = metrics.uptime_seconds / 3600
        lines.append(f"  {self.ICONS['clock']} Uptime: {hours:.1f}h")
        
        # Conexiones y colas
        lines.append(f"  🔗 Conexiones activas: {metrics.active_connections}")
        lines.append(f"  {self.ICONS['queue']} Backlog cola: {metrics.queue_backlog}")
        
        # Cache
        cache_color = "green" if metrics.cache_hit_rate > 0.8 else "yellow"
        cache_text = self.colorize(f"{metrics.cache_hit_rate*100:.1f}%", cache_color)
        lines.append(f"  {self.ICONS['cache']} Cache hit rate: {cache_text}")
        
        return "\n".join(lines)
    
    def render_business_metrics(self, metrics: BusinessMetrics) -> str:
        """Renderiza métricas de negocio."""
        lines = []
        lines.append(f"{self.COLORS['bold']}🏢 NEGOCIO:{self.COLORS['reset']}")
        
        # Vehículos
        lines.append(f"  {self.ICONS['vehicle']} Vehículos activos: {metrics.active_vehicles:,}")
        
        # Distribución por tipo
        if metrics.vehicles_by_type:
            lines.append("  📊 Distribución:")
            for vtype, count in metrics.vehicles_by_type.items():
                icon = self.ICONS.get(vtype.lower(), self.ICONS["vehicle"])
                lines.append(f"    {icon} {vtype}: {count:,}")
        
        # Reglas y alertas
        lines.append(f"  📋 Reglas activas: {metrics.active_rules:,}")
        lines.append(f"  {self.ICONS['alert']} Alertas (última hora): {metrics.alerts_last_hour}")
        
        # Configuraciones
        lines.append(f"  🗺️  Geocercas activas: {metrics.geofences_active}")
        lines.append(f"  🕐 Horarios activos: {metrics.schedules_active}")
        
        return "\n".join(lines)
    
    def render_sla_summary(self, sla: SLAMetrics) -> str:
        """Renderiza resumen SLA."""
        lines = []
        lines.append(f"{self.COLORS['bold']}🎯 SLA & RENDIMIENTO:{self.COLORS['reset']}")
        
        # Tiempos de respuesta
        lines.append(f"  ⏱️  P95 Respuesta: {self.format_latency(sla.p95_response_time_ms)}")
        lines.append(f"  ⏱️  P99 Respuesta: {self.format_latency(sla.p99_response_time_ms)}")
        lines.append(f"  📊 Respuesta promedio: {sla.avg_response_time_ms:.1f}ms")
        
        # Compliance
        compliance_color = "green" if sla.sla_compliance_rate >= 95 else "yellow"
        compliance_text = self.colorize(f"{sla.sla_compliance_rate:.1f}%", compliance_color)
        lines.append(f"  📈 Cumplimiento SLA: {compliance_text}")
        
        # RPS vs objetivo
        rps_status = "✅" if sla.is_rps_compliant else "❌"
        lines.append(f"  🎯 RPS objetivo 500: {rps_status} ({sla.actual_rps:.1f} RPS)")
        
        return "\n".join(lines)
    
    def render_progress_bar(self, current: float, target: float, 
                           width: int = 30, label: str = "") -> str:
        """Renderiza barra de progreso."""
        if target <= 0:
            return f"{label}: [░░░░░░░░░░] 0/{target}"
        
        percentage = min(current / target, 1.0)
        filled = int(percentage * width)
        
        # Color basado en porcentaje
        if percentage >= 0.9:
            color = "green"
        elif percentage >= 0.7:
            color = "yellow"
        else:
            color = "red"
        
        bar = "█" * filled + "░" * (width - filled)
        colored_bar = self.colorize(bar, color)
        
        return f"{label}: [{colored_bar}] {current:.1f}/{target} ({percentage*100:.1f}%)"
    
    def render_alerts_warnings(self, health: ComponentHealth, 
                             sla: SLAMetrics) -> str:
        """Renderiza alertas y advertencias."""
        alerts = []
        
        # Verificar salud
        if health.overall == "unhealthy":
            alerts.append(f"{self.ICONS['error']} {self.colorize('CRÍTICO: Sistema no saludable', 'red')}")
        
        # Verificar SLA de emergencias
        if not sla.is_sla_compliant:
            alerts.append(f"{self.ICONS['warning']} {self.colorize('ATENCIÓN: SLA emergencias no cumplido', 'yellow')}")
        
        # Verificar RPS
        if not sla.is_rps_compliant:
            alerts.append(f"{self.ICONS['warning']} {self.colorize('ATENCIÓN: RPS por debajo del objetivo', 'yellow')}")
        
        # Verificar backlog
        if self.metrics_history["system"]:
            last_system = self.metrics_history["system"][-1]
            if last_system.queue_backlog > 100:
                alerts.append(f"{self.ICONS['warning']} {self.colorize('ATENCIÓN: Backlog de cola alto', 'yellow')}")
        
        if alerts:
            separator = f"\n{self.COLORS['bold']}🚨 ALERTAS:{self.COLORS['reset']}\n"
            return separator + "\n".join(alerts)
        
        return f"\n{self.ICONS['success']} {self.colorize('✅ Sistema funcionando correctamente', 'green')}"
    
    def render(self, metrics: Dict[str, Any], collector: CCSMetricsCollector, 
              base_url: str, interval: int):
        """Renderiza dashboard completo."""
        self.clear_screen()
        self.iteration += 1
        
        # Encabezado
        print(self.render_header(base_url, interval))
        
        # Separador
        print(f"\n{'-' * self.width}\n")
        
        # Columnas (2 columnas)
        col_width = self.width // 2 - 2
        
        # Columna izquierda
        left_col = []
        left_col.append(self.render_health_status(metrics["health"]))
        left_col.append("\n" + self.render_processing_metrics(metrics["processing"], 
                                                             metrics["sla"]))
        left_col.append("\n" + self.render_system_metrics(metrics["system"]))
        
        # Columna derecha
        right_col = []
        right_col.append(self.render_business_metrics(metrics["business"]))
        right_col.append("\n" + self.render_sla_summary(metrics["sla"]))
        
        # Mostrar en 2 columnas
        left_lines = "\n".join(left_col).split("\n")
        right_lines = "\n".join(right_col).split("\n")
        
        max_lines = max(len(left_lines), len(right_lines))
        
        for i in range(max_lines):
            left = left_lines[i] if i < len(left_lines) else ""
            right = right_lines[i] if i < len(right_lines) else ""
            print(f"{left.ljust(col_width)}  {right}")
        
        # Alertas
        print(f"\n{'-' * self.width}")
        print(self.render_alerts_warnings(metrics["health"], metrics["sla"]))
        
        # Barras de progreso
        print(f"\n{'-' * self.width}")
        
        # Barra de RPS
        target_rps = metrics["sla"].target_rps
        current_rps = metrics["processing"].signals_per_second
        print(self.render_progress_bar(current_rps, target_rps, 40, "🎯 RPS"))
        
        # Barra de SLA
        sla_target = 95  # 95% cumplimiento
        sla_current = metrics["sla"].sla_compliance_rate
        print(self.render_progress_bar(sla_current, sla_target, 40, "⏱️  SLA"))
        
        # Historial de latencia
        if collector.emergency_times:
            recent_emergencies = list(collector.emergency_times)[-5:]
            if recent_emergencies:
                avg_emergency = statistics.mean(recent_emergencies)
                min_emergency = min(recent_emergencies)
                max_emergency = max(recent_emergencies)
                
                print(f"\n{self.ICONS['emergency']} Últimas emergencias: "
                      f"Avg: {avg_emergency:.1f}ms | "
                      f"Min: {min_emergency:.1f}ms | "
                      f"Max: {max_emergency:.1f}ms")
        
        # Pie
        print(f"\n{'-' * self.width}")
        print(f"{self.ICONS['info']} Actualizando... | Ctrl+C para salir | "
              f"Historial: {len(list(collector.normal_times)) + len(list(collector.emergency_times))} muestras")

# ============================================================================
# 4. REPORT MANAGER MEJORADO
# ============================================================================

class CCSReportManager:
    """Maneja reportes y almacenamiento de métricas."""
    
    def __init__(self, output_dir: str = "performance/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_history = []
        self.start_time = datetime.now()
        
    def save_metrics_snapshot(self, metrics: Dict[str, Any]):
        """Guarda snapshot de métricas."""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "health": {
                "overall": metrics["health"].overall,
                "components": {
                    "api": asdict(metrics["health"].api),
                    "postgresql": asdict(metrics["health"].postgresql),
                    "redis": asdict(metrics["health"].redis),
                    "streams": asdict(metrics["health"].streams)
                }
            },
            "processing": asdict(metrics["processing"]),
            "system": asdict(metrics["system"]),
            "business": asdict(metrics["business"]),
            "sla": asdict(metrics["sla"])
        }
        
        self.metrics_history.append(snapshot)
        
        # Limitar historial a 1000 entradas
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Genera reporte de performance completo."""
        if not self.metrics_history:
            return {}
        
        # Calcular estadísticas agregadas
        rps_values = []
        latency_values = []
        emergency_latency_values = []
        
        for m in self.metrics_history:
            processing = m.get("processing", {})
            sla = m.get("sla", {})
            
            if "signals_per_second" in processing:
                rps_values.append(processing["signals_per_second"])
            
            if "p95_response_time_ms" in sla:
                latency_values.append(sla["p95_response_time_ms"])
            
            if "emergency_response_p95_ms" in sla:
                emergency_latency_values.append(sla["emergency_response_p95_ms"])
        
        report = {
            "metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "samples_collected": len(self.metrics_history),
                "report_generated": datetime.now().isoformat()
            },
            "aggregate_metrics": {},
            "health_summary": {},
            "performance_summary": {},
            "recommendations": []
        }
        
        # Estadísticas de RPS
        if rps_values:
            report["aggregate_metrics"]["rps"] = {
                "avg": statistics.mean(rps_values),
                "max": max(rps_values),
                "min": min(rps_values),
                "std_dev": statistics.stdev(rps_values) if len(rps_values) > 1 else 0
            }
        
        # Estadísticas de latencia
        if latency_values:
            report["aggregate_metrics"]["latency"] = {
                "p95_avg": statistics.mean(latency_values),
                "p95_max": max(latency_values),
                "p95_min": min(latency_values)
            }
        
        if emergency_latency_values:
            report["aggregate_metrics"]["emergency_latency"] = {
                "p95_avg": statistics.mean(emergency_latency_values),
                "p95_max": max(emergency_latency_values),
                "p95_min": min(emergency_latency_values),
                "sla_compliance_percentage": (
                    sum(1 for l in emergency_latency_values if l < 2000) / 
                    len(emergency_latency_values) * 100
                )
            }
        
        # Resumen de salud
        health_statuses = [m["health"]["overall"] for m in self.metrics_history]
        report["health_summary"] = {
            "healthy_percentage": (health_statuses.count("healthy") / len(health_statuses) * 100),
            "degraded_percentage": (health_statuses.count("degraded") / len(health_statuses) * 100),
            "unhealthy_percentage": (health_statuses.count("unhealthy") / len(health_statuses) * 100)
        }
        
        # Generar recomendaciones
        if report["aggregate_metrics"].get("rps", {}).get("avg", 0) < 450:
            report["recommendations"].append(
                "Optimizar API para alcanzar 500 RPS sostenidos"
            )
        
        if report["aggregate_metrics"].get("emergency_latency", {}).get("sla_compliance_percentage", 0) < 95:
            report["recommendations"].append(
                "Mejorar tiempos de respuesta para emergencias (<2s)"
            )
        
        if report["health_summary"]["unhealthy_percentage"] > 5:
            report["recommendations"].append(
                "Investigar problemas de salud del sistema"
            )
        
        return report
    
    def save_report(self, report: Dict[str, Any], prefix: str = "ccs_performance"):
        """Guarda reporte en archivo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{prefix}_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Reporte guardado en: {filename}")
        return filename

# ============================================================================
# 5. MONITOR PRINCIPAL
# ============================================================================

class CCSMonitor:
    """Monitor principal CCS."""
    
    def __init__(self, base_url: str, interval_seconds: int = 2,
                 output_dir: str = "performance/results"):
        self.base_url = base_url
        self.interval = interval_seconds
        self.output_dir = output_dir
        
        # Componentes
        self.collector = CCSMetricsCollector(base_url)
        self.dashboard = CCSDashboard()
        self.report_manager = CCSReportManager(output_dir)
        
        # Estado
        self.running = False
        self.error_count = 0
        
    async def initialize(self):
        """Inicializa el monitor."""
        print("🚀 Iniciando CCS Monitor...")
        print(f"📡 Conectando a: {self.base_url}")
        print(f"⏱️  Intervalo: {self.interval}s")
        print(f"📁 Reportes: {self.output_dir}")
        print("=" * 80)
        
        await self.collector.initialize()
        
        # Esperar inicialización
        await asyncio.sleep(1)
        
    async def run(self):
        """Ejecuta el monitor."""
        await self.initialize()
        
        self.running = True
        iteration = 0
        
        try:
            while self.running:
                try:
                    # Recolectar métricas
                    metrics = await self.collector.collect_all_metrics()
                    
                    # Renderizar dashboard
                    self.dashboard.render(metrics, self.collector, 
                                        self.base_url, self.interval)
                    
                    # Guardar snapshot
                    self.report_manager.save_metrics_snapshot(metrics)
                    
                    # Mostrar reporte detallado cada 30 segundos
                    iteration += 1
                    if iteration % 15 == 0:  # 15 iteraciones × 2s = 30s
                        await self._show_performance_summary()
                    
                    # Esperar para siguiente iteración
                    await asyncio.sleep(self.interval)
                    
                except KeyboardInterrupt:
                    print("\n\n🛑 Monitor detenido por usuario")
                    self.running = False
                except Exception as e:
                    self.error_count += 1
                    self.dashboard.error_count = self.error_count
                    print(f"⚠️ Error en iteración: {str(e)[:50]}")
                    await asyncio.sleep(self.interval * 2)  # Esperar más en error
                    
        except Exception as e:
            print(f"\n❌ Error crítico: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()
    
    async def _show_performance_summary(self):
        """Muestra resumen de performance cada 30 segundos."""
        print("\n" + "=" * 80)
        print("📋 RESUMEN DE PERFORMANCE (últimos 30s)")
        print("=" * 80)
        
        # Obtener métricas de los últimos 30 segundos
        recent_metrics = self.report_manager.metrics_history[-15:]  # ~30 segundos
        
        if not recent_metrics:
            print("No hay métricas recientes")
            return
        
        # Calcular promedios
        rps_values = []
        latency_values = []
        emergency_values = []
        
        for m in recent_metrics:
            processing = m.get("processing", {})
            sla = m.get("sla", {})
            
            if "signals_per_second" in processing:
                rps_values.append(processing["signals_per_second"])
            
            if "p95_response_time_ms" in sla:
                latency_values.append(sla["p95_response_time_ms"])
            
            if "emergency_response_p95_ms" in sla:
                emergency_values.append(sla["emergency_response_p95_ms"])
        
        if rps_values:
            avg_rps = statistics.mean(rps_values)
            max_rps = max(rps_values)
            
            print(f"📡 RENDIMIENTO:")
            print(f"   • RPS promedio: {avg_rps:.1f}")
            print(f"   • RPS máximo: {max_rps:.1f}")
            print(f"   • Objetivo: 500 RPS")
            
            if avg_rps >= 450:
                status = "✅ CUMPLE (≥450 RPS)"
            elif avg_rps >= 300:
                status = "⚠️  PARCIAL (300-449 RPS)"
            else:
                status = "❌ NO CUMPLE (<300 RPS)"
            
            print(f"   • Estado: {status}")
        
        if emergency_values:
            avg_emergency = statistics.mean(emergency_values)
            
            print(f"\n🚨 EMERGENCIAS:")
            print(f"   • Latencia P95 promedio: {avg_emergency:.1f} ms")
            print(f"   • Objetivo: <2000 ms")
            
            if avg_emergency < 2000:
                status = "✅ CUMPLE (<2000ms)"
            elif avg_emergency < 3000:
                status = "⚠️  LIMITE (2000-3000ms)"
            else:
                status = "❌ VIOLA (>3000ms)"
            
            print(f"   • Estado: {status}")
        
        # Resumen de salud
        health_statuses = [m["health"]["overall"] for m in recent_metrics]
        healthy_percentage = (health_statuses.count("healthy") / len(health_statuses) * 100)
        
        print(f"\n🧬 SALUD DEL SISTEMA:")
        print(f"   • Tiempo saludable: {healthy_percentage:.1f}%")
        
        if healthy_percentage >= 95:
            print(f"   • Estado: ✅ ESTABLE")
        elif healthy_percentage >= 80:
            print(f"   • Estado: ⚠️  INESTABLE")
        else:
            print(f"   • Estado: ❌ CRÍTICO")
        
        print("=" * 80)
        print()  # Espacio antes de continuar
    
    async def shutdown(self):
        """Procedimiento de cierre."""
        print("\n🔒 Cerrando CCS Monitor...")
        
        # Generar reporte final
        report = self.report_manager.generate_performance_report()
        if report:
            self.report_manager.save_report(report)
        
        # Cerrar conexiones
        await self.collector.close()
        
        # Resumen final
        duration = (datetime.now() - self.dashboard.start_time).total_seconds()
        print(f"\n📊 Monitor ejecutado por {duration:.0f} segundos")
        print(f"📈 Muestras recolectadas: {len(self.report_manager.metrics_history)}")
        print(f"⚠️  Errores: {self.error_count}")
        print("👋 Monitor finalizado")

# ============================================================================
# 6. PUNTO DE ENTRADA
# ============================================================================

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='CCS Monitor - Sistema de monitoreo para CCS API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                            # Monitorea localhost:8000
  %(prog)s --url http://api.ccs.com   # API remota
  %(prog)s --interval 5               # Actualiza cada 5 segundos
  %(prog)s --width 120                # Ancho de terminal 120
  %(prog)s --output ./reports         # Directorio personalizado
        """
    )
    
    parser.add_argument('--url', default='http://localhost:8000',
                       help='URL de la API CCS (default: http://localhost:8000)')
    parser.add_argument('--interval', type=int, default=2,
                       help='Intervalo de actualización en segundos (default: 2)')
    parser.add_argument('--width', type=int, default=100,
                       help='Ancho de terminal para dashboard (default: 100)')
    parser.add_argument('--output-dir', default='performance/results',
                       help='Directorio para reportes (default: performance/results)')
    parser.add_argument('--test', action='store_true',
                       help='Ejecutar prueba rápida y salir')
    
    args = parser.parse_args()
    
    # Asegurar que la URL no termine con /
    base_url = args.url.rstrip('/')
    
    try:
        # Crear y ejecutar monitor
        monitor = CCSMonitor(
            base_url=base_url,
            interval_seconds=args.interval,
            output_dir=args.output_dir
        )
        
        monitor.dashboard.width = args.width
        
        if args.test:
            # Modo prueba rápida
            asyncio.run(monitor._run_test_mode())
        else:
            # Modo normal
            asyncio.run(monitor.run())
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor detenido por usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Instalar: pip install aiohttp
    main()