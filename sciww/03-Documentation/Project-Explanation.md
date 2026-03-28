# Explicación del Proyecto

### Resumen Ejecutivo
El proyecto demuestra la capacidad de transformar requerimientos técnicos en una solución de software organizada, escalable y fácil de mantener. Se aplicaron principios de arquitectura limpia para separar la recepción de datos de la lógica de negocio.

### ¿Qué se hizo?

**1. Fundamentos de Lógica (OOP)**
Se creó un modelo de simulación de pagos. La importancia de esto radica en la **reutilización de código**: la clase padre maneja la estructura general de un pago, mientras que las clases hijas se encargan de las reglas específicas (como autorizar una tarjeta), evitando duplicidad de lógica.

**2. Sistema de Gestión de Facturas (API)**
Se desarrolló un servicio Web centralizado para procesar facturas. 
* **Validación Inteligente:** Antes de procesar cualquier dato, el sistema verifica que la información sea íntegra (ej. que no existan montos negativos).
* **Procesamiento Masivo:** Utilizando LINQ, el sistema puede recibir cientos de facturas y limpiar automáticamente los duplicados antes de entregar un reporte financiero exacto.

**3. Procesador Automático de Datos (Consola)**
Se construyó una herramienta para automatizar tareas repetitivas de lectura de archivos. 
* El programa toma un archivo de texto con números extensos.
* Realiza un análisis matemático de los dígitos (suma y divisibilidad).
* Genera un reporte final indicando el resultado de cada operación, ideal para auditoría de datos planos.

### Arquitectura y Calidad
Para este proyecto, prioricé el **Clean Code**. La lógica no está "atrapada" en los archivos principales, sino que reside en servicios independientes. Esto permite que el sistema crezca sin volverse caótico y facilita enormemente la creación de pruebas automatizadas en el futuro.
