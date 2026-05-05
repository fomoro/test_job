# Guía de Anexos – Solución de Arquitectura (EL CÓMO)

**Objetivo:** Construir un contraste visual absoluto entre el estado actual (caos) y el estado objetivo (gobierno, control y desacoplamiento).  
Cada anexo debe comunicar su mensaje en menos de 10 segundos.

---

## A1. Arquitectura Objetivo (To-Be)

**Formato:** Diagrama de arquitectura de alto nivel (conceptual)

**Cómo:**
- Azure como **Landing Zone central (hub)**
- Capa de integración en el centro (API Gateway + eventos + ACL)
- Sistemas (Core Legacy, ERP, Apps) conectados únicamente a la capa de integración
- Bases de datos encapsuladas dentro de su dominio (no accesibles directamente)
- No existen conexiones directas entre aplicaciones y bases de datos externas
- Flujo siempre: sistema → integración → sistema

**Regla visual obligatoria:**
- Todas las líneas convergen en la capa de integración
- No hay líneas punto a punto

**Objetivo:**
Evidenciar control total del ecosistema, eliminación del espagueti y gobierno centralizado de integraciones y datos.

---

## A2. Modelo de Integración Objetivo

**Formato:** Diagrama de flujo lógico / secuencia

**Cómo:**
- Representar un flujo real (ej. sucursal consultando información)
- Secuencia obligatoria:
  - Consumidor → API Gateway → ACL → Servicio → Sistema destino
- La ACL traduce y protege la interacción con el Core Legacy
- No existen accesos directos a bases de datos

**Regla visual obligatoria:**
- El flujo es lineal, claro y sin bifurcaciones caóticas
- El API Gateway es el único punto de entrada

**Objetivo:**
Demostrar el blindaje del Core Legacy y cómo la integración controla todas las interacciones.

---

## A3. Topología Cloud / Datos (To-Be)

**Formato:** Diagrama de bloques (separación lógica)

**Cómo:**
- Azure como núcleo
- Separación clara en dos zonas:
  - Zona transaccional (sistemas + bases de datos protegidas)
  - Zona analítica (consolidación de datos)
- Flujo unidireccional:
  - Sistemas → integración → capa analítica
- No existe acceso directo a bases de datos transaccionales

**Regla visual obligatoria:**
- Las bases de datos están encapsuladas
- La analítica está desacoplada
- No hay consultas cruzadas entre sistemas

**Objetivo:**
Visualizar la eliminación de silos y la habilitación de una visión unificada sin afectar la operación 24/7.

---

## A4. Racionalización de Aplicaciones

**Formato:** Matriz de transición (As-Is vs To-Be)

**Cómo:**
- Listar sistemas actuales (los del A1 del QUÉ)
- Asociar cada uno a:
  - Servicio objetivo (si aplica)
  - Estado:
    - Mantener
    - Migrar
    - Retirar
- Identificar explícitamente duplicidades (Indemnizaciones, Suscripción)

**Regla visual obligatoria:**
- Flechas de transformación (→)
- Reducción visible de cantidad de sistemas

**Objetivo:**
Evidenciar reducción del TCO, simplificación del ecosistema y eliminación de redundancias.

---

## A5. Roadmap Visual

**Formato:** Línea de tiempo por fases

**Cómo:**
Dividir en tres fases:

- **Corto plazo:**
  - Implementación capa de integración
  - Eliminación de accesos directos a bases de datos

- **Mediano plazo:**
  - Consolidación de datos
  - Integración progresiva de sistemas

- **Largo plazo:**
  - Racionalización y apagado de sistemas duplicados
  - Evolución del Core

**Regla visual obligatoria:**
- Secuencia clara de izquierda a derecha
- Sin sobrecarga de texto
- Hitos visibles

**Objetivo:**
Transmitir control, progresividad y cero riesgo de Big Bang.

---

## 💡 Reglas de Oro – Anexos (To-Be)

1. **80% visual, 20% texto:** El mensaje debe entenderse en menos de 10 segundos  
2. **El orden comunica:** Simetría, limpieza y jerarquía visual  
3. **Foco en desacoplamiento:** Cómo se comunican los sistemas y cómo se protegen los datos  
4. **Sin punto a punto:** Todas las conexiones pasan por la capa de integración  
5. **Consistencia con EL QUÉ:** Mismos nombres de sistemas, misma semántica  
6. **Sin ruido técnico:** No incluir detalles irrelevantes (IPs, tamaños, configs)

---

## Validación Final

Los anexos son correctos si:

- El contraste con el estado actual es evidente sin explicación
- La capa de integración es el centro visual
- No existen accesos directos a bases de datos
- Los sistemas están desacoplados
- El flujo es controlado y gobernado
- La arquitectura transmite orden, no complejidad