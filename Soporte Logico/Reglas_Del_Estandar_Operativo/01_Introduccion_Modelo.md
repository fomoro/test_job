# 01 - Introducción al Modelo Operativo DevOps CMMI

## 1. Objetivo práctico

Definir el estándar base, inmutable y reutilizable para configurar y operar Azure DevOps, garantizando trazabilidad, calidad y control mediante:

- CMMI para la gestión de Soporte.
- CMMI ajustado a Scrum para la ejecución de Desarrollo.
- QA integrado orgánicamente al flujo de valor.
- Trazabilidad técnica total entre Work Items, ramas, Pull Requests, pipelines y evidencias de cierre.

Este documento sirve como punto de entrada del **Proyecto 01_Estandar_Operativo**.

---

## 2. Reglas maestras del estándar

- El estándar define la única fuente de verdad sobre cómo se trabaja y se configura el ecosistema técnico.
- Los proyectos reales, pilotos o laboratorios únicamente consumen y aplican este estándar de forma estricta.
- Queda prohibido redefinir roles, flujos de trabajo, políticas de seguridad, ramas, pipelines o criterios de evidencia en las implementaciones derivadas.

---

## 3. Alcance operativo

**Incluye:**
- Configuración y gobierno base de Azure DevOps.
- Estructura centralizada de equipos, perfiles y permisos mínimos.
- Flujos de trabajo independientes para Desarrollo y Soporte.
- Estrategia unificada de Git (Repositorios, Ramas y Pull Requests).
- Políticas de seguridad, protección de ramas y gobierno de promoción.
- Automatización e integración continua (Pipelines, ambientes y versionamiento).
- Quality Gates y validación técnica automatizada con Sonar.

**No incluye:**
- Implementación o diseño de código fuente específico.
- Definición de arquitectura de software para un producto.
- Backlog funcional de un producto en particular.
- Manuales teóricos genéricos de marcos ágiles o de la herramienta Azure DevOps.

---

## 4. Estructura e instancias de aplicación

El presente ecosistema se divide en tres proyectos bajo un enfoque de herencia operativa:

**Proyecto 01_Estandar_Operativo**
└── Contiene la teoría accionable, las políticas de seguridad y las reglas maestras (El estándar actual).

**Proyecto 02_Implementacion_Piloto**
└── Demuestra la configuración total y el uso práctico del estándar en un entorno controlado, utilizando la base de datos de AdventureWorks.

**Proyecto 03_Componente_Reporteria**
└── Aplica el estándar de forma fidedigna sobre el ciclo de vida real de un MVP (API autónoma de reportes).

---

## 5. Continuidad y trazabilidad de los perfiles (Ejemplo Académico)

Para garantizar una asimilación fluida, asegurar el hilo conductor y mantener la trazabilidad de responsabilidades a lo largo de toda la documentación (Proyectos 01, 02 y 03), el modelo emplea perfiles didácticos basados en el universo de Dragon Ball:

- **Desarrollo:** Goku, Vegeta, Bulma, Trunks.
- **Soporte:** Krillin, Ten Shin Han.
- **QA (Rol Integrado):** Piccolo, Gohan.
- **Roles Transversales:** Maestro Roshi (Scrum Master), Freezer (PO), Androide 18 (Jefe BA), Videl (Analista BA).

Estos perfiles deben conservarse intactos en las guías de implementación práctica y reemplazarse por usuarios corporativos reales únicamente al desplegar proyectos productivos externos.

---

## 6. Orden de lectura recomendado

La asimilación de este modelo operativo debe realizarse de forma secuencial:

1. `01_Introduccion_Modelo.md` (Documento actual)
2. `02_Gobierno_Equipos_Roles.md`
3. `03_Estrategia_WorkItems_Boards.md`
4. `04_Gestion_Backlog_BDD.md`
5. `05_Estrategia_Ramas_PR.md`
6. `06_Gobierno_Promocion_Seguridad.md`
7. `07_Calidad_Validacion_Sonar.md`
8. `08_Estrategia_Pipelines_Ambientes.md`
9. `09_Estandar_Versionamiento_Tecnico.md`
10. `10_Ejecucion_Desarrollo_Scrum.md`
11. `11_Ejecucion_Soporte_Kanban.md`

---

## 7. Checklist de cierre y asimilación

- [ ] El equipo entiende que este repositorio (01) es la norma y no se reescribe en otros proyectos.
- [ ] El equipo asimila que Desarrollo y Soporte operan con flujos y tableros distintos.
- [ ] El equipo entiende que QA es un rol transversal integrado y carece de un tablero independiente.
- [ ] El equipo comprende la función de continuidad operativa de los perfiles académicos asignados.
- [ ] El equipo conoce el índice maestro y el orden lógico para implementar la configuración.