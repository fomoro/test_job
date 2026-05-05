# PROMPT: A2. Modelo de Integración Objetivo

CREA UN DIAGRAMA DE ARQUITECTURA EJECUTIVO CON LAS SIGUIENTES ESPECIFICACIONES:

**TÍTULO:** "Modelo de Integración Objetivo - To-Be (Flujo de Protección)"  
**ORIENTACIÓN:** Horizontal (16:9)  
**FONDO:** Blanco  

**ESTILO GENERAL:**  
Diagrama de flujo lógico, lineal y limpio (de izquierda a derecha).  
Debe demostrar cómo una solicitud se gobierna y desacopla antes de llegar al Core Legacy.  
Contraste absoluto con las integraciones punto a punto del estado actual.

---

**ESTRUCTURA VISUAL Y FLUJO PRINCIPAL:**

Representar una petición desde una sucursal en un flujo estricto:

**1. ORIGEN (Fuera de la nube)**
- **Consumidor:** Icono usuario. Etiqueta: "Sucursal (30%)".

**2. ZONA MODERNA (Contenedor con borde azul, etiqueta superior: "Microsoft Azure")**
- **API Gateway:** Rectángulo azul (#0072C6). Etiqueta interna: "Único punto de entrada".
- **Servicio de Dominio:** Rectángulo azul claro. Etiqueta: "Servicio de Indemnizaciones (Nuevo)". Etiqueta pequeña: "Lógica de negocio / contrato".
- **Capa Anticorrupción (ACL):** Rectángulo naranja (#FBC02D). Etiqueta: "ACL - Capa Anticorrupción". Etiquetas pequeñas: "Traduce y aísla" / "Boundary del legacy".

**3. ZONA LEGACY (Contenedor con borde gris, etiqueta superior: "On-Premise / Legacy")**
- **Core Legacy 🔴:** Rectángulo gris oscuro. Etiqueta pequeña: "Capa de Aplicación".
- **Base de Datos:** Cilindro gris claro. Candado visible 🔒 (discreto pero claro). Etiqueta: "Sybase".

---

**CONEXIONES (REGLAS ESTRICTAS):**

- Todas las flechas son unidireccionales hacia la derecha (request).
- Respuesta implícita (no dibujar flechas de retorno para evitar ruido visual).
- Mismo grosor para todas las líneas.

Flujo obligatorio (Izquierda a Derecha):
1. Sucursal → API Gateway 
2. API Gateway → Servicio de Indemnizaciones 
3. Servicio de Indemnizaciones → ACL 
4. ACL → Core Legacy (Debe apuntar estrictamente a la Aplicación, NO a la Base de Datos).
5. Core Legacy → Sybase (Línea interna discreta).

**PROHIBICIONES ABSOLUTAS:**
- NO debe existir ninguna línea desde Sucursal hacia Core Legacy.
- NO debe existir ninguna línea externa (ni siquiera desde la ACL) hacia Sybase. La base de datos solo puede ser tocada por su propia aplicación.
- No incluir bifurcaciones. El flujo es 100% lineal.

---

**MENSAJE VISUAL:**

Debe quedar claro sin explicación:
- La sucursal ya no toca el Core directamente.
- El Core queda protegido por la barrera ACL.
- La base de datos queda estrictamente encapsulada (se elimina el antipatrón).
- Toda solicitud se resuelve primero en la nube a través de un servicio moderno.
- Ningún sistema accede a datos fuera de su dominio; toda interacción pasa por la integración.

---

**LEYENDA (mínima, esquina inferior derecha):**

- → Flecha: Flujo gobernado
- 🔒 Candado: Base de datos aislada (Cero acceso externo)
- 🟧 ACL: Aislamiento del legacy

---

**VALIDACIÓN FINAL:**

El diagrama es correcto si:
- El flujo es lineal (izquierda a derecha) y se entiende en menos de 10 segundos.
- La ACL es visible y actúa como boundary del legacy, comunicándose SOLAMENTE con la aplicación del Core.
- El "Servicio de Indemnizaciones" demuestra el desacoplamiento operativo y la lógica de negocio.
- No hay accesos directos al Core ni a Sybase desde el exterior.