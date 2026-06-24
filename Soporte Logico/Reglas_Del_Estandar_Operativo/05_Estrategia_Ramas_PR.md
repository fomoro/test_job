# 05 - Estrategia de Repositorios, Ramas y Pull Requests

## 1. Objetivo práctico

Definir la disciplina operativa y el uso diario de Git dentro de Azure DevOps para el proyecto. Este documento establece las reglas de juego inmutables sobre repositorios, creación de ramas, convenciones de commits, Pull Requests (PR) y la trazabilidad obligatoria con los Work Items de CMMI.

Esta guía responde a la pregunta operativa: **¿Cómo interactúa el equipo técnico con el código fuente en el día a día?**

*(Nota: Las configuraciones duras de Branch Policies, Branch Security y SonarQube se tratan de forma independiente en los documentos 06 y 07).*

---

## 2. Repositorios del proyecto

Los repositorios se aprovisionan para alojar código fuente, servicios, aplicaciones, APIs, librerías o componentes de infraestructura como código (IaC).

**Ruta de creación:**
`Repos ──> Files ──> New repository`

**Reglas de inicialización:**
- Cada repositorio debe nacer con un commit inicial (generalmente `.gitignore` y `README.md`).
- Es mandatorio el uso exclusivo del sistema de control de versiones Git.
- Todo repositorio debe contar con el esquema completo de ramas permanentes antes de iniciar la construcción.

---

## 3. Topología de Ramas Permanentes

Las ramas permanentes son los canales de flujo estables y representan los ambientes físicos o lógicos del ecosistema. **Bajo ninguna circunstancia representan la versión tecnológica del software.**

- `dev` ──> Integración de desarrollo (Ambiente: Dev)
- `sit` ──> Integración técnica / System Integration Testing (Ambiente: SIT)
- `uat` ──> Validación funcional / User Acceptance Testing (Ambiente: UAT)
- `staging` ──> Validación final pre-productiva (Ambiente: Staging)
- `main` ──> Código estable liberado (Ambiente: Prod)

**Flujo de promoción inmutable:**
`dev ──> sit ──> uat ──> staging ──> main`

---

## 4. Topología de Ramas Temporales

Las ramas temporales encapsulan el trabajo en curso. Nacen para un propósito específico y **deben ser eliminadas (deleted) por Azure DevOps al completar el Pull Request**.

**Nomenclatura obligatoria:** `[tipo]/[id-work-item]-[descripcion-corta]`

| Tipo | Uso | Ejemplo |
|---|---|---|
| `feature/*` | Construcción de nueva funcionalidad o requerimiento. | `feature/125-generar-reportes` |
| `bugfix/*` | Corrección de un defecto no urgente (Detectado en ciclos tempranos). | `bugfix/132-validacion-payload` |
| `hotfix/*` | Corrección de emergencia para un Bug Productivo. | `hotfix/145-error-generacion-prod` |
| `release/*` | Preparación de versión y empaquetamiento. | `release/v2.3.0` |

**Restricciones de ramas temporales:**
- No usar nombres de personas, espacios o caracteres especiales en las ramas.
- Las ramas `feature`, `bugfix` y `hotfix` exigen de forma innegociable el ID del Work Item.
- Las ramas `release` utilizan la versión de entrega explícita.

---

## 5. Matriz de Origen Permitido

Para garantizar la integridad del flujo, Azure DevOps solo debe admitir Pull Requests que respeten la siguiente topología de integración:

| Rama Destino | Origen Permitido (PR) | Objetivo del Merge |
|---|---|---|
| **dev** | `feature/*`, `bugfix/*` | Integración del incremento desarrollado. |
| **sit** | `dev` | Promoción para integración de sistemas. |
| **uat** | `sit` | Promoción para certificación de calidad/negocio. |
| **staging** | `uat`, `hotfix/*` | Promoción pre-productiva y validación de emergencias. |
| **main** | `staging`, `hotfix/*` (previamente validado) | Liberación a producción. |

---

## 6. Convención de Commits (Mensajes)

Cada commit funcional debe evidenciar qué cambio introduce y a qué necesidad de negocio responde.

**Formato obligatorio:**
`#[id-work-item] [verbo en infinitivo] [descripción clara del cambio]`

**Ejemplos correctos:**
- `#125 crear contrato inicial de generacion de reportes`
- `#132 corregir validacion de formato PDF`

**Antipatrones prohibidos:**
- `cambios` / `ajustes varios`
- `fix final` / `prueba pipeline`
- `commit sin ID de Work Item`

---

## 7. Reglas de Pull Requests (PR)

El flujo de trabajo es estrictamente basado en Pull Requests. **El "Push directo" a ramas permanentes está bloqueado por diseño.**

Requisitos ineludibles para abrir y completar un PR:
- Rama origen y destino validadas según la matriz.
- Commits atados a un Work Item (Requirement, Bug, Task).
- Descripción clara del impacto en el PR.
- Ejecución de Build / CI exitosa (Validación técnica).
- Todos los comentarios e iteraciones de la revisión técnica marcados como resueltos.

### 7.1 Plantilla de PR Sugerida
```markdown
## Objetivo
[Explicar qué se cambia y por qué]

## Work Item relacionado
#[id]

## Tipo de cambio
[Feature / Bugfix / Hotfix / Promoción]

## Validaciones previas
- [ ] Build local exitoso.
- [ ] Sin exposición de secretos.
- [ ] SonarQube local ejecutado (si aplica).

## Riesgos o dependencias
[Indicar impacto a otros componentes o "Sin riesgos evidentes"]

```

---

## 8. Trazabilidad de Auditoría CMMI

El objetivo central de esta operativa Git es asegurar que ningún cambio productivo sea huérfano. La cadena de custodia debe ser demostrable:

**Flujo de Trazabilidad:**
`Requirement (Work Item) ──> Rama (feature/*) ──> Commits (#ID) ──> Pull Request ──> Build`

---

## 9. Referencias a siguientes guías

Esta operativa diaria se complementa directamente con la configuración restrictiva de las siguientes guías del Proyecto 01:

* **06_Gobierno_Promocion_Seguridad.md:** Políticas de protección de ramas, obligatoriedad de revisores y bloqueos de seguridad.
* **07_Calidad_Validacion_Sonar.md:** Ejecución de Quality Gates dentro del Pull Request.
