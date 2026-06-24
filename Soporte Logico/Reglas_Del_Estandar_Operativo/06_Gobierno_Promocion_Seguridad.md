# 06 - Gobierno de Promoción y Seguridad de Ramas

## 1. Objetivo práctico

Establecer el gobierno estricto para la promoción de código entre ramas dentro de Azure DevOps. Este documento define quién está autorizado para promover código, bajo qué políticas de integración, y establece las configuraciones de seguridad (Branch Security) y políticas (Branch Policies) necesarias para cumplir con los lineamientos de auditoría CMMI.

---

## 2. Regla rectora de promoción

La promoción de código en el ecosistema sigue un flujo secuencial inmutable. Las alteraciones no documentadas representan una violación a la arquitectura operativa.

**Flujo de promoción regular:**
`dev ──> sit ──> uat ──> staging ──> main`

**Reglas operativas de obligatorio cumplimiento:**
- Prohibido realizar *commits* directos a la rama `main`.
- Prohibido realizar *push* directo a cualquier rama permanente protegida.
- Prohibido liberar código sin un Pull Request (PR) aprobado.
- Prohibido promover código sin un Work Item (Requirement, Bug, CR) asociado.
- Prohibido saltar ambientes de validación.

---

## 3. Modelo de Seguridad en Azure DevOps

El control de flujo se implementa configurando dos capas de gobierno sobre las ramas permanentes ya existentes (`dev`, `sit`, `uat`, `staging`, `main`).

1. **Seguridad sobre Ramas (Branch Security):**
   Define **quién** puede ejecutar acciones sobre la rama (ej. bloquear push directo, denegar reescritura de historia).
2. **Políticas sobre Ramas (Branch Policies):**
   Define **qué condiciones** debe cumplir un PR para ser integrado en la rama (ej. validación técnica de CI, revisores obligatorios, Work Items vinculados).

---

## 4. Configuración de Seguridad sobre Ramas (Branch Security)

Se debe aplicar la siguiente configuración de seguridad base a todas las ramas permanentes.

**Ruta de administración:**
`Repos ──> Branches ──> [rama] ──> More options (...) ──> Branch security`

**Configuración mínima exigida:**
- **Contribute:** Restringido por rol (Deny para roles operativos sobre ramas permanentes para forzar el uso de PR).
- **Force push:** Deny absoluto. Impide reescribir la historia de Git o borrar tags.
- **Bypass policies when pushing:** Deny absoluto. Previene que usuarios eludan políticas vía consola.
- **Bypass policies when completing PRs:** Deny absoluto. Previene forzar el cierre de un PR incompleto.
- **Edit policies / Manage permissions:** Restringido exclusivamente al Líder de Desarrollo y Responsable CI.

---

## 5. Configuración de Políticas sobre Ramas (Branch Policies)

Garantiza que el código entrante tenga calidad técnica y respaldo de auditoría.

**Ruta de administración:**
`Repos ──> Branches ──> [rama] ──> More options (...) ──> Branch policies`

**Configuración obligatoria por política:**
- **Check for linked work items:** Required (Impide PRs huérfanos).
- **Check for comment resolution:** Required (Garantiza que la retroalimentación técnica fue atendida).
- **Limit merge types:** Configurar preferiblemente en *Squash merge* para mantener un historial limpio en la rama destino.
- **Build validation:** Required (Ejecuta el pipeline de Integración Continua asociado a la rama).
- **Require a minimum number of reviewers:** Required (Define la cantidad y roles de aprobadores según la rama destino).

---

## 6. Gobierno Específico por Ambiente (Ramas Permanentes)

La madurez y exigencia de las políticas aumentan conforme el código se acerca a producción.

### 6.1 Rama: dev
- **Objetivo:** Integración continua de Desarrollo.
- **Aprobadores mínimos:** 1 (Líder Desarrollo o par técnico).
- **Validación:** Build CI de desarrollo. SonarQube informativo enfocado en código nuevo.

### 6.2 Ramas: sit / uat
- **Objetivo:** Integración técnica y certificación funcional.
- **Aprobadores mínimos:** Líder Desarrollo (`sit`) + Líder QA (`uat`).
- **Validación:** Build CI. SonarQube con Quality Gate obligatorio (Sin vulnerabilidades críticas nuevas).

### 6.3 Rama: staging
- **Objetivo:** Validación pre-productiva y simulación final.
- **Aprobadores mínimos:** Líder QA + Líder Soporte.
- **Requisito extra:** Evidencia de validación QA adjunta. Release Request si aplica despliegue.

### 6.4 Rama: main
- **Objetivo:** Producción. Entorno de máxima protección.
- **Aprobadores mínimos:** 3 (Líder Soporte + Líder QA + Dueño del Producto).
- **Requisito extra:** Todo paso a `main` exige un Release Request aprobado y un artefacto versionado trazable.

---

## 7. Matriz de Promoción y Aprobación (Roles Académicos)

Esta matriz ejemplifica quién tiene la potestad de crear, aprobar y completar los PRs en el flujo de entrega.

| Promoción | Crea PR | Aprueba PR (Reviewer) | Completa PR (Merge) | Evidencia de Auditoría |
|---|---|---|---|---|
| `feature/*` ──> `dev` | Goku (Dev) | Vegeta (Lead Dev) | Vegeta | Work Item en estado Code Review |
| `dev` ──> `sit` | Bulma (CI) / Vegeta | Vegeta / Bulma | Bulma / Vegeta | Build CI exitoso |
| `sit` ──> `uat` | Bulma / Vegeta | Vegeta + Gohan (Lead QA) | Bulma / Vegeta | QA funcional previo / BDD |
| `uat` ──> `staging`| Bulma / Ten Shin Han | Gohan + Ten Shin Han (Lead Sup)| Bulma / Ten Shin Han | Matriz QA firmada |
| `staging` ──> `main`| Ten Shin Han | Ten Shin Han + Gohan + Freezer (PO)| Ten Shin Han | Release Request aprobado |

---

## 8. Matriz de Permisos Mínimos por Rol

Para hacer cumplir el flujo anterior, la seguridad de los repositorios se parametriza así:

| Rol Funcional | Create branch | Contribute (Push) | Crear PR | Aprobar PR | Completar PR | Force Push / Bypass |
|---|---|---|---|---|---|---|
| **Desarrollador** | Sí | Solo ramas temporales | Sí | No (salvo asignación) | No en protegidas | Deny |
| **Líder Desarrollo** | Sí | Controlado | Sí | Sí en dev/sit/uat | Sí en dev/sit/uat | Deny |
| **Responsable CI** | Sí | Controlado | Sí | Sí (Técnico) | Sí (Autorizado) | Deny |
| **Líder QA** | No requerido | No requerido | No | Sí en uat/staging/main | No | Deny |
| **Líder Soporte** | Sí | Controlado | Sí | Sí en staging/main | Sí en staging/main | Deny |
| **Dueño Producto** | No requerido | No requerido | No | Sí en main (Negocio) | No | Deny |

---

## 9. Protocolo de Emergencia: Hotfix

El flujo `hotfix/*` es la única vía autorizada para atender incidentes productivos de código.

**Criterios de activación:**
1. Existe un "Bug Productivo" registrado y clasificado con severidad crítica/alta.
2. Existe autorización formal del Líder de Soporte y Líder de Desarrollo.

**Ruta de ejecución obligatoria:**
1. La rama `hotfix/[id]-[descripcion]` nace a partir del último tag estable en `main`.
2. El desarrollador ejecuta la corrección y crea un PR directo hacia `staging` para validación y pruebas de regresión.
3. Una vez certificado en Staging, se crea un PR desde `hotfix/*` hacia `main` para liberación productiva.
4. **Sincronización:** Tras liberar en `main`, el código del hotfix **debe integrarse de vuelta a `dev`** vía PR para asegurar que los futuros desarrollos contengan la corrección.

---

## 10. Restricción Operativa: Cherry-Pick

La técnica de *Cherry-Pick* (mover commits aislados entre ramas) **no forma parte del flujo de promoción estándar**. Su uso indiscriminado rompe la trazabilidad de CMMI y genera divergencias entre ambientes.

**Excepciones:**
Solo se permite bajo la aprobación explícita del Líder de Desarrollo para extraer código de ramas trabadas, documentando detalladamente en el Work Item el motivo de la evasión del flujo natural por PR.

---

## 11. Checklist de auditoría de configuración

- [ ] Todas las ramas permanentes tienen el *Force Push* y *Bypass policies* en "Deny".
- [ ] La política *Check for linked work items* está activa como obligatoria en todas las ramas permanentes.
- [ ] Las aprobaciones mínimas están configuradas según el ambiente destino.
- [ ] El *Build validation* está vinculado a las ramas correspondientes asegurando que el código compila antes de integrarse.
- [ ] El equipo domina el protocolo *Hotfix* y la obligatoriedad de sincronizar cambios hacia *Dev* tras una emergencia.

