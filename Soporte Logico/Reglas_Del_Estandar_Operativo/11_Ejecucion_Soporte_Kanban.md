# 11 - Ejecución de Soporte con Kanban e ITSM Liviano

## 1. Objetivo práctico

Definir el modelo de operación para el equipo de Soporte, garantizando la atención del flujo continuo de trabajo mediante un tablero Kanban, prácticas de ITSM liviano para la clasificación de casos y ciclos de mejora continua (Kaizen).

A diferencia de Desarrollo, Soporte no opera mediante Sprints bloqueados, ya que atiende demanda variable, incidentes productivos y solicitudes operativas en tiempo real.

---

## 2. Enfoque Operativo y Beneficios

El modelo se sostiene sobre tres pilares inmutables:

- **Kanban:** Visualiza el flujo de trabajo, limita el trabajo en curso (WIP) y previene la saturación del equipo.
- **ITSM Liviano:** Estandariza la clasificación de incidentes (Triage), solicitudes de cambio y atención de Bugs productivos sin burocracia excesiva.
- **Kaizen:** Institucionaliza la revisión de causas recurrentes para implementar mejoras pequeñas y medibles.

**Beneficio directo:** Elimina el "trabajo invisible" gestionado por chat, fuerza el diagnóstico antes del escalamiento y asegura la preservación de la evidencia operativa.

---

## 3. Tipología de Trabajo Operativo (Work Items)

Para garantizar la correcta segmentación de la demanda, la entrada de trabajo se clasifica en:

- **Issue:** Incidente estándar, duda funcional o solicitud de acceso.
- **Bug Productivo:** Defecto de código confirmado que evadió los filtros de QA y se manifestó en un ambiente productivo.
- **Change Request (CR):** Solicitud formal de cambio que impacta configuración, integraciones o comportamiento de la plataforma.
- **Requirement Operativo:** Necesidad que exige un esfuerzo de implementación o ajuste controlado por parte del equipo de infraestructura/soporte.

---

## 4. Flujo de Atención y Reglas Kanban

El ciclo de vida del tablero de Soporte sigue esta secuencia restrictiva:

1. **Proposed:** Ingreso del caso. *Regla:* No se atiende trabajo por chat; si requiere seguimiento, debe existir el Work Item.
2. **Triage:** Clasificación obligatoria del impacto, urgencia y ambiente.
3. **Analysis:** Diagnóstico inicial. *Regla:* Soporte debe revisar logs, permisos y datos antes de escalar.
4. **Active:** Ejecución de la corrección operativa o coordinación del escalamiento.
5. **Ready for QA / In QA:** Certificación de la solución.
6. **Resolved:** Confirmación técnica de la solución aplicada.
7. **Waiting Release:** Encolado para despliegue formal. *Regla:* Requiere Change Request o Release Request asociado.
8. **Closed:** Caso cerrado con auditoría y evidencia inmutable.

**Control de WIP (Work In Progress):**
El límite de trabajo en progreso se establece en un base de 5 ítems por columna activa. Si el WIP se excede, el equipo tiene prohibido iniciar trabajo nuevo hasta resolver los bloqueos operativos.

---

## 5. Protocolo de Escalamiento a Desarrollo

Uno de los objetivos del nivel operativo es blindar a la célula de Desarrollo de interrupciones innecesarias.

**Criterios obligatorios para autorizar un escalamiento (Pase a Desarrollo):**
- Se descartaron formalmente fallas de configuración, permisos, datos corruptos y caídas de ambiente.
- El síntoma apunta directamente a una falla en la lógica de la aplicación.
- El equipo de Soporte (Ten Shin Han / Krillin) logró reproducir el error y documentó los pasos exactos.
- El impacto y la prioridad del Bug Productivo están claramente definidos.

*Restricción:* Queda prohibido escalar un caso por "falta de información básica" o dudas funcionales que deben ser resueltas por el área de Producto (BA/PO).

---

## 6. Manejo de Emergencias y Change Requests

- **Bugs Productivos:** Todo defecto detectado en producción requiere la creación de un Work Item tipo "Bug" asociado al Issue original. No se cierra sin la evidencia técnica del hotfix aplicado y la validación en Staging.
- **Change Requests:** Requerido para cualquier ajuste que impacte infraestructura o comportamiento. Debe documentar el motivo, riesgo, plan de ejecución y contar con la aprobación del Líder de Soporte.


## 6.1 Definition of Done de Soporte

Un caso de Soporte se considera Done cuando se cerró el ciclo operativo completo: diagnóstico, acción, validación y evidencia.

Condiciones mínimas para `Issue`:

- Triage realizado con impacto, urgencia y ambiente afectados.
- Diagnóstico documentado.
- Acción correctiva o respuesta operativa registrada.
- Confirmación del usuario, sistema o responsable funcional.
- Evidencia adjunta o referenciada en Azure DevOps.

Condiciones mínimas para `Bug Productivo`:

- Síntoma reproducido o evidencia suficiente del fallo.
- Severidad y prioridad definidas.
- Issue original relacionado cuando aplique.
- Corrección técnica relacionada con rama, commit, PR o hotfix.
- Validación en Staging o ambiente definido.
- Evidencia técnica y funcional de la corrección.
- Sincronización del hotfix hacia `dev` cuando aplique.

Un caso no se cierra por atención verbal, chat o percepción de avance. Se cierra únicamente cuando la solución fue validada y dejó trazabilidad.

---

## 7. Cadencias Operativas y Mejora Continua (Kaizen)

A diferencia de las ceremonias de Scrum, Soporte ejecuta las siguientes revisiones:

- **Revisión Diaria de Flujo:** Monitoreo de cuellos de botella. Foco en casos bloqueados en `Analysis`, incidentes en `Active` y Bugs críticos abiertos.
- **Revisión Semanal de Triage:** Evaluación de tiempos de respuesta, escalamientos rebotados y bloqueos de infraestructura.
- **Sesión Kaizen (Mensual):** Análisis de causa raíz de los incidentes recurrentes. Su única salida válida es una acción de mejora asignable, medible y con fecha límite para evitar la repetición del síntoma.

---

## 8. Checklist de Auditoría de Soporte

- [ ] El equipo atiende exclusivamente la demanda registrada en Azure DevOps (Cero soporte por chat).
- [ ] Ningún ticket transita a `Analysis` sin haber sido tipificado en la etapa de `Triage`.
- [ ] Los escalamientos a Desarrollo incluyen siempre el diagnóstico previo y los logs correspondientes.
- [ ] Los límites de WIP se respetan visual y operativamente en el tablero Kanban.
- [ ] Las modificaciones en infraestructura o configuración productiva están amparadas por un Change Request aprobado.


---

# Ajuste complementario — Gestión de incendios y protección del trabajo planificado

## A. Rol del flujo de Soporte frente a urgencias

El Board Soporte debe absorber incidentes, bugs productivos, estabilizaciones y urgencias operativas para evitar que el Board Desarrollo pierda claridad sobre el trabajo planificado.

## B. Regla de interrupción controlada

Cuando un incendio operativo requiera participación de Desarrollo, debe existir un Work Item en Soporte que documente:

```text
- Síntoma.
- Ambiente afectado.
- Severidad.
- Evidencia inicial.
- Diagnóstico preliminar.
- Motivo del escalamiento.
- Relación con la tarea o bug técnico de Desarrollo, si aplica.
```

## C. Evitar trabajo invisible

La participación de Desarrollo en urgencias no debe quedar como conversación informal. Debe quedar trazada como soporte, bug productivo, hotfix o tarea técnica relacionada.

## D. Resultado esperado

```text
Soporte conserva visibilidad de incidentes.
Desarrollo conserva claridad del sprint.
Gerencia puede diferenciar trabajo planificado, interrupciones y carga operativa real.
```

