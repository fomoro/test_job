# 08 - Estrategia de Pipelines y Ambientes (CI/CD)

## 1. Objetivo práctico

Definir la arquitectura y operación de los pipelines de Integración Continua (CI) y Despliegue Continuo (CD), la topología de ambientes y la gestión de variables y secretos dentro de Azure DevOps, desacoplando esta responsabilidad de las definiciones de arquitectura de código.

---

## 2. Reglas rectoras de despliegue

- Prohibido realizar despliegues de artefactos empaquetados manualmente desde estaciones de trabajo locales.
- Prohibido promover código hacia un ambiente superior sin la validación previa del ambiente anterior.
- Todo artefacto desplegado debe poseer una versión explícita y trazable a un build específico.
- Ninguna liberación productiva se cierra sin evidencia de artefacto, validación de ambiente y aprobación formal en el Work Item.

---

## 3. Topología de Ambientes

El ecosistema implementa cinco ambientes lógicos y físicos, estrictamente mapeados a las ramas permanentes del repositorio.

**Ruta en Azure DevOps:**
`Pipelines ──> Environments ──> New environment`

| Ambiente | Rama Origen | Propósito |
|---|---|---|
| **Dev** | `dev` | Entorno de desarrollo para verificación técnica. |
| **SIT** | `sit` | Pruebas de integración de sistemas (System Integration Testing). |
| **UAT** | `uat` | Pruebas funcionales y de aceptación (User Acceptance Testing). |
| **Staging**| `staging` | Entorno pre-productivo para validación final o de emergencias (hotfix). |
| **Prod** | `main` | Entorno de Producción. |

---

## 4. Estructura Mínima de Pipelines

Cada componente de software (API, Web, Worker, etc.) debe contar, como mínimo, con la siguiente configuración:

**1. Pipeline CI (Integración Continua):**
`CI - [NombreProyecto].[Componente]`
- Restaura dependencias del proyecto.
- Compila la solución validando la integridad del código.
- Ejecuta pruebas unitarias o de integración automatizadas (si aplican).
- Ejecuta el análisis de calidad estática integrado con SonarQube.
- Empaqueta y publica el artefacto versionado.
- *Regla de bloqueo:* Si la compilación, las pruebas o el Quality Gate fallan, el pipeline se aborta impidiendo la publicación del artefacto.

**2. Pipeline CD (Despliegue Continuo):**
`CD - [NombreProyecto].[Componente]`
- Consume de manera automática o manual el artefacto certificado por el CI.
- Ejecuta las tareas de liberación técnica sobre los servidores o servicios de nube mapeados a cada ambiente.

---

## 5. Estandarización de Artefactos Versionados

El empaquetado del software (artefacto) debe ser autónomo y auto-descriptivo, garantizando que los equipos de soporte y operaciones reconozcan su origen.

**Formato obligatorio de nomenclatura:**
`[Repositorio]-[version]-[buildId]`

**Ejemplo correcto:**
`ApiLaboratorio-2.3.0-20260522.1`

*Restricción:* Quedan estrictamente prohibidos los nombres genéricos como `latest.zip`, `api-final.zip`, `release.zip` o `ultimo.zip`.

---

## 6. Aprobaciones de Despliegue por Ambiente (Pre-deployment Approvals)

Para garantizar la segregación de funciones y el control de cambios, los pipelines de CD en Azure DevOps deben configurarse con bloqueos de aprobación antes de inyectar código en los ambientes superiores:

- **Dev:** Responsable CI / Líder Desarrollo.
- **SIT:** Líder Desarrollo / Responsable CI.
- **UAT:** Dueño del Producto / Líder QA.
- **Staging:** Líder QA / Líder Soporte.
- **Prod:** Líder Soporte / Dueño del Producto.

*Nota de auditoría:* Todas las aprobaciones o rechazos quedan registrados con estampa de tiempo en el historial nativo de Azure DevOps como evidencia inmutable.

---

## 7. Gestión de Variables, Secretos y Conexiones

### 7.1 Grupos de Variables (Variable Groups)
La configuración de infraestructura, URLs o parámetros dependientes del entorno no debe residir en el código fuente. Se administrarán desde Azure DevOps mediante *Variable Groups* mapeados por ambiente:
- `vg-[proyecto]-dev`
- `vg-[proyecto]-sit`
- `vg-[proyecto]-uat`
- `vg-[proyecto]-staging`
- `vg-[proyecto]-prod`

### 7.2 Protección de Secretos
- Cadenas de conexión a base de datos, tokens externos y contraseñas deben registrarse obligatoriamente como *Secret Variables* (habilitando el candado de encriptación) o, idealmente, integrarse con Azure Key Vault.
- Se prohíbe exponer secretos imprimiéndolos en los logs de consola de los pipelines.

### 7.3 Conexiones de Servicio (Service Connections)
Las conexiones autorizadas para ejecutar el despliegue hacia recursos externos (ej. servidores, Azure App Service, contenedores) deben implementarse siempre a través de *Service Connections* que utilicen Service Principals o Managed Identities de Azure.

---

## 8. Gestión de Liberaciones (Release Request)

Todo despliegue hacia **UAT, Staging o Producción** debe contar con un paraguas de trazabilidad a través de un `Change Request` o `Issue` categorizado con la etiqueta `release-request`.

**Información requerida para respaldar el paso a producción:**
- Número de la versión a liberar.
- Rama de origen y ambiente de destino.
- Nombre exacto del artefacto que será desplegado.
- Lista de IDs de los Work Items (Requirements/Bugs) incluidos en el empaquetado.
- Aprobadores formales involucrados.

---

## 9. Protocolos de Fallo y Rollback

**Gestión ante fallos de despliegue:**
Si un pipeline CD falla o degrada un ambiente, la promoción se interrumpe de inmediato. Se debe registrar el evento, ejecutar la corrección en la rama de origen (`feature` o `bugfix`), generar un nuevo PR, y detonar el flujo CI/CD completo.

**Ejecución de Rollback Productivo:**
La reversión de un despliegue en producción es un acto de emergencia controlado:
1. Se identifica el artefacto de la versión estable previa en el historial del pipeline CD.
2. Se ejecuta el redespliegue de dicho artefacto sobre el ambiente de Producción.
3. Se documenta la acción en el Work Item original.
4. Se crea un nuevo ticket tipo "Bug Productivo" con el fin de iniciar el diagnóstico forense y la corrección de fondo.

---

# Ajuste complementario — Rol de Jefferson en CI/CD, ambientes y coordinación con Infraestructura

## 1. Alcance de Jefferson en CI/CD

Jefferson Contreras puede actuar como apoyo transversal técnico para configurar, acompañar o gobernar técnicamente pipelines, validaciones CI/CD, integración con SonarQube y evidencias técnicas dentro de Azure DevOps.

Su intervención puede incluir:

```text
- Acompañar la creación de pipelines CI.
- Integrar tareas de SonarQube / SonarCloud.
- Apoyar publicación de artefactos versionados.
- Apoyar evidencias técnicas de ejecución.
- Acompañar configuración de variables, ambientes y Service Connections junto con Infraestructura.
- Verificar que el pipeline refleje el flujo de ramas y ambientes definido.
```

## 2. Coordinación con Infraestructura / Operaciones

Jefferson no reemplaza la responsabilidad de Infraestructura / Operaciones sobre ambientes, continuidad, secretos, accesos, recursos cloud, disponibilidad y despliegues operativos.

```text
Jefferson apoya el gobierno técnico CI/CD.
Infraestructura conserva la responsabilidad operativa sobre ambientes y continuidad.
El líder técnico conserva la responsabilidad sobre el componente desplegado.
```

## 3. Matriz de responsabilidad CI/CD

| Tema | Responsable primario | Apoyo |
|---|---|---|
| Pipeline CI | Jefferson / Responsable CI / líder técnico | Desarrollo |
| Pipeline CD | Infraestructura + Jefferson según alcance | Líder técnico |
| Ambientes | Infraestructura / Operaciones | Jefferson |
| Service Connections | Infraestructura / SRE según política interna | Jefferson / líder técnico |
| Sonar en pipeline | Jefferson / Responsable Sonar | CI / Desarrollo |
| Artefacto versionado | Responsable CI / líder técnico | Jefferson |
| Evidencia de despliegue | Infraestructura / responsable de release | Jefferson / Soporte |

## 4. Regla de gobierno

```text
Ningún pipeline debe configurarse como esfuerzo aislado de SRE.
Debe existir articulación entre Jefferson, líder técnico del frente e Infraestructura cuando aplique.
```
