# 09 - Estándar de Versionamiento Técnico

## 1. Objetivo práctico

Definir de manera estricta cómo se declara la base tecnológica de una solución y cómo se versiona un incremento de software, garantizando que exista congruencia absoluta entre el repositorio de código, los metadatos del proyecto y el artefacto finalmente desplegado.

Este estándar es de aplicación obligatoria para:
- Proyectos de nueva construcción (Principalmente ecosistema .NET).
- Proyectos heredados (*legacy*).
- APIs, aplicaciones web, servicios de *backend* y librerías internas.

---

## 2. Regla de congruencia inmutable

Para cumplir con la trazabilidad exigida por el modelo operativo, la versión del incremento de software debe ser idéntica y auditable en tres frentes simultáneos:

1. **Git:** En el nombre de la rama de liberación y en el *tag* del *commit*.
2. **Código fuente:** En los metadatos del proyecto compilable (ej. `.csproj` o `AssemblyInfo.cs`).
3. **Artefacto:** En la nomenclatura del empaquetado generado por el pipeline CI.

**Ejemplo de congruencia esperada:**
- **Rama transitoria:** `release/v2.3.0`
- **Tag en código:** `v2.3.0`
- **Metadato en proyecto:** `Version 2.3.0`
- **Nombre de artefacto:** `ApiLaboratorio-2.3.0-20260522.1`

---

## 3. Separación de conceptos: Producto vs. Tecnología

Es un error conceptual común mezclar la versión del negocio con la versión del marco de trabajo. El equipo técnico debe dominar la siguiente separación:

- `release/v2.3.0`: Rama temporal utilizada exclusivamente para preparar y estabilizar la entrega 2.3.0.
- `tag v2.3.0`: Marca inamovible en la historia de Git que congela el *commit* exacto que se liberó a producción.
- `<Version>2.3.0</Version>`: Versión comercial o funcional del producto/paquete que se está entregando.
- `<TargetFramework>net9.0</TargetFramework>`: Versión tecnológica del compilador o *framework* utilizado. No tiene relación directa con la versión del producto.

---

## 4. Lineamientos de Arquitectura y Tecnologías Base

### 4.1 Proyectos de nueva construcción
- **Backend / APIs:** Todo proyecto nuevo debe iniciarse por defecto utilizando la última versión de soporte a largo plazo (LTS) o estándar vigente (ej. **.NET 9**), salvo que exista una justificación arquitectónica formalmente aprobada para usar una versión distinta.
- **Frontend / Web:** Se prioriza el uso de renderizado del lado del servidor (ej. Razor Pages / MVC) por simplicidad operativa. La adopción de arquitecturas SPA (Single Page Application con Angular, React, Vue) exige una justificación técnica basada en alta interactividad del usuario.

### 4.2 Proyectos heredados (Legacy)
- Los proyectos existentes operan bajo el principio de no disrupción; se mantienen en su tecnología actual (ej. .NET Framework 4.x, WebForms, MVC antiguo).
- Una migración tecnológica no es un ajuste técnico de rutina. Debe gestionarse como una iniciativa independiente, con análisis de impacto, gestión de riesgos y un plan de despliegue controlado.

---

## 5. Implementación técnica del versionamiento

### 5.1 Versionamiento en proyectos modernos (SDK-style .csproj)
Aplica para .NET Core, .NET 5 a .NET 9, y librerías modernas. La versión se declara directamente en el archivo `.csproj`.

```xml
<PropertyGroup>
  <TargetFramework>net9.0</TargetFramework>
  <Version>2.3.0</Version>
  <FileVersion>2.3.0.0</FileVersion>
  <InformationalVersion>2.3.0</InformationalVersion>
</PropertyGroup>

```

**Explicación operativa:**

* `Version`: Define la versión de la entrega para empaquetado (ej. paquetes NuGet).
* `FileVersion`: Estampa la versión física en las propiedades del archivo compilado (`.dll` o `.exe`).
* `InformationalVersion`: Versión legible en texto plano, útil para diagnóstico, auditorías de seguridad y logs de soporte.

### 5.2 Versionamiento en proyectos heredados (.NET Framework Legacy)

Aplica para aplicaciones antiguas donde la configuración reside en el archivo `Properties/AssemblyInfo.cs`.

```csharp
[assembly: AssemblyVersion("2.3.0.0")]
[assembly: AssemblyFileVersion("2.3.0.0")]
[assembly: AssemblyInformationalVersion("2.3.0")]

```

*Regla práctica:* Para aplicaciones internas, el equipo de desarrollo debe mantener estos tres atributos alineados estrictamente con la versión funcional liberada.

---

## 6. Ciclo de vida de una liberación versionada

Para materializar una entrega (ej. versión `2.3.0`), el desarrollador debe ejecutar la siguiente secuencia sin alteraciones:

1. Crear la rama de estabilización desde `dev` o `staging`: `release/v2.3.0`.
2. Ajustar los metadatos en el código (`.csproj` o `AssemblyInfo.cs`) a `2.3.0`.
3. Integrar mediante Pull Request hacia la rama de validación pre-productiva (`staging`).
4. El pipeline CI genera el artefacto empaquetado y versionado: `MiApp-2.3.0-[buildId]`.
5. Se despliega en el ambiente correspondiente y el equipo de QA certifica.
6. Se aprueba la promoción hacia `main`.
7. Tras la integración en `main`, el Responsable CI o el pipeline automatizado genera el tag definitivo `v2.3.0` sobre ese *commit*.

---

## 7. Checklist de auditoría de versión

Antes de autorizar cualquier paso a producción, el Líder de Soporte y el QA deben verificar:

* [ ] La rama de origen utilizada para la entrega es explícita (ej. `release/vX.Y.Z`).
* [ ] El archivo de configuración del proyecto contiene la versión X.Y.Z declarada.
* [ ] El nombre del artefacto listado en Azure DevOps expone visualmente la versión X.Y.Z.
* [ ] El documento de liberación (Release Request) consolida y cruza la versión técnica y los Work Items implementados.
* [ ] Al finalizar el despliegue exitoso, se generó el *tag* de Git respectivo sobre la rama productiva.
