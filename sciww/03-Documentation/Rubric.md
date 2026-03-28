
# Rúbrica de Requerimientos Técnicos

Este documento detalla cómo se abordó cada punto solicitado en la evaluación.

### [cite_start]1. Conceptos OOP (01-OOP-Fundamentals) [cite: 1, 6]
* [cite_start]**Herencia**: Implementada mediante la clase `CreditCardPayment` que extiende de la clase base `Payment`[cite: 1].
* [cite_start]**Polimorfismo**: Uso de métodos `virtual` y `override` para especializar el comportamiento del método `Process()`[cite: 3, 6].
* [cite_start]**Encapsulación**: Protección del campo `_amount` mediante una propiedad de solo lectura con modificador de acceso privado[cite: 2].
* [cite_start]**Sobrecarga**: Método `Process()` definido con múltiples firmas para soportar pagos directos o en cuotas[cite: 4, 5].
* [cite_start]**Constructor**: Inicialización obligatoria del estado del objeto mediante el constructor de la clase base[cite: 1].

### 2. REST API Development (Invoices)
* **Endpoint 1 (POST):** Validación exhaustiva de `Id`, `AccountId`, `Description`, `Total` y `TaxPercentage`.
* **Endpoint 2 (POST):** Sumatoria de totales utilizando LINQ y lógica de deduplicación basada en el identificador único de factura.
* **Endpoint 3 (POST):** Cálculo preciso de monto de impuestos y gran total.
* **Bonus:** Implementación de **Inyección de Dependencias (DI)** para desacoplar la lógica de negocio de los controladores.

### 3. Console Application (File Processing)
* **Entrada:** Lectura de archivo `.txt` línea por línea.
* **Lógica:** Algoritmo de suma de dígitos individuales y verificación de múltiplos de 3.
* **Salida:** Generación de un nuevo archivo de texto con los resultados detallados por línea.

