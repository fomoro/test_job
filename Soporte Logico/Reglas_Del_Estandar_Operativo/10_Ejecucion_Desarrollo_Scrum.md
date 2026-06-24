# 10 - Ejecución de Desarrollo con Scrum Adaptado

## 1. Objetivo práctico

Establecer el modelo de operación diaria para el equipo de Desarrollo, integrando la agilidad del marco Scrum con el rigor, la trazabilidad y las métricas exigidas por el modelo CMMI en Azure DevOps. 

Este documento estandariza las cadencias, las ceremonias y las reglas de ejecución exclusivas para la célula de construcción de software.

---

## 2. Integración CMMI y Scrum (Regla Base)

El uso de CMMI como proceso subyacente en Azure DevOps no compite con Scrum; ambos se complementan bajo el siguiente esquema:

- **CMMI aporta:** La jerarquía estricta de Work Items, los estados del flujo de valor, el control de cambios, las políticas de seguridad y la trazabilidad de auditoría.
- **Scrum aporta:** La cadencia de entrega iterativa (Sprints), la planificación, el seguimiento diario (Daily), el refinamiento del backlog y la mejora continua (Retrospectiva).

**Restricción operativa:** Las Historias de Usuario (Requirements), ramas, Pull Requests, pipelines y evidencias se gestionan obligatoriamente bajo las reglas del Proyecto 01. Scrum no exime al equipo de cumplir con la trazabilidad técnica.

---

## 3. Cadencia del Sprint y Estrategia de Despliegue

**Duración estándar:** 2 semanas (Iteración fija).

Todo Sprint debe contener de forma ineludible:
- Sesión de Sprint Planning.
- Sesiones de refinamiento de backlog (Previas o durante el ciclo).
- Daily Scrum (Días hábiles).
- Actualización continua del tablero (Azure Boards).
- Sprint Review y Sprint Retrospective.
- Cierre formal de métricas y evidencias.

**Relación entre Sprint y Despliegue a Producción:**
- **Regla estándar:** El equipo consolida una versión productiva mayor cada 5 Sprints (Release Train). Durante el Sprint regular, el código integrado solo se promueve hasta ambientes no productivos (SIT / UAT / Staging).
- **Excepción autorizada:** Se permite un despliegue a producción al cierre de un Sprint intermedio única y exclusivamente si existe una necesidad crítica de negocio respaldada por un `Release Request`, QA aprobado, artefacto versionado y la aprobación formal del Dueño del Producto y el Líder de Soporte.

---

## 4. Ceremonias y Reglas de Ejecución

### 4.1 Refinamiento del Backlog (Grooming)
- **Objetivo:** Asegurar que los Requirements estén claros, estimados y cumplan la *Definition of Ready (DoR)* antes de la planificación.
- **Participación:** - *PO:* Prioriza y valida el valor de negocio.
  - *Jefe / Analista BA:* Expone el qué funcional, los criterios de aceptación y el BDD.
  - *Líder Desarrollo:* Valida la factibilidad técnica e identifica dependencias.
  - *Líder QA:* Asegura que los criterios sean testeables.

### 4.2 Sprint Planning
- **Condición de entrada:** No se compromete trabajo al Sprint que no cumpla estrictamente con la DoR.
- **Salidas exigidas:**
  - Objetivo claro del Sprint.
  - Requirements asignados a desarrolladores y QA.
  - Tareas (Tasks) técnicas creadas.
  - Riesgos documentados.

### 4.3 Daily Scrum
- **Frecuencia y duración:** Diaria, máximo 15 minutos.
- **Foco de revisión visual (Azure Boards):**
  1. Historias atascadas en `In QA` o `Code Review`.
  2. Bloqueos técnicos (Impediments).
  3. Riesgos del Sprint y Bugs críticos detectados.
- *Regla:* La Daily identifica los problemas y asigna responsables de resolución; no es una sesión para resolver los problemas de fondo.

### 4.4 Revisión Técnica y QA en el Sprint
- **Code Review (Revisión de pares):** El PR debe contar con un Build exitoso, validación SonarQube (según la Guía 07) y sin exposición de secretos.
- **QA Integrado:** Como no existe un tablero independiente de QA, el analista de calidad interviene en la fase `In QA` del ciclo de vida del Requirement, certificando el incremento funcional y los escenarios BDD sin reemplazar la prueba técnica del desarrollador.

### 4.5 Sprint Review y Retrospective
- **Review:** Demostración del incremento terminado (software funcionando). Se revisan las historias cerradas, la evidencia funcional y los Bugs abiertos.
- **Retrospective:** Análisis del sistema de trabajo. Se evalúa qué funcionó, los cuellos de botella operativos y se define **una (1) acción concreta y medible** para implementar en el siguiente Sprint.


## 4.6 Definition of Done de Desarrollo

Un Requirement de Desarrollo se considera Done cuando cumple simultáneamente con la validación funcional, técnica y de trazabilidad.

Condiciones mínimas:

- El Work Item está asociado a una rama, commits y Pull Request.
- El Pull Request fue revisado, aprobado y completado según las políticas vigentes.
- El build o validación técnica fue exitoso.
- SonarQube / Quality Gate fue aprobado o existe excepción documentada.
- QA validó los criterios de aceptación y escenarios BDD aplicables.
- La evidencia funcional y técnica quedó adjunta o referenciada.
- El estado del tablero refleja la realidad del trabajo.

El Sprint solo debe cerrar como terminado aquello que cumpla esta Definition of Done. Lo que no tenga evidencia o validación debe permanecer abierto, replanificarse o quedar explícitamente justificado.

---

## 5. Checklist de Cierre de Sprint (Auditoría)

El Scrum Master y el Líder de Desarrollo deben garantizar las siguientes condiciones antes de cerrar la iteración en Azure DevOps:

- [ ] Todos los Work Items reflejan su estado real.
- [ ] Los Pull Requests huérfanos están cerrados o justificados.
- [ ] El esfuerzo de QA quedó registrado en las Tasks correspondientes.
- [ ] Las historias movidas a `Closed` contienen trazabilidad y evidencias adjuntas.
- [ ] Si existe un candidato a despliegue productivo, el `Release Request` se encuentra creado y enrutado para aprobación.


---

# Ajuste complementario — Refinamiento continuo y protección del Sprint Planning

## A. Refinamiento continuo a 2–3 sprints

El equipo de Desarrollo no debe esperar al Sprint Planning para descubrir alcance, aclarar necesidad o estimar historias inmaduras.

Mientras se ejecuta el sprint actual, el jefe de línea de negocio, Jenny en rol BA / QA y el líder técnico deben trabajar sobre el backlog candidato de los próximos 2 a 3 sprints.

## B. Participantes mínimos

```text
- Jefe de línea de negocio.
- Jenny como BA / QA.
- Líder técnico del frente.
```

## C. Responsabilidades

| Rol | Responsabilidad |
|---|---|
| Jefe de línea de negocio | Prioridad, valor, impacto, contexto funcional y aceptación. |
| BA / QA | Calidad funcional de HU, criterios de aceptación, BDD y depuración de duplicidades. |
| Líder técnico | Factibilidad, dependencias, riesgos, impacto técnico y estimación preliminar. |
| Equipo Scrum | Compromiso de capacidad durante el Sprint Planning. |

## D. Regla de Sprint Planning

```text
Sprint Planning no es una sesión de descubrimiento.
Sprint Planning es una sesión de compromiso sobre trabajo ya refinado y Ready.
```

## E. Protección frente a urgencias

Los incendios, bugs productivos e incidentes deben entrar por el flujo de Soporte / Kanban. Si requieren interrupción del sprint, deben quedar registrados como demanda no planificada y relacionados con el Work Item correspondiente.

## F. Condición para sprints de dos semanas

La reducción a sprints de dos semanas solo es viable si existe backlog preparado con anticipación, control de duplicidades y separación clara entre trabajo planificado y urgencias operativas.



---

# Ajuste complementario — Calidad técnica durante la ejecución y apoyo de Jefferson

## 1. Responsabilidad de calidad durante el Sprint

Durante la ejecución del Sprint, la calidad técnica del incremento es responsabilidad primaria del desarrollador y del líder técnico del frente.

```text
El desarrollador responde por el código que implementa.
El líder técnico responde por la revisión técnica, coherencia de diseño e impacto del cambio.
QA / BA valida el cumplimiento funcional contra criterios y escenarios.
Jefferson habilita controles automatizados de calidad técnica cuando aplique.
```

## 2. Rol de Jefferson en la ejecución de Desarrollo

Jefferson puede apoyar al equipo mediante mecanismos técnicos como:

```text
- SonarQube / SonarCloud.
- Quality Gates.
- Build Validation.
- Evidencias de pipeline.
- Configuración técnica de repositorios o ramas.
- Soporte al gobierno técnico de CI/CD.
```

Este apoyo no reemplaza la revisión técnica del Pull Request ni la responsabilidad del líder técnico del frente.

## 3. Pull Request y Sonar como controles complementarios

```text
El Pull Request valida criterio técnico humano.
Sonar valida calidad estática automatizada.
QA valida comportamiento funcional.
El Work Item conserva trazabilidad y evidencia.
```

Ningún control por sí solo sustituye a los demás.

## 4. Regla práctica para el equipo

```text
Si Sonar falla, el desarrollador corrige.
Si el diseño técnico no es aceptable, el líder técnico solicita ajustes.
Si el comportamiento no cumple criterios, QA rechaza o devuelve a corrección.
Si el pipeline o Quality Gate está mal configurado, Jefferson apoya la corrección técnica del control.
```


---

# Ajuste complementario final — Carga inicial, refinamiento y compromiso de Sprint

## 1. Distinción clave

La carga inicial de Historias de Usuario durante la migración no equivale a compromiso de Sprint.

```text
Una historia cargada en Azure DevOps todavía debe pasar por revisión, depuración, refinamiento funcional, validación técnica y cumplimiento de DoR.
```

## 2. Entrada correcta al Sprint Planning

El Sprint Planning solo debe recibir Historias de Usuario que ya hayan sido trabajadas previamente por:

```text
- Jefe de línea de negocio.
- Jenny en rol BA / QA.
- Líder técnico del frente.
```

## 3. Relación con la capacitación de Alexandra

La capacitación y carga asistida con Alexandra ocurre antes del refinamiento. Su propósito es que la demanda quede visible y mínimamente organizada, no que quede lista automáticamente para desarrollo.

```text
Alexandra ayuda a cargar y organizar.
Jenny refina funcionalmente.
El líder técnico valida factibilidad.
El equipo compromete capacidad en Sprint Planning.
```

## 4. Protección del sprint de dos semanas

Un sprint de dos semanas solo funciona si el backlog fue preparado con anticipación. Por eso, las historias recién cargadas no deben entrar al Sprint Planning si todavía requieren aclaración funcional, depuración de duplicidades o validación técnica.

## 5. Regla de interrupciones

Si durante el Sprint aparece un incendio, bug productivo o urgencia operativa, debe registrarse en Board Soporte. Si obliga a interrumpir desarrollo, debe quedar como demanda no planificada relacionada al Work Item correspondiente.

```text
No se debe ocultar una interrupción como avance normal del Sprint.
```
