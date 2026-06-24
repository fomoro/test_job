# 07 - Calidad, Validación Técnica y Sonar

## 1. Objetivo práctico

Establecer la automatización del control de calidad estática, seguridad y mantenibilidad del código fuente integrando SonarQube / SonarCloud en el ecosistema Azure DevOps. Esta validación opera como filtro técnico preventivo antes y después de la integración funcional.

---

## 2. Regla operativa base

- Sonar no reemplaza la revisión técnica humana (Pull Request) ni la certificación funcional (QA).
- Constituye un punto de control automatizado e inmutable dentro de las políticas de rama (Branch Policies).
- Todo hallazgo de severidad crítica o vulnerabilidad nueva bloquea automáticamente la promoción de código.

---

## 3. Momentos de validación estática

El análisis de código se ejecuta en dos momentos complementarios dentro del ciclo de vida:

**1. Validación preventiva en Pull Request (PR):**
Actúa como barrera de entrada. Se ejecuta automáticamente mediante el *Build Validation* configurado en Azure DevOps al abrir un PR hacia cualquier rama destino. Su objetivo es detectar problemas en el código nuevo antes de realizar el *merge*.

**2. Validación de salud continua en Ramas Permanentes:**
Se ejecuta posterior al *merge* o mediante tareas programadas sobre las ramas estables (`dev`, `sit`, `uat`, `staging`, `main`). Su objetivo es consolidar la métrica general y visibilizar la deuda técnica acumulada de la solución completa.

---

## 4. Quality Gate (Compuerta de Calidad)

El Quality Gate evalúa el incremento frente a un conjunto de reglas mínimas para determinar si es apto o defectuoso. 

**Métricas mínimas de cumplimiento:**
- Cero bugs críticos nuevos.
- Cero vulnerabilidades críticas nuevas.
- *Security hotspots* mitigados y revisados.
- Duplicación de código nuevo controlada (límite según definición de arquitectura).
- Cobertura de pruebas unitarias sobre código nuevo (si el proyecto las exige).

**Estados del Quality Gate:**
- **Informativo:** Analiza y reporta, pero un estado fallido no bloquea la finalización del PR. Se utiliza en etapas tempranas o de estabilización de pipelines.
- **Obligatorio:** Un estado fallido bloquea inmediatamente las políticas de Azure DevOps, imposibilitando el cierre del PR.

---

## 5. Exigencia del Quality Gate por Ambiente

| Rama Destino | Nivel de Exigencia | Regla de Bloqueo |
|---|---|---|
| **dev** | Informativo / Transitorio | Centrado en código nuevo. No bloquea al inicio para fomentar integración frecuente. |
| **sit** | Obligatorio | Bloquea el PR si ingresan vulnerabilidades críticas o bugs de seguridad. |
| **uat** | Obligatorio | Bloqueo estricto. Código en UAT debe estar saneado de defectos estáticos críticos. |
| **staging** | Obligatorio | Bloqueo estricto. Tolerancia cero a nuevos hallazgos de seguridad. |
| **main** | Obligatorio | Bloqueo absoluto. Todo código productivo debe pasar en verde o poseer excepción aprobada. |

---

## 6. Responsabilidades frente a la Calidad Estática

- **Goku (Desarrollador):** Único responsable de corregir en su rama temporal los hallazgos generados por sus *commits* antes de finalizar el PR.
- **Vegeta (Líder Desarrollo):** Valida la viabilidad de las correcciones y es la autoridad técnica para aceptar riesgos o bloquear PRs defectuosos.
- **Bulma (Responsable CI):** Asegura la integración correcta de las tareas de Sonar (`Prepare`, `Analyze`, `Publish`) dentro de los archivos YAML de los pipelines.
- **Trunks (Responsable Sonar):** Administra el servidor, afina perfiles de calidad y ajusta las reglas de exclusión de código.
- **Gohan (Líder QA):** Consulta el dashboard general para identificar áreas frágiles que requieran mayor cobertura en pruebas de regresión.

---

## 7. Protocolo ante fallos y gestión de Deuda Técnica

Si el Quality Gate falla durante la validación de un Pull Request, el flujo obligatorio es:

1. El PR queda automáticamente inhabilitado para completarse.
2. El desarrollador inspecciona el reporte enlazado en Azure DevOps.
3. El desarrollador ejecuta las refactorizaciones necesarias en su rama temporal (`feature/*` o `bugfix/*`).
4. El nuevo *push* detona otra validación CI.
5. El PR solo avanza cuando el reporte pasa a verde (Success).

**Excepciones (Aceptación de Riesgo):**
En escenarios atípicos donde una corrección técnica sea inviable por tiempo o dependencias, el código puede ser promovido si y solo si se cumplen las siguientes condiciones de trazabilidad:
- Existe una justificación técnica formalizada en el Work Item.
- Se genera un nuevo Work Item (Bug/Task) en el Backlog que represente esta deuda técnica, con fecha compromiso de pago.
- El Líder de Desarrollo y el Líder de Soporte (si afecta producción) aprueban la excepción documentada.

---

# Ajuste complementario — Responsabilidad sobre calidad técnica y rol de Jefferson

## 1. Alcance de Jefferson frente a Sonar y Quality Gates

Jefferson Contreras, como apoyo transversal técnico de Desarrollo y Arquitectura, puede habilitar, configurar y monitorear mecanismos objetivos de calidad técnica asociados a SonarQube / SonarCloud, Quality Gates, pipelines y evidencias técnicas.

Esto incluye:

```text
- Configuración o acompañamiento de SonarQube / SonarCloud.
- Integración de análisis estático en pipelines.
- Publicación de resultados de Quality Gate.
- Acompañamiento en evidencias de calidad técnica.
- Seguimiento a deuda técnica visible en dashboards.
- Apoyo en la estandarización de controles automatizados.
```

## 2. Responsabilidad primaria sobre calidad del código

La existencia de SonarQube no traslada la responsabilidad de la calidad del código a Jefferson ni a SRE.

```text
El desarrollador es responsable de corregir los hallazgos generados por su código.
El líder técnico es responsable de revisar y aprobar técnicamente el Pull Request.
Jefferson habilita los controles automatizados y la evidencia objetiva.
```

## 3. Sonar no reemplaza el Pull Request

SonarQube actúa como control automatizado de calidad estática, seguridad y mantenibilidad, pero no reemplaza:

```text
- Revisión técnica humana.
- Validación de diseño.
- Evaluación de impacto funcional.
- Análisis de dependencias del cambio.
- Validación de criterios de aceptación.
- Aprobación del líder técnico.
```

## 4. Matriz de responsabilidad técnica

| Actividad | Responsable primario | Apoyo / control |
|---|---|---|
| Escribir código mantenible y seguro | Desarrollador | Guías técnicas / Sonar |
| Corregir hallazgos de Sonar | Desarrollador | Líder técnico / Jefferson |
| Revisar Pull Request | Líder técnico / reviewer asignado | Sonar / Build Validation |
| Configurar Quality Gate | Jefferson / responsable Sonar | CI / líder técnico |
| Aprobar excepción técnica | Líder Desarrollo | Jefferson aporta evidencia técnica |
| Validar cumplimiento funcional | QA / BA | Criterios de aceptación / BDD |

## 5. Regla de gobierno

```text
Jefferson gobierna la visibilidad técnica automatizada.
El equipo de Desarrollo conserva la responsabilidad de la calidad técnica del incremento.
QA / BA conserva la validación funcional contra criterios.
```
