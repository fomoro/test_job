# 04 - Gestión del Backlog y Redacción Funcional (BDD)

## 1. Objetivo práctico

Definir el estándar de calidad para la creación, estimación y refinamiento de Historias de Usuario (HU) en Azure DevOps bajo el proceso CMMI. Este documento establece cómo el equipo de Producto (Dueño del Producto y Analistas de Negocio) estructura el trabajo antes de entregarlo a los equipos de Desarrollo o Soporte.

---

## 2. Jerarquía funcional y responsabilidades

El Backlog se organiza estructurando el valor del negocio de mayor a menor granularidad:

- **Feature:** Agrupador funcional principal. Contiene múltiples Historias de Usuario.
- **Requirement (HU de Desarrollo):** Unidad de valor que requiere construcción de software.
- **Requirement Operativo / Issue (HU de Soporte):** Unidad de trabajo operativo o ajuste en producción.
- **Task:** Actividad técnica o de QA hija de una Historia de Usuario.

**Cadena de responsabilidad funcional:**
- **Dueño del Producto (PO):** Autoridad final. Prioriza el Backlog y aprueba el valor de negocio.
- **Jefe BA:** Auditor funcional. Revisa la calidad, claridad y completitud de las HU antes del refinamiento.
- **Analista BA:** Ejecutor. Levanta la necesidad, redacta la historia, define los criterios de aceptación y los escenarios BDD en español.

---

## 3. Campos obligatorios de la Historia de Usuario

Para que un `Requirement` o `Issue` cumpla con el estándar mínimo de registro, debe diligenciar:

1. **Title:** ID del agrupador y nombre corto de la HU.
2. **Description:** Estructura narrativa de la Historia de Usuario + Escenarios BDD.
3. **Acceptance Criteria:** Lista numerada de condiciones verificables para dar por terminada la HU.
4. **Size:** Estimación de esfuerzo en puntos Fibonacci.
5. **Original Estimate:** Horas estimadas derivadas del Size.
6. **Area Path:** Determina en qué tablero (Desarrollo o Soporte) aparecerá la HU.
7. **Parent:** Enlace directo a la `Feature` correspondiente.
8. **Tags:** Etiquetas de clasificación tecnológica o de proceso.

---

## 4. Estructura de redacción y BDD (Behavior-Driven Development)

El `Analista BA` debe redactar la necesidad utilizando el lenguaje de negocio, evitando tecnicismos de implementación.

### 4.1 Formato del Título
`HU-[AGRUPADOR]-[NUMERO] - [Nombre corto y claro]`

### 4.2 Plantilla de Descripción
La descripción debe seguir el modelo tradicional combinado con BDD en español:

Como [Rol / Actor],
quiero [Capacidad o acción esperada],
para [Beneficio o valor de negocio].

**Escenarios BDD:**
Escenario: [Nombre descriptivo del escenario]
Dado que [Contexto inicial o estado del sistema]
Y [Condición adicional]
Cuando [Acción que detona el comportamiento]
Entonces [Resultado esperado verificable]
Y [Efecto secundario o resultado adicional]

**Regla de oro BDD:** Se escribe en español usando estrictamente *Dado / Cuando / Entonces*. Queda prohibido describir nombres de clases, métodos, tablas de base de datos o arquitectura interna.

### 4.3 Criterios de Aceptación
Deben ser afirmaciones objetivas y demostrables. No son tareas de desarrollo (Ej. Mal: "Crear el endpoint". Bien: "El sistema debe rechazar peticiones sin token").

---

## 5. Reglas de Estimación y Esfuerzo

La estimación cubre el ciclo de vida completo de la HU (análisis, diseño, código, pruebas locales, QA, correcciones y documentación).

- **Métrica base:** `Size` utiliza la secuencia de Fibonacci (1, 2, 3, 5, 8, 13).
- **Conversión operativa:** `Original Estimate` es el cálculo en horas para facilitar el seguimiento (1 punto = 2 horas).

**Tabla de conversión estándar:**
- Size 1 = 2 horas
- Size 2 = 4 horas
- Size 3 = 6 horas
- Size 5 = 10 horas
- Size 8 = 16 horas
- Size 13 = 26 horas

**Restricción:** Las `Tasks` técnicas hijas no suman puntos Fibonacci al tablero. El puntaje pertenece a la Historia de Usuario.

---

## 6. Creación de Tareas (Tasks) y Asignación de QA

El trabajo técnico detallado se coordina creando `Tasks` asociadas a la HU padre.

**Ruta Azure DevOps:**
`Abrir HU ──> Links ──> Add link ──> New item ──> Task`

### 6.1 Tareas limpias para Desarrollo
- *Task:* Implementar la solución técnica requerida por la HU. (Asignada a: Desarrollador)
- *Task:* Ejecutar prueba técnica local / Despliegue Dev. (Asignada a: Desarrollador)
- *Task QA:* Diseñar y ejecutar matriz de pruebas y escenarios BDD. (Asignada a: Analista QA)

### 6.2 Regla de asignación de Calidad
Como no existe un tablero independiente para QA, el responsable técnico asume la HU principal y el analista de calidad asume una *Task* hija etiquetada explícitamente para validación.

---

## 7. Checklist de calidad del Analista BA

Antes de presentar la HU en una sesión de refinamiento, el BA debe verificar:
- [ ] La HU tiene título claro y está vinculada a su Feature (Parent).
- [ ] La descripción cuenta con los escenarios BDD redactados en español.
- [ ] Los criterios de aceptación son verificables y no detallan código.
- [ ] La historia cuenta con estimación en puntos Fibonacci (`Size`) y horas (`Original Estimate`).
- [ ] El `Area Path` está asignado al equipo correcto.
- [ ] Las tareas hijas de construcción técnica y de certificación QA están creadas.
- [ ] La HU se encuentra en estado `Proposed` lista para evaluación técnica.

## 7.1 Definition of Done funcional de una Historia de Usuario

Una Historia de Usuario cumple su DoD funcional cuando puede demostrarse que la necesidad fue entendida, desarrollada y validada contra criterios objetivos.

Condiciones mínimas:

- La HU conserva Feature padre, Area Path correcto, responsable y estimación.
- Los criterios de aceptación son verificables y fueron usados como base de validación.
- Los escenarios BDD aplicables fueron ejecutados o cubiertos por QA.
- Las tareas técnicas y de QA asociadas reflejan el trabajo realizado.
- La evidencia funcional quedó adjunta o referenciada en Azure DevOps.
- No quedan defectos críticos o bloqueantes asociados a la HU.

La HU no se cierra por avance verbal ni por finalización del código. Se cierra cuando el valor funcional fue validado con evidencia.


---

# Ajuste complementario — Refinamiento anticipado y control de duplicidades

## A. Preparación anticipada de Historias de Usuario

Las Historias de Usuario candidatas a Sprint deben prepararse con anticipación suficiente, idealmente entre 2 y 3 sprints antes de su ejecución.

La preparación debe incluir al jefe de línea de negocio, Jenny en rol BA / QA y el líder técnico del frente.

## B. Validaciones previas obligatorias

Antes de marcar una HU como lista para Sprint, se debe validar:

```text
- Línea de negocio solicitante.
- Producto, módulo o cliente afectado.
- Existencia de historias similares o duplicadas.
- Posible consolidación con otras solicitudes.
- Prioridad validada por el jefe de línea.
- Responsable funcional de aceptación.
- Criterios de aceptación verificables.
- Escenarios BDD aplicables.
- Dependencias funcionales y técnicas.
- Estimación preliminar revisada con líder técnico.
```

## C. Responsabilidades

| Rol | Responsabilidad |
|---|---|
| Jefe de línea de negocio | Confirma valor, prioridad, impacto y alcance funcional. |
| BA / QA | Estructura la historia, criterios, BDD y calidad funcional. |
| Líder técnico | Valida factibilidad, dependencias, riesgos e impacto técnico. |

## D. Regla complementaria de DoR

Una HU no debe considerarse Ready si aún requiere descubrimiento funcional, si tiene duplicidad no resuelta, si no tiene responsable funcional de aceptación o si sus criterios de aceptación no son verificables.



---

# Ajuste complementario final — Migración/carga asistida de HU y responsabilidades de negocio

## 1. Propósito

Este ajuste define cómo debe realizarse la carga inicial de Historias de Usuario, bugs productivos y casos durante la primera ola de adopción. La carga inicial es una actividad de adopción operativa, no un reemplazo del refinamiento BA ni del Sprint Planning.

## 2. Flujo de entrada de demanda

```text
Demanda identificada por línea de negocio
↓
Capacitación y carga asistida con Alexandra
↓
Revisión de completitud mínima y ubicación correcta
↓
Revisión de duplicidades
↓
Refinamiento funcional con jefe de línea + Jenny BA/QA
↓
Validación técnica con líder técnico
↓
Ready for Sprint
```

## 3. Rol de Alexandra durante la carga

Alexandra acompaña el proceso operativo de carga en Azure DevOps:

```text
- Explica cómo registrar una HU o caso.
- Apoya la ubicación en proyecto y tablero.
- Revisa que existan campos mínimos.
- Ayuda a organizar el backlog inicial.
- Escala dudas funcionales a Jenny / BA-QA.
- Escala dudas técnicas a Jefferson o al líder técnico.
```

Alexandra no define criterios de aceptación, no prioriza, no aprueba funcionalmente y no decide qué entra al Sprint.

## 4. Responsabilidad de negocio al cargar una HU

El jefe de línea o responsable designado debe entregar contexto suficiente para que la historia pueda ser refinada.

Campos mínimos recomendados:

```text
- Línea de negocio solicitante.
- Producto, módulo, cliente o proceso afectado.
- Necesidad descrita en lenguaje funcional.
- Valor esperado o problema que resuelve.
- Prioridad sugerida.
- Responsable funcional de aceptación.
- Evidencia, ejemplo o caso de negocio cuando aplique.
- Fecha objetivo si existe compromiso contractual o externo.
```

## 5. Responsabilidad de negocio al cargar un caso de Soporte

Para incidentes, bugs productivos o afectaciones operativas, el responsable debe registrar:

```text
- Ambiente afectado.
- Usuario, cliente, entidad o proceso afectado.
- Síntoma observado.
- Impacto operativo.
- Urgencia percibida.
- Evidencia disponible.
- Pasos de reproducción si se conocen.
- Fecha y hora aproximada del evento.
```

## 6. Revisión de duplicidades

Antes de que una Historia de Usuario sea considerada Ready, Jenny / BA-QA y el jefe de línea deben revisar si la solicitud ya existe, si está relacionada con otra línea o si puede consolidarse con una Feature común.

```text
No se debe activar trabajo duplicado sin decisión explícita.
```

## 7. Diferencia entre cargar, refinar y comprometer

| Estado | Significado |
|---|---|
| Cargada | La demanda quedó registrada en Azure DevOps. |
| Revisada | Tiene campos mínimos y ubicación correcta. |
| Refinada | Tiene alcance, criterios, prioridad, responsable y duplicidades resueltas. |
| Ready | Cumple DoR y puede ir a Sprint Planning. |
| Comprometida | El equipo la aceptó dentro de un Sprint según capacidad. |

## 8. Guía rápida para negocio

```text
Si pido algo nuevo o una mejora planificada: Desarrollo.
Si reporto una falla, bloqueo, error o afectación actual: Soporte.
Si no estoy seguro: se registra para revisión, preferiblemente por Soporte si hay afectación operativa.
```
