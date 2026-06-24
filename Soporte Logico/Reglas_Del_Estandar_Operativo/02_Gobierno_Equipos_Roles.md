# 02 - Gobierno de Equipos, Roles y Accesos

## 1. Objetivo práctico

Definir las directrices de gobierno para la configuración de usuarios, equipos centrales, matrices de permisos mínimos y administración segura de tokens dentro de Azure DevOps, asegurando el cumplimiento de los controles de auditoría exigidos por el modelo operativo CMMI.

---

## 2. Estructura de equipos en Azure DevOps

El proyecto implementa un modelo de bajo acoplamiento visual y operativo. Se crean exclusivamente dos equipos base dentro de la configuración del proyecto:

```text
[Nombre del Proyecto]
├── Team Desarrollo
└── Team Soporte

```

**Restricciones explícitas de configuración:**

* **Prohibido crear un "Team QA" o "Board QA":** El rol de Aseguramiento de Calidad (QA) opera de manera orgánica y transversal dentro de las células existentes, participando en los tableros de Desarrollo y Soporte según corresponda.

---

## 3. Matriz de usuarios y roles (Ejemplo Académico)

Para mantener la consistencia y la trazabilidad de los ejemplos prácticos en todo el ecosistema, se establece la siguiente distribución oficial de identidades y responsabilidades:

| Persona | Usuario sugerido | Equipo asignado | Rol formal |
| --- | --- | --- | --- |
| **Goku** | goku.dev@laboratorio.local | Team Desarrollo | Desarrollador |
| **Vegeta** | vegeta.leaddev@laboratorio.local | Team Desarrollo | Líder de Desarrollo |
| **Bulma** | bulma.ci@laboratorio.local | Team Desarrollo | Responsable de Integración Continua (CI) |
| **Trunks** | trunks.sonar@laboratorio.local | Team Desarrollo | Responsable Sonar / Calidad Estática |
| **Piccolo** | piccolo.qa@laboratorio.local | Integrado (Desarrollo / Soporte) | Analista QA |
| **Gohan** | gohan.leadqa@laboratorio.local | Integrado (Desarrollo / Soporte) | Líder QA |
| **Krillin** | krillin.support@laboratorio.local | Team Soporte | Analista de Soporte |
| **Ten Shin Han** | tenshinhan.leadsupport@laboratorio.local | Team Soporte | Líder de Soporte |
| **Maestro Roshi** | roshi.scrum@laboratorio.local | Transversal | Scrum Master / Facilitador |
| **Freezer** | freezer.po@laboratorio.local | Transversal / Producto | Dueño del Producto (PO) |
| **Androide 18** | androide18.jefeba@laboratorio.local | Transversal / Producto | Jefe de Análisis de Negocio (Jefe BA) |
| **Videl** | videl.ba@laboratorio.local | Transversal / Producto | Analista de Negocio (Analista BA) |

---

## 4. Niveles de acceso (Access Levels) y aprovisionamiento

El aprovisionamiento de identidades se realiza de manera centralizada en la plataforma.

**Ruta de administración:**

```text
Organization settings ──> Users ──> Add users

```

Al invitar o dar de alta a cada usuario, se debe asignar estrictamente el nivel de acceso requerido para su función técnica:

| Rol de la Suite | Nivel de acceso en Azure DevOps |
| --- | --- |
| Desarrollo, Soporte, CI, Sonar, QA, BA, Scrum Master | **Basic** (Permite edición de Work Items, Repos y Pipelines) |
| QA especializado con uso de Azure Test Plans | **Basic + Test Plans** (Requerido para ejecución avanzada de pruebas) |
| Dueño del Producto (PO) | **Stakeholder** o **Basic** (Según necesidad específica de edición en el Backlog) |

**Regla de control:** El acceso *Stakeholder* se limita a funciones de consulta, priorización o validaciones comerciales simples. El acceso *Basic* se reserva para la ejecución de actividades técnicas y operativas sobre el ciclo de vida del software.

---

## 5. Matriz de permisos mínimos por rol

Se aplica el principio de mínimo privilegio. Queda estrictamente prohibido otorgar permisos administrativos globales (*Project Administrators*) a roles operativos.

| Rol Funcional | Boards | Repositorios (Repos) | Pipelines (Build/Release) | Configuración/Admin |
| --- | --- | --- | --- | --- |
| **Desarrollador** | Editar Work Items asignados | Contribute (Solo ramas temporales) | Ejecutar si aplica | No |
| **Líder Desarrollo** | Editar flujo de Desarrollo | Contribute + Aprobar Pull Requests | Lectura y ejecución | Gestión de políticas técnicas |
| **Responsable CI** | Lectura / Edición técnica | Lectura general | Crear, editar y ejecutar pipelines | Gestión de entornos y agentes |
| **Responsable Sonar** | Lectura | Lectura general | Editar análisis técnicos | Configuración de SonarQube / SonarCloud |
| **Analista Soporte** | Crear y editar Issues | Lectura general | Ejecutar si aplica | No |
| **Líder Soporte** | Administrar flujo de Soporte | Lectura general | Aprobar o ejecutar CD productivo | Configuración de colas de soporte |
| **Analista QA** | Registrar validaciones de QA | Lectura general | Lectura general | No |
| **Líder QA** | Controlar evidencias de cierre | Lectura general | Lectura general | Administración de planes de prueba |
| **Scrum Master** | Consultar y ajustar tableros | Lectura opcional | Lectura general | Gestión de procesos y cadencias |
| **Dueño Producto** | Crear/Editar Features y Requirements | Sin acceso o lectura básica | No | No |
| **Jefe BA** | Revisar calidad funcional del backlog | Sin acceso o lectura básica | No | No |
| **Analista BA** | Crear Requirements, criterios y BDD | Sin acceso | No | No |

---

## 6. Gobierno funcional del Backlog (División BA / PO / QA)

El diseño funcional de los requerimientos sigue una cadena de custodia estricta para asegurar que el desarrollo responda con precisión a las necesidades del negocio:

* **Dueño del Producto (PO):** Máxima autoridad sobre el negocio. Prioriza el valor, define el alcance macro y aprueba el orden secuencial del backlog.
* **Jefe BA:** Gobierna y audita la calidad funcional del backlog. Asegura que los requerimientos cumplan con la estructura formal antes de los ritos de refinamiento.
* **Analista BA:** Responsable del levantamiento de información en el frente de trabajo. Construye las Historias de Usuario, define los criterios de aceptación y redacta los escenarios BDD en español.
* **QA:** Entidad de certificación inalienable. Valida de forma objetiva la entrega técnica contra los criterios de aceptación y escenarios BDD previamente estructurados.

---

## 7. Gobierno de tokens, secretos y automatizaciones

### 7.1 Conexiones de servicio (Service Connections)

* Todas las integraciones con nubes, herramientas de calidad estática o plataformas externas deben ejecutarse mediante **Service Connections**, utilizando *Service Principals*, *Managed Identities* o identidades técnicas controladas.
* **Regla no negociable:** Los pipelines de construcción (CI) y despliegue (CD) jamás deben depender, estar enlazados o autenticarse mediante el token de acceso personal de un usuario humano.

### 7.2 Fichas de acceso personal (Personal Access Token - PAT)

El uso de PAT se cataloga como una medida excepcional y temporal, restringida estrictamente a interacciones desde entornos locales (Git CLI) o herramientas de diagnóstico autorizadas explícitamente por el administrador.

**Políticas de control para el uso de PAT:**

1. **Prohibición de Full Access:** Ningún PAT operativo o de desarrollo puede crearse con el alcance máximo (*Full Access*). Se deben seleccionar detalladamente los alcances mínimos necesarios (ej. *Code Read/Write*).
2. **Ciclo de vida restrictivo:** La vigencia máxima admitida para cualquier PAT dentro del laboratorio es de **30 días calendario**.
3. **Secreto absoluto:** Queda estrictamente prohibido almacenar, registrar o adjuntar un PAT en archivos de código fuente, páginas de Wiki internas, evidencias de cierre de tareas o correos electrónicos.
4. **Asociación de identidad:** Al ser credenciales vinculadas directamente al perfil de un usuario, el administrador del proyecto auditará periódicamente los tokens activos para validar su vigencia y justificación técnica.

---

## 8. Checklist de cumplimiento y cierre

* [ ] Todos los usuarios académicos se encuentran correctamente invitados al entorno Azure DevOps.
* [ ] Los niveles de acceso (*Access Level*) corresponden estrictamente al rol funcional de cada usuario.
* [ ] El *Team Desarrollo* y el *Team Soporte* están creados de manera independiente.
* [ ] Se verificó que **no exista** ningún equipo o tablero independiente denominado "Team QA".
* [ ] Los usuarios transversales de Producto (PO, Jefe BA, Analista BA) están configurados con los accesos correctos al backlog.
* [ ] La matriz de permisos mínimos se aplicó sobre los tableros, repositorios y líneas de pipelines.
* [ ] Se validó que las tareas automáticas utilicen conexiones de servicio e identidades de máquina, descartando el uso de PATs corporativos permanentes.
* [ ] El equipo comprende que los PATs autorizados no deben exceder los 30 días de vigencia ni poseer permisos globales.


---

# Ajuste complementario — Roles operativos reales para adopción Azure DevOps

## 1. Jefferson Contreras — Apoyo transversal técnico

Jefferson Contreras pertenece al área de **Desarrollo y Arquitectura** y opera como apoyo transversal técnico para Azure DevOps, SRE / Cloud, CI-CD, SonarQube y gobierno técnico.

Responsabilidades esperadas:

```text
- Acompañar la configuración técnica de proyectos Azure DevOps.
- Apoyar onboarding técnico de repositorios.
- Configurar o acompañar SonarQube / SonarCloud.
- Integrar Quality Gates en pipelines.
- Apoyar definición de evidencias técnicas.
- Acompañar configuración de ramas, políticas, pipelines y ambientes junto con los responsables correspondientes.
```

Límites explícitos:

```text
- No reemplaza al líder técnico del frente.
- No reemplaza la revisión técnica del Pull Request.
- No asume la responsabilidad primaria sobre la calidad del código implementado.
- No prioriza backlog de negocio.
- No reemplaza a Infraestructura en responsabilidades propias de operación, ambientes y continuidad.
```

## 2. Alexandra Castillo — Apoyo operativo de adopción Azure DevOps

Alexandra Castillo participa como apoyo operativo y documental para la adopción de Azure DevOps dentro del área de Desarrollo y Arquitectura.

Su trabajo se articula funcionalmente con Jefferson para asegurar orden, completitud básica y trazabilidad inicial de los Work Items.

Responsabilidades esperadas:

```text
- Apoyar la carga inicial de Historias de Usuario y bugs productivos.
- Revisar completitud básica de campos requeridos.
- Apoyar organización del backlog inicial.
- Ayudar a ubicar Work Items en proyecto y tablero correcto.
- Apoyar la trazabilidad documental de la adopción.
```

Límites explícitos:

```text
- No reemplaza a BA.
- No define criterios de aceptación.
- No prioriza negocio.
- No aprueba calidad funcional.
- No decide estimaciones técnicas.
```

## 3. Relación funcional Jefferson / Alexandra

```text
Jefferson coordina técnicamente la adopción Azure DevOps.
Alexandra apoya operativamente la carga, organización y trazabilidad.
Ambos se articulan dentro del área de Desarrollo y Arquitectura.
```

Esta relación debe entenderse como coordinación funcional de trabajo para la adopción operativa. Cualquier subordinación jerárquica formal debe ser definida por la organización.

## 4. Regla de responsabilidad sobre calidad del código

```text
El desarrollador responde por la calidad de su código.
El líder técnico responde por la revisión técnica y aprobación del cambio.
Jefferson habilita controles automatizados de calidad técnica.
SonarQube complementa, pero no reemplaza, la revisión técnica ni el Pull Request.
```
