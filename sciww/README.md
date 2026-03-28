
# Invoice & Logic Assessment - Solution Architect

Este repositorio contiene la solución a una prueba técnica integral dividida en tres fases: fundamentos de Programación Orientada a Objetos (OOP), desarrollo de una REST API empresarial y una herramienta de procesamiento de archivos por consola.

## 📂 Estructura del Proyecto

```text
📂 InvoiceAssessment_Wolfan/
├── 📄 README.md                    # Explicación general del proyecto (portada)
├── 📄 .gitignore                   # Exclusión de archivos binarios (bin/obj)
├── 📂 01-OOP-Fundamentals/         # Fase 1: Conceptos base de C#
│   └── 📄 OOPConcepts.cs           # Implementación de Herencia, Polimorfismo, etc.
│
├── 📂 02-Invoice-Solution/         # Fase 2: Solución técnica principal
│   ├── 📄 InvoiceSystem.sln        # Solución única de Visual Studio
│   ├── 📂 Invoices.Api/            # REST API (Validación, Sumas y Taxes)
│   └── 📂 FileProcessor.Console/   # App de Consola (Procesamiento de TXT)
│
└── 📂 03-Documentation/            # Fase 3: Documentación de soporte
    ├── 📄 Rubric.md                # Mapeo de requerimientos vs solución
    └── 📄 Project-Explanation.md   # Explicación funcional del proyecto
```

## 🚀 Tecnologías Utilizadas
* **Lenguaje:** C# (.NET 8)
* **API:** ASP.NET Core Web API
* **Lógica:** LINQ (Language Integrated Query)
* **Arquitectura:** Inyección de Dependencias (DI) y Separación de Capas.

## 🛠️ Cómo ejecutar
1. Clonar el repositorio.
2. Abrir el archivo `.sln` en Visual Studio 2022 o VS Code.
3. Para la **API**: Establecer `Invoices.Api` como proyecto de inicio y ejecutar (F5).
4. Para la **Consola**: Establecer `FileProcessor.Console` como proyecto de inicio y ejecutar.
