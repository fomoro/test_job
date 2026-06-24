# 03 - Estrategia de Work Items y Configuración de Tableros

## 1. Objetivo práctico

Establecer la configuración inmutable de los tableros (Boards) para los equipos de Desarrollo y Soporte dentro del ecosistema Azure DevOps. Este documento define las columnas, estados, límites de trabajo en progreso (WIP), jerarquía de Work Items y las reglas estrictas de transición (Definition of Ready / Definition of Done).

---

## 2. Regla de gobierno visual

El modelo opera exclusivamente con dos tableros independientes para separar la naturaleza del trabajo planificado del trabajo reactivo/operativo:

- **Board Desarrollo:** Gestiona la construcción de incrementos planificados.
- **Board Soporte:** Gestiona el flujo continuo de incidentes y requerimientos operativos.

**Restricción absoluta:** No se crea un "Board QA". El aseguramiento de calidad es una fase obligatoria dentro del flujo de ambos tableros, no un silo aislado.

---

## 3. Configuración del Board de Desarrollo

**Ruta de administración:**
`Boards ──> Boards ──> Team Desarrollo ──> Board settings ──> Columns`

### 3.1 Columnas y mapeo de estados

La secuencia lógica de construcción sigue este estándar:

1. **Proposed (Estado: Proposed):** Historia creada o pendiente de refinamiento técnico.
2. **Active (Estado: Active | WIP: 5):** Desarrollo técnico en ejecución.
3. **Code Review (Estado: Active | WIP: 5):** Pull Request creado, código subido y pendiente de revisión por el Líder Técnico.
4. **Ready for QA (Estado: Active | WIP: 5):** Pull Request aprobado e integrado. El incremento está listo para certificación.
5. **In QA (Estado: Active | WIP: 5):** QA ejecuta validación funcional, escenarios BDD y pruebas de regresión.
6. **Resolved (Estado: Resolved):** QA certificó el incremento de forma exitosa.
7. **Closed (Estado: Closed):** Historia cerrada formalmente con trazabilidad y evidencia adjunta.

---

## 4. Configuración del Board de Soporte

**Ruta de administración:**
`Boards ──> Boards ──> Team Soporte ──> Board settings ──> Columns`

### 4.1 Columnas y mapeo de estados

La secuencia lógica de atención ITSM sigue este estándar:

1. **Proposed (Estado: Proposed):** Caso o incidente reportado con información base.
2. **Triage (Estado: Active | WIP: 5):** Clasificación del impacto, prioridad, severidad y ambiente afectado.
3. **Analysis (Estado: Active | WIP: 5):** Diagnóstico inicial, lectura de logs y definición de ruta de atención.
4. **Active (Estado: Active | WIP: 5):** Ejecución de la corrección operativa, ajuste de datos o escalamiento.
5. **Ready for QA (Estado: Active | WIP: 5):** Solución operativa terminada y lista para validación cruzada.
6. **In QA (Estado: Active | WIP: 5):** Validación por parte del equipo funcional o de calidad.
7. **Resolved (Estado: Resolved):** Solución confirmada como exitosa en el entorno de prueba/operativo.
8. **Waiting Release (Estado: Resolved | WIP: 5):** Cambio aprobado y encolado para promoción a entorno superior o productivo.
9. **Closed (Estado: Closed):** Caso finalizado con cierre de ticket y evidencia de despliegue.

---

## 5. Arquitectura de Work Items (Tipología CMMI)

Se debe respetar la tipología nativa del marco CMMI para garantizar la generación correcta de métricas.

### 5.1 Jerarquía de Desarrollo
- **Feature:** Agrupador funcional mayor. Representa una capacidad entregable del producto.
- **Requirement:** Historia de Usuario implementable. Unidad de valor de negocio.
- **Task:** Actividad de coordinación técnica, revisión o tarea de certificación QA.
- **Bug:** Defecto de código detectado en etapas tempranas (antes del despliegue productivo).

### 5.2 Jerarquía de Soporte
- **Issue:** Incidente estándar, solicitud de acceso o caso operativo de rutina.
- **Change Request:** Solicitud formal que impacta arquitectura, infraestructura o funcionalidad existente.
- **Requirement (Operativo):** Necesidad técnica de soporte que requiere esfuerzo de implementación.
- **Bug (Productivo):** Defecto de código que logró evadir los filtros y se manifestó en producción.
- **Release Request (Tag o CR):** Solicitud controlada para autorizar una liberación de ambiente.


### 5.3 Criterios de clasificación Desarrollo vs Soporte

La clasificación no depende de quién solicita el trabajo ni de quién lo atiende. Depende de la naturaleza de la demanda.

| Criterio | Board Desarrollo | Board Soporte |
|---|---|---|
| Naturaleza | Trabajo planificado, evolutivo o de construcción de producto. | Trabajo reactivo, operativo, de diagnóstico, estabilización o corrección productiva. |
| Tipo común | Feature, Requirement, Task, Bug de ciclo temprano. | Issue, Bug Productivo, Change Request, Requirement Operativo, Release Request. |
| Propósito | Crear, cambiar o mejorar una capacidad del producto. | Mantener, restablecer o asegurar la operación actual. |
| Ritmo | Iteración / Sprint / planificación. | Flujo continuo / Kanban / atención operativa. |
| Ejemplos | Nueva funcionalidad, mejora planificada, refactorización priorizada, nuevo reporte, integración nueva. | Incidente, bug productivo, diagnóstico, ajuste urgente, estabilización, escalamiento L2/L3. |

**Regla de decisión:**

```text
Si crea, cambia o mejora una capacidad del producto de forma planificada, va a Desarrollo.
Si corrige, diagnostica, estabiliza o restablece la operación actual, va a Soporte.
```

---

## 6. Reglas de Transición y Definition of Ready (DoR)

Ningún Work Item puede transitar a las columnas operativas sin cumplir criterios mínimos de madurez.

### 6.1 DoR para Requirements (Desarrollo)
Para mover un requerimiento de `Proposed` a `Active`, debe tener:
- Título conciso y descripción clara del valor esperado.
- Criterios de aceptación objetivos y verificables.
- Feature padre asociada (trazabilidad ascendente).
- Estimación funcional (Puntos Fibonacci) diligenciada.
- Bloqueos o dependencias resueltas.

### 6.2 DoR para Issues / Bugs (Soporte)
Para mover un caso operativo a `Analysis` o `Active`, debe tener:
- Descripción técnica del síntoma.
- Identificación precisa del ambiente afectado (Dev, SIT, UAT, Prod).
- Evidencia inicial del fallo (Logs, capturas de pantalla, correlaciones).
- Clasificación de severidad asignada en el Triage.

---

## 7. Criterios de Trazabilidad y Evidencia de Cierre

El modelo prohíbe cerrar tareas sin un rastro auditable. La evidencia mínima exigida para mover a `Closed` es:

- **Requirement:** Pull Request(s) completado(s), resultados de la matriz de QA y evidencia visual/funcional del software operando.
- **Bug:** Pasos exactos de reproducción, comportamiento esperado vs. obtenido y evidencia técnica del hotfix/corrección.
- **Issue:** Registro del diagnóstico, acción correctiva ejecutada y confirmación explícita del usuario o sistema afectado.
- **Change / Release Request:** Rama y tag origen, ambiente destino, y registros de aprobación de los líderes técnicos y de negocio.


## 7.1 Definition of Done general por tipo de Work Item

La Definition of Done se interpreta como el mínimo de trazabilidad, validación y evidencia requerido antes de cerrar un Work Item.

| Tipo de Work Item | Condición mínima para considerarse Done |
|---|---|
| Requirement | Criterios de aceptación validados, PR relacionado cuando aplica, QA aprobado y evidencia funcional adjunta o referenciada. |
| Bug | Reproducción documentada, corrección relacionada a rama/commit/PR, validación de no recurrencia y evidencia de cierre. |
| Issue | Diagnóstico registrado, acción correctiva documentada y confirmación explícita del usuario, sistema o responsable operativo. |
| Change Request | Riesgo, alcance, aprobación, ejecución y evidencia documentados. |
| Release Request | Versión, artefacto, ambiente destino, aprobadores y Work Items incluidos trazables. |

**Regla de cierre:** ningún elemento se mueve a `Closed` si no tiene responsable, estado coherente, evidencia suficiente y relación con los cambios técnicos o acciones operativas ejecutadas.

---

## 8. Estandarización de Etiquetas (Tags)

Se deben utilizar etiquetas estandarizadas para facilitar la creación de consultas (Queries) y Dashboards:

- **Componentes:** `api`, `web`, `db`, `infra`
- **Flujos:** `qa`, `soporte`, `sonar`, `seguridad`
- **Entregas:** `release`, `release-request`, `hotfix`
- **Ambientes:** `dev`, `sit`, `uat`, `staging`, `prod`
- **Estado excepcional:** `bloqueado`

---

## 9. Checklist de cumplimiento de configuración

- [ ] Las columnas de los tableros de Desarrollo y Soporte están creadas exactamente según el estándar.
- [ ] Los estados nativos de CMMI están mapeados correctamente a cada columna visual.
- [ ] Los límites de trabajo en progreso (WIP) se establecieron en un valor base de 5.
- [ ] El equipo domina la diferencia entre un Bug (detectado en ciclo temprano) y un Bug Productivo.
- [ ] Las reglas de transición entre `Ready for QA` e `In QA` están claras para el equipo técnico.
- [ ] El equipo comprende que no se inicia trabajo sin DoR y no se cierra sin evidencia de trazabilidad.


---

# Ajuste complementario — Separación de demanda planificada, urgencias e incendios operativos

## A. Precisión operativa

El Board Desarrollo debe proteger el trabajo planificado y evolutivo. Los incendios operativos, incidentes productivos y bugs productivos no deben distorsionar la lectura del sprint ni mezclarse sin clasificación con las historias comprometidas.

## B. Regla complementaria de clasificación

```text
Una solicitud planificada, evolutiva o de construcción de producto va a Board Desarrollo.
Un incidente, bug productivo, diagnóstico, estabilización o urgencia operativa va a Board Soporte.
```

## C. Demanda no planificada

Cuando un incidente productivo obligue a interrumpir trabajo de Desarrollo, debe quedar visible como demanda no planificada, relacionada al Issue o Bug Productivo correspondiente, y no como una simple desviación informal del sprint.

## D. Control de duplicidades antes de activar trabajo

Antes de mover un Requirement a Active, debe revisarse si existe otro Work Item similar, duplicado o solapado, especialmente cuando varias líneas de negocio impactan el mismo producto o módulo.

## E. Regla complementaria de cierre

Un Work Item no debe cerrarse si fue desplazado por urgencias, quedó parcialmente construido o no completó validación. Debe permanecer abierto, replanificarse o documentar explícitamente su estado real.



---

# Ajuste complementario final — Guía de clasificación para negocio y reglas de entrada al tablero

## 1. Propósito

Este ajuste complementa la regla técnica de clasificación Desarrollo vs Soporte con una explicación simple para jefes de línea de negocio. La intención es que las personas no técnicas puedan cargar la demanda sin bloquearse por conceptos internos de Azure DevOps.

## 2. Regla simple para negocio

```text
Desarrollo construye o cambia capacidades.
Soporte restablece, diagnostica o estabiliza la operación.
```

## 3. Preguntas de clasificación rápida

| Pregunta | Respuesta | Tablero |
|---|---|---|
| ¿Quiero que el sistema haga algo nuevo? | Sí | Board Desarrollo |
| ¿Quiero mejorar algo existente de forma planificada? | Sí | Board Desarrollo |
| ¿Quiero cambiar una regla de negocio para futuros procesos? | Sí | Board Desarrollo |
| ¿Algo que ya existía dejó de funcionar? | Sí | Board Soporte |
| ¿Hay usuarios, procesos o clientes afectados hoy? | Sí | Board Soporte |
| ¿Se requiere diagnóstico de datos, permisos, ambiente o configuración? | Sí | Board Soporte |
| ¿El problema ocurre en producción? | Sí | Board Soporte |
| ¿No sé si es falla o mejora? | Sí | Board Soporte inicialmente para Triage |

## 4. Ejemplos para jefes de línea

| Solicitud | Tablero | Tipo sugerido |
|---|---|---|
| Nuevo reporte. | Desarrollo | Requirement |
| Nuevo campo en una pantalla. | Desarrollo | Requirement |
| Nueva regla de validación. | Desarrollo | Requirement |
| Mejora en una consulta existente. | Desarrollo | Requirement |
| Error en reporte existente. | Soporte | Issue / Bug Productivo según diagnóstico |
| Usuario sin acceso. | Soporte | Issue |
| Proceso caído o bloqueado. | Soporte | Issue / Bug Productivo |
| Cálculo incorrecto en producción. | Soporte | Issue inicialmente; Bug Productivo si se confirma código |
| Solicitud de liberación de una versión aprobada. | Soporte | Release Request |

## 5. Regla de Triage para casos dudosos

Cuando negocio no pueda clasificar con seguridad, el caso debe entrar por Soporte para diagnóstico inicial si existe afectación actual, error, bloqueo o incertidumbre operativa.

Después del Triage, el líder de Soporte, Jenny / BA-QA o el líder técnico podrán reclasificar, relacionar o derivar el caso hacia Desarrollo si corresponde a una nueva capacidad o mejora planificada.

## 6. Carga inicial no equivale a activación

Durante la migración o carga asistida, un Work Item puede quedar registrado en `Proposed`, pero no debe pasar a trabajo activo hasta completar las validaciones mínimas.

```text
Todo elemento cargado debe ser revisado antes de entrar a Active.
La revisión debe validar proyecto, tablero, duplicidad, responsable, prioridad, evidencia y DoR aplicable.
```
