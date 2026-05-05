# Diagnóstico de Arquitectura (EL QUÉ)

**Propósito:** Alinear contexto, problema y restricciones. NO propone soluciones.

---

## 0. Resumen Ejecutivo
*(Síntesis breve: contexto, problema y objetivo. Máx. 4–5 líneas)*
> **Ejemplo:** Seguros del Estado enfrenta el reto de gobernar un ecosistema de más de 30 aplicaciones fragmentadas (multicloud/multibase de datos). El objetivo es centralizar la integración y simplificar la operación para reducir costos y riesgos sin afectar la continuidad 24/7.

---

## 1. Enfoque del Problema
* **Tipo de reto:** _____________________________________________
* **Límites críticos (restricciones operativas/financieras):** _____________________________________________

---

## 2. Contexto General
* **Portafolio actual:** _____________________________________________
* **Procesos de negocio críticos:** _____________________________________________
* **Distribución de uso y actores impactados:** _____________________________________________
* **Gobierno y madurez:** _____________________________________________

---

## 3. Problema Estructural (Causa raíz)
*(Qué está mal realmente a nivel de diseño o estrategia)*
> **Ejemplo:** Ausencia de un gobierno arquitectónico centralizado y falta de estándares de integración, lo que ha permitido un crecimiento orgánico desordenado en silos tecnológicos.

---

## 4. Síntomas y Riesgos
* **Consecuencias observables (dolor actual):** _____________________________________________
* **Riesgos inminentes (qué pasa si no se actúa):** _____________________________________________

---

## 5. Complejidad Técnica
* **Entorno (nubes):** _____________________________________________
* **Datos (bases de datos):** _____________________________________________
* **Deuda / madurez tecnológica:** _____________________________________________

---

## 6. Objetivo del Negocio
*(Qué valor espera el negocio de TI)*
> **Ejemplo:** Consolidar una arquitectura escalable que permita la visión unificada de la información, reduzca el TCO (Total Cost of Ownership) y mejore la experiencia de usuario en sucursales.

---

## 7. Supuestos Clave para el Análisis
*(Condiciones base para defender el diseño)*
> **Ejemplo:** Se asume que las aplicaciones core no pueden tener ventanas de mantenimiento mayores a 2 horas y que la estrategia multicloud es una restricción de negocio a mediano plazo.

---

## 8. Conclusión del Diagnóstico
*(Cierre que conecta directamente con la fase de solución)*
> **Ejemplo:** El ecosistema es operativamente insostenible bajo el modelo actual. Se requiere una transición hacia una arquitectura orientada a servicios (SOA/Microservicios) con un gobierno de datos centralizado.

---

## Anexos

### A1. Mapa de Capacidades vs Aplicaciones

* **Formato:** Matriz de Calor (Heatmap) / Tabla.
* **Cómo:**
  - Filas: capacidades de negocio  
  - Columnas: aplicaciones  
  - Marcas: Usar colores para resaltar duplicidad.
* **Objetivo:** evidenciar duplicidad funcional.

### A2. Inventario de Aplicaciones
* **Formato:** Tabla estructurada con semáforos (Rojo/Amarillo/Verde).
* **Cómo:** Columnas de Sistema, Proceso, Criticidad, Nube, BD y Origen.
* **Objetivo:** Evidenciar el **desorden administrativo** y facilita la priorización técnica.

### A3. Topología Cloud / Datos (Estado Actual)
* **Formato:** Diagrama de Bloques (Arquitectura Conceptual).
* **Cómo:** 4 bloques de nubes (Azure, AWS, GCP, IBM) con aplicaciones y bases de datos por bloque  
* **Objetivo:** evidenciar complejidad multicloud.


### A4. Mapa de Integraciones (Espagueti)
* **Formato:** Diagrama de Red Punto a Punto (Caótico intencional).
* **Cómo:** Nodos interconectados de forma desordenada. 
* **Nota clave:** ausencia de API Gateway o bus de integración.
* **Objetivo:** evidenciar complejidad e inestabilidad en integraciones.


---

### 💡 Reglas de Oro para los Anexos
1.  **80% Visual, 20% Texto:** El jurado debe entender el problema en menos de 10 segundos.
2.  **Impacto sobre Estética:** Un diagrama "feo" que muestre el caos es mejor que uno "bonito" que lo oculte.
3.  **Evitar el Exceso:** No metas detalle técnico que no sume al diagnóstico del problema estructural.