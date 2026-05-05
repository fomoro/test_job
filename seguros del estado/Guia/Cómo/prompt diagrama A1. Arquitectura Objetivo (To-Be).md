# PROMPT: A1. Arquitectura Objetivo (To-Be)

CREA UN DIAGRAMA DE ARQUITECTURA EJECUTIVO CON LAS SIGUIENTES ESPECIFICACIONES:

**TÍTULO:** "Arquitectura Objetivo - To-Be"
**ORIENTACIÓN:** Horizontal (16:9)
**FONDO:** Blanco

**ESTILO GENERAL:**
Diagrama conceptual de alto nivel.
Debe transmitir orden, control y gobierno.
Contraste absoluto con el diagrama de integraciones actual (espagueti).

**TODAS LAS LÍNEAS:**
- Mismo grosor
- Sin variación
- Sin conexiones punto a punto

---

**ESTRUCTURA POR CAPAS (DE ARRIBA HACIA ABAJO):**

**1. CAPA DE CONSUMO (superior)**
- Oficina Principal (70%)
- Sucursales (30%)
- Sistemas externos (opcional)
- Representados como iconos simples de usuario.

---

**MARCO ENVOLVENTE (ZONA CLOUD):**
- Agrupar las capas 2 y 3 dentro de un gran recuadro con borde sutil azul.
- Etiqueta superior del recuadro: "Microsoft Azure - Landing Zone"

---

**2. CAPA DE INTEGRACIÓN (centro - elemento más importante)**
Rectángulo ancho, destacado que divida a los usuarios de los sistemas:
- Texto principal: "API Gateway + Eventos + ACL"
- Color fondo: azul muy claro (#E6F2FF)
- Borde: azul fuerte (#0072C6)
- Etiquetas internas pequeñas: "Único punto de acceso" / "Gobierno de integraciones"

---

**3. CAPA DE SERVICIOS / SISTEMAS (debajo de integración)**
Cada sistema representado como un CONTENEDOR con borde punteado.
Dentro de cada contenedor:
- Aplicación (rectángulo superior)
- Base de datos (cilindro inferior)
- **OBLIGATORIO:** Un icono de candado (🔒) visible sobre cada cilindro para indicar encapsulamiento.
- Conexión interna (línea gris claro app-bd)

**Sistemas a distribuir:**
- Core Legacy 🔴 (gris oscuro)
- ERP Tercero (gris medio)
- App Interna 1, 2, 3 (azul)
- Sistema Tercero B (sin base de datos)

*IMPORTANTE:* Las bases de datos están VISUALMENTE encapsuladas dentro del sistema. No salen del contenedor. No se dibuja una capa de datos separada.

---

**CONEXIONES (REGLAS ESTRICTAS):**
- Consumidores → Capa de Integración
- Capa de Integración → Aplicaciones de los Sistemas
- Sistemas → Capa de Integración (respuesta)

**PROHIBIDO:**
- Sistema ↔ Sistema directo
- Sistema → Base de datos de otro sistema
- Consumidor → Sistema directo
- Consumidor → Base de datos

---

**LEYENDA (mínima, esquina inferior derecha):**
- Línea gris: Comunicación gobernada
- 🔒 Base de datos: Encapsulada (Acceso restringido)
- 🟦 Integración: Punto único de comunicación

---

**VALIDACIÓN FINAL:**
El diagrama es correcto si:
- La capa de integración es el centro visual absoluto que ataja todo el tráfico.
- No existen líneas punto a punto.
- Los candados son visibles en todas las bases de datos.
- El marco de Azure contiene todo el backend.